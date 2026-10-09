"""
化妆品检测报告标准化样例原型

演示如何从多机构报告中抽取同一功效指标并统一输出为长表。
参考自：liangchao-cosmetic-standardization/prototype_extract_indicator.py

运行:
    python sample.py --indicator tewl
    python sample.py --indicator skin_moisture_content
"""

import argparse
import json
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any


# ---------------------------------------------------------------------------
# 指标本体：标准码 → 标准名称、同义词、单位、改善方向
# ---------------------------------------------------------------------------

INDICATOR_ONTOLOGY: dict[str, dict[str, Any]] = {
    "skin_moisture_content": {
        "canonical_name": "皮肤角质层水分含量",
        "aliases": [
            "皮肤角质层水分含量",
            "皮肤水分含量",
            "水分含量",
            "皮肤含水量",
            "Corneometer Unit",
        ],
        "unit": "instrument_index",
        "effect_direction": "higher_is_better",
    },
    "tewl": {
        "canonical_name": "经表皮水分流失 TEWL",
        "aliases": [
            "皮肤经表皮水分流失TEWL值",
            "皮肤经表皮水分流失 TEWL 值",
            "经皮失水率TEWL",
            "经皮失水率 TEWL",
            "TEWL",
            "transepidermal water loss",
        ],
        "unit": "g/(h·m²) or instrument_index",
        "effect_direction": "lower_is_better",
    },
    "skin_firmness_r0": {
        "canonical_name": "面部紧致度 R0",
        "aliases": ["面部紧致度R0", "面部紧致度 R0", "紧致度", "R0"],
        "unit": "instrument_index",
        "effect_direction": "lower_is_better",
    },
    "skin_elasticity_r2": {
        "canonical_name": "面部皮肤弹性 R2",
        "aliases": ["面部皮肤弹性R2", "面部皮肤弹性 R2", "皮肤弹性", "R2"],
        "unit": "instrument_index",
        "effect_direction": "higher_is_better",
    },
    "skin_color_ita": {
        "canonical_name": "皮肤颜色 ITA°",
        "aliases": ["皮肤颜色ITA", "皮肤颜色 ITA°", "ITA", "ITA°"],
        "unit": "degree",
        "effect_direction": "higher_is_better",
    },
}


# ---------------------------------------------------------------------------
# 模拟抽取层输出的半结构化行（生产环境中由 PDF/OCR/表格抽取模块产生）
# ---------------------------------------------------------------------------

