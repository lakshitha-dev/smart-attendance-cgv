"""Single Local DB gateway (AD-4): the ONLY module importing sqlite3.

`AttendanceRepository` is a cohesive class (OOP is a graded criterion) owning
every SQLite access. Design invariants (AD-4):

- The schema auto-creates on open (`ensure_schema`); no separate migration step.
- Attendance is upserted keyed (Student Index, Sheet Identifier) — re-processing
  updates, never duplicates.
- `resolved_by_operator` survives re-processing unless `overwrite=True`.
- Connections are per-operation via a context manager — no cached, global, or
  long-lived connections (Streamlit worker threads + concurrent CLI safety).
- The canonical 8-digit Student Index is the ONLY key form stored/queried; the
  short ordinal (`002`/`2`) is resolved by `resolve_student_index` — the ONE
  resolver — before any read/write. No adapter parses index forms itself.
- No image blobs: only signature-image *paths* are registered.
- One sheet's persistence (`persist_run`) is a SINGLE transaction (AD-12): a
  failure mid-persist rolls everything back — never partial state.

This module never imports a UI framework and never prints/exits (AD-6).
"""

import sqlite3
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path

from sams_core import config
from sams_core.errors import ProcessingError
from sams_core.models import AttendanceRecord, AttendanceStatus


