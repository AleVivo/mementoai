"""
Utility per cifratura simmetrica con Fernet (AES-128).

La chiave è derivata da JWT_SECRET_KEY tramite SHA-256, così non serve
una variabile d'ambiente aggiuntiva.

Tre funzioni pubbliche:
    encrypt(value)       → cifra una stringa
    decrypt(value)       → decifra, None se fallisce
    mask_secret(value)   → maschera per le response HTTP
"""

import base64
import hashlib
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

logger = logging.getLogger(__name__)

def _build_fernet() -> Fernet:
    key_bytes = hashlib.sha256(settings.jwt_secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)

def encrypt(value: str) -> str:
    return _build_fernet().encrypt(value.encode()).decode()

def decrypt(value: str) -> str | None:
    try:
        return _build_fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        logger.warning("[encryption] impossibile decifrare il valore — InvalidToken")
        return None
    
def mask_secret(value: Optional[str]) -> Optional[str]:
    return "***" if value is not None else None