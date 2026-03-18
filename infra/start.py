"""
Avvia il container MongoDB.
 
    python infra/start.py
"""
 
import sys
from pathlib import Path
 
from dotenv import load_dotenv
 
load_dotenv(Path(__file__).parent.parent / ".env")
 
sys.path.insert(0, str(Path(__file__).parent))
 
from docker_mongo import ensure_mongodb_running  # noqa: E402
 
if __name__ == "__main__":
    ensure_mongodb_running()
    print("\nMongoDB ready.\n")
 