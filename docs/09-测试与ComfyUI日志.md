# 09 - 测试方法与 ComfyUI 日志查看

状态：2026-09-18 新增。记录两类日常手段：前端自动化测试、ComfyUI 日志查看。

## 1. 前端自动化测试（playwright-core 单进程脚本）

### 1.1 为什么不用 agent-browser 守护进程

本机环境下 agent-browser 的后台守护进程会被反复终止（SIGTERM），且多次调用间页面状态丢失，不适合做链路测试。**统一用单进程 playwright-core 脚本**：一次启动 Chromium、跑完整链路、退出，无守护进程。

### 1.2 环境依赖（已装好，换机需重装）

- Chromium：`%LOCALAPPDATA%\ms-playwright\chromium-1234\chrome-win64\chrome.exe`
- playwright-core：装在隔离 workspace `C:\Users\Administrator\.workbuddy\binaries\node\workspace\node_modules`（不污染全局）
- Node 22：`C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-2\node.exe`

### 1.3 现有脚本（放工作区，不进 aicg 仓库）

| 脚本 | 用途 |
|---|---|
| `登录测试.js` | 端到端：打开 → 登录 → 跳壳 → 进模型配置，带截图 |
| `全菜单测试.js` | 逐个真实点击侧栏 14 个菜单项，断言页面渲染非空白、页标题正确，带截图 |

### 1.4 运行方式（Git Bash）

```bash
cd "C:\Users\Administrator\WorkBuddy\2026-09-18-14-35-36"
NODE_PATH="C:\Users\Administrator\.workbuddy\binaries\node\workspace\node_modules" \
  "C:\Users\Administrator\.workbuddy\binaries\node\versions\22.22.2-2\node.exe" 全菜单测试.js
```

前提：后端 8001、前端 8080 都在跑。

### 1.5 写测试脚本的三条纪律

1. 登录表单定位用 `input[placeholder="用户名"]`、`input[placeholder="密码"]`，按钮用 `.el-button--primary`。
2. 菜单项**没有 `index` 属性**（Element UI 不渲染），只能按文字定位：`page.locator('li.el-menu-item', { hasText: '技能管理' })`；子菜单组已展开时**不要再点组标题**（会把它合上），先试点、失败再点组标题展开。
3. 断言空白页：`.壳-内容` 文本长度 < 5 即空白。

### 1.6 前端模板事件绑定纪律（防回归）

模板里事件处理器**必须带括号**：`@click="提交()"`。裸中文方法名 `@click="提交"` 会被编译器当内联语句（isSimplePath 正则 `[\w$]` 不匹配中文），只读方法引用不调用，点击无任何反应且无报错。

## 2. ComfyUI 日志查看（共享目录）

- ComfyUI 机器：`192.168.31.121`，ComfyUI 服务：`192.168.31.121:8188`
- **日志共享路径（Windows 资源管理器直接打开）**：`\\192.168.31.121\ComfyUI-aki-v3`
- 看生成日志：进共享后看 ComfyUI 主控台日志（`user\` 或根目录下最新日志文件）；任务是否真正开跑以日志里出现任务执行（prompt 加载/progress 条）为准，`任务列表` 接口的 `开始时间` 必须等于 Comfy 真正开跑时间（见 `08`）。
- Git Bash 下可直接 `ls '//192.168.31.121/ComfyUI-aki-v3'` 查看。

## 3. 后端接口自测（curl）

Git Bash 的 curl 对中文 URL 要用百分号编码（浏览器会自动编码，无需处理）。例：

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8001/api/%E7%99%BB%E5%BD%95 -H "Content-Type: application/json" -d '{"用户名":"zhsw","密码":"Zhsw@123456"}' | sed 's/.*"token":"\([^"]*\)".*/\1/')
curl -s "http://127.0.0.1:8001/api/%E4%BB%BB%E5%8A%A1%E5%88%97%E8%A1%A8" -H "Authorization: Bearer $TOKEN"
```

（登录=%E7%99%BB%E5%BD%95，任务列表=%E4%BB%BB%E5%8A%A1%E5%88%97%E8%A1%A8）

## 4. 任务页交互约定（2026-09-18 用户拍板）

