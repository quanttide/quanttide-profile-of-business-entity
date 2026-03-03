# 学习频道

本目录记录外部学习来源，包括 GitHub 仓库、Bilibili 频道等。

## 目录结构

```
learn/channel/
├── README.md                 # 本文件
├── bilibili_频道名.yaml      # Bilibili 频道配置
└── github_组织名.yaml         # GitHub 组织/仓库配置
```

## 配置规范

### GitHub 配置模板

```yaml
name: "组织/仓库名"
github_url: "https://github.com/..."
description: "项目描述"
expertise:
  - "专业领域"
tags:
  - "标签"
language: "主要语言"
license: "许可证"
commits: 提交数
releases: 发布数
features:
  - "功能1"
  - "功能2"
recommended_reason: "推荐理由"
```

### Bilibili 配置模板

```yaml
name: "频道名称"
bilibili_url: "https://space.bilibili.com/..."
description: "频道描述"
expertise:
  - "专业领域"
tags:
  - "标签"
video_count: 视频总数
series_count: 合集数
latest_video:
  title: "最新视频标题"
  publish_date: "YYYY-MM-DD"
  views: "播放量"
  likes: 点赞数
collections:
  - name: "合集名称"
    video_count: 视频数量
    videos:
      - title: "视频标题"
        views: "播放量"
        likes: 点赞数
        duration: "时长"
recommended_reason: "推荐理由"
```

## 更新流程

1. 添加新频道 → 创建对应的 YAML 文件
2. 内容更新 → 定期同步最新信息
3. 重大变更 → 提交更新

## 已有频道

- **github_quanttide**: quanttide 团队的 GitHub 项目
- **bilibili_一杯氢气H2**: 哲学、历史、政治领域的 B 站频道
