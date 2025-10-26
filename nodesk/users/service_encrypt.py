import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


class EncryptionService:
    @staticmethod
    def generate_key_iv():
        key = os.urandom(32)
        iv = os.urandom(16)
        return base64.b64encode(key).decode(), base64.b64encode(iv).decode()

    @staticmethod
    def encrypt(data: str, key_b64: str, iv_b64: str) -> str:
        if data is None:
            return None
        key = base64.b64decode(key_b64)
        iv = base64.b64decode(iv_b64)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Padding (PKCS7)
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data.encode()) + padder.finalize()

        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(encrypted).decode()

    @staticmethod
    def decrypt(encrypted_b64: str, key_b64: str, iv_b64: str) -> str:
        if encrypted_b64 is None:
            return None
        key = base64.b64decode(key_b64)
        iv = base64.b64decode(iv_b64)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        decrypted_padded = decryptor.update(base64.b64decode(encrypted_b64)) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()
        return decrypted.decode()