1. **3 秒轮询**：所有测试页任务列表每 3 秒自动刷新（共用混入 `frontend/src/共用/任务页混入.js`，页面不可见时暂停），**不需要手动刷新页面/列表**。「刷新列表」按钮保留但只是兜底。
2. **缩略图显示**：任务表里「输入」「产物」列直接显示图片/视频缩略图（共用组件 `共用/媒体缩略图`），**禁止只显示路径文字**。表单里刚上传的媒体也立刻显示缩略图。
3. **点击放大 + 上一个/下一个**：点缩略图打开共用媒体预览弹窗（`共用/媒体预览弹窗`），图片/视频大图展示，左右箭头在该行全部媒体（输入+产物）间切换，显示 `N / 总数`。
4. **媒体访问走鉴权直链**：`GET /api/媒体/<相对路径>?token=...`，服务 `资源/` 目录文件（防路径穿越）；`<img>/<video>` 发不出 Authorization 头，所以用 `?token=`。前端拼地址统一用 `src/接口/媒体.js` 的 `媒体地址()`。
5. **登录页记住账号密码**：勾选后存 `localStorage['记住登录']`（含密码，本机单管理员场景），不勾选则清除；下次打开自动回填。

## 5. 提示词扩写（学旧项目 promptgen）

- 后端 `POST /api/提示词/扩写`：`{技能id, 模式, 需求, 引用:[{名称,类型}], 声音模式}` → 读技能包 `SKILL.md + references/base-en.txt（single_frame|image 用）或 ref-en.txt（multi_reference 用）` 作为规范 → 连同用户需求喂 LLM → 返回提示词。`GET /api/提示词/技能列表` 列出有 SKILL.md 的技能。
- 三种模式：`image`（图片页通用扩写）、`single_frame`（首尾帧，I2VA/FL2VA 标签规则）、`multi_reference`（人物替换/参考生视频/二采重绘，六段式 + `<Subject/Picture/Video/Audio N>` 标签）。
- ⚠️ **标签规范有两套，尚未选定**（`14-两套方案对照（待实测选型）.md` 选型点 P1）：
  - **方案 A 官方原生**：t2va 裸文本；fl2va 用 `<Picture 1>` / `<Picture 2>`；ref2va 用 `<Picture i>` / `<Video k>` / `<Audio j>`（出处 `ComfyUI/comfy/text_encoders/minimax.py` 文件头）。
  - **方案 B 技能包六段式**（当前 `base-en.txt` / `ref-en.txt` 正在用的）：`<Subject N>` / `<Picture N>` / `<Video N>` / `<Audio N>`。其中 **`<Subject N>` 在官方 presentation 里没有出处**，是否被模型识别待实测。
  - 上面「三种模式」的描述属于**方案 B**；选 A 后本节要改。细节与切换成本见 `14` §2。
- 硬规则（沿旧项目用户拍板，不偏离）：图片不发给本地 LLM，仅命名锚点；`@图N/@视频N/@音频N` 是硬占位符，必须替换成规范标签，输出不得残留 `@`；不擅自添加用户未要求的元素。**两套方案共用这条，不变。**
- 前端测试页的「AI扩写」行（共用组件 `共用/扩写行`）：选技能 → 写需求 → 生成提示词 → 自动填入正向提示词。

## 6. ComfyUI 显存释放纪律（2026-09-18 教训，必守）

**事故**：T4 单图编辑采样 57 分钟（同机同工作流旧项目只要 75 秒）。根因不是算力——是执行器任务结束后不清理显存，上一段的 Z-Image、文本编码器等模型一直驻留 + LLM 服务占卡，Comfy 被迫低显存模式采样。

**纪律**：
- 每个 Comfy 任务终态后必须调 `POST /free {"unload_models": true, "free_memory": true}`（`/free` 失败退 `/api/free`；再失败只 WARN 不影响任务）。注意 `/free` 是打 flag，**真正的卸载发生在下一段 prompt 启动时**，所以必须带这两个参数，发 `{}` 等于没设。
- 已实现在 `能力/提交并等待.py` 的 `_free_vram()`，在 comfy 线程的 finally 里调用。
- 诊断耗时问题**必须先看远端日志逐节点耗时**（`[DIAG][NODE] node=105 耗时=xxx`），同机同工作流的历史耗时就是对照基准；不要拿"模型大/矿卡慢"当借口——同一模型前后两个任务耗时差 85 倍就一定是代码问题。
- queue/history 查询瞬时失败（如 503）不算中断：连续容忍 120 秒，超过才判中断。

## 7. LLM 与 Comfy 同卡抢显存（2026-09-19 补充，必读）

