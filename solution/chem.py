"""初中化学溶液计算：质量分数、稀释加水、溶解度查询。

所有对外函数都会校验参数：布尔值不算数值，NaN 与无穷大一律拒绝，
非法输入统一抛出带中文说明的 ValueError。
"""

import math
from typing import Dict, Tuple

# 溶解度表：单位 g / 100 g 水，温度为 0/20/40/60/80/100 摄氏度。
SOLUBILITY_TABLE: Dict[str, Dict[int, float]] = {
    "氯化钠": {0: 35.7, 20: 36.0, 40: 36.6, 60: 37.3, 80: 38.4, 100: 39.8},
    "硝酸钾": {0: 13.3, 20: 31.6, 40: 63.9, 60: 110.0, 80: 169.0, 100: 246.0},
    "蔗糖": {0: 179.2, 20: 203.9, 40: 238.1, 60: 287.3, 80: 362.1, 100: 487.2},
    "氢氧化钙": {0: 0.185, 20: 0.165, 40: 0.141, 60: 0.116, 80: 0.094, 100: 0.077},
}

SUBSTANCES: Tuple[str, ...] = ("氯化钠", "硝酸钾", "蔗糖", "氢氧化钙")
TEMPERATURES: Tuple[int, ...] = (0, 20, 40, 60, 80, 100)


def to_number(value: object, label: str) -> float:
    """把外部输入转成有限浮点数，失败时抛出中文 ValueError。"""
    if isinstance(value, bool):
        raise ValueError("%s不能是布尔值" % label)
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("%s不能为空" % label)
        try:
            number = float(text)
        except ValueError:
            raise ValueError("%s必须是数值：%s" % (label, text)) from None
    else:
        raise ValueError("%s必须是数值：%r" % (label, value))
    if math.isnan(number) or math.isinf(number):
        raise ValueError("%s必须是有限数值" % label)
    return number


def to_integer(value: object, label: str) -> int:
    """把外部输入转成整数，允许 "8" 与 8.0，拒绝小数与布尔值。"""
    if isinstance(value, bool):
        raise ValueError("%s必须是整数" % label)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value) or not value.is_integer():
            raise ValueError("%s必须是整数：%r" % (label, value))
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("%s不能为空" % label)
        try:
            return int(text)
        except ValueError:
            raise ValueError("%s必须是整数：%s" % (label, text)) from None
    raise ValueError("%s必须是整数：%r" % (label, value))


def format_number(value: float, digits: int = 4) -> str:
    """格式化数值：最多保留 digits 位小数，并去掉末尾多余的 0。"""
    number = to_number(value, "数值")
    if digits < 0 or digits > 10:
        raise ValueError("小数位数必须在 0 到 10 之间：%d" % digits)
    text = ("%." + str(digits) + "f") % number
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("-0", ""):
        text = "0"
    return text


def mass_fraction(solute: float, solvent: float) -> float:
    """溶质质量分数（百分数）：solute / (solute + solvent) * 100。"""
    solute_value = to_number(solute, "溶质质量")
    solvent_value = to_number(solvent, "溶剂质量")
    if solute_value < 0:
        raise ValueError("溶质质量不能为负数：%s" % format_number(solute_value))
    if solvent_value < 0:
        raise ValueError("溶剂质量不能为负数：%s" % format_number(solvent_value))
    total = solute_value + solvent_value
    if total <= 0:
        raise ValueError("溶质与溶剂质量之和必须大于 0")
    return round(solute_value / total * 100.0, 4)


def solute_needed(fraction: float, solution_mass: float) -> float:
    """已知溶液质量与质量分数，求所需溶质质量。"""
    fraction_value = to_number(fraction, "质量分数")
    mass_value = to_number(solution_mass, "溶液质量")
    if fraction_value <= 0 or fraction_value > 100:
        raise ValueError(
            "质量分数必须大于 0 且不超过 100：%s" % format_number(fraction_value)
        )
    if mass_value <= 0:
        raise ValueError("溶液质量必须大于 0：%s" % format_number(mass_value))
    return round(mass_value * fraction_value / 100.0, 4)


def water_to_add(mass: float, from_pct: float, to_pct: float) -> float:
    """稀释：由 from_pct 稀释到 to_pct，需要加入的水的质量。"""
    mass_value = to_number(mass, "原溶液质量")
    from_value = to_number(from_pct, "原质量分数")
    to_value = to_number(to_pct, "目标质量分数")
    if mass_value <= 0:
        raise ValueError("原溶液质量必须大于 0：%s" % format_number(mass_value))
    if from_value <= 0 or from_value > 100:
        raise ValueError(
            "原质量分数必须大于 0 且不超过 100：%s" % format_number(from_value)
        )
    if to_value <= 0 or to_value >= from_value:
        raise ValueError(
            "目标质量分数必须大于 0 且小于原质量分数：%s" % format_number(to_value)
        )
    solute_mass = mass_value * from_value / 100.0
    target_total = solute_mass * 100.0 / to_value
    return round(target_total - mass_value, 4)


def normalize_substance(name: object) -> str:
    """校验物质名称，返回去掉首尾空白后的标准名称。"""
    if not isinstance(name, str):
        raise ValueError("物质名称必须是字符串")
    text = name.strip()
    if not text:
        raise ValueError("物质名称不能为空")
    if text not in SOLUBILITY_TABLE:
        raise ValueError(
            "未知物质：%s，可选物质：%s" % (text, "、".join(SUBSTANCES))
        )
    return text


def temperature_key(temp: object) -> int:
    """把温度对齐到溶解度表中的温度，不在表内则报错。"""
    value = to_number(temp, "温度")
    if value < 0 or value > 100:
        raise ValueError("温度必须在 0 到 100 摄氏度之间：%s" % format_number(value))
    for key in TEMPERATURES:
        if abs(value - key) < 1e-9:
            return key
    raise ValueError(
        "温度必须是表中的 0/20/40/60/80/100 摄氏度之一：%s" % format_number(value)
    )


def solubility_at(name: str, temp: float) -> float:
    """查询某物质在某温度下的溶解度（g / 100 g 水）。"""
    substance = normalize_substance(name)
    key = temperature_key(temp)
    return SOLUBILITY_TABLE[substance][key]


def max_dissolve(name: str, temp: float, water: float = 100.0) -> float:
    """某温度下，给定质量的水最多能溶解的溶质质量。"""
    substance = normalize_substance(name)
    key = temperature_key(temp)
    water_value = to_number(water, "水的质量")
    if water_value <= 0:
        raise ValueError("水的质量必须大于 0：%s" % format_number(water_value))
    solubility = SOLUBILITY_TABLE[substance][key]
    return round(solubility * water_value / 100.0, 6)