RAW_EXTRACTED_ROWS: list[dict[str, Any]] = [
    # SGS 报告 GZCPCH25001949-01_CN
    {
        "report_id": "SGS_GZCPCH25001949-01_CN",
        "agency": "SGS",
        "sample_name": "皙之密 焕活安瓶液",
        "raw_indicator": "皮肤角质层水分含量",
        "timepoint": "D14",
        "group": "测试样品",
        "n": 32,
        "value_cell": None,
        "change_rate_pct": "30.37%",
        "p_value": None,
        "significance": "有显著性差异",
        "method": "仪器探头测量",
        "source_page": 4,
    },
    {
        "report_id": "SGS_GZCPCH25001949-01_CN",
        "agency": "SGS",
        "sample_name": "皙之密 焕活安瓶液",
        "raw_indicator": "皮肤角质层水分含量",
        "timepoint": "D28",
        "group": "测试样品",
        "n": 32,
        "value_cell": None,
        "change_rate_pct": "42.59%",
        "p_value": None,
        "significance": "有显著性差异",
        "method": "仪器探头测量",
        "source_page": 4,
    },
    {
        "report_id": "SGS_GZCPCH25001949-01_CN",
        "agency": "SGS",
        "sample_name": "皙之密 焕活安瓶液",
        "raw_indicator": "皮肤经表皮水分流失TEWL值",
        "timepoint": "D14",
        "group": "测试样品",
        "n": 29,
        "value_cell": None,
        "change_rate_pct": "-5.62%",
        "p_value": None,
        "significance": "有显著性差异",
        "method": "仪器探头测量",
        "source_page": 4,
    },
    {
        "report_id": "SGS_GZCPCH25001949-01_CN",
        "agency": "SGS",
        "sample_name": "皙之密 焕活安瓶液",
        "raw_indicator": "皮肤经表皮水分流失TEWL值",
        "timepoint": "D28",
        "group": "测试样品",
        "n": 30,
        "value_cell": None,
        "change_rate_pct": "-10.44%",
        "p_value": None,
        "significance": "有显著性差异",
        "method": "仪器探头测量",
        "source_page": 4,
    },
    # CTI 华测报告 A2190104206101001C
    {
        "report_id": "CTI_A2190104206101001C",
        "agency": "CTI 华测",
        "sample_name": "Beauté の Hee 面膜仪",
        "raw_indicator": "皮肤水分含量",
        "timepoint": "0h",
        "group": "面膜+面膜仪测试区",
        "n": 33,
        "value_cell": "24.94±4.62",
        "change_rate_pct": None,
        "p_value": None,
        "significance": None,
        "method": "Corneometer 皮肤水分测试",
        "source_page": 10,
    },
    {
        "report_id": "CTI_A2190104206101001C",
        "agency": "CTI 华测",
        "sample_name": "Beauté の Hee 面膜仪",
        "raw_indicator": "皮肤水分含量",
        "timepoint": "0.5h",
        "group": "面膜+面膜仪测试区",
        "n": 33,
        "value_cell": "35.55±8.33",
        "change_rate_pct": "42.51%",
        "p_value": "0.014",
        "significance": "相对面膜测试区有显著性差异",
        "method": "Corneometer 皮肤水分测试",
        "source_page": 10,
    },
    {
        "report_id": "CTI_A2190104206101001C",
        "agency": "CTI 华测",
        "sample_name": "Beauté の Hee 面膜仪",
        "raw_indicator": "皮肤水分含量",
        "timepoint": "1h",
        "group": "面膜+面膜仪测试区",
        "n": 33,
        "value_cell": "33.28±8.00",
        "change_rate_pct": "33.42%",
        "p_value": "0.000",
        "significance": "相对面膜测试区有显著性差异",
        "method": "Corneometer 皮肤水分测试",
        "source_page": 10,
    },
    {
        "report_id": "CTI_A2190104206101001C",
        "agency": "CTI 华测",
        "sample_name": "Beauté の Hee 面膜仪",
        "raw_indicator": "皮肤水分含量",
        "timepoint": "2h",
        "group": "面膜+面膜仪测试区",
        "n": 33,
        "value_cell": "31.52±6.85",
        "change_rate_pct": "26.38%",
        "p_value": "0.000",
        "significance": "相对面膜测试区有显著性差异",
        "method": "Corneometer 皮肤水分测试",
        "source_page": 10,
    },
    # PONY 谱尼报告 MSEPCHUG6541947R7
    {
        "report_id": "PONY_MSEPCHUG6541947R7",
        "agency": "PONY 谱尼",
        "sample_name": "高透活肌技术热水器",
        "raw_indicator": "经皮失水率TEWL",
        "timepoint": "D0",
        "group": "测试样品",
        "n": 30,
        "value_cell": "16.73±4.87",
        "change_rate_pct": None,
        "p_value": None,
        "significance": None,
        "method": "仪器测试",
        "source_page": 21,
    },
    {
        "report_id": "PONY_MSEPCHUG6541947R7",
        "agency": "PONY 谱尼",
        "sample_name": "高透活肌技术热水器",
        "raw_indicator": "经皮失水率TEWL",
        "timepoint": "D14",
        "group": "测试样品",
        "n": 30,
        "value_cell": "13.20±3.20",
        "change_rate_pct": "-21.10%",
        "p_value": "0.000",
        "significance": "***",
        "method": "仪器测试",
        "source_page": 21,
    },
    {
        "report_id": "PONY_MSEPCHUG6541947R7",
        "agency": "PONY 谱尼",
        "sample_name": "高透活肌技术热水器",
        "raw_indicator": "经皮失水率TEWL",
        "timepoint": "D28",
        "group": "测试样品",
        "n": 30,
        "value_cell": "11.21±2.98",
        "change_rate_pct": "-32.99%",
        "p_value": "0.000",
        "significance": "***",
        "method": "仪器测试",
        "source_page": 21,
    },
]