`192.168.31.121` 一张卡同时跑 **LLM 服务(8080, Qwen3.8-27B) 和 ComfyUI(8188)**：

- LLM 服务**没有远程卸载接口**（`/api/generate`、`/api/v0/*` 均 404），调用后长驻显存（约 15-75 分钟后闲置自动卸载，具体 TTL 由该服务自身决定）。
- LLM 驻留 + Comfy 39GB 大模型（Qwen-Image-Edit-2511）同时跑 → 空闲显存不足 → 采样被迫低速，**同样 8 步采样 41 秒的活能拖到 57 分钟**；LLM 退出显存后同工作流只要 40-75 秒。
- 已做的防护（`能力/提交并等待.py`）：① 提交前显存预检，空闲 <12% 时任务日志记 `[显存][WARN]`；② 任务终态后 `/free` 清 Comfy 自己的模型。
- **彻底解法只能改 121 上的 LLM 服务**：把它的 keep_alive / 闲置卸载时间调短（或换成支持 `keep_alive:0` 的启动参数）。这一条需要用户在 121 机器上改，平台侧无法远程卸载。
- 排查耗时问题的顺序：先看任务日志有没有 `[显存][WARN]` → 再看远端 `comfyui.log` 逐节点 `[DIAG][NODE]` 耗时 → 再对照同工作流历史耗时。不要猜。

## 8. in-DOM 模板禁止中文组件标签（2026-09-19 大坑，必守）

页面模板是 **in-DOM 模板**（index.vue 里 `<script src>` 引逻辑，模板本体由浏览器先解析）。浏览器的 HTML 解析器**只认 ASCII 字母开头的标签名**，`<媒体缩略图>` 这种中文标签会被当**纯文本**原样显示、组件根本不渲染，且无任何报错。

纪律：
- 页面模板里用组件必须写 **ASCII kebab-case 标签**：`<run-log-dialog>`、`<media-thumbs>`、`<media-preview>`、`<ai-expand>`、`<add-category-dialog>`、`<upload-skill-dialog>`；
- 在页面 index.js 的 `components` 里注册别名：`components: { 'media-thumbs': 媒体缩略图, ... }`（键 ASCII，值还是中文命名的组件文件）；
- 页面自身的 `.页标题`、类名（`.媒体缩略图` 等）、placeholder、菜单文字不受影响——**只有自定义标签名受限**（`<el-*>` 是 ASCII 所以没事）。
- 已知的另一处同类坑：模板事件绑定中文裸方法名必须带括号（见 1.6），同一根源（编译器对中文标识符的兼容边界）。

## 9. T10 二采重绘排障记录（2026-09-19 已修复，四个坑）

T10 提交后 Comfy 端 2.6 秒即"成功"但零产物，根因四个，全部修复：

1. **成对摘除缺失（主因）**：摘未用参考图/音频槽位时只摘了 LoadImage/LoadAudio，没把成对的 Resize（198,234-240）/ AudioCrop（303-305）中间件一起摘 → 302.ref_image_x / ref_audios 悬空 → Comfy 校验失败，**168 等视频输出节点被静默忽略**，只剩 LLM 文本节点执行。已照旧项目 `Minimax_H3二采重绘.py` 的成对摘除修复（`能力/二采重绘.py` 的 `图中间件`/`音频中间件`）。教训：**Comfy 图里摘任何加载节点，必须连带它的成对中间件整链摘**；执行"成功"但 outputs 无产物 = 失败，不能死等。
2. **沙箱代理劫持内网请求**：本机环境变量 `HTTP_PROXY=127.0.0.1:1706`，Python urllib 默认走代理 → 间歇 10053/10054/503，任务被误判中断。已把 `提交并等待.py`/`工作流工具.py`/`LLM调用.py` 全部 urlopen 换成 `直连opener.open()`（`ProxyHandler({})` 绕代理）。
3. **成功但无产物判失败**：history 终态且 outputs 为空时不再 `continue` 死等，立即判失败。
4. **任务提交漏字段**：`任务提交.py` 白名单补 `一采MP`/`二采MP`（二采重绘专用参数此前根本没落库）。

修复后实测（task_21，2026-09-19 01:00-01:07）：提交 → 生成中 → **6.5 分钟成功**，产物 task_21_1.mp4（一采 2.8MB）+ task_21_2.mp4（二采 6.2MB）。
