#!/usr/bin/env python3


def main():
    # For executable bundles
    try:
        import multiprocessing

        multiprocessing.freeze_support()
    except Exception:
        pass

    # For encoding
    try:
        import sys

        reconfigure = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
    except Exception:
        pass

    # Remove colors from terminal in CI
    import os

    if os.getenv("CI"):
        os.environ["TERM"] = "dumb"
        os.environ["NO_COLOR"] = "1"

    # Start the app
    from .app import app

    app()


if __name__ == "__main__":
    main()
