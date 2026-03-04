# AGENTS.md - Agent 工作指南

## 相关文档

- [README](README.md) - 格式规范与构建命令
- [CHANGELOG](CHANGELOG.md) - 版本历史

## 项目概述

本项目是**量潮科技档案**知识库，基于 Jupyter Book 构建的文档项目。非代码仓库，无需 lint/test 流程。

## 目录结构

```
entity/company/
├── index.md           # 首页
├── _config.yml        # Jupyter Book 配置
├── _toc.yml           # 目录结构
├── CHANGELOG.md       # 版本历史
├── README.md          # 项目说明
├── AGENTS.md          # 工作指南
│
├── qtclass/           # 量潮课堂（业务）
├── qtdata/            # 量潮数据（业务）
│
├── connect/           # 沟通（职能）
├── delib/             # 议事（职能）
├── execute/           # 执行（职能）
├── agent/             # 智能体（职能）
├── brand/             # 品牌（职能）
├── code/              # 编程（职能）
├── enterpr/           # 企业（职能）
├── hr/                # 人力资源（职能）
├── iam/               # 身份与访问管理（职能）
├── learn/             # 学习（职能）
├── mr/                # 市场研究（职能）
├── product/           # 产品（职能）
└── scm/               # 供应链（职能）
```

## 构建命令

### Jupyter Book 构建

```bash
# 构建 HTML（单文件方式，避免 EISDIR 错误）
jupyter-book build index.md --site

# 构建并预览
jupyter-book start .

# 清理构建文件
jupyter-book clean .
```

### 质量检查

```bash
# Markdown linting
markdownlint "**/*.md"

# 验证 YAML 配置
yamllint .
```

### 验证清单

- [ ] 所有内部链接指向已存在的文件
- [ ] `_toc.yml` 中引用的文件均已创建
- [ ] YAML 文件语法正确
- [ ] 新增文件已添加到 `_toc.yml`
- [ ] 构建无错误

---

## 人机协作范式

### 核心原则

1. **最小干预**：仅在用户明确请求时操作，不主动修改非相关文件
2. **信息复用**：优先使用已有文档内容，避免重复记录已知信息
3. **查询 index**：每次维护前先查询相关 index.md 了解内容结构和关联
4. **维护 index**：修改内容后同步更新对应 index.md 的内容摘要
5. **验证优先**：完成修改后必须运行构建命令验证
6. **原子提交**：每次提交应包含完整且独立的变更

### 工作流程

1. **理解需求**：明确用户的具体任务和范围
2. **查询 index**：查看相关 index.md 了解内容结构和关联
3. **检查现状**：查看 _toc.yml 确认文件注册状态
4. **执行操作**：按规范进行修改
5. **更新 index**：同步更新相关 index.md 的内容摘要
6. **验证结果**：运行构建命令确认无错误
7. **提交推送**：创建提交并推送到远程

---

## 文档编写规范

### Markdown 风格

- 标题使用中文或英文，保持一致性
- 列表使用 `-` 或 `1.`，保持统一
- 代码块标注语言：` ```python `、` ```bash ` 等
- 链接使用相对路径，内部引用用 `[文字](目录/文件.md)`

### 文件命名

- 使用小写字母
- 单词间用下划线 `_` 分隔
- 示例：`qtclass/index.md`、`big_data.md`

### 目录结构

```
板块名/
├── index.md        # 板块入口，内容摘要
├── README.md       # 板块说明（可选）
├── 子1.md
└── 子目录主题/
    ├── index.md
    └── 内容.md
```

---

## 常见任务

### 添加新文档

1. 在对应目录下创建 `.md` 文件
2. 更新该目录的 `index.md`
3. 在 `_toc.yml` 中注册文件
4. 运行构建命令验证

### 添加新板块

1. 创建目录（遵循命名规范：小写）
2. 创建 `index.md` 介绍板块内容
3. 在 `_toc.yml` 中注册
4. 运行构建验证

### 发布新版本

1. **检查 CHANGELOG**：查看已有版本记录格式
2. **更新 CHANGELOG**：在 `[Unreleased]` 下新增版本块
3. **提交推送**：确保所有变更已推送到远程
4. **创建标签**：`git tag <version>`
5. **推送标签**：`git push --tags`
6. **创建 Release**：`gh release create <version> --title "v<version>" --notes-file CHANGELOG.md`

---

## 版本规范

### 版本号语义

遵循语义化版本（SemVer）：`主版本.次版本.修订号`

### 版本更新规则

| 类型 | 场景 | 示例 |
|------|------|------|
| 修订号 | 错别字修正、格式调整 | 0.1.0 → 0.1.1 |
| 次版本 | 新增内容、新增板块 | 0.1.0 → 0.2.0 |
| 主版本 | 架构调整、板块边界变化 | 0.1.0 → 1.0.0 |

---

## 注意事项

- 本项目为文档项目，无需传统 lint/test 流程
- Jupyter Book 2.x 版本使用 `jupyter-book build .` 会报 EISDIR 错误，需使用单文件构建
- 更新目录结构后需同步更新 index.md、README.md、_toc.yml 三处
