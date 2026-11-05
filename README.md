# ComfyUI AI 漫剧本地运行系统（AICG Platform / AI Drama Studio)

> **作者**：QQ 13288793 ｜ 微信 b13052782321

![Local](https://img.shields.io/badge/运行方式-本地纯免费-success) ![ComfyUI](https://img.shields.io/badge/推理后端-ComfyUI-orange) ![Vue](https://img.shields.io/badge/前端-Vue2.7%20·%20Vue3-blue) ![Django](https://img.shields.io/badge/后端-Django%204.2%20·%20DRF-green)

> **💰 本地纯免费**：整套系统跑在你自己的电脑上——数据存本机 MySQL、图和视频用本机 ComfyUI 出、成片用本机 FFmpeg 拼。**没有云服务、没有订阅、没有按张计费，生成多少都不花钱。**

> 一套完全本地运行的 **AI 漫剧（短剧/漫剧/微短剧/AI 动画）生产平台**：从一句话创意到成片，覆盖
> **AI 剧本创作 → 人物/资产设定 → 美术出图 → AI 分镜拆解 → 单镜生成视频（图生视频/文生视频/首尾帧/参考生视频）→ 一键合成成片** 全流程。
> 视频与图片生成全部基于本机 **ComfyUI**，通过「技能（Skill）」机制封装 ComfyUI 工作流，
> **技能自选、自由扩展**——把你的任何工作流包装成技能，就能在平台各页面直接调用。

**English**: A 100% local-first, free & open-source AI drama / comic short-film studio. One-stop pipeline: AI screenplay writing → character design → art asset generation → AI storyboard → shot-by-shot video generation (image-to-video, text-to-video, first-last-frame, reference-to-video, video-to-video) → one-click FFmpeg film composing. All inference runs on your own ComfyUI; any workflow can be wrapped as a selectable "Skill" plugin. No cloud, no subscription, no per-image billing.

**适合谁**：个人创作者 / 漫剧工作室 / AI 短剧团队 / 想把散装 ComfyUI 工作流管起来的人——只要你会装 ComfyUI，就能用这个平台把「写剧本 → 出图 → 出片」整条流水线跑起来。

---

## 🖼️ 效果预览（实机截图）

### 剧本创作线

**① 剧本列表** —— 剧卡片网格，状态/进度/集数一眼清：

![剧本列表](docs/images/01-剧本列表.png)

**② 创作方案** —— 一句话创意，AI 一次产出 4 个方向明显不同的方案供比稿：

![创作方案](docs/images/02-创作方案.png)

**③ 人物设定** —— AI 批量生成角色卡（本剧角色 5 项），支持一键解析入表：

![人物设定](docs/images/03-人物设定.png)

**④ 分集目录** —— 情绪流曲线 + 商业三要素 + 台词体检，节奏问题自动标红：

![分集目录](docs/images/04-分集目录.png)

### 视频生产模块

**⑤ 剧集列表** —— 剧本线完成的项目在这里继续出片：

![剧集列表](docs/images/05-剧集列表.png)

**⑥ 资产清单** —— 本集四分类资产（角色 13 / 场景 2 / 道具 8 / 服装 8），可直接 AI 重写/预览：

![资产清单](docs/images/06-资产清单.png)

**⑦ 美术资产** —— 逐资产出图（定装图版本管理）+ 音色合成 + 关联角色同步：

![美术资产](docs/images/07-美术资产.png)

**⑧ 拆分分镜** —— AI 拆镜（6 镜 / 79 字 / 总时长 ~93s），逐镜景别·运镜·台词·推荐生成方式，可连续生成：

![拆分分镜](docs/images/08-拆分分镜.png)

**⑨ 成片剪辑** —— 时间线按时长加权、片段列表带「正式使用」标、一键 ffmpeg 合成成片：

![成片剪辑](docs/images/09-成片剪辑.png)

---

## ✨ 核心特性

### 🎬 一站式漫剧生产线（双模块 16+ 页面）

**剧本创作线（/script）**
- 新建剧本 → AI 生成 4 个方向的创作方案 → 方案详情
- 人物设定（AI 批量生成 + 手动编辑 + 一键解析入表）
- 分集目录（节奏总览）→ 分集剧本（AI 生成/改写，先预览后写入）

**视频生产模块（/video）**
- 剧集管理 / 剧本编辑 / 关卡进度概览（剧本 40% + 资产 20% + 分镜 40% 统一口径）
- 资产清单（本集/全剧双视图）+ 美术资产（四分类：人物/场景/道具/服装，版本管理、图生图、音色合成）
- 拆分分镜（AI 拆镜 + 逐镜推荐生成方式 + 连续生成）
- **单镜生成（导演台）**：8 种生成方式（图生视频/文生视频/首尾帧/参考生视频/多参考/二采重绘/视频转视频/参考改视频），每镜独立资源区（参考图≤9 / 参考视频≤3 / 参考音频≤3）、参数面板与版本历史（可回选、指定正式使用）
- **成片剪辑**：自动取各镜「正式使用」版本，ffmpeg 归一拼接合成、成片历史与下载

### 🧩 技能系统（自选 + 自由扩展）

- ComfyUI 工作流封装为「技能包」（zip 上传 / 本地导入），按分类管理
- 每类能力（文生图 / 图生图 / 生视频 / 重绘 / 音色…）可挂多个技能，**页面上自选使用哪个**
- 每个技能带独立的提示词扩写引导词配置（可编辑，按页面/模式记忆）
- 内置技能示例：三图编辑一致版、参考生视频、二采重绘、动漫转真人、人物替换、去水印、加速生视频等（见 `backend/能力/`）

### ⚙️ 工程细节

- 任务单表管理（task 宽表），生成中占位 + 定时对账回写，防悬挂
- 分镜全量替换语义下，视频/图版本挂业务键（剧id+集号+镜号），换行 id 不丢历史
- 媒体文件统一鉴权流式服务；JWT 登录；全中文命名代码库（表/接口/组件一一对应）

---

## 🏗️ 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11 · Django 4.2 · DRF · SimpleJWT · PyMySQL |
| 主前端 | Vue 2.7 · Vite 4 · Element UI（端口 8081） |
| 四模块前端 | Vue 3 · Vite（端口 5199，四模块演示/预览） |
| 数据库 | MySQL / MariaDB 11.4（库名 `aicg`，utf8mb4） |
| 推理后端 | 本机 ComfyUI（HTTP API，工作流经技能包调度） |
| 成片 | FFmpeg（归一 + concat 拼接） |

---

## 📦 目录结构

```
aicg/
├── backend/            # Django 后端（全中文函数视图）
│   ├── 接口/controllers/   # 全部 REST 接口（剧本/资产/美术/分镜/任务/成片…）
│   ├── 接口/models/        # 数据模型（21 张业务表）
│   ├── 能力/               # 技能执行器（ComfyUI 工作流调用封装）
│   ├── 后端/settings.py    # Django 配置（DB / JWT / CORS）
│   └── 资源/               # 运行时媒体目录（上传/产物/技能包/工作流，git 不含生成物）
├── frontend/           # 主平台前端（Vue 2.7 + Vite，8081）
│   └── src/views/          # 剧本创作 / 视频生成 两大模块页面
├── 四模块/              # 四模块演示前端（Vue 3，5199）
├── docs/               # 项目文档（01 项目文档 / 02 数据库文档 / 10 任务清单…）
├── 表结构.sql           # 建库建表 SQL
├── 开发标准手册.md      # 开发规范（唯一参照）
├── start-platform.bat  # 一键启动（MariaDB + Django 8001 + Vite 8081）
├── 数据库导出_aicg_2026-11-04.sql  # 全库导出（33 张表，含表结构，可直接导入）
└── 表结构.sql           # 建库建表 SQL（空库结构版）
```

---

## 🚀 快速开始

> 前置要求：本机已安装并启动 **ComfyUI**（默认 `127.0.0.1:8188`）、Python 3.11、Node.js、MySQL/MariaDB。

### 1. 建库（二选一）

**方式 A：直接导入全量导出**（含表结构 + 全部 33 张表，最快上手）：

```bash
mysql -uroot -p -e "CREATE DATABASE aicg DEFAULT CHARACTER SET utf8mb4"
mysql -uroot -p aicg < 数据库导出_aicg_2026-11-04.sql
```

**方式 B：只建空库结构**（干净起步）：导入 `表结构.sql`，再按需执行 `docs/02-数据库文档.md` 中的增量 ALTER（分镜线两张表）。

### 2. 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8001
```

数据库连接在 `backend/后端/settings.py`（默认 `127.0.0.1 / root / root`，按需修改）。

### 3. 前端

```bash
cd frontend
npm install
npm run dev     # http://localhost:8081
```

或直接双击 `start-platform.bat` 一键拉起数据库 + 后端 + 前端。

### 4. 配置模型地址与技能

登录后进入「模型配置」：填入 LLM 接口与本机 ComfyUI 地址（`http://127.0.0.1:8188`）；
再到「技能库」上传/导入你的 ComfyUI 工作流技能包（zip），分类挂好后即可在剧本/美术/单镜生成各页面**自选技能**使用。

---

## 📚 文档

- `开发标准手册.md` —— 开发规范与全局约定（唯一参照）
- `docs/01-项目文档.md` —— 项目总览
- `docs/02-数据库文档.md` —— 数据库设计（21 张业务表字段级细则）
- `docs/10-任务清单.md` —— 迭代记录（A~J 节：检查 → 修复 → 成片合成 → 资产库…）

---

## 🔍 关键词 / Keywords

**中文**：AI 漫剧 · AI 短剧 · 微短剧 · AI 动画 · AI 漫画 · 竖屏短剧 · AI 视频生成 · 文生视频 · 图生视频 · 首尾帧生成 · 参考生视频 · 视频转视频 · AI 分镜 · 分镜生成 · AI 剧本创作 · AI 编剧 · 小说转短剧 · 人物一致性 · 角色一致性 · 美术资产 · AI 出图 · 音色合成 · AI 配音 · 一键成片 · 视频拼接 · ComfyUI 工作流 · 工作流编排 · 技能插件 · 本地部署 · 离线运行 · 免费开源 · 不花钱 · 拒绝按张计费 · 个人创作者 · 漫剧工作室 · Django · Vue · FFmpeg · MySQL

**English**: AI drama · AI comic · AI animation · short drama · vertical video · AI video generation · text-to-video · image-to-video · first-last frame · reference-to-video · video-to-video · AI storyboard · AI screenplay · script writing · character consistency · art asset · voice cloning · TTS dubbing · one-click film composing · ComfyUI workflow · workflow orchestration · skill plugin · local-first · self-hosted · offline · free open source · no subscription · indie creator · Vue · Django · FFmpeg · MySQL

---

## 📄 License

仅供学习交流使用。生成内容请遵守各模型/平台的版权与使用条款。
