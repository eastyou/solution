# solution

[![CI](https://github.com/eastyou/solution/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/solution/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

初中化学「溶液」单元的计算与出题工具：质量分数、求溶质、稀释加水、溶解度查询，以及可打印的 A4 练习纸。全部使用 Python 标准库，零第三方依赖，输入一律先校验，出错时给出中文提示。

## 特性

- `mass-fraction`：由溶质与溶剂质量直接算出溶质质量分数。
- `solute`：已知溶液质量与质量分数，求所需溶质质量与对应溶剂质量。
- `dilute`：按「稀释前后溶质质量不变」计算需要加入的水量，并给出稀释后的溶液质量。
- `solubility`：内置氯化钠、硝酸钾、蔗糖、氢氧化钙四种物质在 0/20/40/60/80/100 ℃ 的溶解度表，可顺带计算给定水量最多溶解的质量。
- `sheet`：生成 A4 排版的练习纸，题目覆盖四种题型，`--answers` 可附加答案与解析页。
- `demo`：生成概念、公式与例题卡片页，可直接打印或用浏览器查看。
- 所有数值参数都会校验：布尔值不算数值，NaN 与无穷大拒绝，质量、分数、温度均有范围检查。
- 同一个 `--seed` 生成的练习纸完全一致，便于批改与复现。
- 输出文件统一使用 UTF-8 编码，写盘失败时返回中文错误并退出码 2。

## 安装

```bash
python3 -m pip install .
```

也可以不安装，直接在仓库根目录运行：

```bash
python3 -m solution --help
```

## 使用

### 查询版本与帮助

```console
$ python3 -m solution --version
solution 0.1.0
```

### 溶质质量分数

20 g 溶质溶于 80 g 水：

```console
$ python3 -m solution mass-fraction --solute 20 --solvent 80
溶质质量：20 g，溶剂质量：80 g
溶液质量：100 g
溶质质量分数：20%
```

### 求溶质质量

配制 100 g 质量分数为 20% 的溶液：

```console
$ python3 -m solution solute --fraction 20 --solution 100
溶液质量：100 g，质量分数：20%
所需溶质质量：20 g
对应溶剂质量：80 g
```

### 稀释加水

把 100 g 20% 的溶液稀释到 10%：

```console
$ python3 -m solution dilute --mass 100 --fraction 20 --target 10
原溶液：100 g，质量分数：20%
目标质量分数：10%
需要加水：100 g
稀释后溶液质量：200 g
```

### 溶解度查询

```console
$ python3 -m solution solubility --substance 氯化钠 --temp 20
物质：氯化钠
温度：20 ℃
溶解度：36 g / 100 g 水
100 g 水中最多溶解：36 g
```

指定水的质量，会同时给出该温度下的最大溶解量：

```console
$ python3 -m solution solubility --substance 氢氧化钙 --temp 100 --water 200
物质：氢氧化钙
温度：100 ℃
溶解度：0.077 g / 100 g 水
200 g 水中最多溶解：0.154 g
```

### 生成练习纸与示例页

```console
$ python3 -m solution sheet --count 8 --seed 1 -o sheet.html --answers
已生成练习纸：sheet.html（共 8 题，含答案）
$ python3 -m solution demo -o demo.html
已生成示例页：demo.html
```

练习纸为 A4 打印样式，题目下方留有作答横线；加上 `--answers` 后会在文末另起一页输出「参考答案」，每题附一行解析。

### 参数

| 子命令 | 参数 | 说明 |
| --- | --- | --- |
| `mass-fraction` | `--solute` | 溶质质量（g），必须不小于 0 |
| | `--solvent` | 溶剂质量（g），必须不小于 0；溶质与溶剂之和必须大于 0 |
| `solute` | `--fraction` | 质量分数（%），必须大于 0 且不超过 100 |
| | `--solution` | 溶液质量（g），必须大于 0 |
| `dilute` | `--mass` | 原溶液质量（g），必须大于 0 |
| | `--fraction` | 原质量分数（%），必须大于 0 且不超过 100 |
| | `--target` | 目标质量分数（%），必须大于 0 且小于原质量分数 |
| `solubility` | `--substance` | 物质名称：氯化钠、硝酸钾、蔗糖、氢氧化钙 |
| | `--temp` | 温度（℃），仅支持 0/20/40/60/80/100 |
| | `--water` | 水的质量（g），默认 100，必须大于 0 |
| `sheet` | `--count` | 题目数量，1 到 50，默认 8 |
| | `--seed` | 随机种子，默认 1，相同种子结果一致 |
| | `-o` / `--output` | 输出 HTML 路径，必填 |
| | `--answers` | 追加参考答案页 |
| `demo` | `-o` / `--output` | 输出 HTML 路径，必填 |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 执行成功 |
| 2 | 参数缺失或非法、数值校验失败、物质名称未知、温度不在表内、写文件失败 |

## 作为库使用

```python
from solution import (
    mass_fraction,
    solute_needed,
    water_to_add,
    solubility_at,
    max_dissolve,
    make_questions,
    render_sheet,
)

print(mass_fraction(20, 80))              # 20.0
print(solute_needed(20, 100))             # 20.0
print(water_to_add(100, 20, 10))          # 100.0
print(solubility_at("氯化钠", 20))         # 36.0
print(max_dissolve("氯化钠", 20, 50))      # 18.0

questions = make_questions(8, 1)
html_text = render_sheet(questions, answers=True)
with open("sheet.html", "w", encoding="utf-8") as handle:
    handle.write(html_text)
```

`make_questions(count, seed)` 返回 `Question` 列表，每项包含 `kind`、`prompt`、`answer`、`detail` 四个字段；`render_sheet(questions, answers=True)` 返回完整 HTML 字符串，可直接写入文件。

## 开发与测试

测试基于标准库 `unittest`，共 151 个测试方法，覆盖正常值、边界值（0、负数、超范围、空输入、未知物质）、命令行退出码与错误输出、HTML 可被 `html.parser` 解析、以及种子可复现。

```bash
python3 -m unittest discover -s tests -v
```

已在 Python 3.9.6 与 Python 3.15.2 下运行，151 个用例全部通过，两个解释器用例数一致。

## License

[MIT](LICENSE) © 2026 eastyou
