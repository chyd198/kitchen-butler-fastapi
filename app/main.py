import base64
import io
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

from app.agent import agent
from app.schemas import RecommendResponse

app = FastAPI(title="AI Kitchen Butler")
app.mount("/static", StaticFiles(directory="static"), name="static")


def _compress(file_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(file_bytes))
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/api/recommend", response_model=RecommendResponse)
async def recommend(
    message: str = Form("帮我推荐几个食谱"),
    thread_id: str = Form(None),
    image: UploadFile = File(None),
):
    thread_id = thread_id or uuid.uuid4().hex

    if image is not None:
        raw = await image.read()
        compressed = _compress(raw)
        # Kimi's vision API rejects external image URLs outright (tested against
        # both OSS signed URLs and a public URL — "unsupported image url"),
        # so it only ever gets a base64 data URI.
        b64 = base64.b64encode(compressed).decode()
        content = [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": message},
        ]
    else:
        content = message

    try:
        result = agent.invoke(
            {"messages": [("human", content)]},
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent call failed: {e}")

    answer = result["messages"][-1].content
    return RecommendResponse(thread_id=thread_id, answer=answer)
