# 镜头 / 景别 / 运镜 词典

> 写 prompt 时挑词用，确保镜头语言精准而专业。这一份只在生成时按需加载，不要替 SKILL.md 喧宾夺主。

---

## 一、景别（Shot Scale）

| 景别 | 英文 | 用途 | 提示要点 |
|---|---|---|---|
| 远景 | Extreme Wide Shot (EWS) | 交代环境、地貌、规模 | 主体在画面占比 < 15%；强调「渺小感」 |
| 全景 | Wide Shot (WS) | 交代人物在空间中的位置 | 人物全身可见；环境与人物平衡 |
| 中景 | Medium Shot (MS) | 强调肢体动作、姿态 | 膝盖以上；最常用对话镜头 |
| 中近景 | Medium Close-Up (MCU) | 强调表情 + 部分肢体 | 胸部以上 |
| 近景 | Close-Up (CU) | 强调面部表情、眼神 | 肩部以上；情绪镜头首选 |
| 大特写 | Extreme Close-Up (ECU) | 强调局部细节（瞳孔、刀尖、字符） | 单一部位占满画面 |

**网文短视频风格首选**：近景 / 特写 / 大特写（让情绪怼到观众脸上）
**电影写实首选**：中景 / 中近景 / 全景（让观众呼吸）

---

## 二、运镜（Camera Movement）

| 中文 | 英文 | 提示写法 | 情绪感受 |
|---|---|---|---|
| 固定 | Static / Locked | `static camera, locked-off shot` | 冷静、凝视、稳定 |
| 推 | Push In / Dolly In | `slow push-in, dolly forward` | 聚焦、紧张、临近揭示 |
| 拉 | Pull Out / Dolly Out | `slow pull-out, dolly backward` | 疏离、揭示全貌、悲伤 |
| 摇 | Pan | `pan left/right, slow pan` | 跟随目光、揭示空间 |
| 移 | Tracking / Truck | `tracking shot left/right` | 跟拍人物动线 |
| 跟 | Follow | `follow shot behind subject` | 沉浸、主体化 |
| 升 | Crane Up / Boom Up | `crane up, drone ascending` | 全知视角、神性、不祥 |
| 降 | Crane Down / Boom Down | `crane down, drone descending` | 揭示、压迫 |
| 手持 | Handheld | `handheld camera, slight shake` | 紧张、临场、纪录片感 |
| 甩镜 | Whip Pan | `whip pan, fast pan` | 网文快剪转场、混乱感 |
| 环绕 | Orbit / Arc | `360 orbit, arc shot` | 戏剧性对峙、决战感 |

**组合写法示例**：`slow push-in with subtle pan`, `handheld tracking shot from behind`, `dolly zoom (vertigo effect)`

---

## 三、构图与轴线

| 术语 | 写法 | 何时用 |
|---|---|---|
| 180 度轴线 | `maintaining 180-degree axis` | 两人对话时确保视线方向一致 |
| 过肩镜头 | `over-the-shoulder shot (OTS)` | 对话 / 冲突 |
| 主观视角 | `POV shot, first-person view` | 代入、恐怖、悬疑 |
| 荷兰角 | `Dutch angle, tilted frame` | 不安、疯狂、压迫 |
| 对称构图 | `symmetrical composition, centered` | 仪式感、宿命感、恐怖 |
| 三分法 | `rule of thirds` | 通用自然感 |
| 留白 | `negative space, lone figure in vast environment` | 孤独、渺小、史诗 |
| 前景遮挡 | `foreground occlusion, frame within frame` | 窥视感、悬疑 |

---

## 四、调色 / 光线 / 氛围词

### 光线

- `golden hour lighting`, `magic hour`
- `Rembrandt lighting`, `chiaroscuro`(明暗对比)
- `backlit silhouette`, `rim lighting`(轮廓光)
- `low-key lighting`(暗调), `high-key lighting`(高调)
- `volumetric light, god rays`(体积光)
- `neon glow, cyberpunk lighting`
- `diffused soft light`(漫射柔光)
- `hard shadows`(硬光)

### 调色 / 风格

- `teal and orange`(电影经典调)
- `desaturated, muted color`(低饱)
- `high saturation, vivid color`(高饱)
- `film grain`, `analog film texture`
- `anamorphic lens flare`
- `bleach bypass`(漂白跳轨)
- `cyberpunk neon palette`
- `wuxia ink wash palette`(水墨)
- `pastel dreamy palette`

### 天气 / 氛围

- `heavy rain`, `misty fog`, `dust storm`, `snowfall`
- `smoke haze`, `embers floating`(余烬)
- `timelapse clouds`, `fast motion wind`

---

## 五、动作 / 节奏术语

| 写法 | 用途 |
|---|---|
| `freeze frame`(定格) | 高潮定格 |
| `speed ramp, slow motion`(速度渐变 / 慢动作) | 关键动作展开 |
| `motion blur`(动态模糊) | 高速动作 |
| `smash cut`(硬切) | 网文风格转场 |
| `cross-cut`(交叉剪辑) | 多线并行 |

---

## 六、人物外貌统一描述示例模板

> 同一人物在所有镜头 prompt 里**整段复制**用，不做任何变形。

**中文模板**：
```
（年龄）+（身高体态）+（发色发型）+（面部特征）+（典型服饰）
```
示例：`二十岁出头的青年，剑眉星目，黑发散落肩头，身着玄色长袍，腰悬古朴长剑`

**英文模板**：
```
a (age)-year-old (build), (hair), (facial feature), wearing (clothing detail), (signature element)
```
示例：`a young man in his early twenties, sharp brows and bright eyes, long loose black hair, wearing a dark celestial robe with a worn antique sword at his waist`

---

## 七、提示词禁忌

- ❌「不要出现 X」(negative prompt) — 豆包主模型对此不敏感，且会浪费 token
- ❌ 长复合句、嵌套从句 — 用短陈述句堆叠即可
- ❌ 抽象情绪形容词（「悲伤的」）单独出现 — 必须配具象细节（"泪水滑落""下颌微颤"）
- ❌ 多主体多动作 — 「他出剑，他吐血，她哭」三件套压到一个镜里必翻车
- ❌ 数字编号、文本字符、画面内文字
- ❌ 跨镜头断章：「3 秒后他走了」 — 镜头节奏由时长与运镜控制，不在文字里写时间

---

## 八、推荐的提示词中文字数区间

- 中文 prompt：80–150 字
- 英文 prompt：60–120 词

过短→画面单调；过长→信息冲突。
