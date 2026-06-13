"""Allow: python -m engine (same as python -m engine.translate_cli)."""

from engine.translate_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
