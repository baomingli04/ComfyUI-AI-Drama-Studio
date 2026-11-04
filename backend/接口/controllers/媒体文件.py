# -*- coding: utf-8 -*-
"""媒体文件服务：GET api/媒体/<相对路径>?token=... 供前端 <img>/<video> 直接显示。

只允许读 资源/ 目录下的文件（上传/产物/技能…），拒绝路径穿越。
图片/视频标签发不出 Authorization 头，这里手动校验 ?token=。

2026-10-26 修复「视频在网页上播不出来」：
    原来一律 200 全量返回，既没有 Accept-Ranges 也没有 Content-Range。
    浏览器（尤其 Chrome 的媒体栈、Safari/iOS）取视频时发的是
    `Range: bytes=0-`，服务端不认 Range 就等于把整个文件硬塞过去：
    进度条拖不动、Safari 直接拒播，个别视频干脆一帧都不出。
    同一个文件走 ComfyUI 的 /view 能播，就是因为 aiohttp 支持 206。
    现在按 RFC 7233 处理单段 Range，并补 ETag / Last-Modified 让缓存可校验。
"""
import io
import mimetypes
import os
import traceback

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotModified, StreamingHttpResponse
from rest_framework_simplejwt.exceptions import InvalidToken

from 接口.认证.JWT认证 import JWT认证
from 接口.返回.错误 import 取错误位置

# 流式读盘的块大小：太小系统调用多，太大首帧慢。256K 兼顾两者。
块大小 = 256 * 1024


def 媒体文件(请求, 相对路径):
    try:
        # 校验 token（?token=），无效一律 401
        令牌 = 请求.GET.get('token') or ''
        if not 令牌:
            return _错误响应(401, 'missing token')
        try:
            验证 = JWT认证()
            已验证 = 验证.get_validated_token(令牌)
            用户 = 验证.get_user(已验证)
        except InvalidToken:
            return _错误响应(401, 'invalid token')
        if 用户 is None or not 用户.启用:
            return _错误响应(401, 'user disabled')

        根 = settings.RESOURCE_DIR.resolve()
        目标 = (根 / 相对路径).resolve()
        # 防穿越：解析后必须仍在资源目录内
        if not str(目标).startswith(str(根)):
            return _错误响应(403, 'forbidden')

        if not 目标.is_file():
            return _错误响应(404, 'not found')

        类型 = _媒体类型(目标)
        总长 = os.path.getsize(str(目标))
        状态 = os.stat(str(目标))
        标记 = '"%x-%x"' % (int(状态.st_mtime * 1000), 总长)
        最后修改 = 状态.st_mtime

        # 缓存校验：内容没变直接 304，省流量也避免「旧缓存播不出来」的怪现象
        if 请求.META.get('HTTP_IF_NONE_MATCH') == 标记:
            return HttpResponseNotModified()

        范围 = _解析范围(请求.META.get('HTTP_RANGE'), 总长)

        # 416：Range 越界，按规范带上总长让浏览器自己重来
        if 范围 == '无效':
            响应 = HttpResponse(b'', status=416, content_type='text/plain; charset=utf-8')
            响应['Content-Range'] = 'bytes */%d' % 总长
            响应['Accept-Ranges'] = 'bytes'
            return 响应

        if 范围:
            起, 止 = 范围
            状态码 = 206
        else:
            起, 止 = 0, 总长 - 1
            状态码 = 200

        长度 = 止 - 起 + 1

        # HEAD：只要头，不要流
        if 请求.method == 'HEAD':
            响应 = HttpResponse(b'', status=状态码, content_type=类型)
        else:
            响应 = StreamingHttpResponse(
                _流式(目标, 起, 长度), status=状态码, content_type=类型)

        响应['Content-Length'] = str(长度)
        响应['Accept-Ranges'] = 'bytes'
        响应['ETag'] = 标记
        响应['Last-Modified'] = _http日期(最后修改)
        # no-cache = 可以存，但每次必须回源校验（配合 ETag 走 304）
        响应['Cache-Control'] = 'no-cache'
        if 状态码 == 206:
            响应['Content-Range'] = 'bytes %d-%d/%d' % (起, 止, 总长)
        return 响应

    except Exception as 异常:
        位置 = 取错误位置(异常)
        traceback.print_exc()
        return _错误响应(500, 'error: %s | %s:%s %s' % (异常, 位置['file'], 位置['line'], 位置['func']))


def _媒体类型(目标):
    """按扩展名给 Content-Type，猜不出时给 octet-stream（别让浏览器乱猜）。"""
    类型, _编码 = mimetypes.guess_type(str(目标))
    if 类型:
        return 类型
    后缀 = 目标.suffix.lower()
    表 = {'.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime',
          '.m4a': 'audio/mp4', '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
          '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
          '.webp': 'image/webp', '.gif': 'image/gif'}
    return 表.get(后缀, 'application/octet-stream')


def _解析范围(头, 总长):
    """解析 Range 头，只认单段（多段浏览器几乎不用，硬塞反而更容易出错）。

    返回：None = 没带 Range（走 200 全量）
          '无效' = 越界/格式错（走 416）
          (起, 止) = 要返回的闭区间（走 206）
    """
    if not 头 or not 头.startswith('bytes='):
        return None
    段 = 头[len('bytes='):].split(',')[0].strip()
    if '-' not in 段:
        return '无效'
    左, _sep, 右 = 段.partition('-')
    左, 右 = 左.strip(), 右.strip()
    try:
        if 左 == '':
            # bytes=-N：要最后 N 字节
            if not 右:
                return '无效'
            长 = int(右)
            if 长 <= 0:
                return '无效'
            起 = max(0, 总长 - 长)
            止 = 总长 - 1
        else:
            起 = int(左)
            止 = int(右) if 右 else 总长 - 1
    except ValueError:
        return '无效'
    if 起 < 0 or 起 > 止 or 起 >= 总长:
        return '无效'
    return (起, min(止, 总长 - 1))


def _流式(目标, 起, 长度):
    """按区间流式读盘；生成器退出时 with 会关掉文件句柄。"""
    def 生成器():
        with open(str(目标), 'rb') as 文件:
            if 起:
                文件.seek(起)
            剩 = 长度
            while 剩 > 0:
                数据 = 文件.read(min(块大小, 剩))
                if not 数据:
                    break
                剩 -= len(数据)
                yield 数据
    return 生成器()


def _http日期(时间戳):
    from email.utils import formatdate
    return formatdate(时间戳, usegmt=True)


def _错误响应(状态码, 文本):
    响应 = HttpResponse(文本.encode('utf-8'), status=状态码,
                        content_type='text/plain; charset=utf-8')
    return 响应
