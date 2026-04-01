# 量潮科技工作简介

## 文件说明

| 文件/目录 | 含义 |
|-----------|------|
| `index.md` | Jupyter Book 首页入口 |
| `_config.yml` | Jupyter Book 配置（站点设置、主题等） |
| `_toc.yml` | 目录结构配置（定义侧边栏导航） |
| `CHANGELOG.md` | 版本历史/更新日志 |
| `README.md` | 项目说明文档 |
| `AGENTS.md` | AI 代理工作指南 |
| `.gitignore` | Git 忽略文件配置 |

## 目录结构

### 业务板块

- `qtclass/` - 量潮课堂
- `qtdata/` - 量潮数据

### 职能板块

- `agent/` - 智能体
- `brand/` - 品牌
- `code/` - 编程
- `connect/` - 沟通
- `delib/` - 议事
- `enterpr/` - 企业
- `execute/` - 执行
- `hr/` - 人力资源
- `iam/` - 身份与访问管理
- `learn/` - 学习
- `mr/` - 市场研究
- `product/` - 产品
- `scm/` - 供应链

## 构建命令

```bash
# 构建 HTML
jupyter-book build index.md --site

# 清理构建文件
jupyter-book clean .
```
