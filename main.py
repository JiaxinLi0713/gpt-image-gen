# ── 标准库 ──────────────────────────────────────────────────────────────────
import io
import os

# ── 第三方库 ─────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from PIL import Image  # Pillow：将上传的任意格式图片转为 OpenAI 要求的 RGBA PNG

# ── 配置：从 .env 文件读取，不硬编码在源码里 ──────────────────────────────────
# load_dotenv() 读取当前目录的 .env 并写入环境变量，文件不存在时静默跳过
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]  # 缺失时启动即报错，避免运行时才发现
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # 可选，None 时 SDK 使用官方默认地址

# ── 初始化 ────────────────────────────────────────────────────────────────────
# OpenAI 客户端：复用单一实例，避免每次请求重复建立 HTTP 连接
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
app = FastAPI(title="GPT Image Generator")

# ── 静态资源 & 根路由 ─────────────────────────────────────────────────────────
# 把 static/ 目录挂载为 /static，index.html 里的 CSS/JS 引用走这个路径
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    # 直接返回 HTML 文件，让浏览器渲染前端页面
    return FileResponse("static/index.html")


# ── 图像生成接口 ───────────────────────────────────────────────────────────────
@app.post("/api/generate")
async def generate_image(
    prompt: str = Form(...),  # 必填：图像描述文字
    size: str = Form("1024x1024"),  # 输出尺寸，默认正方形
    quality: str = Form("medium"),  # 质量档位：low / medium / high
    image: UploadFile | None = File(
        None
    ),  # 可选：参考图片；有则走 edit，无则走 generate
):
    try:
        if image and image.filename:
            # ── 多模态路径：图片 + 文字 → 编辑/再创作 ──────────────────────────
            raw = await image.read()  # 读取上传的原始字节

            # OpenAI edit 接口要求图片为 RGBA PNG；
            # 用 Pillow 统一转换，兼容 JPEG / WebP / PNG 等任意来源格式
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)  # 重置指针，确保 SDK 从头读取

            response = client.images.edit(
                model="gpt-image-2",
                image=("input.png", buf, "image/png"),  # (文件名, 文件对象, MIME)
                prompt=prompt,
                n=1,
                size=size,
            )
        else:
            # ── 纯文本路径：只用 prompt 生图 ────────────────────────────────────
            response = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,  # edit 接口不支持 quality 参数，故只在此传入
            )

        # ── 处理响应 ──────────────────────────────────────────────────────────
        item = response.data[0]

        if item.b64_json:
            # 常规情况：模型直接返回 base64 编码的图片数据
            return JSONResponse({"image": item.b64_json})

        # 某些配置下模型返回临时 URL 而非 base64
        if item.url:
            return JSONResponse({"url": item.url})

        raise HTTPException(status_code=500, detail="No image data in response")

    except HTTPException:
        raise  # 直接透传已封装好的 HTTP 错误，不重复包装
    except Exception as e:
        # 将 OpenAI SDK 异常（鉴权失败、内容政策拒绝等）统一转为 500 返回给前端
        raise HTTPException(status_code=500, detail=str(e))
