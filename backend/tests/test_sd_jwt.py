
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.credentials.crypto.ed25519 import generate_keypair, sign, verify
from app.credentials.crypto.utils import (
    generate_salt,
    create_disclosure,
    hash_disclosure,
    decode_disclosure,
)
from app.credentials.crypto.sd_jwt import (
    create_sd_jwt,
    create_presentation,
    verify_presentation,
)


class TestEd25519:
    def test_generate_keypair(self):
        private_key, public_key = generate_keypair()
        assert len(private_key) == 64
        assert len(public_key) == 64

    def test_sign_and_verify(self):
        private_key, public_key = generate_keypair()
        message = b"hello world"
        signature = sign(message, private_key)
        assert verify(message, signature, public_key)

    def test_invalid_signature(self):
        private_key, public_key = generate_keypair()
        message = b"hello world"
        signature = sign(message, private_key)
        assert not verify(b"tampered message", signature, public_key)

    def test_wrong_key(self):
        private_key1, public_key1 = generate_keypair()
        _, public_key2 = generate_keypair()
        message = b"test"
        signature = sign(message, private_key1)
        assert not verify(message, signature, public_key2)


class TestDisclosures:
    def test_create_and_decode(self):
        salt = generate_salt()
        disclosure = create_disclosure(salt, "name", "Vishnu")
        decoded = decode_disclosure(disclosure)
        assert decoded == (salt, "name", "Vishnu")

    def test_hash_consistency(self):
        salt = generate_salt()
        d = create_disclosure(salt, "degree", "M.Sc")
        h1 = hash_disclosure(d)
        h2 = hash_disclosure(d)
        assert h1 == h2

    def test_different_salts(self):
        s1 = generate_salt()
        s2 = generate_salt()
        d1 = create_disclosure(s1, "name", "Vishnu")
        d2 = create_disclosure(s2, "name", "Vishnu")
        assert hash_disclosure(d1) != hash_disclosure(d2)


class TestSDJWT:
    def setup_method(self):
        self.private_key, self.public_key = generate_keypair()
        self.claims = {
            "name": "Vishnu Aravind",
            "degree": "M.Sc TCS",
            "college": "PSG College of Technology",
            "cgpa": "8.5",
            "graduationYear": "2028",
        }

    def test_create_sd_jwt(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        assert "sd_jwt" in result
        assert "disclosures" in result
        assert len(result["disclosures"]) == 5

    def test_full_disclosure(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        all_fields = list(self.claims.keys())
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], all_fields)
        verification = verify_presentation(presentation, self.public_key)
        assert verification["verified"] is True
        assert len(verification["disclosed_fields"]) == 5
        assert verification["hidden_count"] == 0

    def test_selective_disclosure(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        selected = ["name", "degree"]
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], selected)
        verification = verify_presentation(presentation, self.public_key)
        assert verification["verified"] is True
        assert len(verification["disclosed_fields"]) == 2
        assert "name" in verification["disclosed_fields"]
        assert "degree" in verification["disclosed_fields"]
        assert "cgpa" not in verification["disclosed_fields"]
        assert verification["hidden_count"] == 3

    def test_wrong_public_key(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], ["name"])
        _, wrong_key = generate_keypair()
        verification = verify_presentation(presentation, wrong_key)
        assert verification["verified"] is False

    def test_issuer_info_preserved(self):
        result = create_sd_jwt(self.claims, "PSG College", "user123", self.private_key)
        presentation = create_presentation(result["sd_jwt"], result["disclosures"], ["name"])
        verification = verify_presentation(presentation, self.public_key)
        assert verification["issuer"] == "PSG College"
        assert verification["subject"] == "user123"
