# -*- coding: utf-8 -*-
"""LLM 调用：读模型配置的 LLM地址/模型名/密钥，OpenAI 兼容 chat/completions。"""
import base64
import json
import urllib.error
import urllib.request


# 内网直连：本机环境变量可能带 HTTP_PROXY（沙箱代理），访问 Comfy/LLM 必须绕开，
# 否则代理会间歇性掐断连接（10053/10054/503），任务被误判中断。
直连opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

from 能力.提交并等待 import 补协议, 取模型配置


def 调用LLM(消息列表, 超时=300):
    """消息列表 = [{'role':..., 'content':...}]，返回模型回复文本。"""
    配置 = 取模型配置()
    地址 = 补协议(配置.LLM地址)
    if not 地址:
        raise RuntimeError('模型配置未填写 LLM地址，请先到「模型配置」页保存。')
    模型名 = 配置.LLM模型名 or 配置.大模型名称 or ''
    body = {'model': 模型名, 'messages': 消息列表, 'stream': False}
    头 = {'Content-Type': 'application/json'}
    if 配置.LLM密钥:
        头['Authorization'] = 'Bearer ' + 配置.LLM密钥
    req = urllib.request.Request(
        地址 + '/v1/chat/completions',
        data=json.dumps(body).encode('utf-8'), headers=头)
    try:
        with 直连opener.open(req, timeout=超时) as resp:
            数据 = json.loads(resp.read().decode('utf-8', 'replace'))
    except urllib.error.HTTPError as e:
        明细 = e.read().decode('utf-8', 'replace')[:300]
        raise RuntimeError('LLM 返回 HTTP %s：%s' % (e.code, 明细))
    try:
        return 数据['choices'][0]['message']['content']
    except (KeyError, IndexError):
        raise RuntimeError('LLM 返回格式异常：%s' % json.dumps(数据, ensure_ascii=False)[:300])


def 调用LLM流式(消息列表, 超时=300, on增量=None):
    """流式调用 LLM：on增量(累计文本) 每收到一块回调一次，返回完整回复文本。

    服务端不支持 stream 或流式过程中断时，自动回退到一次性的 调用LLM。
    """
    配置 = 取模型配置()
    地址 = 补协议(配置.LLM地址)
    if not 地址:
        raise RuntimeError('模型配置未填写 LLM地址，请先到「模型配置」页保存。')
    模型名 = 配置.LLM模型名 or 配置.大模型名称 or ''
    body = {'model': 模型名, 'messages': 消息列表, 'stream': True}
    头 = {'Content-Type': 'application/json', 'Accept': 'text/event-stream'}
    if 配置.LLM密钥:
        头['Authorization'] = 'Bearer ' + 配置.LLM密钥
    req = urllib.request.Request(
        地址 + '/v1/chat/completions',
        data=json.dumps(body).encode('utf-8'), headers=头)
    累计 = []
    try:
        with 直连opener.open(req, timeout=超时) as resp:
            for 原始行 in resp:
                行 = 原始行.decode('utf-8', 'replace').strip()
                if not 行.startswith('data:'):
                    continue
                数据块 = 行[len('data:'):].strip()
                if not 数据块 or 数据块 == '[DONE]':
                    if 数据块 == '[DONE]':
                        break
                    continue
                try:
                    片 = json.loads(数据块)
                except ValueError:
                    continue
                选择们 = 片.get('choices') or [{}]
                delta = 选择们[0].get('delta') or {}
                文本 = delta.get('content') or ''
                if 文本:
                    累计.append(文本)
                    if on增量:
                        try:
                            on增量(''.join(累计))
                        except Exception:
                            pass
        结果 = ''.join(累计)
        if 结果:
            return 结果
    except Exception:
        # 流式链路任何异常（服务端不支持 stream / 中途断流）都回退一次性调用
        pass
    return 调用LLM(消息列表, 超时=超时)


def 图片转数据URI(文件路径):
    后缀 = 文件路径.rsplit('.', 1)[-1].lower() or 'png'
    with open(文件路径, 'rb') as f:
        数据 = f.read()
    return 'data:image/%s;base64,%s' % (后缀, base64.b64encode(数据).decode('ascii'))
