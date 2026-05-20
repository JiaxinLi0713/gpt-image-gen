import io
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from PIL import Image

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
app = FastAPI(title="GPT Image Generator")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/api/generate")
async def generate_image(
    prompt: str = Form(...),
    size: str = Form("1024x1024"),
    quality: str = Form("medium"),
    image: UploadFile | None = File(None),
):
    try:
        if image and image.filename:
            raw = await image.read()
            img = Image.open(io.BytesIO(raw)).convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            response = client.images.edit(
                model="gpt-image-2",
                image=("input.png", buf, "image/png"),
                prompt=prompt,
                n=1,
                size=size,
            )
        else:
            response = client.images.generate(
                model="gpt-image-2",
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,
            )

        item = response.data[0]

        if item.b64_json:
            return JSONResponse({"image": item.b64_json})

        if item.url:
            return JSONResponse({"url": item.url})

        raise HTTPException(status_code=500, detail="No image data in response")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
