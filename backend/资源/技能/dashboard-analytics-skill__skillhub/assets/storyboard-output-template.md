# 分镜稿 · 输出模板（参考样板）

> 实际输出时请把此模板**完整复制**到对话里，按小说内容填字段；保留字段结构和分隔符，方便用户在腾讯文档/Notion/语雀 里粘贴后自动成表。

---

## 一、题材与风格判读

| 项 | 取值（示例） |
|---|---|
| **题材** | 玄幻 / 都市 / 言情 / 悬疑 / 古风 / 科幻 / 历史 / 军事 / 其他 |
| **人称** | 第一人称 / 第三人称 |
| **情绪基调** | 阴郁 / 热血 / 轻松 / 悲怆 / 紧张 / 暧昧 / 压抑 / 爆发 / 其他 |
| **视觉风格** | 网文短视频（默认） / 电影写实 / 自定义 |
| **风格标签前缀** | digital illustration, stylized, high contrast, 8K |

---

## 二、主角色统一外貌描述

> **重要**：以下描述会在所有镜头该人物出现的 prompt 中**原样复用**。请一次性写完整。

| 角色 | 外貌统一描述块（中英双发） |
|---|---|
| **主角名** | 中文：`...（外貌描写）`<br>英文：`... (appearance)` |
| **配角1** | 中文：`...`<br>英文：`...` |
| **配角2** | 中文：`...`<br>英文：`...` |

---

## 三、场景清单

| 场景编号 | 场景一句话描述 |
|---|---|
| S1 | （例：雨夜小巷，男女主初遇） |
| S2 | （例：咖啡馆第二次对话，关系推进） |
| S3 | （例：废弃工厂对峙，大战前夕） |

---

## 四、分镜表（主交付物）

| 编号 | 时长 | 景别 | 运镜 | 中文 prompt | 英文 prompt |
|---|---|---|---|---|---|
| S1-1 | 4s | 近景 | 推 + 微摇 | 黑袍男子剑眉星目、发丝凌乱，缓缓抬头看向雨幕。深夜小巷，路灯昏黄，雨丝在他发梢汇成水滴。近景，推镜微摇，情绪压抑而隐忍。digital illustration, stylized, high contrast, neon accents, 8K | A black-robed man with sharp brows and disheveled hair slowly looks up into the rain. Dim alleyway, yellow streetlight, raindrops gathering at his hair tips. Close-up, slow push-in with subtle pan, restrained anguish. digital illustration, stylized, high contrast, neon accents, 8K |
| S1-2 | 3s | 特写 | 固定 | ... | ... |
| ... | | | | | |

---

## 五、可复制提示词块（用于一键粘到豆包）

> 每个镜头独立一段，前后用 `--- 镜头 S1-1 ---` 分隔。整个块一次性复制即可。

### 镜头 S1-1（4s · 近景 · 推 + 微摇）

**中文 prompt：**
> 黑袍男子剑眉星目、发丝凌乱，缓缓抬头看向雨幕。深夜小巷，路灯昏黄，雨丝在他发梢汇成水滴。近景，推镜微摇，情绪压抑而隐忍。digital illustration, stylized, high contrast, neon accents, 8K

**English prompt：**
> A black-robed man with sharp brows and disheveled hair slowly looks up into the rain. Dim alleyway, yellow streetlight, raindrops gathering at his hair tips. Close-up, slow push-in with subtle pan, restrained anguish. digital illustration, stylized, high contrast, neon accents, 8K

---

### 镜头 S1-2（3s · 特写 · 固定）

**中文 prompt：**
> （照填）

**English prompt：**
> （照填）

---

## 六、风格切换备选版（按需选用）

> 仅当用户明确要求"换成电影写实风"时，附一版对照：

| 编号 | 中文 prompt（电影写实版） | 英文 prompt（电影写实版） |
|---|---|---|
| S1-1 | ... | ... |
| ... | | |

---

## 七、生成后使用提示

1. **豆包视频生成工具粘贴位置**：豆包官网 → 视频生成 / AI 视频 → 文本生视频 → 把上方"提示词块"对应镜头粘入 → 选风格与时长 → 生成
2. **如果生成结果不理想**：
   - 人物外形漂移 → 复制前几镜已成功的该人物外貌描述，强制粘贴到当前镜 prompt
   - 动作卡顿 / 不连贯 → 把单镜时长压到 3s；精简到只保留 1 个核心动作
   - 风格跑偏 → 在 prompt 末尾追加 2–3 个精准风格词
   - 主体消失 → 强化"前景中央""直视镜头"等位置信号
3. **风格切换**：如果想换成电影写实版，告诉我"给一版电影感的"，会把同样脚本按 § 六 重发一版。

---

## 八、自检清单（生成完对照打勾）

- [ ] 同一个人物在所有镜头外貌描述是否一致？
- [ ] 每个镜头是否只声明了 1 个核心动作？
- [ ] 环境段是否覆盖时间 / 光线 / 空间 / 至少 1 个具象元素？
- [ ] 每镜时长是否落在 2–8 秒区间？
- [ ] 是否避免了文本 / 否定句 / 抽象形容词？
- [ ] 风格标签是否放在 prompt 末尾、用逗号分隔？
- [ ] 中文字数是否落在 80–150 字区间？英文是否 60–120 词？
- [ ] 单次输出总镜数是否 ≤ 30？如超过，按 § 三 场景清单顺序分批。