# ---------------------------------------------------------------------------
# 标准化核心逻辑
# ---------------------------------------------------------------------------


@dataclass
class NormalizedObservation:
    """标准化后的单行观测事实"""

    report_id: str
    agency: str
    sample_name: str
    canonical_indicator_code: str
    canonical_indicator_name: str
    raw_indicator: str
    timepoint: str
    timepoint_order: float
    group: str
    n: int | None
    value: float | None
    sd: float | None
    change_rate_pct: float | None
    effect_direction: str
    improvement: bool | None
    p_value: float | None
    significance: str | None
    method: str | None
    source_page: int | None


def compact_text(text: str) -> str:
    """压缩文本：去空格、去特殊符号、转小写"""
    return re.sub(r"[\s_\-：:，,。()（）°值含量]", "", text).lower()


def canonicalize_indicator(raw_name: str, threshold: float = 0.58) -> tuple[str, float]:
    """将原始指标名映射到标准指标码"""
    if raw_name in INDICATOR_ONTOLOGY:
        return raw_name, 1.0

    raw_compact = compact_text(raw_name)

    # 强特征优先匹配
    if "tewl" in raw_compact or "经皮失水" in raw_compact or "经表皮水分流失" in raw_compact:
        return "tewl", 1.0
    if "ita" in raw_compact:
        return "skin_color_ita", 1.0
    if re.search(r"(^|[^a-z0-9])r0($|[^a-z0-9])", raw_compact) or "紧致度r0" in raw_compact:
        return "skin_firmness_r0", 1.0
    if re.search(r"(^|[^a-z0-9])r2($|[^a-z0-9])", raw_compact) or "弹性r2" in raw_compact:
        return "skin_elasticity_r2", 1.0

    best_code, best_score = "", 0.0
    for code, meta in INDICATOR_ONTOLOGY.items():
        candidates = [meta["canonical_name"], *meta["aliases"]]
        for alias in candidates:
            alias_compact = compact_text(alias)
            if not alias_compact:
                continue
            contains_match = alias_compact in raw_compact or raw_compact in alias_compact
            if contains_match and len(alias_compact) >= 4:
                score = 1.0
            else:
                score = SequenceMatcher(None, raw_compact, alias_compact).ratio()
            if score > best_score:
                best_code, best_score = code, score

    if best_score < threshold:
        raise ValueError(f"无法映射指标: {raw_name!r}, best_score={best_score:.2f}")
    return best_code, best_score


def parse_mean_sd(value_cell: str | None) -> tuple[float | None, float | None]:
    """从 'mean±sd' 格式解析均值与标准差"""
    if not value_cell:
        return None, None
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*[±+]\s*(-?\d+(?:\.\d+)?)", value_cell)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.search(r"-?\d+(?:\.\d+)?", value_cell)
    return (float(m.group(0)), None) if m else (None, None)


def parse_percent(value: str | float | None) -> float | None:
    """解析百分比字符串为浮点数"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(m.group(0)) if m else None


def parse_p_value(value: str | float | None) -> float | None:
    """解析 P 值"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if value.strip().startswith("<"):
        return float(value.strip()[1:])
    m = re.search(r"\d+(?:\.\d+)?", value)
    return float(m.group(0)) if m else None


