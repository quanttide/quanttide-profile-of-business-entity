# SEC信贷协议识别

## 背景

项目涉及从美国贷款合同网站批量下载文档，需要从下载的各类文件中筛选出 Credit Agreement 文件。

当前实现的问题：所有匹配 `loan` / `credit` 关键词的 8-K 附件都被处理，未做 Credit Agreement 分类，存在大量误召回。

## 模式识别

### 分类对象：Exhibit 级别，而不是 Filing 级别

8-K 主文主要用于发现和解析 Exhibit links。Credit Agreement 分类应发生在 Exhibit level，而不是 Filing level。

流程：

```
8-K Filing
    ↓
解析 Exhibit Index / Exhibit links
    ↓
逐个 Exhibit 提取 metadata 和 text_head
    ↓
对每个 Exhibit 做 Credit Agreement 分类
    ↓
目标附件进入后续字段抽取
```

### 文件标题特征

目标文件不一定标题就是 `CREDIT AGREEMENT`。需要覆盖以下子类型：

**Original Agreement 类：**
- `Credit Agreement` / `Loan Agreement`
- `Amended and Restated Credit Agreement`
- `First Lien Credit Agreement` / `Revolving Credit Agreement`

**Amendment 类：**
- `Amendment No. X to ... Credit Agreement`
- `First Amendment`（正文引用 Existing Credit Agreement）
- `Amended Credit Agreement`

**Extension 类：**
- `Extension Agreement`
- `Commitment Extension`
- `Maturity Date Extension`

**Related Letter 类：**
- Extension Consent Letter（Administrative Agent 发给 Bank Group 征求意见）

### 章节结构：Article II 的主题比编号更有区分度

`Article I` / `Article II` 本身区分度不足——Indenture 也有类似章节结构。

真正有区分度的是 **章节主题**：

| 维度 | Credit Agreement 倾向 | Indenture / Notes 倾向 |
|------|----------------------|----------------------|
| Article II 主题 | The Loans / Commitments / Borrowings | The Notes |
| 合同角色 | Borrower, Lender, Administrative Agent | Issuer, Trustee, Indenture Trustee |
| 交易对象 | Loans, Commitments, Credit Facility | Notes, Debt Securities |
| 常见条款 | Maturity Date, Interest Rate, Revolving Credit | Trust Indenture Act, Note Register |

### 角色实体比普通关键词更稳定

`loan` / `credit` 等通用关键词太宽。合同角色更能体现文件类型。

**强正特征（Credit Agreement 倾向）：**
- Borrower / Lender / Lenders
- Administrative Agent / Issuing Bank
- Revolving Credit Lender / Extending Bank
- Commitment / Credit Facility

**强负特征（Indenture / Notes 倾向）：**
- Issuer / Trustee / Indenture Trustee
- Noteholder / Holder
- Notes / Trust Indenture Act / Debt Securities

单个词不一定足够——`Notes` 也可能出现在 Credit Agreement 的引用条款中。更稳妥的方式是组合判断：

- `INDENTURE` + `Indenture Trustee` + `The Notes` → 强负
- `Borrower` + `Administrative Agent` + `Credit Agreement` → 强正
- `Extension Agreement` + `Credit Agreement` + `Maturity Date` → Credit Agreement Extension

### 分类输出：证据驱动

不输出简单 true / false，输出结构化结果：

```
{
  "document_type": "credit_agreement_amendment",
  "is_target": true,
  "confidence": 0.94,
  "positive_evidence": [
    "title contains Amendment to Credit Agreement",
    "text references Existing Credit Agreement",
    "Administrative Agent appears in the opening section"
  ],
  "negative_evidence": []
}
```

`document_type` 包括：
- `credit_agreement_original`
- `credit_agreement_amendment`
- `credit_agreement_extension`
- `credit_agreement_related_letter`
- `indenture_or_notes`（跳过）
- `eight_k_summary`（不进入抽取，只用于发现 Exhibit links）
- `other`（跳过）

不同 `document_type` 后续抽取策略不同：

| document_type | 后续抽取重点 |
|--------------|-------------|
| `credit_agreement_original` | Borrower、Lender、Administrative Agent、Commitment、Interest Rate、Maturity Date |
| `credit_agreement_amendment` | Amendment Effective Date、被修改条款、Commitment、Maturity Date |
| `credit_agreement_extension` | 新的 Maturity Date / Revolving Credit Termination Date |
| `credit_agreement_related_letter` | 先保留标记，不进入完整合同字段抽取 |
| `indenture_or_notes` | 跳过 |
| `eight_k_summary` | 只用于发现 Exhibit links |

