# 化妆品检测报告样例数据

本目录的 `normalize_indicator.py` 原型使用以下公开检测报告作为样例数据，演示多机构多版式报告的指标标准化过程。

---

## 样例报告来源

### SGS 通标

| 项目 | 内容 |
|---|---|
| 报告编号 | GZCPCH25001949-01_CN |
| 样品名称 | 皙之密 焕活安瓶液 |
| 机构 | 通标标准技术服务有限公司广州分公司 |
| 日期 | 2025-05-21 |
| 页数 | 30 页 |
| 版式 | 文本型 PDF，包含样品信息、评估要求、仪器评估、自我评估、统计分析、附录 |
| 来源 | [PDF 链接](https://bwlchina.com/Upload/Template/yizhu/Files/202509/dfc07da5-28a6-445c-9492-89808f1422c4.pdf) |

抽取指标：皮肤角质层水分含量、皮肤经表皮水分流失 TEWL 值

### CTI 华测

| 项目 | 内容 |
|---|---|
| 报告编号 | A2190104206101001C |
| 样品名称 | Beauté の Hee 面膜仪 |
| 机构 | 华测检测认证集团股份有限公司 |
| 日期 | 2019-05-15 |
| 页数 | 17 页正文 |
| 版式 | 文本型 PDF，目录清晰，含测试区域、时间点、描述性统计、变化值和 P 值 |
| 来源 | [PDF 链接](https://www.facehelper.jp/img/data_ch.pdf) |

抽取指标：皮肤水分含量

### PONY 谱尼

| 项目 | 内容 |
|---|---|
| 报告编号 | MSEPCHUG6541947R7 |
| 样品名称 | 高透活肌技术热水器 |
| 机构 | 谱尼测试集团 |
| 日期 | 2024-12-09 |
| 版式 | 扫描型 PDF，封面/声明/目录/结果页均为图片；每个指标一页左右，含均值、变化率、P 值、柱状图和结果解释 |
| 来源 | [PDF 链接](https://report.ponytest.com/doc/MSEPCHUG6541947R7.pdf) |

抽取指标：经皮失水率 TEWL

---

## 样例数据字段说明

`normalize_indicator.py` 中的 `RAW_EXTRACTED_ROWS` 模拟了 PDF/OCR/表格抽取后的半结构化行，每行包含以下字段：

| 字段 | 说明 | 示例 |
|---|---|---|
| `report_id` | 报告唯一标识 | `SGS_GZCPCH25001949-01_CN` |
| `agency` | 检测机构 | `SGS` / `CTI 华测` / `PONY 谱尼` |
| `sample_name` | 样品名称 | `皙之密 焕活安瓶液` |
| `raw_indicator` | 原始指标名称 | `皮肤经表皮水分流失TEWL值` |
| `timepoint` | 时间点 | `D0` / `D14` / `D28` / `0h` / `0.5h` |
| `group` | 组别 | `测试样品` / `面膜+面膜仪测试区` |
| `n` | 样本量 | `30` |
| `value_cell` | 原始值单元格 | `16.73±4.87` |
| `change_rate_pct` | 变化率 | `-21.10%` / `30.37%` |
| `p_value` | P 值 | `0.000` / `0.014` |
| `significance` | 显著性文字 | `***` / `有显著性差异` |
| `method` | 测试方法 | `仪器探头测量` / `Corneometer 皮肤水分测试` |
| `source_page` | 来源页码 | `4` / `10` / `21` |

---

## 运行示例

```bash
# 提取 TEWL 指标，输出 Markdown 表格
python normalize_indicator.py --indicator tewl

# 提取皮肤水分含量指标，输出 JSON
python normalize_indicator.py --indicator skin_moisture_content --format json
```

### TEWL 输出

| agency | sample | indicator | raw_name | time | group | n | value±sd | change% | improved | p | page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PONY 谱尼 | 高透活肌技术热水器 | 经表皮水分流失 TEWL | 经皮失水率TEWL | D0 | 测试样品 | 30 | 16.73±4.87 | | | | 21 |
| PONY 谱尼 | 高透活肌技术热水器 | 经表皮水分流失 TEWL | 经皮失水率TEWL | D14 | 测试样品 | 30 | 13.2±3.2 | -21.1 | True | 0 | 21 |
| PONY 谱尼 | 高透活肌技术热水器 | 经表皮水分流失 TEWL | 经皮失水率TEWL | D28 | 测试样品 | 30 | 11.21±2.98 | -32.99 | True | 0 | 21 |
| SGS | 皙之密 焕活安瓶液 | 经表皮水分流失 TEWL | 皮肤经表皮水分流失TEWL值 | D14 | 测试样品 | 29 | | -5.62 | True | | 4 |
| SGS | 皙之密 焕活安瓶液 | 经表皮水分流失 TEWL | 皮肤经表皮水分流失TEWL值 | D28 | 测试样品 | 30 | | -10.44 | True | | 4 |

### 皮肤水分含量输出

| agency | sample | indicator | raw_name | time | group | n | value±sd | change% | improved | p | page |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CTI 华测 | Beauté の Hee 面膜仪 | 皮肤角质层水分含量 | 皮肤水分含量 | 0h | 面膜+面膜仪测试区 | 33 | 24.94±4.62 | | | | 10 |
| CTI 华测 | Beauté の Hee 面膜仪 | 皮肤角质层水分含量 | 皮肤水分含量 | 0.5h | 面膜+面膜仪测试区 | 33 | 35.55±8.33 | 42.51 | True | 0.014 | 10 |
| CTI 华测 | Beauté の Hee 面膜仪 | 皮肤角质层水分含量 | 皮肤水分含量 | 1h | 面膜+面膜仪测试区 | 33 | 33.28±8 | 33.42 | True | 0 | 10 |
| CTI 华测 | Beauté の Hee 面膜仪 | 皮肤角质层水分含量 | 皮肤水分含量 | 2h | 面膜+面膜仪测试区 | 33 | 31.52±6.85 | 26.38 | True | 0 | 10 |
| SGS | 皙之密 焕活安瓶液 | 皮肤角质层水分含量 | 皮肤角质层水分含量 | D14 | 测试样品 | 32 | | 30.37 | True | | 4 |
| SGS | 皙之密 焕活安瓶液 | 皮肤角质层水分含量 | 皮肤角质层水分含量 | D28 | 测试样品 | 32 | | 42.59 | True | | 4 |

---

## 参考

- [liangchao-cosmetic-standardization](https://github.com/ztzzh/liangchao-cosmetic-standardization) 原始项目
- `blueprint.md` 本目录下的数据标准化蓝图
- 国家药监局《[化妆品功效宣称评价规范](https://www.nmpa.gov.cn/xxgk/fgwj/xzhgfxwj/20210409160321110.html)》
