# 独立安全审计指引

> 使用方式：开一个全新 Claude Code 对话，复制下面这段话发给 AI

---

**粘贴以下内容到新对话：**

```
你是安全审计员。请审查以下三个脱敏后的 Blueprint 文件，检查是否残留业务敏感信息：

/data/profile/ghtorrent/blueprint.md
/data/profile/ghtorrent/blueprint.cue
/data/profile/ghtorrent/blueprint.html

这些文件是从私有数据仓库脱敏后准备开源发布的，原始数据包含：
- 经济学研究者的计量模型变量定义
- 特定客户样本的用户量
- 私有仓库文件名和路径
- 云服务商和区域配置
- 项目成员姓名

请逐项检查以下六类信息是否仍有残留，每条发现标出文件:行号和具体内容：

1. 真实人名/邮箱/联系方式
2. 精确用户量/样本量（≥1000 的具体数字，CSS 色号除外）
3. 真实业务变量名（如 user_id、login、project_count、commit_count、pull_request_count、fork_count、active_fork_count、pull_request_merge_count、self_merged_count、external_merged_count、weekend 及其变体）
4. 具体文件名（.csv、.tar.gz、.sql 后缀的文件名，占位符 {{xxx}} 不算）
5. 云服务商/区域（阿里云、AWS、ecs.、us-west、硅谷 等）
6. 私有仓库地址（github.com/quanttide-tech 等）

输出格式：
- 如果无残留：报告"审计通过，未发现敏感信息残留"
- 如果有残留：逐条列出 file:line → 内容 → 风险等级（高/中/低）
```

---

## 审计后的处理

- **通过**：回到当前对话，执行 squash commit
- **有残留**：回到当前对话，按发现的问题修改文件，再次审计直到通过
