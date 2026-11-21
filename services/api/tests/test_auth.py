"""Authentication and Security Unit Tests [M3]."""

import unittest
from datetime import timedelta
from app.auth.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


class TestAuthSecurity(unittest.TestCase):

    def test_password_hashing_and_verification(self):
        password = "SecurePassword123!"
        hashed = get_password_hash(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("pbkdf2:sha256:"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_jwt_token_creation_and_decoding(self):
        payload = {"sub": "user-12345", "email": "handler@test.org", "role": "handler"}
        token = create_access_token(payload, expires_delta=timedelta(minutes=30))

        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.get("sub"), "user-12345")
        self.assertEqual(decoded.get("email"), "handler@test.org")
        self.assertEqual(decoded.get("role"), "handler")

    def test_invalid_jwt_token(self):
        invalid_token = "invalid.token.string"
        decoded = decode_access_token(invalid_token)
        self.assertIsNone(decoded)


if __name__ == "__main__":
    unittest.main()
