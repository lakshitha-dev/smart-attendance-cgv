# 📋 SAMS — Smart Attendance Management System

Photograph a paper class attendance sheet, and SAMS works out who actually signed it, saves the
records, and turns them into charts.

Built for **CS402.3 — Computer Graphics and Visualization** at NSBM Green University Town.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%20%7C%203.13-3776AB?logo=python&logoColor=white" alt="Python 3.12 or 3.13"/>
  <img src="https://img.shields.io/badge/OpenCV-4.13-5C3EE8?logo=opencv&logoColor=white" alt="OpenCV 4.13"/>
  <img src="https://img.shields.io/badge/NumPy-2.5-013243?logo=numpy&logoColor=white" alt="NumPy 2.5"/>
  <img src="https://img.shields.io/badge/Matplotlib-3.11-11557C" alt="Matplotlib 3.11"/>
  <img src="https://img.shields.io/badge/Streamlit-1.59-FF4B4B?logo=streamlit&logoColor=white" alt="Streamlit 1.59"/>
  <img src="https://img.shields.io/badge/tests-269%20passing-2E7D32" alt="269 tests passing"/>
  <img src="https://img.shields.io/badge/detection%20accuracy-30%2F30-2E7D32" alt="Detection accuracy 30 of 30"/>
</p>

<div align="center">
  <img src="docs/walkthrough/desktop-1-dashboard.png" alt="SAMS dashboard showing roster size, sessions recorded, average attendance, students needing attention, the latest session's attendance rate and signature alerts" width="820"/>
</div>

---

## 📖 Overview

Attendance is still taken on paper in a lot of classrooms, and somebody then has to squint at the
sheet and type it all in. SAMS replaces that step: hand it a phone photo of the sheet plus the
session's `info.xml` roster, and it reads the signatures, saves the attendance, and builds the
charts.

There are two front-ends and **one engine** — command-line tools and an optional web app that call
exactly the same code, so they always agree.

---

## ✨ What it does

- 🖼️ **Reads the sheet as an image** — a seven-stage pipeline cleans the photo, straightens it,
  finds the table, and inspects every signature cell on its own.
- 🎯 **Finds the table anywhere in frame** — no OCR and no hard-coded pixel coordinates, so the
  sheet doesn't have to be photographed the same way twice.
- ✅ **Decides per student** — Present, Absent, or **Ambiguous**. A faint smudge gets escalated to a
  human instead of being quietly guessed.
- 💾 **Keeps a history** — records go to a local SQLite database, so sessions build up over time.
- 📈 **Charts the history** — attendance timelines and rate bars, with ✓ / ? / ✕ markers and one
  consistent green / ochre / red encoding so colour is never the only signal.
- ✍️ **Flags odd signatures** — each signature is scored against that student's reference
  signatures, and a low score is raised for a person to check.

---

## 🖼️ Screens

<div align="center">

<table>
  <tr>
    <td align="center" width="33%">
      <img src="docs/walkthrough/desktop-1-dashboard.png" alt="Dashboard with quick actions, date range, four stat tiles, latest session panel and needs-attention panel" width="380"/><br/>
      <strong>Dashboard</strong><br/>
      <sub>Who needs attention</sub>
    </td>
    <td align="center" width="33%">
      <img src="docs/walkthrough/desktop-2-ready.png" alt="Mark today's attendance page with the signing sheet photo and info.xml both uploaded and marked ready" width="380"/><br/>
      <strong>Mark attendance</strong><br/>
      <sub>Upload sheet and roster</sub>
    </td>
    <td align="center" width="33%">
      <img src="docs/walkthrough/desktop-3-results.png" alt="Processing results page listing all seven pipeline stages followed by the per-student attendance results" width="380"/><br/>
      <strong>Pipeline stages</strong><br/>
      <sub>All seven, then results</sub>
    </td>
  </tr>
  <tr>
    <td align="center" width="33%">
      <img src="docs/walkthrough/desktop-4-history.png" alt="Session history page with attendance trend chart and per-session attendance rate bars" width="380"/><br/>
      <strong>Session history</strong><br/>
      <sub>Trend and per-session rates</sub>
    </td>
    <td align="center" width="33%">
      <img src="docs/walkthrough/desktop-5-lookup.png" alt="Student lookup page showing the attendance timeline chart for one student across six sessions with a 100 percent attendance rate" width="380"/><br/>
      <strong>Look up a student</strong><br/>
      <sub>Attendance timeline</sub>
    </td>
    <td align="center" width="33%">
      <img src="docs/walkthrough/desktop-6-investigate.png" alt="Signature check page comparing a reference signature with the signature from a sheet, showing a similarity score of 51 against a threshold of 40" width="380"/><br/>
      <strong>Check a signature</strong><br/>
      <sub>Reference vs sheet, scored</sub>
    </td>
  </tr>
</table>

**On a phone**

