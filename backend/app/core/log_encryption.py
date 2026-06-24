"""
Log Encryption - Crittografia audit logs sensibili.

Usa Fernet (symmetric encryption) per proteggere dati sensibili nei log.
Compliance:
- ISO 27001:2022 - A.8.24 (Use of cryptography)
- GDPR Art. 32 (Security of processing)
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Singleton cache per istanza Fernet
_fernet_instance: Optional[Fernet] = None


def generate_key() -> bytes:
    """
    Genera una nuova chiave Fernet.

    Uso: solo per setup iniziale o rotazione chiavi.
    Salvare la chiave in environment variable AUDIT_LOG_ENCRYPTION_KEY.

    Returns:
        bytes: Chiave Fernet (44 bytes, base64-encoded)
    """
    key = Fernet.generate_key()
    logger.info("Generated new Fernet key for audit log encryption")
    return key


def get_fernet() -> Fernet:
    """
    Carica istanza Fernet dalla chiave in environment.

    Usa singleton pattern per evitare ricreazione costante.
    Chiave: AUDIT_LOG_ENCRYPTION_KEY (deve essere base64 Fernet valida)

    Returns:
        Fernet: Istanza per encrypt/decrypt

    Raises:
        ValueError: Se chiave mancante o invalida
    """
    global _fernet_instance

    if _fernet_instance is not None:
        return _fernet_instance

    key_str = os.getenv("AUDIT_LOG_ENCRYPTION_KEY")
    if not key_str or not key_str.strip():
        raise ValueError(
            "AUDIT_LOG_ENCRYPTION_KEY non configurata. "
            "Genera con: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )

    key_str = key_str.strip()
    try:
        key_bytes = key_str.encode() if isinstance(key_str, str) else key_str
        _fernet_instance = Fernet(key_bytes)
        logger.info("Fernet instance initialized for audit log encryption")
        return _fernet_instance
    except Exception as e:
        logger.error("Invalid AUDIT_LOG_ENCRYPTION_KEY: %s", e)
        raise ValueError(f"Chiave encryption invalida: {e}") from e


def encrypt_log(data: str) -> str:
    """
    Cripta dati sensibili per storage in audit log.

    Input: stringa plaintext (JSON o testo)
    Output: token Fernet base64 (inizia con gAAAAA)

    Args:
        data: Stringa plaintext da criptare

    Returns:
        str: Token criptato base64, o "" se input vuoto, o data originale se fallisce
    """
    if data is None or (isinstance(data, str) and not data.strip()):
        return ""

    try:
        fernet = get_fernet()
        encrypted_bytes = fernet.encrypt(data.encode("utf-8"))
        result = encrypted_bytes.decode("ascii")
        logger.debug("Encrypted audit log data (%d chars -> %d chars)", len(data), len(result))
        return result
    except ValueError as e:
        # Chiave non configurata - non criptare (backward compat)
        logger.warning("Encryption skipped (key not configured): %s", e)
        return data
    except Exception as e:
        logger.warning("Encryption failed, returning plaintext: %s", e)
        return data


def decrypt_log(encrypted: str) -> str:
    """
    Decripta dati sensibili da audit log.

    Gestisce backward compatibility: log vecchi non criptati restituiti
    invariati.

    Args:
        encrypted: Token Fernet base64 o plaintext legacy

    Returns:
        str: Plaintext decriptato, o "" se input vuoto, o encrypted se fallisce
    """
    if encrypted is None or (isinstance(encrypted, str) and not encrypted.strip()):
        return ""

    # Backward compatibility: se non è encrypted, ritorna così com'è
    if not is_encrypted(encrypted):
        return encrypted

    try:
        fernet = get_fernet()
        decrypted_bytes = fernet.decrypt(encrypted.encode("ascii"))
        result = decrypted_bytes.decode("utf-8")
        logger.debug("Decrypted audit log data")
        return result
    except ValueError as e:
        # Chiave non configurata o cambiata
        logger.warning("Decryption skipped (key not configured or changed): %s", e)
        return encrypted
    except InvalidToken as e:
        logger.warning("Decryption failed (invalid token): %s", e)
        return encrypted
    except Exception as e:
        logger.warning("Decryption failed, returning encrypted: %s", e)
        return encrypted


def is_encrypted(data: str) -> bool:
    """
    Verifica se una stringa è un token Fernet criptato.

    I token Fernet in base64 iniziano con "gAAAAA" (primi 4 byte
    encoded = timestamp + IV).

    Args:
        data: Stringa da verificare

    Returns:
        bool: True se sembra encrypted, False altrimenti
    """
    if data is None or not isinstance(data, str):
        return False
    if not data.strip():
        return False

    # Fernet token: base64 URL-safe, inizia con gAAAAA
    return data.strip().startswith("gAAAAA")
