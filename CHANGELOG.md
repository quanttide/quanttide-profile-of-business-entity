# CHANGELOG

## [Unreleased]

## [0.1.5] - 2026-06-18

### 新增

- 全业务域配置数据：employees.json、departments.json、courses.json、resources.json、projects.json、datasets.json、interviews.json、resumes.json
- positions.json：岗位定义数据
- auth/users.json：用户认证数据
- .gitignore：排除构建和 IDE 产物

### 变更

- 笔试题统一归入 qtrecurit/questions/ 文件夹
- hr/ 目录更名为 human/
- 运行时认证数据移出版本控制
- 规则文档从 human/ 移至 connect/

## [0.1.4] - 2026-03-28

### 新增

- AGENTS.md、CONTRIBUTING.md、ROADMAP.md：项目管理与协作文档体系
- 招聘考核文档：HR 经理、销售经理、数据工程师、商务拓展、课程助教、项目经理岗位笔试题及邮件模板
- 报价档案：含人员分级、价格表、客户类型、溢价让利规则、审批层级
- 课程文档：量潮课堂大数据导论实践课
- 客户画像与交付清单
- GitHub 组织关系梳理文档

### 变更

- delib/ 目录重构：分拆议事档案、执行记录等子目录
- 许可证切换至 CC-BY-4.0
- 移入 founder 仓库中的招聘考核题和邮件模板

## [0.1.3] - 2026-03-05

### 新增

- 新增 mr/share/license.md：许可分享文档

## [0.1.2] - 2026-03-04

### 新增

- 新增 _config.yml：Jupyter Book 配置
- 新增 _toc.yml：目录结构（业务/职能分类）
- 新增 AGENTS.md：Agent 工作指南

### 变更

- 更新 connect/asset.md 版本信息

## [0.1.1] - 2026-03-04

### 变更

- 重构 delib/ 目录结构
- 重构 execute/ 目录结构
- 删除 delib/asset、delib/default、delib/public 目录
- 新增 delib/bylaw、delib/issue 目录
- 新增 execute/qtclass、execute/learn 目录

## [0.1.0] - 2026-03-03

### 新增

大规模目录重构，新增多个工作区模块。

- 新增 agent/：智能体工程
- 新增 brand/：品牌管理
- 新增 code/：编程
- 新增 delib/：议事
- 新增 enterpr/：企业
- 新增 execute/：执行
- 新增 hr/：人力资源
- 新增 iam/：身份与访问管理
- 新增 learn/：学习
- 新增 mr/：市场研究
- 新增 product/：产品
- 新增 qtclass/：量潮课堂（培训品牌）
- 新增 qtdata/：量潮数据（数据品牌）
- 新增 scm/：供应链
