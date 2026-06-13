.PHONY: clean test test-pytest install install-dev desktop desktop-native install-desktop build-desktop preflight doctor doctor-download doctor-render doctor-ocr

# Remove __pycache__, *.pyc, caches, run.log (does not delete workspace/jobs).
clean:
	powershell -NoProfile -ExecutionPolicy Bypass -File scripts/clean_runtime.ps1

# Base runtime deps for browser mode / backend flows.
install:
	python -m pip install -r engine/requirements.txt

# Default: use the stdlib unittest runner. No extra deps required.
test:
	python -m unittest discover -s engine/tests -v

# Quiet suite + clean caches (run before packaging smoke).
preflight: clean
	python -m unittest discover -s engine/tests -p "test_*.py" -q

# Optional pytest runner (install engine/requirements-dev.txt first).
test-pytest:
	python -m pytest engine/tests -v

install-dev:
	python -m pip install -r engine/requirements-dev.txt

# Runtime doctor helpers.
doctor:
	python scripts/backend_smoke.py preflight

doctor-download:
	python scripts/backend_smoke.py preflight --require-download

doctor-render:
	python scripts/backend_smoke.py preflight --require-render

doctor-ocr:
	python scripts/backend_smoke.py preflight --require-render --require-ocr --ocr-provider paddleocr

# Start the local desktop HTTP shell on 127.0.0.1:8765 (opens default browser).
desktop:
	python -m desktop.server

# Start the native desktop shell (pywebview window — no browser needed).
desktop-native:
	python -m desktop.native

# Install native-shell + packaging deps.
install-desktop:
	python -m pip install -r engine/requirements-desktop.txt

# Build the distributable via PyInstaller (writes dist/VLTool/).
build-desktop:
	python -m PyInstaller packaging/vltool.spec --noconfirm
