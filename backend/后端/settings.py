"""Django 配置：本地局域网平台，分端口（后端 8001）。"""
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'aicg-local-platform-secret-key-zhsw-2026-0826-stable'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'corsheaders',
    'rest_framework',
    '接口',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = '后端.urls'
WSGI_APPLICATION = '后端.wsgi.application'
ASGI_APPLICATION = '后端.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'aicg',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['接口.认证.JWT认证'],
    'UNAUTHENTICATED_USER': None,
    'EXCEPTION_HANDLER': '接口.返回.统一异常处理',
}

CORS_ALLOW_ALL_ORIGINS = True

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False

# 媒体根目录（约定路径，不进配置表）
# 注意：Django settings 只拷贝全大写属性（setting.isupper()），中文属性名进不了
# settings 对象，所以业务代码一律用下面的英文大写别名。
资源目录 = BASE_DIR / '资源'
上传目录 = 资源目录 / '上传'
产物目录 = 资源目录 / '产物'
技能目录 = 资源目录 / '技能'
日志目录 = 资源目录 / '日志'
RESOURCE_DIR = 资源目录
UPLOAD_DIR = 上传目录
OUTPUT_DIR = 产物目录
SKILL_DIR = 技能目录
LOG_DIR = 日志目录

# ffmpeg：本机 PATH 里没有 ffmpeg，用本机 ComfyUI 环境里 imageio-ffmpeg 自带的那份。
# 注意 imageio-ffmpeg 只带 ffmpeg、不带 ffprobe，所以音频信息（时长/采样率/声道）
# 由 能力/音频剪辑.py 解析 `ffmpeg -i` 的 stderr 得到。
#
# 2026-10-20 修正：原路径指向 D:\LiblibAI-workspace\...（该目录已不在本机），
# 换成绘世启动器版 ComfyUI 里实际存在的那份 ffmpeg 7.1。
FFMPEG_EXE = r'D:\ComfyUI-aki-v3\python\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'

# JWT：登录签发 AccessToken，有效期 30 天（不满足 simplejwt 默认 5 分钟，避免动不动掉线）
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=30),
}
