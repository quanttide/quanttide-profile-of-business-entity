# Roadmap

## v0.1.x - 渐进式升级

当前版本系列，进行渐进式升级和优化。

## v0.2.0 - 记忆矩阵重构

### 分解 profile 到陈述型记忆矩阵

将 profile 内容分解到整个陈述型记忆矩阵中：

- **Archive** - 工作归档
- **Report** - 工作报告
- **Story** - 品牌故事
- **Journal** - 工作日志
- **Profile** - 工作简介（当前仓库）
- **Brochure** - 宣传册
- **Roadmap** - 工作蓝图
- **Context** - 工作语境
- **Vision** - 工作愿景

### 单仓规范重组

按照单仓规范重新组织仓库结构：

```
/
├── assets/          # 静态资源
├── docs/            # 文档内容
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── AGENTS.md
```