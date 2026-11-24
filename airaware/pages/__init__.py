"""Page renderers for each AirAware AI module.

One module per page plus ``_common`` for shared helpers. The historical
``airaware.pages.<name>_page`` callables are re-exported here so app.py
and the test-suite keep working unchanged.
"""

from .about import about_page
from .assistant import assistant_page
from .community import community_page
from .daily_plan import planner_page
from .explorer import explorer_page
from .home import home_page
from .impact_tracker import impact_page
from .indoor_guardian import indoor_page
from .lifestyle_planner import lifestyle_page

__all__ = [
    "about_page",
    "assistant_page",
    "community_page",
    "explorer_page",
    "home_page",
    "impact_page",
    "indoor_page",
    "lifestyle_page",
    "planner_page",
]