class AttendanceRepository:
    """Cohesive gateway to the SAMS Local DB (AD-4)."""

    def __init__(self, db_path: Path | None = None):
        """`db_path` defaults to `config.DB_PATH`; injectable for headless tests."""
        self._db_path = Path(db_path) if db_path is not None else config.DB_PATH

    # --- Connection lifecycle -------------------------------------------------

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Per-operation connection: open, ensure schema, yield, commit/rollback, close.

        No connection is cached or shared — every call opens its own, so
        Streamlit worker threads and concurrent CLI runs never contend over one
        handle (AD-4). A busy writer is waited on up to the configured timeout;
        sqlite-level operational failures surface as `ProcessingError` (AD-6 —
        never a raw sqlite3 exception past the engine boundary).
        """
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path, timeout=config.DB_BUSY_TIMEOUT_S)
        conn.row_factory = sqlite3.Row
        try:
            self._ensure_schema(conn)
            yield conn
            conn.commit()
        except sqlite3.OperationalError as exc:
            conn.rollback()
            raise ProcessingError(f"Local DB unavailable: {exc}") from exc
        except BaseException:  # incl. KeyboardInterrupt: never leave a half-open tx
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _ensure_schema(conn: sqlite3.Connection) -> None:
        """Create the three tables if absent (idempotent). Glossary-verbatim columns.

        Key columns are NOT NULL explicitly: SQLite's TEXT PRIMARY KEY quirk
        would otherwise admit NULL keys that the upsert can never deduplicate.
        """
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_index TEXT NOT NULL PRIMARY KEY,
                no            TEXT,
                title         TEXT,
                name          TEXT
            );

            CREATE TABLE IF NOT EXISTS attendance (
                student_index        TEXT NOT NULL,
                sheet_id             TEXT NOT NULL,
                status               TEXT NOT NULL,
                subject_code         TEXT,
                subject_name         TEXT,
                session_time         TEXT,
                lecturer             TEXT,
                resolved_by_operator INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (student_index, sheet_id)
            );

            CREATE TABLE IF NOT EXISTS signature_images (
                student_index TEXT NOT NULL,
                sheet_id      TEXT NOT NULL,
                kind          TEXT NOT NULL,
                path          TEXT NOT NULL,
                PRIMARY KEY (student_index, sheet_id, kind)
            );
            """
        )

    def ensure_schema(self) -> None:
        """Public schema bootstrap (FR-15). Opening a connection already ensures it."""
        with self._connect():
            pass

    # --- Students -------------------------------------------------------------

    @staticmethod
    def _upsert_students(conn: sqlite3.Connection, students: Iterable) -> None:
        rows = [(s.index, s.no, s.title, s.name) for s in students]
        conn.executemany(
            """
            INSERT INTO students (student_index, no, title, name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_index) DO UPDATE SET
                no = excluded.no,
                title = excluded.title,
                name = excluded.name
            """,
            rows,
        )

    def upsert_students(self, students: Iterable) -> None:
        """Insert/update Student Records keyed on the canonical Student Index.

        Idempotent: re-processing the same roster updates in place, never
        duplicates. Accepts `StudentRecord`-shaped objects (no/index/title/name).
        """
        with self._connect() as conn:
            self._upsert_students(conn, students)

    def list_students(self) -> list[dict]:
        """All known Student Records (AD-4 read API), ordered by canonical index.

        (Ordering by `no` would sort TEXT lexicographically — "10" < "2" — and
        `no` is roster-relative, so the stable canonical index orders instead.)
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "SELECT student_index, no, title, name FROM students ORDER BY student_index"
            )
            return [dict(row) for row in cursor.fetchall()]

    def resolve_student_index(self, alias: str) -> str | None:
        """The ONE index resolver (AD-4): alias -> canonical 8-digit index or None.

        - An 8-digit form passes through unchanged (the canonical key).
        - A short ordinal (`002`, `2`) resolves via the rosters' `no` values.
          Ordinals are roster-relative: if the same ordinal maps to MORE THAN
          ONE student across the rosters ever ingested, the alias is ambiguous
          and resolves to None (a no-data outcome the frontends present with
          the valid-indices list) rather than an arbitrary student.
        - Anything unresolvable returns None — never raises (AD-6: unknown index
          is a no-data result, not an error).
        """
        if alias is None:
            return None
        candidate = alias.strip()
        if candidate.isascii() and candidate.isdigit() and len(candidate) == 8:
            return candidate
        if not (candidate.isascii() and candidate.isdigit()):
            return None
        with self._connect() as conn:
            rows = conn.execute("SELECT student_index, no FROM students").fetchall()
        matches = {
            row["student_index"]
            for row in rows
            if str(row["no"] or "").strip().isdigit() and int(row["no"]) == int(candidate)
        }
        return matches.pop() if len(matches) == 1 else None

    # --- Attendance -----------------------------------------------------------

    @staticmethod
    def _save_attendance(
        conn: sqlite3.Connection, records: Iterable[AttendanceRecord], overwrite: bool
    ) -> tuple[int, int]:
        """Upsert records on an open connection. Returns (saved, preserved)."""
        saved = preserved = 0
        for record in records:
            existing = conn.execute(
                "SELECT resolved_by_operator FROM attendance "
                "WHERE student_index = ? AND sheet_id = ?",
                (record.student_index, record.sheet_id),
            ).fetchone()
            if (
                existing is not None
                and existing["resolved_by_operator"] == 1
                and not overwrite
            ):
                # Preserve the operator's status + flag, but keep the row's
                # session metadata current (a corrected Info File must not
                # leave resolved rows carrying stale subject/session values).
                conn.execute(
                    "UPDATE attendance SET subject_code = ?, subject_name = ?, "
                    "session_time = ?, lecturer = ? "
                    "WHERE student_index = ? AND sheet_id = ?",
                    (
                        record.subject_code,
                        record.subject_name,
                        record.session_time,
                        record.lecturer,
                        record.student_index,
                        record.sheet_id,
                    ),
                )
                preserved += 1
                continue
            conn.execute(
                """
                INSERT INTO attendance (
                    student_index, sheet_id, status, subject_code,
                    subject_name, session_time, lecturer, resolved_by_operator
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_index, sheet_id) DO UPDATE SET
                    status = excluded.status,
                    subject_code = excluded.subject_code,
                    subject_name = excluded.subject_name,
                    session_time = excluded.session_time,
                    lecturer = excluded.lecturer,
                    resolved_by_operator = excluded.resolved_by_operator
                """,
                (
                    record.student_index,
                    record.sheet_id,
                    record.status.value,
                    record.subject_code,
                    record.subject_name,
                    record.session_time,
                    record.lecturer,
                    1 if record.resolved_by_operator else 0,
                ),
            )
            saved += 1
        return saved, preserved

    def save_attendance(
        self, records: Iterable[AttendanceRecord], overwrite: bool = False
    ) -> tuple[int, int]:
        """Upsert one Attendance Record per Student Record (AD-4).

        Overwrite semantics:
        - An existing row with `resolved_by_operator=1` and `overwrite=False`
          keeps the human's status and flag (re-processing never clobbers a
          hand resolution); its session metadata is still refreshed.
        - With `overwrite=True`, the row is replaced using the record's own
          `resolved_by_operator` value.
        - Re-processing updates in place, keyed (Student Index, Sheet Identifier)
          — never duplicates.

        Returns (saved, preserved) row counts so frontends can report honestly.
        """
        with self._connect() as conn:
            return self._save_attendance(conn, records, overwrite)

    def persist_run(
        self,
        students: Iterable,
        records: Sequence[AttendanceRecord],
        sheet_id: str,
        registrations: Sequence[tuple[str, str, str, str]] = (),
        overwrite: bool = False,
    ) -> tuple[int, int]:
        """Persist one processed sheet ATOMICALLY (AD-12): one transaction for
        the roster upsert, all attendance rows, and the signature-image
        registrations. A failure anywhere rolls the whole run back — the DB is
        never left with a roster but no attendance, or half the registrations.

        Stale `signature_images` rows for this sheet are cleared first (issued
        as the transaction's opening write, which also serializes concurrent
        writers): a re-run may produce fewer/renamed crops, and dangling paths
        from the previous run must not survive.

        Returns (saved, preserved) attendance row counts.
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM signature_images WHERE sheet_id = ?", (sheet_id,))
            self._upsert_students(conn, students)
            saved, preserved = self._save_attendance(conn, records, overwrite)
            conn.executemany(
                """
                INSERT INTO signature_images (student_index, sheet_id, kind, path)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_index, sheet_id, kind) DO UPDATE SET
                    path = excluded.path
                """,
                [(idx, sid, kind, str(path)) for idx, sid, kind, path in registrations],
            )
            return saved, preserved

    def _write_status(
        self,
        conn: sqlite3.Connection,
        sheet_id: str,
        student_index: str,
        status: AttendanceStatus,
        by_operator: bool,
    ) -> bool:
        """Shared write path for resolve/undo — updates status + operator flag in place.

        Subject/session metadata on the existing row is preserved (this is a
        status change on an already-persisted Attendance Record). Returns True
        when a row was actually updated — callers must not treat a zero-row
        UPDATE (typo'd index/sheet) as success.
        """
        cursor = conn.execute(
            "UPDATE attendance SET status = ?, resolved_by_operator = ? "
            "WHERE student_index = ? AND sheet_id = ?",
            (status.value, 1 if by_operator else 0, student_index, sheet_id),
        )
        return cursor.rowcount > 0

    def resolve(
        self,
        sheet_id: str,
        student_index: str,
        status: AttendanceStatus,
        by_operator: bool = True,
    ) -> bool:
        """Operator resolution of a Signature Cell (AD-4 write API).

        Sets the status and marks `resolved_by_operator` so re-processing without
        `overwrite=True` will not clobber it. Returns True if the row existed and
        was updated; False means nothing matched (typo'd sheet/index) and the
        caller must surface that — a silent no-op is not a resolution.
        """
        with self._connect() as conn:
            return self._write_status(conn, sheet_id, student_index, status, by_operator)

    def undo_resolution(self, sheet_id: str, student_index: str) -> bool:
        """Undo an operator resolution: restore Ambiguous and clear the flag (AD-4).

        Guarded on `resolved_by_operator = 1`: undoing a row that was never
        operator-resolved must not destroy the machine's Present/Absent verdict.
        Returns True if an operator resolution was actually undone.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE attendance SET status = ?, resolved_by_operator = 0 "
                "WHERE student_index = ? AND sheet_id = ? AND resolved_by_operator = 1",
                (AttendanceStatus.AMBIGUOUS.value, student_index, sheet_id),
            )
            return cursor.rowcount > 0

    def has_operator_resolutions(self, sheet_id: str) -> bool:
        """True if any row for this sheet carries an operator resolution (AD-4).

        Read pre-Process so the CLI/Web UI can warn before an overwrite.
        """
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM attendance "
                "WHERE sheet_id = ? AND resolved_by_operator = 1 LIMIT 1",
                (sheet_id,),
            ).fetchone()
        return row is not None

    def get_attendance(
        self, student_index: str | None = None, sheet_id: str | None = None
    ) -> list[AttendanceRecord]:
        """Read Attendance Records, optionally filtered by index and/or sheet.

        Joins the roster for the student name so each returned `AttendanceRecord`
        is self-describing (AD-2). Unknown index/sheet yields an empty list — a
        no-data result, not an error (AD-6).
        """
        query = (
            "SELECT a.student_index, a.sheet_id, a.status, a.subject_code, "
            "a.subject_name, a.session_time, a.lecturer, a.resolved_by_operator, "
            "s.name AS student_name "
            "FROM attendance a LEFT JOIN students s "
            "ON a.student_index = s.student_index"
        )
        conditions = []
        params: list = []
        if student_index is not None:
            conditions.append("a.student_index = ?")
            params.append(student_index)
        if sheet_id is not None:
            conditions.append("a.sheet_id = ?")
            params.append(sheet_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.sheet_id, a.student_index"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            AttendanceRecord(
                student_index=row["student_index"],
                student_name=row["student_name"] or "",
                sheet_id=row["sheet_id"],
                status=AttendanceStatus(row["status"]),
                subject_code=row["subject_code"],
                subject_name=row["subject_name"],
                session_time=row["session_time"],
                lecturer=row["lecturer"],
                resolved_by_operator=bool(row["resolved_by_operator"]),
            )
            for row in rows
        ]

    # --- Signature image paths (no blobs; AD-4/AD-10) -------------------------

    def register_signature_image(
        self, student_index: str, sheet_id: str, kind: str, path: str | Path
    ) -> None:
        """Register a signature-image *path* (probe crop or reference), keyed by kind.

        No image bytes are stored — only the filesystem path (AD-4/AD-10).
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signature_images (student_index, sheet_id, kind, path)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(student_index, sheet_id, kind) DO UPDATE SET
                    path = excluded.path
                """,
                (student_index, sheet_id, kind, str(path)),
            )

    def get_signature_image(
        self, student_index: str, sheet_id: str, kind: str
    ) -> str | None:
        """Return the registered path for (index, sheet, kind), or None if unregistered."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT path FROM signature_images "
                "WHERE student_index = ? AND sheet_id = ? AND kind = ?",
                (student_index, sheet_id, kind),
            ).fetchone()
        return row["path"] if row is not None else None
