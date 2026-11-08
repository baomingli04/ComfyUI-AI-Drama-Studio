# 06 — Manuscripts

正文稿件。

## 用途

此目录存放每一章的正式文稿（草稿及修订版本）。

## 文件命名规范

| 命名格式 | 含义 |
|----------|------|
| `ch_001_draft.md` | 第1章初稿 |
| `ch_001_v2.md` | 第1章第2版 |
| `ch_001_v3.md` | 第1章第3版 |
| `ch_001_final.md` | 第1章定稿 |

## 文稿格式

```markdown
# 第XXX章：章节名

---

（正文内容，纯净的叙事文本）

（不要在正文中插入批注或修改标记，评审意见放在 07_chapter_reviews）

---

<!-- metadata
word_count: XXXX
status: draft | revised | final
drafted_at: 2026-04-10
last_modified: 2026-04-10
-->
```

## 推荐文件结构

```
06_manuscripts/
├── README.md
├── ch_001_draft.md
├── ch_001_v2.md
├── ch_002_draft.md
└── ...
```

## 注意事项

- **永远不要覆盖原始稿件**，创建新版本文件
- 正文应保持干净，不包含编辑注释
- 每次写作前先阅读对应的章节细纲（`05_chapter_outlines`）
- 写作时遵循风格控制规则（`08_style_control`）
- 可使用提示词模板（`09_prompt_templates`）辅助写作