## 真实样本验证

| Filing | Exhibit | 类型 | 关键证据 |
|--------|---------|------|---------|
| ENVIRI Corp 8-K EX-10.1 | Amendment No. 14 | Credit Agreement Amendment | 标题含 Amendment；正文引用 Existing Credit Agreement；出现 Administrative Agent、Revolving Credit Commitments |
| Goodyear 10-Q EX-10.2 | First Amendment | Credit Agreement Amendment | 标题 First Amendment；正文引用 Amended and Restated First Lien Credit Agreement；出现 Administrative Agent、Lenders、Term SOFR |
| CenterPoint Energy 8-K EX-10.1 | Extension Agreement | Extension | 标题 Extension Agreement；出现 Borrower、Administrative Agent、Credit Agreement、Maturity Date |
| OGE Energy 8-K EX-10.01 | Extension Consent Letter | Related Letter | To/From 格式；Administrative Agent 发给 Bank Group；请求延长 Revolving Credit Termination Date |
| Ford Credit Auto Lease Trust 8-K EX-4.1 | INDENTURE | 负例（Indenture） | 标题 INDENTURE；主体为 Issuer 和 Indenture Trustee；Article II 主题为 The Notes |

## 实现方案

### Step 1：解析 Exhibit

对每个 8-K Filing，先解析 Exhibit Index 或 Exhibit links，得到每个附件的基础信息：

```
form_type
exhibit_type
exhibit_description
file_name
source_url
text_head（前几十 KB，不需要加载完整文件）
```

### Step 2：抽取证据

对每个 Exhibit，先抽取可解释证据，不直接给结论：

```
title_evidence
role_evidence
section_topic_evidence
term_evidence
negative_evidence
```

### Step 3：LLM 判断 + 规则验收

LLM 基于已抽取的证据判断 `document_type`，规则引擎验收强正/强负特征：

- LLM 判断为 `credit_agreement_original` 但标题是 `INDENTURE` + 正文出现 `Indenture Trustee`、`The Notes` → 降级为 `indenture_or_notes`
- 标题是 `Extension Agreement` + 正文引用 `Credit Agreement`、`Borrower`、`Administrative Agent`、`Maturity Date` → `credit_agreement_extension`
- 8-K 主文摘要 → 不进入合同正文抽取

### Step 4：人工复核（仅冲突样本）

不设全量人工复核，只在以下情况引入：
- LLM 判断为 Credit Agreement，但规则检测到强负特征
- LLM 判断为非目标文件，但标题或 Exhibit description 明确包含 `Credit Agreement`
- 新出现的文档类型无法归入现有 `document_type`
- 需要沉淀新的专家规则或更新 few-shot

## 验收标准

- [ ] 8-K 主文不应直接进入合同字段抽取
- [ ] 明确的 Indenture / Notes 文件应被排除
- [ ] Amendment / Extension 类 Credit Agreement 不应因缺少 Article I/II 被误删
- [ ] 每个分类结果输出 `positive_evidence` 和 `negative_evidence`
- [ ] 规则和 LLM 冲突的样本被记录，便于后续更新

## 性能优化

难点：批量下载爆内存

当前措施：
- V18 版本已实现流式写入 CSV（非全量内存缓存）
- 每个 CIK 处理完释放内存 + 每 10 轮 GC.collect()

仍存在的风险：
- **全量索引 OOM**：初始下载索引一次性拉取整个 CIK 历史目录
- **大文本内存穿透**：附件提取时全量加载文本到内存
- **I/O 与 CPU 资源竞争**：下载与 extract 同时进行，峰值内存叠加

已确认的优化方案：
- **流式提取**：按行/分块读取（yield 生成器）
- **内存映射**：超过 50MB 的超大附件使用 mmap
- **索引流式构建**：分页或按年滚动查询
- **生产者-消费者解耦**：[验证通过] 下载与提取彻底分离，消除资源竞争
- **Phase 实施策略**：Phase 1 文件读取改造，Phase 2 Producer-Consumer 架构，Phase 3 内存和速率监控

## 参考资料

- **数据下载器**：[ryansmccoy/py-sec-edgar](https://github.com/ryansmccoy/py-sec-edgar) — SEC EDGAR 专业下载器，支持 10-K/10-Q/8-K 等表单类型的批量下载与提取
- **SEC EDGAR 主页**：[https://www.sec.gov/edgar](https://www.sec.gov/edgar) — 美国证监会 EDGAR 数据库入口
- **SEC EDGAR 开发者指南**：[https://www.sec.gov/developer](https://www.sec.gov/developer) — SEC 数据访问规范与 Fair Access 指南
