from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Servizio per criptare/decriptare dati sensibili (PIN, PUK)"""
    
    KEY_FILE = Path("/app/data/.encryption_key")
    
    @classmethod
    def _get_or_create_key(cls) -> bytes:
        """Ottiene la chiave di criptazione o ne crea una nuova"""
        if cls.KEY_FILE.exists():
            with open(cls.KEY_FILE, 'rb') as f:
                return f.read()
        else:
            # Genera nuova chiave
            key = Fernet.generate_key()
            # Crea directory se non esiste
            cls.KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Salva chiave
            with open(cls.KEY_FILE, 'wb') as f:
                f.write(key)
            # Imposta permessi restrittivi
            os.chmod(cls.KEY_FILE, 0o600)
            logger.info(f"Chiave di crittografia creata in {cls.KEY_FILE}")
            return key
    
    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Cripta una stringa in chiaro
        
        Args:
            plaintext: Testo da criptare (es: "1234")
            
        Returns:
            Testo criptato in base64 (es: "gAAAAABf...")
            
        Raises:
            ValueError: Se il plaintext non è valido
        """
        if not plaintext:
            return ""
        
        try:
            key = cls._get_or_create_key()
            f = Fernet(key)
            encrypted_bytes = f.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Errore durante la crittografia: {e}")
            raise ValueError(f"Errore durante la crittografia: {e}")
    
    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        """
        Decripta una stringa criptata
        
        Args:
            encrypted_text: Testo criptato (es: "gAAAAABf...")
            
        Returns:
            Testo in chiaro (es: "1234")
            
        Raises:
            ValueError: Se il testo criptato non è valido o la chiave è errata
        """
        if not encrypted_text:
            return ""
        
        try:
            key = cls._get_or_create_key()
            f = Fernet(key)
            decrypted_bytes = f.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Errore: token di crittografia non valido o chiave errata")
            raise ValueError("Impossibile decrittare: token non valido o chiave errata")
        except Exception as e:
            logger.error(f"Errore durante la decrittazione: {e}")
            raise ValueError(f"Errore durante la decrittazione: {e}")
