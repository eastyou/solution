"""练习纸题目生成：质量分数、求溶质、稀释加水、溶解度。

同一个 seed 生成完全相同的题目列表，方便教师复现与批改。
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .chem import (
    SUBSTANCES,
    TEMPERATURES,
    format_number,
    mass_fraction,
    max_dissolve,
    solubility_at,
    solute_needed,
    to_integer,
    water_to_add,
)

KIND_LABELS: Dict[str, str] = {
    "fraction": "溶质质量分数",
    "solute": "求溶质质量",
    "dilute": "溶液稀释",
    "solubility": "溶解度",
}

# 适合配制溶液的三种物质（氢氧化钙溶解度太小，不参与质量分数练习）。
_SOLUTION_NAMES: Tuple[str, ...] = ("氯化钠", "硝酸钾", "蔗糖")

# (溶质质量, 溶剂质量)，质量分数均为整数百分数。
_FRACTION_PAIRS: Tuple[Tuple[int, int], ...] = (
    (10, 90),
    (20, 80),
    (25, 75),
    (15, 45),
    (30, 70),
    (40, 60),
    (5, 95),
    (50, 50),
    (8, 32),
    (12, 48),
)

# (溶液质量, 质量分数)，溶质质量均为整数克。
_SOLUTE_COMBOS: Tuple[Tuple[int, int], ...] = (
    (200, 10),
    (150, 20),
    (200, 15),
    (200, 25),
    (300, 5),
    (250, 40),
    (300, 50),
    (100, 30),
)

# (原溶液质量, 原质量分数, 目标质量分数)，需加水的质量均为整数克。
_DILUTE_COMBOS: Tuple[Tuple[int, int, int], ...] = (
    (100, 20, 10),
    (150, 20, 10),
    (200, 25, 10),
    (100, 10, 5),
    (120, 15, 5),
    (200, 40, 20),
    (50, 20, 5),
    (80, 25, 5),
)

_WATER_AMOUNTS: Tuple[int, ...] = (50, 100, 200, 250)


@dataclass(frozen=True)
class Question:
    """一道练习题：题干、答案与解析。"""

    kind: str
    prompt: str
    answer: str
    detail: str


def _fraction_question(rng: random.Random) -> Question:
    solute, solvent = rng.choice(_FRACTION_PAIRS)
    name = rng.choice(_SOLUTION_NAMES)
    percent = mass_fraction(solute, solvent)
    prompt = "把 %s g %s 完全溶解在 %s g 水中，所得溶液的溶质质量分数是多少？" % (
        format_number(solute),
        name,
        format_number(solvent),
    )
    answer = "%s%%" % format_number(percent)
    detail = "w = %s / (%s + %s) × 100%% = %s%%" % (
        format_number(solute),
        format_number(solute),
        format_number(solvent),
        format_number(percent),
    )
    return Question(kind="fraction", prompt=prompt, answer=answer, detail=detail)


def _solute_question(rng: random.Random) -> Question:
    solution_mass, fraction = rng.choice(_SOLUTE_COMBOS)
    name = rng.choice(_SOLUTION_NAMES)
    solute = solute_needed(fraction, solution_mass)
    solvent_mass = solution_mass - solute
    prompt = "要配制 %s g 质量分数为 %s%% 的 %s 溶液，需要 %s 多少克？" % (
        format_number(solution_mass),
        format_number(fraction),
        name,
        name,
    )
    answer = "%s g" % format_number(solute)
    detail = "m(溶质) = %s g × %s%% = %s g，m(水) = %s - %s = %s g" % (
        format_number(solution_mass),
        format_number(fraction),
        format_number(solute),
        format_number(solution_mass),
        format_number(solute),
        format_number(solvent_mass),
    )
    return Question(kind="solute", prompt=prompt, answer=answer, detail=detail)


def _dilute_question(rng: random.Random) -> Question:
    mass, from_pct, to_pct = rng.choice(_DILUTE_COMBOS)
    name = rng.choice(_SOLUTION_NAMES)
    water = water_to_add(mass, from_pct, to_pct)
    final_mass = mass + water
    prompt = "将 %s g 质量分数为 %s%% 的 %s 溶液稀释成质量分数为 %s%% 的溶液，需要加水多少克？" % (
        format_number(mass),
        format_number(from_pct),
        name,
        format_number(to_pct),
    )
    answer = "%s g" % format_number(water)
    detail = "稀释前后溶质质量不变：%s × %s%% = %s × %s%%，需要加水 %s g" % (
        format_number(mass),
        format_number(from_pct),
        format_number(final_mass),
        format_number(to_pct),
        format_number(water),
    )
    return Question(kind="dilute", prompt=prompt, answer=answer, detail=detail)


def _solubility_question(rng: random.Random) -> Question:
    name = rng.choice(SUBSTANCES)
    temp = rng.choice(TEMPERATURES)
    water = rng.choice(_WATER_AMOUNTS)
    solubility = solubility_at(name, temp)
    amount = max_dissolve(name, temp, water)
    prompt = "已知 %s ℃ 时 %s 的溶解度为 %s g/100 g 水，则 %s g 水中最多能溶解多少克 %s？" % (
        format_number(temp),
        name,
        format_number(solubility),
        format_number(water),
        name,
    )
    answer = "%s g" % format_number(amount)
    detail = "%s g × %s g / 100 g = %s g" % (
        format_number(water),
        format_number(solubility),
        format_number(amount),
    )
    return Question(kind="solubility", prompt=prompt, answer=answer, detail=detail)


_MAKERS = {
    "fraction": _fraction_question,
    "solute": _solute_question,
    "dilute": _dilute_question,
    "solubility": _solubility_question,
}

_KIND_ORDER: Tuple[str, ...] = ("fraction", "solute", "dilute", "solubility")


def make_questions(count: int, seed: int) -> List[Question]:
    """按 count 与 seed 生成题目，题型尽量均匀覆盖四种。"""
    total = to_integer(count, "题目数量")
    if total < 1 or total > 50:
        raise ValueError("题目数量必须在 1 到 50 之间：%d" % total)
    seed_value = to_integer(seed, "随机种子")
    rng = random.Random(seed_value)
    kinds: List[str] = [_KIND_ORDER[index % len(_KIND_ORDER)] for index in range(total)]
    rng.shuffle(kinds)
    return [_MAKERS[kind](rng) for kind in kinds]
