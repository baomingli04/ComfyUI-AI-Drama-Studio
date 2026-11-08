#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视觉识别.py — 图片视觉识别后端（技能通用能力，供 ② 角色图解析等流程复用）。

【用途】
  把「给一张图、返回视觉描述文本」抽象为可复用后端，当前内置两类：
    1) 远程 llama.cpp 视觉端点（OpenAI 兼容 /v1/chat/completions），如 192.168.31.131:8488
    2) 本地 ComfyUI 反推工作流（技能内置 ② 反推，反推提示词.run_reverse）

【智能回退策略（核心规则，用户明确要求）】
  每次识别前先看远程端点忙不忙：
    · 远程在线 且 不忙  → 用远程（快，约 1–3 秒/张）
    · 远程忙 / 不在线   → 自动回退 ComfyUI（慢，约 90 秒/张，但稳）
  这样既不冲击繁忙的共享端点，又始终有可用后端，不卡死。

【忙闲探测】
  对 llama.cpp 视觉端点 GET /slots，统计 is_processing==true 的槽位数：
    · 不可达 / 无 /slots        → 视为不在线，触发回退
    · 处理中槽位数 ≥ busy_threshold → 视为忙
    · busy_threshold 默认 = 槽位总数（即全部饱和才算忙，允许并发）；
      传 1 则表示「任一槽位在跑就算忙」。
  若 /slots 不可用但 /health 可达，则乐观视为不忙（能连上就试着用）。

【用法（作为库）】
  from 视觉识别 import VisionRecognizer
  rec = VisionRecognizer(remote_url="http://192.168.31.131:8488",
                         comfy_url="http://127.0.0.1:8188")
  text, src = rec.recognize("x.png", prompt="描述这张图...")
  # src ∈ {"remote", "comfy", "comfy(fallback)", "comfy(远程已失联)"}

【用法（命令行自测）】
  python 视觉识别.py --check --remote-url http://192.168.31.131:8488
  python 视觉识别.py --image x.png --prompt "描述..." --remote-url http://192.168.31.131:8488
