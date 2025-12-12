"""
Dependency helpers per le routes (es. settings, AiEngine, ecc.).
"""

from ..core.config import Settings, get_settings
from ..services.ai_engine import AiEngine, get_ai_engine


def get_settings_dep() -> Settings:
    """
    Wrapper da usare nelle Depends() delle routes per i settings.
    Per ora è solo un alias di get_settings().
    """
    return get_settings()


def get_ai_engine_dep() -> AiEngine:
    """
    Dependency per ottenere un'istanza di AiEngine.
    """
    return get_ai_engine()