<table>
  <tr>
    <td align="center">
      <img src="docs/walkthrough/phone-1-dashboard.png" alt="Dashboard at 360 pixels wide" width="180"/><br/>
      <sub>Dashboard</sub>
    </td>
    <td align="center">
      <img src="docs/walkthrough/phone-3-results.png" alt="Processing results at 360 pixels wide" width="180"/><br/>
      <sub>Results</sub>
    </td>
    <td align="center">
      <img src="docs/walkthrough/phone-4-history.png" alt="Session history at 360 pixels wide" width="180"/><br/>
      <sub>History</sub>
    </td>
    <td align="center">
      <img src="docs/walkthrough/phone-5-lookup.png" alt="Student lookup and attendance timeline at 360 pixels wide" width="180"/><br/>
      <sub>Lookup</sub>
    </td>
  </tr>
</table>

</div>

---

## 🏗️ How it works

<div align="center">
  <img src="docs/report/architecture.png" alt="Architecture diagram: the signing-sheet photo and info.xml feed into sams_core, which contains the seven-stage pipeline, table localization and cell detection, the info.xml parser and mapping, HOG signature verification, the Matplotlib chart builders and the SQLite repository; outputs are the three CLI tools, the Streamlit web app and the output directory" width="820"/>
</div>

`sams_core/` is the engine — the only package that touches OpenCV, SQLite, or Matplotlib, and it
returns data rather than drawing anything itself. The CLI tools and the web app are thin adapters
over it.

---

## 🚀 Quick start

Needs **Python 3.12 or 3.13**. On Linux, also `sudo apt install libgl1 libglib2.0-0`.

```bash
pip install -r requirements.txt
```

Then, from the project root:

```bash
# 1. Read a signing sheet and save the attendance
python sams.py 10.07.2019.png info.xml

# 2. Show one student's records and attendance timeline
python infovis.py 001

# 3. Check that student's signature against their references
python investigate.py 001
```

Five more sample sheets to try are in `sample_signin-sheets/` — pass a photo and its matching
`.xml`, for example `python sams.py sample_signin-sheets/1.jpeg sample_signin-sheets/1.xml`.

---

## 🌐 Web UI

The browser front-end is an optional extra — the command-line tools never need it.

```bash
pip install -r requirements-web.txt
streamlit run webui/app.py
```

Run it from the project root so Streamlit picks up the theme in `.streamlit/`.

---

## 🛠️ Built with

- **Python** 3.12 / 3.13
- **OpenCV** — the image-processing pipeline and signature descriptors
- **NumPy** — the numerics underneath it
- **Matplotlib** — every chart
- **Streamlit** — the optional web front-end
- **SQLite** — the attendance records
- **pytest** — 269 tests, including an accuracy gate on the sample sheets

---

> 📄 Pipeline internals, configuration, accuracy results, the full CLI reference and deployment:
> **[docs/TECHNICAL.md](docs/TECHNICAL.md)**

---

## 👥 Team Members

<div align="left">

| <img src="https://github.com/lakshitha-dev.png" width="50px" height="50px"/> | <img src="https://github.com/JMAdikari.png" width="50px" height="50px"/> | <img src="https://github.com/NethmiJayasinghee.png" width="50px" height="50px"/> | <img src="https://github.com/RuwaniChandrarathne.png" width="50px" height="50px"/> |
|:---:|:---:|:---:|:---:|
| **Lakshitha Wijerathne** | **Jayani Adikari** | **Nethmi Jayasinghe** | **Ruwani Chandrarathne** |
| [@lakshitha-dev](https://github.com/lakshitha-dev) | [@JMAdikari](https://github.com/JMAdikari) | [@NethmiJayasinghee](https://github.com/NethmiJayasinghee) | [@RuwaniChandrarathne](https://github.com/RuwaniChandrarathne) |

| <img src="https://github.com/Janandie.png" width="50px" height="50px"/> | <img src="https://github.com/ChamudiRathnayake.png" width="50px" height="50px"/> | <img src="https://github.com/DhananjaGangoda.png" width="50px" height="50px"/> | <img src="https://github.com/Imashichathu.png" width="50px" height="50px"/> |
|:---:|:---:|:---:|:---:|
| **Janandi Samarawickrama** | **Chamudi Rathnayake** | **Dhananja Gangoda** | **Imashi Chathurangi Gunarathna** |
| [@Janandie](https://github.com/Janandie) | [@ChamudiRathnayake](https://github.com/ChamudiRathnayake) | [@DhananjaGangoda](https://github.com/DhananjaGangoda) | [@Imashichathu](https://github.com/Imashichathu) |

</div>

All eight members contributed to both halves of the module — the image-processing pipeline and the
data-visualization work.

---

<div align="center">
  <sub><strong>CS402.3 — Computer Graphics and Visualization</strong><br/>
  NSBM Green University Town</sub>
</div>
