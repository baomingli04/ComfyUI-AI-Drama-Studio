# 09 — Prompt Templates

AI 辅助写作提示词模板。

## 用途

存放可复用的 Prompt 模板，用于各种 AI 辅助写作场景，提高写作效率与质量一致性。

## 模板格式规范

每个模板文件应包含：

```markdown
# 模板名称

## 用途
说明此模板用于什么场景

## 所需输入
列出需要填入的变量

| 变量 | 说明 | 来源 |
|------|------|------|
| `{{variable}}` | 描述 | 来自哪个模块的文件 |

## Prompt 模板

（完整的提示词，使用 `{{变量名}}` 标记占位符）
```

## 推荐模板清单

| 模板 | 文件名 | 用途 |
|------|--------|------|
| 章节写作 | `write_chapter.md` | 从细纲生成章节正文 |
| 场景扩写 | `expand_scene.md` | 将简要描述扩展为完整场景 |
| 对话生成 | `write_dialogue.md` | 根据角色性格生成对话 |
| 环境描写 | `describe_setting.md` | 生成沉浸式环境描写 |
| 战斗场景 | `write_combat.md` | 撰写战斗/冲突场景 |
| 章节审阅 | `review_chapter.md` | 对已写章节进行系统审阅 |
| 角色背景 | `character_backstory.md` | 生成角色详细背景故事 |
| 剧情脑暴 | `brainstorm_plot.md` | 头脑风暴剧情发展方向 |
| 章节衔接 | `chapter_transition.md` | 优化章节首尾衔接 |
| 伏笔设计 | `foreshadowing.md` | 设计与规划伏笔 |

## 推荐文件结构

```
09_prompt_templates/
├── README.md
├── write_chapter.md
├── expand_scene.md
├── write_dialogue.md
├── describe_setting.md
├── write_combat.md
├── review_chapter.md
├── character_backstory.md
├── brainstorm_plot.md
├── chapter_transition.md
└── foreshadowing.md
```

## 使用方式

1. 选择对应场景的模板
2. 填入所需变量（从其他模块的文件中获取）
3. 将完成的 Prompt 发送给 AI
4. 根据需要迭代调整输出

## 注意事项

- 所有模板应包含对 `08_style_control` 的风格规则引用
- 模板中应提醒 AI 参考相关的角色设定和世界观
- 持续优化模板，记录效果好的版本
