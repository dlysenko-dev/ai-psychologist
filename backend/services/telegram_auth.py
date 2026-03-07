"""Telegram WebApp authentication — validates initData from Mini App"""
import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote

from loguru import logger

from backend.config import settings


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp initData and extract user info.

    Returns dict with telegram user data or None if invalid.
    See: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        # Build data-check-string (all params except hash, sorted alphabetically)
        data_pairs = []
        for key, values in parsed.items():
            if key == "hash":
                continue
            data_pairs.append(f"{key}={unquote(values[0])}")
        data_pairs.sort()
        data_check_string = "\n".join(data_pairs)

        # Compute HMAC
        secret_key = hmac.new(
            b"WebAppData",
            settings.telegram_bot_token.encode(),
            hashlib.sha256,
        ).digest()

        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if computed_hash != received_hash:
            logger.warning("Telegram initData hash mismatch")
            return None

        # Extract user
        user_str = parsed.get("user", [None])[0]
        if not user_str:
            return None

        user_data = json.loads(unquote(user_str))
        return {
            "id": user_data.get("id"),
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "username": user_data.get("username"),
            "is_premium": user_data.get("is_premium", False),
        }
    except Exception as e:
        logger.error(f"Failed to validate initData: {e}")
        return None
