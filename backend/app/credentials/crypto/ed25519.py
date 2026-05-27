
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError


def generate_keypair() -> tuple:
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key
    return (
        signing_key.encode().hex(),
        verify_key.encode().hex(),
    )


def sign(message: bytes, private_key_hex: str) -> str:
    signing_key = SigningKey(bytes.fromhex(private_key_hex))
    signed = signing_key.sign(message)
    return signed.signature.hex()


def verify(message: bytes, signature_hex: str, public_key_hex: str) -> bool:
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key_hex))
        verify_key.verify(message, bytes.fromhex(signature_hex))
        return True
    except BadSignatureError:
        return False
