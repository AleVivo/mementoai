"""
Gestisce il lifecycle del container MongoDB (atlas-local) all'avvio del backend.
Viene chiamato dal lifespan di FastAPI solo se settings.mongodb_mode == "docker".

Flusso startup:
  1. Docker disponibile?           → se no, RuntimeError (mode=docker richiede Docker)
  2. Container esiste?             → se no, docker pull + docker run
  3. Container running?            → se no (stopped), docker start
  4. Health check (ping MongoDB)   → aspetta max MAX_WAIT secondi

Flusso shutdown:
  stop_container() → docker stop (chiamata da main.py se l'utente lo sceglie)
"""

import logging
import os
import subprocess
import time

import pymongo

logger = logging.getLogger(__name__)

# ── Costanti ─────────────────────────────────────────────────────────────────

CONTAINER_NAME = "memento-mongodb"
IMAGE_NAME = "mongodb/mongodb-atlas-local:latest"

MAX_WAIT = 60
RETRY_INTERVAL = 3


# ── Helper subprocess ─────────────────────────────────────────────────────────

def _run(cmd: list[str], check: bool = False) -> subprocess.CompletedProcess:
    """
    Esegue un comando di sistema e ritorna il risultato.
    capture_output=True  → cattura stdout/stderr invece di stamparli
    text=True            → decodifica output come stringa UTF-8
    check=True           → lancia CalledProcessError se returncode != 0
    """
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


# ── Stato container ───────────────────────────────────────────────────────────

def _docker_available() -> bool:
    try:
        return _run(["docker", "info"]).returncode == 0
    except FileNotFoundError:
        return False


def _container_exists() -> bool:
    """docker inspect → returncode 0 se esiste (running o stopped), 1 se no."""
    return _run(["docker", "inspect", CONTAINER_NAME]).returncode == 0


def _container_is_running() -> bool:
    """Estrae il campo State.Running dal JSON di inspect via Go template."""
    result = _run([
        "docker", "inspect",
        "--format", "{{.State.Running}}",
        CONTAINER_NAME,
    ])
    return result.stdout.strip() == "true"


# ── Operazioni container ──────────────────────────────────────────────────────

def _pull_image() -> None:
    """Scarica l'immagine se non presente. Idempotente: no-op se già aggiornata."""
    logger.info(f"Pulling image {IMAGE_NAME} (only needed on first run)...")
    _run(["docker", "pull", IMAGE_NAME], check=True)


def _start_new_container() -> None:
    """
    Crea e avvia il container con volumi persistenti.

    Flag notevoli:
      -d                  detached — gira in background
      -v name:/path       named volume — Docker lo crea se non esiste;
                          i dati sopravvivono a `docker stop` e `docker rm`
      --restart           unless-stopped → si riavvia col PC, non se stoppato manualmente
    """
    logger.info(f"Creating container '{CONTAINER_NAME}'...")
    _run([
        "docker", "run", "-d",
        "--name", CONTAINER_NAME,
        "-p", "27017:27017",
        "-v", "memento-mongodb-data:/data/db",
        "-v", "memento-mongodb-config:/data/configdb",
        "-v", "memento-mongot-data:/data/mongot",
        "--restart", "unless-stopped",
        "-e", "MONGODB_INITDB_ROOT_USERNAME=memento",
        "-e", "MONGODB_INITDB_ROOT_PASSWORD=memento",
        IMAGE_NAME,
    ], check=True)


def _wait_for_mongodb() -> None:
    """
    Polling su MongoDB finché non risponde al ping o scade il timeout.

    Usa pymongo sincrono (non AsyncMongoClient) perché siamo nel lifespan
    startup — più semplice che creare un client async solo per un ping.
    serverSelectionTimeoutMS=2000 → fallisce veloce invece di aspettare 30s default.
    """
    logger.info("Waiting for MongoDB to be ready...")
    deadline = time.time() + MAX_WAIT

    while time.time() < deadline:
        try:
            client = pymongo.MongoClient(
                os.getenv("MONGODB_URL"),
                serverSelectionTimeoutMS=2000,
            )
            client.admin.command("ping")
            client.close()
            logger.info("MongoDB is ready.")
            return
        except Exception:
            remaining = int(deadline - time.time())
            logger.info(f"MongoDB not ready yet, retrying... ({remaining}s remaining)")
            time.sleep(RETRY_INTERVAL)

    raise RuntimeError(
        f"MongoDB did not become ready within {MAX_WAIT}s. "
        f"Check logs: docker logs {CONTAINER_NAME}"
    )


# ── Entry point startup ───────────────────────────────────────────────────────

def ensure_mongodb_running() -> None:
    """
    Chiamata dal lifespan di FastAPI durante lo startup (solo se mode=docker).
    Garantisce che il container esista, sia running e risponda al ping
    prima che il backend inizi ad accettare richieste.
    """
    if not _docker_available():
        raise RuntimeError(
            "MONGODB_MODE=docker but Docker is not available. "
            "Start Docker Desktop or set MONGODB_MODE=external in .env."
        )

    try:
        if not _container_exists():
            _pull_image()
            _start_new_container()
            logger.info(f"Container '{CONTAINER_NAME}' created and started.")
        elif not _container_is_running():
            logger.info(f"Container '{CONTAINER_NAME}' is stopped — starting it...")
            _run(["docker", "start", CONTAINER_NAME], check=True)
        else:
            logger.info(f"Container '{CONTAINER_NAME}' is already running.")

        _wait_for_mongodb()

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Docker command failed: {' '.join(e.cmd)}\n"
            f"stderr: {e.stderr}"
        ) from e


# ── Entry point shutdown ──────────────────────────────────────────────────────

def stop_container() -> None:
    """
    Stoppa il container. Chiamata da main.py dopo conferma utente.
    I dati rimangono nei named volumes — il prossimo avvio sarà immediato.
    Non lancia eccezioni: un errore di stop non deve bloccare lo shutdown.
    """
    if not _container_is_running():
        logger.info(f"Container '{CONTAINER_NAME}' is already stopped.")
        return

    logger.info(f"Stopping container '{CONTAINER_NAME}'...")
    result = _run(["docker", "stop", CONTAINER_NAME])

    if result.returncode == 0:
        logger.info(f"Container '{CONTAINER_NAME}' stopped.")
    else:
        logger.warning(
            f"Failed to stop container '{CONTAINER_NAME}': {result.stderr.strip()}"
        )