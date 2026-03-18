"""
Stoppa il container MongoDB.

    python infra/stop.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from docker_mongo import stop_container  # noqa: E402

if __name__ == "__main__":
    answer = input("Stop MongoDB container? [y/N] ").strip().lower()
    if answer == "y":
        stop_container()
    else:
        print("Container left running.")