"""
import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error

DEFAULT_COMFY_URL = "http://127.0.0.1:8188"


def _get(url, timeout=10, decode="json"):
    """GET 一个 URL，返回解析后的对象或原始文本；失败抛 urllib.error/异常。"""
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    if decode == "json":
        return json.loads(raw)
    return raw.decode("utf-8", "ignore")


class VisionRecognizer:
    def __init__(self, remote_url=None, remote_model=None,
                 comfy_url=DEFAULT_COMFY_URL, timeout=120,
                 busy_threshold=None, busy_check=True, no_fallback=False):
        self.remote_url = remote_url.rstrip("/") if remote_url else None
        self.remote_model = remote_model
        self.comfy_url = comfy_url.rstrip("/") if comfy_url else None
        self.timeout = timeout
        self.busy_threshold = busy_threshold
        self.busy_check = busy_check          # 是否启用忙闲探测（默认开）
        self.no_fallback = no_fallback        # 远程失败/忙时不回退 ComfyUI
        self._remote_dead = False             # 运行期内若远程彻底失联则锁死→直走 ComfyUI

    # ── 远程端点状态 ──────────────────────────────────────────────
    def remote_status(self):
        """返回 (up, busy, detail)。
        up: 端点是否可达；busy: 当前是否视为忙；detail: 人类可读说明。"""
        if not self.remote_url:
            return False, False, "未配置远程端点"
        url = self.remote_url
        # 优先用 /slots 同时判定「可达 + 忙闲」
        try:
            slots = _get(url + "/slots", timeout=8)
            if isinstance(slots, list):
                total = len(slots)
                processing = sum(1 for s in slots
                                 if isinstance(s, dict) and s.get("is_processing"))
                thr = self.busy_threshold if self.busy_threshold is not None else max(1, total)
                busy = processing >= thr
                detail = f"slots 总={total} 处理中={processing} 阈值={thr}"
                return True, busy, detail
        except Exception:
            pass  # /slots 不可用，退化到 /health
        # 退化：只判可达
        try:
            _get(url + "/health", timeout=8)
            return True, False, "可达（/slots 不可用，乐观视为不忙）"
        except Exception:
            pass
        return False, True, "远程不可达"

    def ensure_model(self):
        """远程模式：在线且未指定模型时，自动取 /v1/models 第一个。失败 fail-loud。"""
        if not self.remote_url or self.remote_model:
            return
        try:
            mj = _get(self.remote_url + "/v1/models", timeout=10)
            if mj.get("data"):
                self.remote_model = mj["data"][0]["id"]
                print(f"[vision] 远程自动选用模型: {self.remote_model}")
            else:
                raise RuntimeError(f"远程 {self.remote_url} 未返回任何模型")
        except Exception as e:
            raise RuntimeError(
                f"未指定 --backend-model 且无法从远程列举模型: {e}")

    # ── 两个具体后端 ─────────────────────────────────────────────
    def recognize_remote(self, image_path, prompt):
        self.ensure_model()
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        payload = {
            "model": self.remote_model,
            "messages": [{"role": "user", "content": [
                {"type": "image_url",
                 "image_url": {"url": "data:image/png;base64," + b64}},
                {"type": "text", "text": prompt},
            ]}],
        }
        body = json.dumps(payload).encode()
        url = self.remote_url + "/v1/chat/completions"
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"远程识别 HTTP {e.code} @ {url}: "
                f"{e.read().decode('utf-8', 'ignore')[:300]}")
        except Exception as e:
            raise RuntimeError(f"远程识别失败 @ {url}: {e}")

    def recognize_comfy(self, image_path, prompt):
        # 延迟导入，避免只用远程时也强依赖 ComfyUI 侧脚本
        from 反推提示词 import run_reverse
        return run_reverse(image_path, prompt=prompt,
                           url=self.comfy_url, timeout=self.timeout)

    # ── 编排：先探测忙闲，忙/不在线则回退 ComfyUI ─────────────────
    def recognize(self, image_path, prompt):
        """返回 (text, source)。source 标识实际走的后端，便于日志与排查。"""
        if not self.remote_url:
            # 未配置远程：纯 ComfyUI
            return self.recognize_comfy(image_path, prompt), "comfy"

        if self._remote_dead:
            return self.recognize_comfy(image_path, prompt), "comfy(远程已失联)"

        up, busy, detail = self.remote_status()
        if not up:
            self._remote_dead = True
            print(f"[vision] 远程不在线（{detail}），回退 ComfyUI。")
            return self.recognize_comfy(image_path, prompt), "comfy(fallback)"
        if self.busy_check and busy:
            print(f"[vision] 远程忙（{detail}），回退 ComfyUI（慢但稳）。")
            return self.recognize_comfy(image_path, prompt), "comfy(fallback)"

        # 远程在线且不忙 → 走远程；若远程调用失败则回退 ComfyUI（除非 --no-fallback）
        try:
            return self.recognize_remote(image_path, prompt), "remote"
        except Exception as e:
            if self.no_fallback:
                raise
            print(f"[vision] 远程识别异常（{e}），回退 ComfyUI。")
            return self.recognize_comfy(image_path, prompt), "comfy(fallback)"


def _cli():
    ap = argparse.ArgumentParser(
        description="图片视觉识别（远程优先，忙/不在线则回退 ComfyUI）")
    ap.add_argument("--image", help="待识别图片路径")
    ap.add_argument("--prompt", default=None, help="识别提示词（--check 时可省略）")
    ap.add_argument("--remote-url", default=None, help="远程 llama.cpp 视觉端点")
    ap.add_argument("--backend-model", default=None, help="远程模型名（不给自动取）")
    ap.add_argument("--comfy-url", default=DEFAULT_COMFY_URL)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--busy-threshold", type=int, default=None,
                    help="远程忙闲阈值（处理中槽位数 ≥ 此值才算忙）；默认=槽位总数")
    ap.add_argument("--no-fallback", action="store_true",
                    help="远程失败/忙时不回退 ComfyUI，强制只用远程")
    ap.add_argument("--check", action="store_true",
                    help="只打印远程忙闲状态，不做识别")
    args = ap.parse_args()

    rec = VisionRecognizer(
        remote_url=args.remote_url, remote_model=args.backend_model,
        comfy_url=args.comfy_url, timeout=args.timeout,
        busy_threshold=args.busy_threshold, no_fallback=args.no_fallback)

    if args.check:
        up, busy, detail = rec.remote_status()
        print(f"远程 {args.remote_url}")
        print(f"  在线={up}  忙={busy}")
        print(f"  {detail}")
        return

    if not args.image:
        ap.error("--image 必填（除非用 --check）")
    if not args.prompt:
        ap.error("--prompt 必填（除非用 --check）")
    if not os.path.exists(args.image):
        ap.error(f"图片不存在: {args.image}")

    text, src = rec.recognize(args.image, args.prompt)
    print(f"[backend] {src}")
    print("---- 识别结果 ----")
    print(text)


if __name__ == "__main__":
    _cli()
