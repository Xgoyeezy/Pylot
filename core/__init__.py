from __future__ import annotations

from . import ai
from . import code_arena
from . import debug
from . import engagement
from . import explain
from . import file_analyzer
from . import memory
from . import onboarding
from . import practice
from . import progress_hub
from . import project
from . import review
from . import run_project
from . import settings_page

from .auth import (
    account_badge,
    auth_is_configured,
    auth_sidebar,
    init_auth,
)

__all__ = [
    "account_badge",
    "auth_is_configured",
    "auth_sidebar",
    "init_auth",
    "ai",
    "code_arena",
    "debug",
    "engagement",
    "explain",
    "file_analyzer",
    "memory",
    "onboarding",
    "practice",
    "progress_hub",
    "project",
    "review",
    "run_project",
    "settings_page",
]
