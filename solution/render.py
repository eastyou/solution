"""HTML 渲染：A4 练习纸与概念示例页。

只做字符串拼接，不使用 xml.etree；所有动态文本都经过 html.escape。
"""

import html
from typing import List, Sequence

from .questions import KIND_LABELS, Question

_BASE_STYLE = """
    @page { size: A4; margin: 16mm; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 24px 12px;
      background: #f4f5f7;
      color: #1f2328;
      font-family: "Songti SC", "SimSun", "Noto Serif CJK SC", serif;
      font-size: 15px;
      line-height: 1.8;
    }
    .page {
      max-width: 820px;
      margin: 0 auto;
      padding: 36px 40px;
      background: #ffffff;
      border-radius: 10px;
      box-shadow: 0 2px 12px rgba(31, 35, 40, 0.08);
    }
    h1 { font-size: 24px; margin: 0 0 6px; text-align: center; letter-spacing: 2px; }
    h2 { font-size: 16px; margin: 0 0 6px; }
    .meta { margin: 0; text-align: center; color: #57606a; font-size: 13px; }
    .divider { border: 0; border-top: 1px solid #d0d7de; margin: 18px 0; }
    .questions { display: block; }
    .question { margin: 0 0 20px; page-break-inside: avoid; }
    .no { color: #0b5cad; font-weight: bold; }
    .tag {
      display: inline-block;
      margin-left: 6px;
      padding: 0 8px;
      border-radius: 10px;
      background: #e8f0fb;
      color: #0b5cad;
      font-size: 12px;
      font-weight: normal;
      vertical-align: 2px;
    }
    .prompt { margin: 0 0 8px; }
    .workline { border-bottom: 1px solid #c9d1d9; height: 26px; margin: 0 0 6px; }
    .empty { color: #57606a; text-align: center; }
    .answers { page-break-before: always; margin-top: 32px; }
    .answers ol { margin: 0; padding-left: 22px; }
    .answers li { margin: 0 0 14px; page-break-inside: avoid; }
    .answer { margin: 0; font-weight: bold; color: #0b5cad; }
    .detail { margin: 2px 0 0; color: #57606a; font-size: 13px; }
    .sheet-footer { margin-top: 24px; text-align: center; color: #8c959f; font-size: 12px; }
    .card {
      margin: 0 0 18px;
      padding: 14px 18px;
      border: 1px solid #d0d7de;
      border-left: 4px solid #0b5cad;
      border-radius: 6px;
      page-break-inside: avoid;
    }
    .card h2 { color: #0b5cad; }
    .formula {
      display: block;
      margin: 6px 0;
      padding: 8px 10px;
      background: #f6f8fa;
      border-radius: 4px;
      font-family: "Menlo", "Consolas", monospace;
      font-size: 14px;
    }
    .note { margin: 4px 0 0; color: #57606a; font-size: 13px; }
    .step { margin: 2px 0 0; font-size: 14px; }
    code { font-family: "Menlo", "Consolas", monospace; font-size: 13px; }
"""


def _escape(text: str) -> str:
    """转义 HTML 特殊字符。"""
    return html.escape(text, quote=True)


def _document(title: str, body: str) -> str:
    """拼装完整 HTML 文档。"""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>%s</style>\n"
        "</head>\n"
        "<body>\n"
        '<main class="page">\n'
        "%s"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    ) % (_escape(title), _BASE_STYLE, body)


def _question_blocks(questions: Sequence[Question]) -> str:
    """生成题干区。"""
    if not questions:
        return '<p class="empty">暂无题目。</p>\n'
    parts: List[str] = []
    for index, item in enumerate(questions, start=1):
        label = KIND_LABELS.get(item.kind, "溶液计算")
        parts.append(
            '<section class="question">\n'
            '<h2><span class="no">%d.</span><span class="tag">%s</span></h2>\n'
            '<p class="prompt">%s</p>\n'
            '<div class="workline"></div>\n'
            '<div class="workline"></div>\n'
            '<div class="workline"></div>\n'
            "</section>\n"
            % (index, _escape(label), _escape(item.prompt))
        )
    return "".join(parts)


