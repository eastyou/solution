"""solution 命令行入口。"""

import argparse
import pathlib
import sys
from typing import Optional, Sequence

from . import __version__
from .chem import (
    format_number,
    mass_fraction,
    max_dissolve,
    solubility_at,
    solute_needed,
    SUBSTANCES,
    to_number,
    water_to_add,
)
from .questions import make_questions
from .render import render_demo, render_sheet


def _ensure_utf8_console() -> None:
    """尽量把标准输出与标准错误切到 UTF-8，失败时忽略。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def _build_parser() -> argparse.ArgumentParser:
    """构造命令行解析器。"""
    parser = argparse.ArgumentParser(
        prog="solution",
        description="初中化学溶液工具：质量分数、稀释加水、溶解度查询与练习纸生成。",
        epilog="示例：solution mass-fraction --solute 20 --solvent 80",
    )
    parser.add_argument(
        "--version", action="version", version="solution %s" % __version__
    )
    subparsers = parser.add_subparsers(dest="command", metavar="命令", required=True)

    fraction_parser = subparsers.add_parser(
        "mass-fraction", help="由溶质与溶剂质量求溶质质量分数"
    )
    fraction_parser.add_argument("--solute", type=float, required=True, help="溶质质量（g）")
    fraction_parser.add_argument("--solvent", type=float, required=True, help="溶剂质量（g）")

    solute_parser = subparsers.add_parser("solute", help="由溶液质量与质量分数求溶质质量")
    solute_parser.add_argument("--fraction", type=float, required=True, help="质量分数（%%）")
    solute_parser.add_argument("--solution", type=float, required=True, help="溶液质量（g）")

    dilute_parser = subparsers.add_parser("dilute", help="计算稀释到目标质量分数需加的水")
    dilute_parser.add_argument("--mass", type=float, required=True, help="原溶液质量（g）")
    dilute_parser.add_argument("--fraction", type=float, required=True, help="原质量分数（%%）")
    dilute_parser.add_argument("--target", type=float, required=True, help="目标质量分数（%%）")

    solubility_parser = subparsers.add_parser("solubility", help="查询内置物质在指定温度下的溶解度")
    solubility_parser.add_argument(
        "--substance", type=str, required=True, help="物质名称：%s" % "、".join(SUBSTANCES)
    )
    solubility_parser.add_argument(
        "--temp", type=float, required=True, help="温度（℃），仅支持 0/20/40/60/80/100"
    )
    solubility_parser.add_argument(
        "--water", type=float, default=100.0, help="水的质量（g），默认 100"
    )

    sheet_parser = subparsers.add_parser("sheet", help="生成 A4 练习纸")
    sheet_parser.add_argument("--count", type=int, default=8, help="题目数量，1 到 50")
    sheet_parser.add_argument("--seed", type=int, default=1, help="随机种子")
    sheet_parser.add_argument("-o", "--output", type=str, required=True, help="输出 HTML 文件")
    sheet_parser.add_argument("--answers", action="store_true", help="附加参考答案页")

    demo_parser = subparsers.add_parser("demo", help="生成概念与例题示例页")
    demo_parser.add_argument("-o", "--output", type=str, required=True, help="输出 HTML 文件")
    return parser


def _write_html(path_text: str, content: str) -> pathlib.Path:
    """写出 HTML 文件，OSError 统一转成中文 ValueError。"""
    if not isinstance(path_text, str) or not path_text.strip():
        raise ValueError("输出路径不能为空")
    path = pathlib.Path(path_text).expanduser()
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ValueError("无法写入文件 %s：%s" % (path, exc)) from None
    return path


def _cmd_mass_fraction(args: argparse.Namespace) -> int:
    solute = to_number(args.solute, "溶质质量")
    solvent = to_number(args.solvent, "溶剂质量")
    fraction = mass_fraction(solute, solvent)
    print("溶质质量：%s g，溶剂质量：%s g" % (format_number(solute), format_number(solvent)))
    print("溶液质量：%s g" % format_number(solute + solvent))
    print("溶质质量分数：%s%%" % format_number(fraction))
    return 0


def _cmd_solute(args: argparse.Namespace) -> int:
    fraction = to_number(args.fraction, "质量分数")
    solution_mass = to_number(args.solution, "溶液质量")
    solute = solute_needed(fraction, solution_mass)
    print(
        "溶液质量：%s g，质量分数：%s%%"
        % (format_number(solution_mass), format_number(fraction))
    )
    print("所需溶质质量：%s g" % format_number(solute))
    print("对应溶剂质量：%s g" % format_number(solution_mass - solute))
    return 0


def _cmd_dilute(args: argparse.Namespace) -> int:
    mass = to_number(args.mass, "原溶液质量")
    from_pct = to_number(args.fraction, "原质量分数")
    to_pct = to_number(args.target, "目标质量分数")
    water = water_to_add(mass, from_pct, to_pct)
    print(
        "原溶液：%s g，质量分数：%s%%" % (format_number(mass), format_number(from_pct))
    )
    print("目标质量分数：%s%%" % format_number(to_pct))
    print("需要加水：%s g" % format_number(water))
    print("稀释后溶液质量：%s g" % format_number(mass + water))
    return 0


def _cmd_solubility(args: argparse.Namespace) -> int:
    name = args.substance.strip()
    temp = to_number(args.temp, "温度")
    water = to_number(args.water, "水的质量")
    solubility = solubility_at(name, temp)
    amount = max_dissolve(name, temp, water)
    print("物质：%s" % name)
    print("温度：%s ℃" % format_number(temp))
    print("溶解度：%s g / 100 g 水" % format_number(solubility))
    print("%s g 水中最多溶解：%s g" % (format_number(water), format_number(amount)))
    return 0


def _cmd_sheet(args: argparse.Namespace) -> int:
    questions = make_questions(args.count, args.seed)
    content = render_sheet(questions, answers=bool(args.answers))
    path = _write_html(args.output, content)
    note = "，含答案" if args.answers else ""
    print("已生成练习纸：%s（共 %d 题%s）" % (path, len(questions), note))
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    content = render_demo()
    path = _write_html(args.output, content)
    print("已生成示例页：%s" % path)
    return 0


def _run(args: argparse.Namespace) -> int:
    """按子命令分发。"""
    command = args.command
    if command == "mass-fraction":
        return _cmd_mass_fraction(args)
    if command == "solute":
        return _cmd_solute(args)
    if command == "dilute":
        return _cmd_dilute(args)
    if command == "solubility":
        return _cmd_solubility(args)
    if command == "sheet":
        return _cmd_sheet(args)
    if command == "demo":
        return _cmd_demo(args)
    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数：成功返回 0，输入非法或写文件失败返回 2。"""
    _ensure_utf8_console()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
