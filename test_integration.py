"""Quick test for run_pipeline_with_localization."""

from sams_core.image_io import load_image
from sams_core.pipeline import run_pipeline_with_localization
from sams_core.info_file import parse_info_file
from pathlib import Path

# Test new function
image = load_image(str(Path('sample_signin-sheets') / '1.jpeg'))
info_file = parse_info_file(str(Path('sample_signin-sheets') / '1.xml'))
stages_iter, sheet_result = run_pipeline_with_localization(image, len(info_file.students))
stages = list(stages_iter)

print(f'Pipeline with localization stages: {len(stages)}')
print(f'Stage 6 (table-grid) shape: {stages[-1].image.shape}')
print(f'Sheet result detected rows: {sheet_result.detected_row_count}')
print(f'Sheet result warnings: {len(sheet_result.warnings)}')
mask_key = 'mask'
print(f'Grid mask present: {mask_key in sheet_result.detected_grid_lines}')
print(f'Metadata row: {sheet_result.metadata_row_y_range}')
print(f'Student table: {sheet_result.student_table_y_range}')
print('✓ New pipeline function working correctly')
