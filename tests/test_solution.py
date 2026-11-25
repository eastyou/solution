"""solution 包的单元测试（仅使用标准库 unittest）。"""

import contextlib
import dataclasses
import html.parser
import io
import math
import os
import re
import sys
import tempfile
import unittest
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import solution
from solution import (
    KIND_LABELS,
    SOLUBILITY_TABLE,
    SUBSTANCES,
    TEMPERATURES,
    Question,
    format_number,
    make_questions,
    mass_fraction,
    max_dissolve,
    normalize_substance,
    render_demo,
    render_sheet,
    solubility_at,
    solute_needed,
    temperature_key,
    to_integer,
    to_number,
    water_to_add,
)
from solution.cli import main


class _TagCollector(html.parser.HTMLParser):
    """收集 HTML 标签与文本，用于校验生成的页面。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: List[str] = []
        self.texts: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        self.tags.append(tag)

    def handle_data(self, data: str) -> None:
        self.texts.append(data)


def parse_html(text: str) -> Tuple[List[str], str]:
    """解析 HTML，返回标签列表与拼接后的文本。"""
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector.tags, "".join(collector.texts)


def run_main(argv: List[str]) -> Tuple[int, str, str]:
    """执行 main 并捕获标准输出与标准错误。"""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def main_exit_code(argv: List[str]) -> int:
    """执行 main，返回退出码（含 argparse 触发的 SystemExit）。"""
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            return main(argv)
        except SystemExit as exc:
            return int(exc.code) if exc.code is not None else 0


def answer_value(text: str) -> float:
    """从答案字符串中取出数值。"""
    return float(text.replace(" g", "").replace("%", "").strip())


class TestToNumber(unittest.TestCase):
    def test_accepts_int(self) -> None:
        self.assertEqual(to_number(3, "质量"), 3.0)

    def test_accepts_float(self) -> None:
        self.assertEqual(to_number(2.5, "质量"), 2.5)

    def test_accepts_numeric_string(self) -> None:
        self.assertEqual(to_number(" 12.5 ", "质量"), 12.5)

    def test_rejects_bool(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            to_number(True, "质量")
        self.assertIn("布尔", str(ctx.exception))

    def test_rejects_text(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            to_number("abc", "质量")
        self.assertIn("必须是数值", str(ctx.exception))

    def test_rejects_empty_string(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            to_number("   ", "质量")
        self.assertIn("不能为空", str(ctx.exception))

    def test_rejects_nan(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            to_number(float("nan"), "质量")
        self.assertIn("有限数值", str(ctx.exception))

    def test_rejects_inf(self) -> None:
        with self.assertRaises(ValueError):
            to_number(float("inf"), "质量")

    def test_rejects_none(self) -> None:
        with self.assertRaises(ValueError):
            to_number(None, "质量")


class TestToInteger(unittest.TestCase):
    def test_accepts_int(self) -> None:
        self.assertEqual(to_integer(8, "数量"), 8)

    def test_accepts_integral_string(self) -> None:
        self.assertEqual(to_integer(" 12 ", "数量"), 12)

    def test_accepts_integral_float(self) -> None:
        self.assertEqual(to_integer(8.0, "数量"), 8)

    def test_rejects_fraction_float(self) -> None:
        with self.assertRaises(ValueError):
            to_integer(8.5, "数量")

    def test_rejects_bool(self) -> None:
        with self.assertRaises(ValueError):
            to_integer(False, "数量")

    def test_rejects_decimal_string(self) -> None:
        with self.assertRaises(ValueError):
            to_integer("8.0", "数量")

    def test_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            to_integer("", "数量")

    def test_rejects_inf_float(self) -> None:
        with self.assertRaises(ValueError):
            to_integer(float("inf"), "数量")


class TestFormatNumber(unittest.TestCase):
    def test_strips_trailing_zeros(self) -> None:
        self.assertEqual(format_number(20.0), "20")

    def test_keeps_significant_decimals(self) -> None:
        self.assertEqual(format_number(20.5), "20.5")

    def test_small_value(self) -> None:
        self.assertEqual(format_number(0.185), "0.185")

    def test_negative_zero(self) -> None:
        self.assertEqual(format_number(-0.0000001), "0")

    def test_custom_digits(self) -> None:
        self.assertEqual(format_number(0.185, 1), "0.2")

    def test_rejects_bad_digits(self) -> None:
        with self.assertRaises(ValueError):
            format_number(1.0, 11)

    def test_rejects_nan(self) -> None:
        with self.assertRaises(ValueError):
            format_number(float("nan"))


class TestMassFraction(unittest.TestCase):
    def test_normal(self) -> None:
        self.assertAlmostEqual(mass_fraction(20, 80), 20.0)

    def test_zero_solute(self) -> None:
        self.assertAlmostEqual(mass_fraction(0, 80), 0.0)

    def test_zero_solvent(self) -> None:
        self.assertAlmostEqual(mass_fraction(20, 0), 100.0)

    def test_both_zero_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            mass_fraction(0, 0)
        self.assertIn("大于 0", str(ctx.exception))

    def test_negative_solute_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            mass_fraction(-1, 80)
        self.assertIn("负数", str(ctx.exception))

    def test_negative_solvent_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mass_fraction(20, -80)

    def test_accepts_numeric_strings(self) -> None:
        self.assertAlmostEqual(mass_fraction("20", "80"), 20.0)

    def test_rejects_bool(self) -> None:
        with self.assertRaises(ValueError):
            mass_fraction(True, 80)

    def test_rejects_nan(self) -> None:
        with self.assertRaises(ValueError):
            mass_fraction(float("nan"), 80)

    def test_one_third(self) -> None:
        self.assertAlmostEqual(mass_fraction(1, 3), 25.0)

    def test_large_values(self) -> None:
        self.assertAlmostEqual(mass_fraction(1e9, 1e9), 50.0)


class TestSoluteNeeded(unittest.TestCase):
    def test_normal(self) -> None:
        self.assertAlmostEqual(solute_needed(20, 100), 20.0)

    def test_decimal_fraction(self) -> None:
        self.assertAlmostEqual(solute_needed(1.5, 200), 3.0)

    def test_full_fraction(self) -> None:
        self.assertAlmostEqual(solute_needed(100, 50), 50.0)

    def test_zero_fraction_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solute_needed(0, 100)

    def test_over_hundred_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solute_needed(101, 100)

    def test_zero_solution_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solute_needed(20, 0)

    def test_negative_solution_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solute_needed(20, -5)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solute_needed(True, 100)

    def test_string_inputs(self) -> None:
        self.assertAlmostEqual(solute_needed("20", "100"), 20.0)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solute_needed(20, float("nan"))


class TestWaterToAdd(unittest.TestCase):
    def test_normal(self) -> None:
        self.assertAlmostEqual(water_to_add(100, 20, 10), 100.0)

    def test_strong_dilution(self) -> None:
        self.assertAlmostEqual(water_to_add(50, 20, 5), 150.0)

    def test_from_hundred(self) -> None:
        self.assertAlmostEqual(water_to_add(100, 100, 50), 100.0)

    def test_zero_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(0, 20, 10)

    def test_equal_fractions_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(100, 20, 20)

    def test_target_above_source_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(100, 10, 20)

    def test_zero_target_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(100, 20, 0)

    def test_zero_source_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(100, 0, 10)

    def test_source_over_hundred_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(100, 120, 10)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            water_to_add(100, float("nan"), 10)

    def test_result_is_finite(self) -> None:
        self.assertTrue(math.isfinite(water_to_add(80, 25, 5)))


class TestSolubility(unittest.TestCase):
    def test_sodium_chloride_20(self) -> None:
        self.assertAlmostEqual(solubility_at("氯化钠", 20), 36.0)

    def test_potassium_nitrate_60(self) -> None:
        self.assertAlmostEqual(solubility_at("硝酸钾", 60), 110.0)

    def test_sucrose_100(self) -> None:
        self.assertAlmostEqual(solubility_at("蔗糖", 100), 487.2)

    def test_calcium_hydroxide_0(self) -> None:
        self.assertAlmostEqual(solubility_at("氢氧化钙", 0), 0.185)

    def test_float_temperature(self) -> None:
        self.assertAlmostEqual(solubility_at("氯化钠", 20.0), 36.0)

    def test_surrounding_spaces(self) -> None:
        self.assertAlmostEqual(solubility_at(" 氯化钠 ", 20), 36.0)

    def test_temperature_not_in_table(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            solubility_at("氯化钠", 30)
        self.assertIn("0/20/40/60/80/100", str(ctx.exception))

    def test_temperature_below_zero(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            solubility_at("氯化钠", -20)
        self.assertIn("温度必须在", str(ctx.exception))

    def test_temperature_above_hundred(self) -> None:
        with self.assertRaises(ValueError):
            solubility_at("氯化钠", 120)

    def test_bool_temperature_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solubility_at("氯化钠", True)

    def test_unknown_substance(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            solubility_at("白糖", 20)
        self.assertIn("未知物质", str(ctx.exception))

    def test_empty_substance(self) -> None:
        with self.assertRaises(ValueError):
            solubility_at("  ", 20)

    def test_non_string_substance(self) -> None:
        with self.assertRaises(ValueError):
            solubility_at(123, 20)

    def test_all_table_values_positive(self) -> None:
        for name in SUBSTANCES:
            for temp in TEMPERATURES:
                value = solubility_at(name, temp)
                self.assertGreater(value, 0.0, msg="%s %d" % (name, temp))
                self.assertTrue(math.isfinite(value))


class TestMaxDissolve(unittest.TestCase):
    def test_hundred_grams_water(self) -> None:
        self.assertAlmostEqual(max_dissolve("氯化钠", 20, 100), 36.0)

    def test_fifty_grams_water(self) -> None:
        self.assertAlmostEqual(max_dissolve("氯化钠", 20, 50), 18.0)

    def test_two_hundred_grams_water(self) -> None:
        self.assertAlmostEqual(max_dissolve("硝酸钾", 60, 200), 220.0)

    def test_hardly_soluble_substance(self) -> None:
        self.assertAlmostEqual(max_dissolve("氢氧化钙", 20, 1000), 1.65)

    def test_default_water(self) -> None:
        self.assertAlmostEqual(max_dissolve("蔗糖", 20), 203.9)

    def test_zero_water_rejected(self) -> None:
        with self.assertRaises(ValueError):
            max_dissolve("氯化钠", 20, 0)

    def test_negative_water_rejected(self) -> None:
        with self.assertRaises(ValueError):
            max_dissolve("氯化钠", 20, -1)

    def test_nan_water_rejected(self) -> None:
        with self.assertRaises(ValueError):
            max_dissolve("氯化钠", 20, float("nan"))

    def test_unknown_substance_rejected(self) -> None:
        with self.assertRaises(ValueError):
            max_dissolve("未知物", 20, 100)


class TestHelpers(unittest.TestCase):
    def test_normalize_substance(self) -> None:
        self.assertEqual(normalize_substance("  硝酸钾 "), "硝酸钾")

    def test_normalize_rejects_unknown(self) -> None:
        with self.assertRaises(ValueError):
            normalize_substance("盐酸")

    def test_temperature_key_integer(self) -> None:
        self.assertEqual(temperature_key(40.0), 40)

    def test_temperature_key_rejects(self) -> None:
        with self.assertRaises(ValueError):
            temperature_key(45)


class TestQuestions(unittest.TestCase):
    def test_count_one(self) -> None:
        self.assertEqual(len(make_questions(1, 1)), 1)

    def test_count_fifty(self) -> None:
        self.assertEqual(len(make_questions(50, 1)), 50)

    def test_count_zero_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            make_questions(0, 1)
        self.assertIn("1 到 50", str(ctx.exception))

    def test_count_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(51, 1)

    def test_count_bool_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(True, 1)

    def test_seed_reproducible(self) -> None:
        self.assertEqual(make_questions(12, 7), make_questions(12, 7))

    def test_different_seed_differs(self) -> None:
        first = make_questions(20, 1)
        second = make_questions(20, 2)
        self.assertNotEqual([item.prompt for item in first], [item.prompt for item in second])

    def test_all_kinds_covered(self) -> None:
        kinds = {item.kind for item in make_questions(8, 3)}
        self.assertEqual(kinds, {"fraction", "solute", "dilute", "solubility"})

    def test_items_are_questions(self) -> None:
        for item in make_questions(10, 4):
            self.assertIsInstance(item, Question)

    def test_fields_not_empty(self) -> None:
        for item in make_questions(20, 5):
            self.assertIn(item.kind, KIND_LABELS)
            self.assertTrue(item.prompt.strip())
            self.assertTrue(item.answer.strip())
            self.assertTrue(item.detail.strip())

    def test_fraction_answers_consistent(self) -> None:
        questions = [item for item in make_questions(40, 11) if item.kind == "fraction"]
        self.assertTrue(questions)
        for item in questions:
            matched = re.search(
                r"把 (\d+(?:\.\d+)?) g .*? 完全溶解在 (\d+(?:\.\d+)?) g 水中", item.prompt
            )
            self.assertIsNotNone(matched, msg=item.prompt)
            solute = float(matched.group(1))
            solvent = float(matched.group(2))
            expected = solute / (solute + solvent) * 100.0
            self.assertAlmostEqual(answer_value(item.answer), expected, places=4)

    def test_solute_answers_consistent(self) -> None:
        questions = [item for item in make_questions(40, 12) if item.kind == "solute"]
        self.assertTrue(questions)
        for item in questions:
            matched = re.search(r"要配制 (\d+(?:\.\d+)?) g 质量分数为 (\d+(?:\.\d+)?)%", item.prompt)
            self.assertIsNotNone(matched, msg=item.prompt)
            mass = float(matched.group(1))
            fraction = float(matched.group(2))
            expected = mass * fraction / 100.0
            self.assertAlmostEqual(answer_value(item.answer), expected, places=4)

    def test_dilute_answers_consistent(self) -> None:
        questions = [item for item in make_questions(40, 13) if item.kind == "dilute"]
        self.assertTrue(questions)
        for item in questions:
            matched = re.search(
                r"将 (\d+(?:\.\d+)?) g 质量分数为 (\d+(?:\.\d+)?)% 的 .*?"
                r"稀释成质量分数为 (\d+(?:\.\d+)?)%",
                item.prompt,
            )
            self.assertIsNotNone(matched, msg=item.prompt)
            mass = float(matched.group(1))
            from_pct = float(matched.group(2))
            to_pct = float(matched.group(3))
            expected = mass * (from_pct - to_pct) / to_pct
            self.assertAlmostEqual(answer_value(item.answer), expected, places=4)

    def test_solubility_answers_consistent(self) -> None:
        questions = [item for item in make_questions(40, 14) if item.kind == "solubility"]
        self.assertTrue(questions)
        for item in questions:
            matched = re.search(
                r"溶解度为 (\d+(?:\.\d+)?) g/100 g 水，则 (\d+(?:\.\d+)?) g 水中", item.prompt
            )
            self.assertIsNotNone(matched, msg=item.prompt)
            solubility = float(matched.group(1))
            water = float(matched.group(2))
            expected = solubility * water / 100.0
            self.assertAlmostEqual(answer_value(item.answer), expected, places=4)

    def test_question_is_frozen(self) -> None:
        item = make_questions(1, 1)[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.prompt = "改不了"  # type: ignore[misc]


class TestRenderSheet(unittest.TestCase):
    def test_returns_doctype(self) -> None:
        text = render_sheet(make_questions(4, 1))
        self.assertTrue(text.startswith("<!DOCTYPE html>"))

    def test_parsed_by_html_parser(self) -> None:
        tags, text = parse_html(render_sheet(make_questions(4, 1), answers=True))
        for tag in ("html", "head", "body", "main", "title", "style"):
            self.assertIn(tag, tags)
        self.assertIn("溶质质量分数", text)

    def test_default_title(self) -> None:
        self.assertIn("初中化学 溶液 练习纸", render_sheet(make_questions(2, 1)))

    def test_answers_hidden_by_default(self) -> None:
        self.assertNotIn("参考答案", render_sheet(make_questions(3, 1)))

    def test_answers_shown_when_requested(self) -> None:
        self.assertIn("参考答案", render_sheet(make_questions(3, 1), answers=True))

    def test_answers_contain_details(self) -> None:
        text = render_sheet(make_questions(4, 2), answers=True)
        self.assertIn("解析：", text)

    def test_title_escaped(self) -> None:
        text = render_sheet(make_questions(1, 1), title="<script>")
        self.assertIn("&lt;script&gt;", text)
        self.assertNotIn("<script>", text)

    def test_prompt_escaped(self) -> None:
        item = Question(kind="fraction", prompt="<b>题干</b>", answer="1%", detail="略")
        text = render_sheet([item])
        self.assertIn("&lt;b&gt;", text)
        self.assertNotIn("<b>题干</b>", text)

    def test_empty_questions_allowed(self) -> None:
        text = render_sheet([])
        self.assertIn("暂无题目", text)
        tags, _ = parse_html(text)
        self.assertIn("body", tags)

    def test_question_count_matches(self) -> None:
        text = render_sheet(make_questions(8, 6))
        self.assertEqual(text.count('class="question"'), 8)

    def test_accepts_tuple_sequence(self) -> None:
        items = tuple(make_questions(2, 1))
        self.assertIn("共 2 题", render_sheet(items))

    def test_none_questions_rejected(self) -> None:
        with self.assertRaises(TypeError):
            render_sheet(None)  # type: ignore[arg-type]

    def test_non_question_item_rejected(self) -> None:
        with self.assertRaises(TypeError):
            render_sheet(["不是题目"])  # type: ignore[list-item]

    def test_non_bool_answers_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(make_questions(1, 1), answers="yes")  # type: ignore[arg-type]

    def test_empty_title_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_sheet(make_questions(1, 1), title="   ")


class TestRenderDemo(unittest.TestCase):
    def test_returns_doctype(self) -> None:
        self.assertTrue(render_demo().startswith("<!DOCTYPE html>"))

    def test_parsed_by_html_parser(self) -> None:
        tags, text = parse_html(render_demo())
        for tag in ("html", "head", "body", "main"):
            self.assertIn(tag, tags)
        self.assertIn("溶解度", text)

    def test_contains_concepts(self) -> None:
        text = render_demo()
        for keyword in ("溶质质量分数", "稀释", "溶解度", "饱和溶液"):
            self.assertIn(keyword, text)

    def test_custom_title_escaped(self) -> None:
        text = render_demo("<img src=x>")
        self.assertIn("&lt;img", text)
        self.assertNotIn("<img src=x>", text)

    def test_empty_title_rejected(self) -> None:
        with self.assertRaises(ValueError):
            render_demo("   ")


class TestCli(unittest.TestCase):
    def make_temp_dir(self) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return tmp.name

    def test_mass_fraction_success(self) -> None:
        code, out, err = run_main(["mass-fraction", "--solute", "20", "--solvent", "80"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("溶质质量分数：20%", out)

    def test_mass_fraction_zero_solute(self) -> None:
        code, out, _ = run_main(["mass-fraction", "--solute", "0", "--solvent", "80"])
        self.assertEqual(code, 0)
        self.assertIn("0%", out)

    def test_mass_fraction_zero_both_returns_two(self) -> None:
        code, _, err = run_main(["mass-fraction", "--solute", "0", "--solvent", "0"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_mass_fraction_negative_returns_two(self) -> None:
        code, _, err = run_main(["mass-fraction", "--solute", "-5", "--solvent", "80"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_mass_fraction_nan_returns_two(self) -> None:
        code, _, err = run_main(["mass-fraction", "--solute", "nan", "--solvent", "80"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_solute_success(self) -> None:
        code, out, err = run_main(["solute", "--fraction", "20", "--solution", "100"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("所需溶质质量：20 g", out)
        self.assertIn("对应溶剂质量：80 g", out)

    def test_solute_bad_fraction_returns_two(self) -> None:
        code, _, err = run_main(["solute", "--fraction", "120", "--solution", "100"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_dilute_success(self) -> None:
        code, out, err = run_main(
            ["dilute", "--mass", "100", "--fraction", "20", "--target", "10"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("需要加水：100 g", out)
        self.assertIn("稀释后溶液质量：200 g", out)

    def test_dilute_target_above_source_returns_two(self) -> None:
        code, _, err = run_main(
            ["dilute", "--mass", "100", "--fraction", "10", "--target", "20"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_solubility_success(self) -> None:
        code, out, err = run_main(["solubility", "--substance", "氯化钠", "--temp", "20"])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("溶解度：36 g / 100 g 水", out)
        self.assertIn("100 g 水中最多溶解：36 g", out)

    def test_solubility_custom_water(self) -> None:
        code, out, _ = run_main(
            ["solubility", "--substance", "氯化钠", "--temp", "20", "--water", "50"]
        )
        self.assertEqual(code, 0)
        self.assertIn("50 g 水中最多溶解：18 g", out)

    def test_solubility_unknown_returns_two(self) -> None:
        code, _, err = run_main(["solubility", "--substance", "白糖", "--temp", "20"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)
        self.assertIn("未知物质", err)

    def test_solubility_temp_missing_from_table_returns_two(self) -> None:
        code, _, err = run_main(["solubility", "--substance", "氯化钠", "--temp", "25"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_solubility_zero_water_returns_two(self) -> None:
        code, _, err = run_main(
            ["solubility", "--substance", "氯化钠", "--temp", "20", "--water", "0"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_sheet_writes_file(self) -> None:
        target = os.path.join(self.make_temp_dir(), "sheet.html")
        code, out, err = run_main(["sheet", "--count", "8", "--seed", "1", "-o", target])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("已生成练习纸", out)
        with open(target, encoding="utf-8") as handle:
            data = handle.read()
        self.assertTrue(data.startswith("<!DOCTYPE html>"))
        self.assertNotIn("参考答案", data)

    def test_sheet_with_answers(self) -> None:
        target = os.path.join(self.make_temp_dir(), "sheet.html")
        code, out, _ = run_main(["sheet", "--count", "5", "--seed", "2", "-o", target, "--answers"])
        self.assertEqual(code, 0)
        self.assertIn("含答案", out)
        with open(target, encoding="utf-8") as handle:
            self.assertIn("参考答案", handle.read())

    def test_sheet_default_count_is_eight(self) -> None:
        target = os.path.join(self.make_temp_dir(), "sheet.html")
        code, out, _ = run_main(["sheet", "-o", target])
        self.assertEqual(code, 0)
        self.assertIn("共 8 题", out)

    def test_sheet_custom_count(self) -> None:
        target = os.path.join(self.make_temp_dir(), "sheet.html")
        code, _, _ = run_main(["sheet", "--count", "3", "--seed", "5", "-o", target])
        self.assertEqual(code, 0)
        with open(target, encoding="utf-8") as handle:
            self.assertEqual(handle.read().count('class="question"'), 3)

    def test_sheet_seed_reproducible(self) -> None:
        folder = self.make_temp_dir()
        first = os.path.join(folder, "a.html")
        second = os.path.join(folder, "b.html")
        run_main(["sheet", "--count", "6", "--seed", "42", "-o", first])
        run_main(["sheet", "--count", "6", "--seed", "42", "-o", second])
        with open(first, encoding="utf-8") as handle:
            first_text = handle.read()
        with open(second, encoding="utf-8") as handle:
            second_text = handle.read()
        self.assertEqual(first_text, second_text)

    def test_sheet_count_zero_returns_two(self) -> None:
        target = os.path.join(self.make_temp_dir(), "sheet.html")
        code, _, err = run_main(["sheet", "--count", "0", "-o", target])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_sheet_count_too_large_returns_two(self) -> None:
        target = os.path.join(self.make_temp_dir(), "sheet.html")
        code, _, err = run_main(["sheet", "--count", "51", "-o", target])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_sheet_write_failure_returns_two(self) -> None:
        target = os.path.join(self.make_temp_dir(), "缺失目录", "sheet.html")
        code, _, err = run_main(["sheet", "-o", target])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_demo_writes_file(self) -> None:
        target = os.path.join(self.make_temp_dir(), "demo.html")
        code, out, err = run_main(["demo", "-o", target])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("已生成示例页", out)
        with open(target, encoding="utf-8") as handle:
            self.assertIn("溶质质量分数", handle.read())

    def test_demo_write_failure_returns_two(self) -> None:
        target = os.path.join(self.make_temp_dir(), "缺失目录", "demo.html")
        code, _, err = run_main(["demo", "-o", target])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_help_exits_zero(self) -> None:
        self.assertEqual(main_exit_code(["--help"]), 0)

    def test_version_exits_zero(self) -> None:
        self.assertEqual(main_exit_code(["--version"]), 0)

    def test_no_command_exits_two(self) -> None:
        self.assertEqual(main_exit_code([]), 2)

    def test_unknown_command_exits_two(self) -> None:
        self.assertEqual(main_exit_code(["unknown"]), 2)

    def test_missing_argument_exits_two(self) -> None:
        self.assertEqual(main_exit_code(["mass-fraction", "--solute", "20"]), 2)


class TestPackage(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(solution.__version__, "0.1.0")

    def test_exports_callable(self) -> None:
        for name in (
            "mass_fraction",
            "solute_needed",
            "water_to_add",
            "solubility_at",
            "max_dissolve",
            "make_questions",
            "render_sheet",
            "render_demo",
        ):
            self.assertTrue(callable(getattr(solution, name)), msg=name)

    def test_solubility_table_shape(self) -> None:
        self.assertEqual(set(SOLUBILITY_TABLE), set(SUBSTANCES))
        for name in SUBSTANCES:
            self.assertEqual(tuple(sorted(SOLUBILITY_TABLE[name])), TEMPERATURES)

    def test_kind_labels(self) -> None:
        self.assertEqual(
            set(KIND_LABELS), {"fraction", "solute", "dilute", "solubility"}
        )


if __name__ == "__main__":
    unittest.main()
