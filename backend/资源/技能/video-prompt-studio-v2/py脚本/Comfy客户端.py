"""
Comfy客户端.py — video-prompt-studio 底层 ComfyUI 客户端。

职责：加载工作流 JSON（支持 ComfyUI 导出的 API 格式 / UI 格式）、
按 class_type 或节点标题查找节点、修改参数、提交并轮询结果。

约定：
- 本项目工作流均为 API 格式（顶层即 {节点id: {class_type, inputs, _meta}}），可直接提交。
- **图片路径规则（重要，踩过坑）**：单图 `LoadImage` 节点**绝不收绝对路径**——
  ComfyUI 只认自己 input/ 下的文件名，外部绝对路径会 400。传本地图必须用
  `set_image()`（内部先 `/upload/image` 上传再写回文件名）。
  `LoadImagesFromPath` / `Load Image Batch` / `VHS_LoadVideo` / `VHS_LoadAudioUpload`
  这类**按路径读 ComfyUI 服务端磁盘**的加载器，则用本地/绝对路径是正常用法（同机即可）。
- 视频/音频参考也遵循上面"按路径读服务端"的机制，绝对/本地路径 OK。
- ComfyUI 需本地运行于 http://127.0.0.1:8188。

典型用法见 scripts/run_*.py。
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

DEFAULT_URL = "http://127.0.0.1:8188"

# ---------------------------------------------------------------------------
# ComfyUI 在线探活（可靠的预检，防误判宕机）
# ---------------------------------------------------------------------------
def is_comfy_up(url=DEFAULT_URL, timeout=5):
    """可靠的 ComfyUI 在线探活。

    必须用根路径 '/' 或 '/object_info'（本环境稳定返回 200）。
    ⚠️ 禁止用 '/system_stats' 探活：该端点在本环境会返回 HTTP 500，
       仅代表统计接口异常、不代表 ComfyUI 宕机；误用会误判"ComfyUI 挂了"而报错退出。
    """
    for ep in ("/", "/object_info"):
        try:
            req = urllib.request.Request(f"{url}{ep}")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False


def require_comfy(url=DEFAULT_URL):
    """运行前预检：ComfyUI 不可达就清晰报错退出，避免后续 /prompt 抛出晦涩错误。"""
    if not is_comfy_up(url):
        raise RuntimeError(
            f"ComfyUI 不可达或未启动：{url}\n"
            f"请先启动 ComfyUI（默认 http://127.0.0.1:8188）再运行本脚本。\n"
            f"（注意：'/system_stats' 返回 500 属正常统计接口异常，不是宕机信号，勿据此判断。）"
        )


# ---------------------------------------------------------------------------
# 亮度 / 美颜 硬规则（用户规则，脚本层强制注入）
# ---------------------------------------------------------------------------
# 用途：无论出图（Qwen）还是出视频（FL2VA/Ref2VA），都强制"画面/人物不要太暗、
#       禁止灰沉沉、男女都要美颜（男帅女美）"。脚本自动把这句加进正向提示词末尾，
#       把对应的禁止暗/灰词加进负向，使规则不依赖用户每次手写。
# 注意：这不是"美白/把皮肤涂白"——保持 ② 反推的"健康肤色"，只是提亮 + 磨皮美颜 + 不灰暗。
# ⚠️ 已弃用（2026-08-13 用户规则）：不再自动追加美颜句。
#   用户判定「明亮均匀柔光、色彩鲜活自然、人物皮肤干净透亮美颜」这段写得不好，
#   且提示词一律中文（含视频提示词）。美颜/亮度语义改由提示词正文自然表达，
#   不再由脚本注入任何英文模板。保留定义仅为兼容旧引用，勿再使用。
BEAUTY_CLAUSE = (
    "Bright, even, soft lighting; vivid yet natural colors; "
    "characters with flawless, clear, well-lit skin and a beautified, "
    "refined, handsome or beautiful appearance — no dark, gloomy, "
    "grayish, dull, or murky tones."
)
# 负向补充：禁止偏暗/灰沉（同样弃用，禁止灰暗语义由中文负向覆盖）
BEAUTY_NEGATIVE = (
    "grayish, gloomy, dull, murky, desaturated, muddy colors, "
    "low-key lighting, dark tones, shadowy, dim"
)

# ⚠️ 已弃用（2026-08-13 用户规则）：不再注入 BACKGROUND_LIGHT / BACKGROUND_NEGATIVE。
#   实测：同提示词手动生成正常；脚本追加 BACKGROUND_LIGHT（"明亮/光线充足"）会拉爆曝光；
#   脚本追加 BACKGROUND_NEGATIVE（"禁止昏暗/阴影/欠曝"）同样会迫使模型提亮、高光过曝。
#   光线/干净/无阴影语义靠提示词正文自然表达即可。以下 BACKGROUND_* 定义保留仅为兼容旧引用，勿再使用。
BACKGROUND_LIGHT = (
    "明亮、清新、干净、光线充足的场景，采光通透；"
    "即便是洞穴或林间等天然偏暗之处也须光亮整洁；"
    "色彩鲜活干净，无昏暗、阴沉或暗调氛围"
)
BACKGROUND_NEGATIVE = (
    "昏暗，阴沉，暗淡，灰蒙，阴影浓重，低调光，暗色调，"
    "色彩暗淡脏污，场景欠曝"
)



# ---------------------------------------------------------------------------
# 加载
# ---------------------------------------------------------------------------
def load_workflow(path):
    """加载工作流 JSON，返回 API 格式字典（节点id -> {class_type, inputs, _meta}）。
    若原始为 UI 格式（含 nodes 数组），自动转换为 API 格式。"""
    with open(path, encoding="utf-8") as f:
        wf = json.load(f)
    if "nodes" in wf:
        return _ui_to_api(wf)
    return wf  # API 格式：直接用


def _ui_to_api(wf):
    """最简 UI->API 转换（处理 Reroute / links / widgets）。"""
    reroute = {n["id"] for n in wf["nodes"] if n.get("type") == "Reroute"}
    new_links = []
    for l in wf.get("links", []):
        if l[1] in reroute:
            src = next((sl for sl in wf["links"] if sl[3] == l[1] and sl[4] == l[2]), None)
            if src:
                new_links.append([l[0], src[1], src[2], l[3], l[4], l[5]])
        elif l[3] not in reroute:
            new_links.append(l)
    wf["links"] = new_links
    nodes = [n for n in wf["nodes"] if n.get("type") != "Reroute"]
    link_map = {l[0]: (l[1], l[2], l[3], l[4]) for l in wf["links"]}
    api = {}
    for node in nodes:
        nid = str(node["id"])
        inputs = {}
        wv = node.get("widgets_values", [])
        wi = 0
        wv_is_dict = isinstance(wv, dict)
        for inp in node.get("inputs", []):
            if inp.get("link") and inp["link"] in link_map:
                sn, ss, _, _ = link_map[inp["link"]]
                inputs[inp["name"]] = [str(sn), ss]
                if "widget" in inp:
                    wi += 1
            elif "widget" in inp:
                # dict 型 widgets_values（如 VHS_LoadVideo/VHS_LoadAudioUpload）：按 widget 名取值；
                # list 型按出现顺序取值（D21：此前对 dict 型直接 wv[wi] 会 KeyError）
                if wv_is_dict:
                    wname = inp.get("widget")
                    if isinstance(wname, dict):
                        wname = wname.get("name")
                    if wname is not None and wname in wv:
                        inputs[inp["name"]] = wv[wname]
                elif wi < len(wv):
                    inputs[inp["name"]] = wv[wi]
                    wi += 1
        api[nid] = {
            "class_type": node.get("type"),
            "inputs": inputs,
            "_meta": {"title": node.get("title", node.get("type"))},
        }
    return api


# ---------------------------------------------------------------------------
# 查找 / 设置
# ---------------------------------------------------------------------------
def node_title(api, nid):
    n = api.get(str(nid), {})
    return n.get("_meta", {}).get("title", "") if "_meta" in n else n.get("title", "")


def find_nodes(api, class_type=None, title=None):
    """返回所有匹配的节点 id 列表。class_type 精确匹配；title 子串匹配。"""
    res = []
    for nid, n in api.items():
        ct = n.get("class_type", "")
        t = node_title(api, nid)
        if class_type and ct != class_type:
            continue
        if title and title not in t:
            continue
        res.append(str(nid))
    return res


def _looks_like_class(s):
    """简单判断：含大写字母+无中文，多半是 class_type。"""
    return any(c.isupper() for c in s) and not any(ord(c) > 127 for c in s)


def set_param(api, ident, param, value):
    """设置参数。
    ident 可以是：节点 id（精确）/ class_type（该类型全部）/ title 子串（匹配标题）。
    返回被修改的节点 id 列表。"""
    matched = []
    if str(ident) in api:
        matched = [str(ident)]
    elif _looks_like_class(str(ident)):
        matched = find_nodes(api, class_type=ident)
    else:
        matched = find_nodes(api, title=ident)

    updated = []
    for nid in matched:
        ins = api[nid].get("inputs", {})
        # 若当前是链接（[node, slot]），直接覆盖为标量值
        ins[param] = value
        updated.append(nid)
    if not updated:
        print(f"  [warn] 未找到匹配节点: ident={ident} param={param}")
    return updated


def set_text(api, node_id_or_title, text):
    """设置文本类节点的内容（兼容 text / value 两种 key）。"""
    nids = [str(node_id_or_title)] if str(node_id_or_title) in api else find_nodes(
        api, title=node_id_or_title)
    if not nids:
        nids = find_nodes(api, class_type=node_id_or_title)
    for nid in nids:
        ins = api[nid].get("inputs", {})
        if "text" in ins:
            ins["text"] = text
        elif "value" in ins:
            ins["value"] = text
        else:
            # 兜底：PrimitiveStringMultiline 多用 value
            ins["value"] = text
    return nids


def upload_image(url, image_path):
    """通过 ComfyUI /upload/image 上传图片到其 input 目录，返回存储后的文件名字符串。"""
    boundary = "----wbcomfy%s" % int(time.time() * 1000)
    # Windows 上源文件名（中文角色图）常超长，直接当上传名会触发 MAX_PATH，
    # 文件存进 input 后系统无法访问，ComfyUI LoadImage 扫描/读取时抛 Errno 13 Permission denied。
    # 改成短名（纳秒时间戳 + 原扩展名），保证唯一且 Windows 可访问。
    ext = os.path.splitext(image_path)[1].lower() or ".png"
    fname = "u%d%s" % (time.time_ns(), ext)
    with open(image_path, "rb") as fh:
        payload = fh.read()
    crlf = b"\r\n"
    body = b""
    body += ("--" + boundary + "\r\n").encode()
    body += ('Content-Disposition: form-data; name="image"; filename="%s"\r\n'
             % fname).encode("utf-8")
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += payload
    body += crlf
    body += ("--" + boundary + "--\r\n").encode()
    req = urllib.request.Request(
        f"{url}/upload/image", data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print("  [HTTPError upload]", e.code,
              e.read().decode("utf-8", "replace")[:300])
        raise
    return result.get("name", fname)


def set_image(api, class_type, image_path, index=0, url=DEFAULT_URL):
    """设置 LoadImage 类节点的 image 参数（多个时按 index 顺序）。

    若 image_path 是真实存在的本地文件，先上传到 ComfyUI input 目录，
    再把返回的文件名写进节点（ComfyUI 只认自己 input/ 下的文件名，外部绝对路径会 400）；
    若文件不存在（说明已是 ComfyUI 内部的文件名），则原样写入，兼容旧用法。
    """
    nids = find_nodes(api, class_type=class_type)
    nids = sorted(nids, key=lambda x: int(x))
    if index >= len(nids):
        print(f"  [warn] LoadImage 不足 index={index}（共 {len(nids)} 个）")
        return None
    if os.path.isfile(image_path):
        require_comfy(url)  # 上传前先确认 ComfyUI 在线，失败信息更清晰
        name = upload_image(url, image_path)
        api[nids[index]]["inputs"]["image"] = name
    else:
        api[nids[index]]["inputs"]["image"] = image_path
    return nids[index]


# ResolutionSelector.aspect_ratio 的 combo 完整标签映射。
# ⚠️ 必须传完整标签（如 '9:16 (Portrait Widescreen)'），裸 '9:16' 会校验失败 →
# ComfyUI 报 "Value not in list" 并忽略整条输出、0.05s 空跑、0 产出（D16 实测）。
_ASPECT_LABELS = {
    "1:1":  "1:1 (Square)",
    "2:3":  "2:3 (Portrait Photo)",
    "3:2":  "3:2 (Photo)",
    "3:4":  "3:4 (Portrait Standard)",
    "4:3":  "4:3 (Standard)",
    "9:16": "9:16 (Portrait Widescreen)",
    "16:9": "16:9 (Widescreen)",
    "21:9": "21:9 (Ultrawide)",
}


def set_resolution(api, aspect_ratio, megapixels):
    """覆盖 ResolutionSelector 的 aspect_ratio / megapixels。

    aspect_ratio 兼容裸比例（'9:16'）与完整标签（'9:16 (Portrait Widescreen)'），
    裸比例自动映射为 combo 标签，避免 ComfyUI 校验失败空跑。
    """
    if aspect_ratio is not None:
        aspect_ratio = _ASPECT_LABELS.get(aspect_ratio, aspect_ratio)
    for nid in find_nodes(api, class_type="ResolutionSelector"):
        ins = api[nid]["inputs"]
        if aspect_ratio is not None:
            ins["aspect_ratio"] = aspect_ratio
        if megapixels is not None:
            ins["megapixels"] = megapixels


# ---------------------------------------------------------------------------
# 提交 / 轮询
# ---------------------------------------------------------------------------
def submit(api, url=DEFAULT_URL, client_id=None):
    payload = {"prompt": api}
    if client_id:
        payload["client_id"] = client_id
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/prompt", data=data,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print("  [HTTPError]", e.code, body[:500])
        raise
    if "error" in result:
        print("  [ComfyUI error]", json.dumps(result, ensure_ascii=False)[:500])
        raise RuntimeError("workflow submit failed")
    return result["prompt_id"]


def get_queue_status(url=DEFAULT_URL, prompt_id=None):
    """探测 ComfyUI 队列积压状态。

    返回 dict: {running:int, pending:int, our_position:Optional[int], running_ours:bool, error:str|None}
      - our_position：我们的 prompt 在 pending 队列中的 0-based 位次；不在 pending 中则为 None。
      - running_ours：我们的 prompt 当前是否正在 queue_running 中执行。
    用途：提交前/等待中感知队列深度，避免盲排在大量遗留任务之后却毫无提示
          （曾导致 1800s 静默超时返回 {}，把"队列堵了"掩盖成"成功"）。
    """
    try:
        req = urllib.request.Request(f"{url}/queue")
        with urllib.request.urlopen(req, timeout=10) as resp:
            q = json.loads(resp.read())
    except Exception as e:
        return {"running": 0, "pending": 0, "our_position": None,
                "running_ours": False, "error": str(e)}
    running = q.get("queue_running", [])
    pending = q.get("queue_pending", [])
    running_ours = False
    if prompt_id:
        for item in running:
            pid = item[1] if isinstance(item, list) and len(item) > 1 else item
            if pid == prompt_id:
                running_ours = True
                break
    our_position = None
    if prompt_id and not running_ours:
        for i, item in enumerate(pending):
            pid = item[1] if isinstance(item, list) and len(item) > 1 else item
            if pid == prompt_id:
                our_position = i
                break
    return {"running": len(running), "pending": len(pending),
            "our_position": our_position, "running_ours": running_ours, "error": None}


def clear_queue(url=DEFAULT_URL):
    """清空 ComfyUI 队列（running + pending）。

    仅删除待执行的生成任务，**不删任何文件/模型**。一般留给用户手动在 ComfyUI 面板
    Queue → Clear 操作。执行器已不再自动清空队列（用户要求：失败不取消任务），如需清理请用户手动在 ComfyUI 面板 Queue → Clear。
    """
    data = json.dumps({"clear": True, "delete": True}).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/queue", data=data,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def free_vram(url=DEFAULT_URL, quiet=False):
    """强制 ComfyUI 卸载当前所有已加载模型并清空显存缓存。

    ⚠️ best-effort 释放显存，建议每段结束后调用，但需知：
    /free 只能卸载「当前正常加载」的模型，无法回收「失败/中断任务泄漏的孤儿显存」
    （孤儿显存才是连续批量 CUDA 类型不匹配错误的真因，而非段间没清显存）。
    故 free_vram 是必要的卫生动作（每段结束卸载模型，避免脏模型占卡拖累下段）。

    调用时机（由上层执行器负责）：
      - 批量任务开始（clear_queue 之后）：从干净显存起跑；
      - 每一段成功 / 失败之后：立刻卸载该段模型，让下一段从干净显存开始。
    容错：/free 在个别 ComfyUI 版本 / 忙时会返回 500，此时退化为 /api/free；
          再失败仅 WARN 不中断整轮（清不了显存不应让生成任务本身失败），
          但会在日志明确提示"若下段报 CUDA 类型不匹配多半是显存未释放"。
    """
    # ⚠️ 关键：/free 不是"立即卸载"，而是给 prompt_queue 打 flag，
    #    真正的 unload_all_models() 发生在【下一段 prompt 启动时】（main.py:401-403）。
    #    因此必须带 unload_models/free_memory=true 才生效；发 {} 等于没设 flag，
    #    上一轮 CUDA 错误就是这个原因（flag 没设→上段模型一直缓存→下段 OOM）。
    payload = json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8")
    last_err = None
    for path in ("/free", "/api/free"):
        try:
            req = urllib.request.Request(
                f"{url}{path}", data=payload,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    if not quiet:
                        print("  [free_vram] 已请求 ComfyUI 在下一任务启动时卸载模型"
                              "（unload_models=true；真正的释放发生在下一段 prompt 执行时）")
                    return True
                last_err = f"HTTP {resp.status}"
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue
    print(f"  [free_vram][WARN] 清理显存接口未生效（{last_err}）；"
          f"若后续段报 CUDA 类型不匹配，多半是显存被上一段占用未释放，"
          f"请到 ComfyUI 面板 Queue → Clear / 重启后重跑。")
    return False



def wait(prompt_id, url=DEFAULT_URL, timeout=None, queue_timeout=None):
    """轮询直到完成，返回 outputs 字典。

    等待时间无限（用户要求）：任务**不超时**，会一直等到 ComfyUI 执行结束。
    只有 ComfyUI 工作流**执行报错**（status_str=='error'）才会抛出，
    交由上层执行器处理（当前策略：报错直接跳到下一段，不取消任务、不清理队列）。
    轮询期间每 ~30s 打印一次队列位次，便于观察是否卡在积压队列后。
    """
    submit_time = time.time()
    last_report = submit_time
    exec_start = None

    def _check_history():
        """返回 (state, payload)：state ∈ done|error|running_no_out|absent。"""
        try:
            req = urllib.request.Request(f"{url}/history/{prompt_id}")
            with urllib.request.urlopen(req, timeout=10) as resp:
                history = json.loads(resp.read())
        except Exception as e:
            print(f"  [poll-history] {e}")
            return "absent", None
        if prompt_id not in history:
            return "absent", None
        h = history[prompt_id]
        st = h.get("status", {})
        status_str = st.get("status_str", "")
        if status_str == "error" or (not h.get("outputs") and st.get("completed") is False):
            msgs = st.get("messages", [])
            err_parts = []
            for m in msgs:
                if isinstance(m, (list, tuple)) and len(m) >= 2:
                    d = m[1]
                    if isinstance(d, dict):
                        err_parts.append(d.get("message") or d.get("exception_message") or str(d))
                    else:
                        err_parts.append(str(d))
            return "error", ("; ".join(p for p in err_parts if p) or "未知错误，outputs 为空")
        if h.get("outputs"):
            return "done", h["outputs"]
        return "running_no_out", None

    # ── 无限等待：任务不超时，直到 ComfyUI 执行结束（或执行报错才抛出）──
    while True:
        now = time.time()
        state, payload = _check_history()
        if state == "done":
            return payload
        if state == "error":
            raise RuntimeError(f"ComfyUI 工作流执行失败 (prompt {prompt_id[:8]}): {payload}")
        if now - last_report > 30:
            last_report = now
            qs = get_queue_status(url, prompt_id)
            waited = int(now - submit_time)
            if qs.get("error"):
                print(f"  [{waited}s] 等待中；队列探测失败: {qs['error']}")
            elif qs["our_position"] is not None:
                ahead = qs["our_position"] + (1 if qs["running"] else 0)
                print(f"  [{waited}s] 任务仍在排队，前方约 {ahead} 个任务"
                      f"（running={qs['running']}, pending 共 {qs['pending']}）")
            else:
                print(f"  [{waited}s] 任务执行中（不在 history，也不在 pending 队列）")
        time.sleep(3)


def extract_outputs(outputs):
    """提取生成结果：返回 {nid: {kind: [filenames]}} 与 文本节点输出。

    文本节点输出形态各异，需兼容：
      - 纯字符串：{"text": "..."}
      - 字符串列表（ComfyUI ShowText 常见）：{"text": ["...", "..."]}
      - 字典含 string：{"string": "..."} 或 {"text": {"string": "..."}}
    """
    if not outputs:
        return {}
    out = {}
    for nid, o in outputs.items():
        if not isinstance(o, dict):
            continue
        for kind in ("images", "videos", "gifs", "audio"):
            if kind in o:
                files = [it.get("filename") for it in o[kind]]
                out.setdefault(nid, {})[kind] = files
        # 文本类（ShowText / AILab 等）
        for k, v in o.items():
            texts = []
            if isinstance(v, str) and v:
                texts = [v]
            elif isinstance(v, list):
                texts = [x for x in v if isinstance(x, str)]
            elif isinstance(v, dict):
                if "string" in v and isinstance(v["string"], str):
                    texts = [v["string"]]
                else:
                    for vv in v.values():
                        if isinstance(vv, str) and vv:
                            texts.append(vv)
            if texts:
                out.setdefault(nid, {})[f"text:{k}"] = "\n".join(texts)
    return out


def run(api, url=DEFAULT_URL, timeout=None):
    """提交并等待，返回 extract_outputs 结果。

    任何失败都会向上抛出（ComfyUI 不可达 / 执行报错），不静默返回空。
    注意：等待时间无限（wait 不超时），只有 ComfyUI 工作流执行报错才抛出。
    提交前先感知队列积压：若有 pending 任务，打印警告（不阻断，用户可能本就想排队），
    避免盲排在大量遗留任务之后却毫无提示。
    """
    require_comfy(url)  # 提前明确报错：ComfyUI 未启动/不可达
    qs = get_queue_status(url)
    if qs["error"]:
        print(f"  [队列探测失败] {qs['error']}（仍尝试提交）")
    elif qs["pending"] > 0:
        print(f"  [队列警告] ComfyUI 当前 pending 队列有 {qs['pending']} 个任务"
              f"{('，含 1 个正在执行' if qs['running'] else '')}。"
              f"您的任务将排在其后；若其中是上一轮遗留的批量任务，"
              f"建议先到 ComfyUI 面板 Queue → Clear 清空再跑。")
    pid = submit(api, url)
    print(f"  prompt_id={pid}")
    outputs = wait(pid, url, timeout)
    return extract_outputs(outputs)


if __name__ == "__main__":
    # 简单自检：列出某工作流节点
    if len(sys.argv) < 2:
        print("usage: python Comfy客户端.py <workflow.json> [--list]")
        sys.exit(1)
    wf = load_workflow(sys.argv[1])
    if "--list" in sys.argv:
        for nid in sorted(wf, key=lambda x: int(x)):
            print(f"  [{nid}] {wf[nid].get('class_type')}  '{node_title(wf, nid)}'")
