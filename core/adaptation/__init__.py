"""Deterministic adaptation decisions based on observable evidence."""

from .adaptation_engine import AdaptationDecision, decide_adaptation

__all__ = ["AdaptationDecision", "decide_adaptation"]
