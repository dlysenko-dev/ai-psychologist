"""Tests for KMSI scoring and interpretation."""
import pytest

from backend.api.assessments import score_kmsi, interpret_kmsi


class TestScoreKMSI:
    """Test KMSI-R scoring logic."""

    def test_all_fives(self):
        answers = {str(i): 5 for i in range(1, 21)}
        scores = score_kmsi(answers)
        assert scores["money_avoidance"] == 5.0
        assert scores["money_worship"] == 5.0
        assert scores["money_status"] == 5.0
        assert scores["money_vigilance"] == 5.0

    def test_all_ones(self):
        answers = {str(i): 1 for i in range(1, 21)}
        scores = score_kmsi(answers)
        for scale in scores.values():
            assert scale == 1.0

    def test_mixed_scores(self):
        answers = {}
        # money_avoidance (1-5): all 3s
        for i in range(1, 6):
            answers[str(i)] = 3
        # money_worship (6-10): all 4s
        for i in range(6, 11):
            answers[str(i)] = 4
        # money_status (11-15): all 2s
        for i in range(11, 16):
            answers[str(i)] = 2
        # money_vigilance (16-20): all 5s
        for i in range(16, 21):
            answers[str(i)] = 5
        scores = score_kmsi(answers)
        assert scores["money_avoidance"] == 3.0
        assert scores["money_worship"] == 4.0
        assert scores["money_status"] == 2.0
        assert scores["money_vigilance"] == 5.0

    def test_empty_answers(self):
        scores = score_kmsi({})
        for scale in scores.values():
            assert scale == 0

    def test_partial_answers(self):
        answers = {"1": 4, "2": 2}  # only 2 of 5 for avoidance
        scores = score_kmsi(answers)
        assert scores["money_avoidance"] == 3.0  # (4+2)/2
        assert scores["money_worship"] == 0  # no answers

    def test_string_values(self):
        """Values come as strings from JSON."""
        answers = {"1": "5", "2": "3", "3": "4", "4": "2", "5": "1"}
        scores = score_kmsi(answers)
        assert scores["money_avoidance"] == 3.0  # (5+3+4+2+1)/5

    def test_rounding(self):
        answers = {"1": 3, "2": 4, "3": 3}  # 10/3 = 3.333...
        scores = score_kmsi(answers)
        assert scores["money_avoidance"] == 3.33


class TestInterpretKMSI:
    """Test KMSI interpretation text generation."""

    def test_high_scores(self):
        scores = {
            "money_avoidance": 4.5,
            "money_worship": 4.0,
            "money_status": 3.8,
            "money_vigilance": 4.2,
        }
        text = interpret_kmsi(scores)
        assert "высокий" in text
        assert "Избегание денег" in text

    def test_low_scores(self):
        scores = {
            "money_avoidance": 1.5,
            "money_worship": 2.0,
            "money_status": 1.0,
            "money_vigilance": 2.2,
        }
        text = interpret_kmsi(scores)
        assert "низкий" in text

    def test_medium_scores(self):
        scores = {
            "money_avoidance": 3.0,
            "money_worship": 2.8,
            "money_status": 3.2,
            "money_vigilance": 2.5,
        }
        text = interpret_kmsi(scores)
        assert "средний" in text

    def test_returns_string(self):
        scores = {"money_avoidance": 3.0}
        result = interpret_kmsi(scores)
        assert isinstance(result, str)
        assert len(result) > 0
