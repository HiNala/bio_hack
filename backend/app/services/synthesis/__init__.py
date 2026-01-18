"""
Synthesis Service Module

AI-powered research synthesis with multiple modes.
"""

from app.services.synthesis.service import SynthesisService
from app.services.synthesis.prompts import get_prompt_for_mode, get_user_prompt

__all__ = ["SynthesisService", "get_prompt_for_mode", "get_user_prompt"]
