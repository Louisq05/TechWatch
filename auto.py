"""Run the automated pipeline (entry point for the Windows scheduled task).

Launched by absolute path (python auto.py), so it works from any directory.
"""
from techwatch.pipeline import main

if __name__ == "__main__":
    main()
