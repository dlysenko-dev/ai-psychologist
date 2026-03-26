"""Tests for crisis detection module."""
import pytest

from backend.services.crisis_detector import check_crisis, get_crisis_response


class TestCheckCrisis:
    """Test keyword-based crisis detection."""

    # --- Russian keywords ---

    def test_detects_suicide_ru(self):
        assert check_crisis("хочу убить себя") is True

    def test_detects_suicide_intent_ru(self):
        assert check_crisis("я хочу покончить с собой") is True

    def test_detects_suicid_word_ru(self):
        assert check_crisis("думаю про суицид") is True

    def test_detects_want_to_die_ru(self):
        assert check_crisis("хочу умереть") is True

    def test_detects_no_will_to_live_ru(self):
        assert check_crisis("не хочу жить") is True

    def test_detects_better_without_me_ru(self):
        assert check_crisis("лучше бы меня не было") is True

    def test_detects_no_meaning_ru(self):
        assert check_crisis("нет смысла жить дальше") is True

    def test_detects_hanging_ru(self):
        assert check_crisis("хочу повеситься") is True

    def test_detects_cutting_ru(self):
        assert check_crisis("начала резать себя") is True

    def test_detects_cutting_veins_ru(self):
        assert check_crisis("резать вены") is True

    # --- English keywords ---

    def test_detects_kill_myself_en(self):
        assert check_crisis("I want to kill myself") is True

    def test_detects_want_to_die_en(self):
        assert check_crisis("I want to die") is True

    def test_detects_suicide_en(self):
        assert check_crisis("thinking about suicide") is True

    def test_detects_end_it_all_en(self):
        assert check_crisis("I want to end it all") is True

    def test_detects_self_harm_en(self):
        assert check_crisis("I started self-harm again") is True

    def test_detects_self_harm_nospace_en(self):
        assert check_crisis("selfharm is my coping") is True

    def test_detects_better_off_dead_en(self):
        assert check_crisis("everyone is better off dead without me") is True

    # --- Case insensitivity ---

    def test_case_insensitive_ru(self):
        assert check_crisis("СУИЦИД") is True

    def test_case_insensitive_en(self):
        assert check_crisis("SUICIDE") is True

    # --- Negative cases (should NOT trigger) ---

    def test_normal_message(self):
        assert check_crisis("у меня сегодня плохое настроение") is False

    def test_normal_sadness(self):
        assert check_crisis("мне грустно и одиноко") is False

    def test_normal_stress(self):
        assert check_crisis("на работе стресс, устал") is False

    def test_normal_english(self):
        assert check_crisis("I feel sad today") is False

    def test_empty_string(self):
        assert check_crisis("") is False

    def test_random_text(self):
        assert check_crisis("привет, как дела?") is False


class TestCrisisResponse:
    """Test crisis response message."""

    def test_response_not_empty(self):
        response = get_crisis_response()
        assert len(response) > 100

    def test_response_contains_hotline(self):
        response = get_crisis_response()
        assert "8-800-2000-122" in response

    def test_response_contains_trust_phone(self):
        response = get_crisis_response()
        assert "8-495-988-44-34" in response
