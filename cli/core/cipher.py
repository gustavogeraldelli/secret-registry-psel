import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag

class Cipher:
    @staticmethod
    def encrypt(senha: str, texto: str) -> dict:
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000
        )
        
        aes = AESGCM(kdf.derive(senha.encode()))
        nonce = os.urandom(12)
        ciphertext = aes.encrypt(nonce, texto.encode(), None)
        
        return {
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode()
        }

    @staticmethod
    def decrypt(senha: str, payload: dict) -> str:
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        ciphertext = base64.b64decode(payload["ciphertext"])
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000
        )
        aes = AESGCM(kdf.derive(senha.encode()))
        
        try:
            return aes.decrypt(nonce, ciphertext, None).decode()
        except InvalidTag:
            raise PermissionError("falha na decriptacao: senha incorreta ou arquivo adulterado.")