"""Tests for JWT authentication."""
import os
import pytest

# Set test secret before importing
os.environ["APP_SECRET_KEY"] = "test-secret-key-for-unit-tests"

from backend.api.auth import create_token, decode_token


class TestJWT:
    """Test JWT token creation and validation."""

    def test_create_token_returns_string(self):
        token = create_token(user_id=1, telegram_id=123456)
        assert isinstance(token, str)
        assert len(token) > 20

    def test_decode_valid_token(self):
        token = create_token(user_id=42, telegram_id=789)
        user_id = decode_token(token)
        assert user_id == 42

    def test_decode_preserves_user_id(self):
        for uid in [1, 100, 999999]:
            token = create_token(user_id=uid, telegram_id=111)
            assert decode_token(token) == uid

    def test_decode_invalid_token(self):
        result = decode_token("invalid.token.here")
        assert result is None

    def test_decode_empty_token(self):
        result = decode_token("")
        assert result is None

    def test_decode_tampered_token(self):
        token = create_token(user_id=1, telegram_id=123)
        tampered = token[:-5] + "XXXXX"
        result = decode_token(tampered)
        assert result is None

    def test_different_users_different_tokens(self):
        t1 = create_token(user_id=1, telegram_id=100)
        t2 = create_token(user_id=2, telegram_id=200)
        assert t1 != t2
