"""Run the whole pipeline from raw files to tested marts with one command:  python pipeline/run_pipeline.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
steps = ["pipeline/02_build_external.py", "pipeline/10_build_staging.py", "pipeline/20_build_marts.py"]
for s in steps:
    print(f"\n>>> {s}")
    subprocess.run([sys.executable, str(ROOT / s)], check=True, cwd=ROOT)
print("\n>>> data quality tests")
sys.exit(subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=ROOT).returncode)
