# 00 — Project Control

项目级元数据与全局设置。

## 用途

此目录存放整个小说项目的核心配置信息，是所有其他模块的参照基准。

## 应包含的内容

| 字段 | 说明 | 示例 |
|------|------|------|
| 书名 | 小说正式名称 | 《星辰大海》 |
| 作者 | 作者笔名 | 沐风 |
| 类型 | 小说类型/标签 | 玄幻、冒险、热血 |
| 目标读者 | 受众群体 | 18-35岁男性读者 |
| 总字数目标 | 计划总字数 | 200万字 |
| 单章字数 | 每章目标字数 | 3000-4000字 |
| 更新计划 | 更新频率 | 每日两更 |
| 当前状态 | 项目进度 | 连载中 / 大纲阶段 / 完结 |
| 创建日期 | 项目启动日期 | 2026-04-10 |

## 推荐文件

- `project.yaml` — 项目配置文件（机器可读）
- `project_notes.md` — 项目备忘与自由笔记
- `progress.md` — 进度追踪日志

## 模板

```yaml
# project.yaml
title: ""
author: ""
genre: []
target_audience: ""
total_word_count_goal: 0
chapter_word_count: "3000-4000"
update_schedule: ""
status: "planning"  # planning | outlining | drafting | revising | complete
created_at: "2026-04-10"
volumes: 0
chapters: 0
```
