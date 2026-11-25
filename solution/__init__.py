"""初中化学溶液工具（教学向，零依赖）。

对外提供质量分数、稀释加水、溶解度查询与练习纸生成等 API。
"""

from .chem import (
    SOLUBILITY_TABLE,
    SUBSTANCES,
    TEMPERATURES,
    format_number,
    mass_fraction,
    max_dissolve,
    normalize_substance,
    solubility_at,
    solute_needed,
    temperature_key,
    to_integer,
    to_number,
    water_to_add,
)
from .questions import KIND_LABELS, Question, make_questions
from .render import render_demo, render_sheet

__version__ = "0.1.0"

__all__ = [
    "SOLUBILITY_TABLE",
    "SUBSTANCES",
    "TEMPERATURES",
    "KIND_LABELS",
    "Question",
    "format_number",
    "mass_fraction",
    "max_dissolve",
    "normalize_substance",
    "solubility_at",
    "solute_needed",
    "temperature_key",
    "to_integer",
    "to_number",
    "water_to_add",
    "make_questions",
    "render_demo",
    "render_sheet",
    "__version__",
]
