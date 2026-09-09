"""Compatibility runner: regression coverage now lives in tests/."""
if __name__ == "__main__":
    import subprocess
    import sys
    from pathlib import Path
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest"], cwd=Path(__file__).resolve().parents[1]))