def timepoint_order(timepoint: str) -> float:
    """将时间点字符串转为可排序数值（以天为单位）"""
    lower = timepoint.lower().replace(" ", "")
    if lower.endswith("h"):
        return float(lower[:-1]) / 24
    if lower.startswith("d"):
        return float(lower[1:])
    return 9999.0


def infer_improvement(
    effect_direction: str, change_rate_pct: float | None
) -> bool | None:
    """根据指标改善方向和变化率判断结果是否改善"""
    if change_rate_pct is None:
        return None
    if effect_direction == "higher_is_better":
        return change_rate_pct > 0
    if effect_direction == "lower_is_better":
        return change_rate_pct < 0
    return None


def normalize_rows(rows: list[dict[str, Any]]) -> list[NormalizedObservation]:
    """批量标准化抽取行为标准化观测事实"""
    observations: list[NormalizedObservation] = []
    for row in rows:
        code, _score = canonicalize_indicator(row["raw_indicator"])
        meta = INDICATOR_ONTOLOGY[code]
        mean, sd = parse_mean_sd(row.get("value_cell"))
        change_rate = parse_percent(row.get("change_rate_pct"))
        effect_direction = meta["effect_direction"]
        observations.append(
            NormalizedObservation(
                report_id=row["report_id"],
                agency=row["agency"],
                sample_name=row["sample_name"],
                canonical_indicator_code=code,
                canonical_indicator_name=meta["canonical_name"],
                raw_indicator=row["raw_indicator"],
                timepoint=row["timepoint"],
                timepoint_order=timepoint_order(row["timepoint"]),
                group=row["group"],
                n=row.get("n"),
                value=mean,
                sd=sd,
                change_rate_pct=change_rate,
                effect_direction=effect_direction,
                improvement=infer_improvement(effect_direction, change_rate),
                p_value=parse_p_value(row.get("p_value")),
                significance=row.get("significance"),
                method=row.get("method"),
                source_page=row.get("source_page"),
            )
        )
    return observations


def extract_same_indicator(
    rows: list[dict[str, Any]], target_indicator: str
) -> list[NormalizedObservation]:
    """从多份报告中提取同一指标，输出统一长表"""
    target_code, _score = canonicalize_indicator(target_indicator)
    normalized = normalize_rows(rows)
    matched = [r for r in normalized if r.canonical_indicator_code == target_code]
    return sorted(matched, key=lambda r: (r.report_id, r.group, r.timepoint_order))


# ---------------------------------------------------------------------------
# 输出格式化
# ---------------------------------------------------------------------------


def to_markdown(rows: list[NormalizedObservation]) -> str:
    headers = [
        "agency",
        "sample",
        "indicator",
        "raw_name",
        "time",
        "group",
        "n",
        "value±sd",
        "change%",
        "improved",
        "p",
        "page",
    ]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        value_sd = ""
        if r.value is not None:
            value_sd = f"{r.value:g}" + (f"±{r.sd:g}" if r.sd is not None else "")
        lines.append(
            "| "
            + " | ".join(
                [
                    r.agency,
                    r.sample_name,
                    r.canonical_indicator_name,
                    r.raw_indicator,
                    r.timepoint,
                    r.group,
                    "" if r.n is None else str(r.n),
                    value_sd,
                    "" if r.change_rate_pct is None else f"{r.change_rate_pct:g}",
                    "" if r.improvement is None else str(r.improvement),
                    "" if r.p_value is None else f"{r.p_value:g}",
                    "" if r.source_page is None else str(r.source_page),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="化妆品检测报告指标标准化")
    parser.add_argument(
        "--indicator",
        default="tewl",
        help="原始或标准指标名称，如 tewl / skin_moisture_content / TEWL",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="markdown",
        help="输出格式",
    )
    args = parser.parse_args()

    rows = extract_same_indicator(RAW_EXTRACTED_ROWS, args.indicator)
    if args.format == "json":
        print(json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2))
    else:
        print(to_markdown(rows))


if __name__ == "__main__":
    main()