def _answer_blocks(questions: Sequence[Question]) -> str:
    """生成答案与解析区。"""
    if not questions:
        return ""
    parts: List[str] = ['<section class="answers">\n<h2>参考答案</h2>\n<ol>\n']
    for item in questions:
        parts.append(
            "<li>\n"
            '<p class="answer">答案：%s</p>\n'
            '<p class="detail">解析：%s</p>\n'
            "</li>\n" % (_escape(item.answer), _escape(item.detail))
        )
    parts.append("</ol>\n</section>\n")
    return "".join(parts)


def render_sheet(
    questions: Sequence[Question],
    answers: bool = False,
    title: str = "初中化学 溶液 练习纸",
) -> str:
    """渲染 A4 练习纸，answers 为真时追加答案页。"""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("标题不能为空")
    if not isinstance(answers, bool):
        raise ValueError("answers 参数必须是布尔值")
    if questions is None:
        raise TypeError("题目列表不能为 None")
    items: List[Question] = []
    for item in questions:
        if not isinstance(item, Question):
            raise TypeError("题目必须是 Question 对象")
        items.append(item)
    body = [
        '<header class="sheet-header">\n<h1>%s</h1>\n' % _escape(title),
        '<p class="meta">共 %d 题　姓名：__________　班级：__________　日期：__________</p>\n'
        "</header>\n" % len(items),
        '<hr class="divider">\n<section class="questions">\n',
        _question_blocks(items),
        "</section>\n",
    ]
    if answers:
        body.append(_answer_blocks(items))
    body.append(
        '<footer class="sheet-footer">由 solution 生成　共 %d 题</footer>\n' % len(items)
    )
    return _document(title, "".join(body))


def render_demo(title: str = "初中化学 溶液 概念与例题") -> str:
    """渲染概念卡片示例页。"""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("标题不能为空")
    cards: List[str] = []
    cards.append(
        '<section class="card">\n'
        "<h2>一、溶质质量分数</h2>\n"
        '<span class="formula">w = m(溶质) ÷ m(溶液) × 100%　　m(溶液) = m(溶质) + m(溶剂)</span>\n'
        '<p class="note">质量分数是溶质质量占溶液质量的百分比，不随溶液总量变化。</p>\n'
        '<p class="step">例：20 g 氯化钠溶于 80 g 水，w = 20 ÷ (20 + 80) × 100% = 20%。</p>\n'
        "</section>\n"
    )
    cards.append(
        '<section class="card">\n'
        "<h2>二、溶液的稀释</h2>\n"
        '<span class="formula">m1 × w1 = m2 × w2　　加水质量 = m2 - m1</span>\n'
        '<p class="note">加水稀释时，溶质质量保持不变，只是溶液总质量变大。</p>\n'
        '<p class="step">例：100 g 20% 的溶液稀释到 10%，加水 100 g，溶液变为 200 g。</p>\n'
        "</section>\n"
    )
    cards.append(
        '<section class="card">\n'
        "<h2>三、溶解度</h2>\n"
        '<span class="formula">S = 饱和溶液中溶质质量 ÷ 溶剂质量 × 100 g</span>\n'
        '<p class="note">溶解度必须指明温度，单位是 g / 100 g 水；多数固体溶解度随温度升高而增大，'
        "氢氧化钙例外。</p>\n"
        '<p class="step">例：20 ℃ 时氯化钠溶解度为 36 g/100 g 水，50 g 水最多溶解 18 g 氯化钠。</p>\n'
        '<p class="step">饱和溶液的溶质质量分数 = S ÷ (100 + S) × 100%。</p>\n'
        "</section>\n"
    )
    cards.append(
        '<section class="card">\n'
        "<h2>四、常见物质溶解度（g / 100 g 水）</h2>\n"
        '<span class="formula">氯化钠：36.0（20 ℃）　硝酸钾：31.6（20 ℃）</span>\n'
        '<span class="formula">蔗糖：203.9（20 ℃）　氢氧化钙：0.165（20 ℃）</span>\n'
        '<p class="note">数据随温度变化，做题时以题目给出的表为准。</p>\n'
        "</section>\n"
    )
    body = (
        '<header class="sheet-header">\n<h1>%s</h1>\n'
        '<p class="meta">概念、公式与例题</p>\n</header>\n'
        '<hr class="divider">\n' % _escape(title)
    ) + "".join(cards) + '<footer class="sheet-footer">由 solution 生成</footer>\n'
    return _document(title, body)
