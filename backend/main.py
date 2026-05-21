from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from watermark_engine.processor import watermark_processor
from watermark_engine.cropper import PhotoCropper
import io

app = FastAPI(title="Watermark Removal API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WatermarkRegion(BaseModel):
    x: float = 0.0
    y: float = 0.85
    w: float = 1.0
    h: float = 0.15


class BrushRegion(BaseModel):
    x: float
    y: float
    w: float = 0.05
    h: float = 0.05


class AutoRemoveRequest(BaseModel):
    region: WatermarkRegion | None = None


class ManualRemoveRequest(BaseModel):
    brush_regions: list[BrushRegion]


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "watermark-removal"}


@app.post("/api/detect")
async def detect_watermark(file: UploadFile = File(...)):
    contents = await file.read()
    result = watermark_processor.detect_watermark_region(contents)
    return result


@app.post("/api/remove/auto")
async def remove_auto(
    file: UploadFile = File(...),
    x: float = 0.0,
    y: float = 0.0,
    w: float = 0.0,
    h: float = 0.0
):
    contents = await file.read()
    region = None
    if w > 0 and h > 0:
        region = {"x": x, "y": y, "w": w, "h": h}
    result_bytes = watermark_processor.remove_watermark_auto(contents, region)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/remove/manual")
async def remove_manual(
    file: UploadFile = File(...),
    mask: UploadFile = File(...)
):
    import cv2
    import numpy as np

    contents = await file.read()
    mask_contents = await mask.read()

    img = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    mask_img = cv2.imdecode(np.frombuffer(mask_contents, np.uint8), cv2.IMREAD_GRAYSCALE)

    if mask_img is not None:
        mask_img = cv2.resize(mask_img, (img.shape[1], img.shape[0]))

    result_bytes = watermark_processor.remove_watermark_manual_with_mask(contents, mask_img)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/crop")
async def crop_photo(
    file: UploadFile = File(...),
    x: float = 0.0,
    y: float = 0.0,
    w: float = 0.5,
    h: float = 0.5,
    target_w: int = 295,
    target_h: int = 413
):
    contents = await file.read()
    result_bytes = PhotoCropper.crop_and_resize(contents, x, y, w, h, target_w, target_h)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/layout")
async def layout_photo(
    file: UploadFile = File(...),
    spec: str = "1inch"
):
    contents = await file.read()
    result_bytes = PhotoCropper.generate_layout(contents, spec)
    return StreamingResponse(io.BytesIO(result_bytes), media_type="image/png")


@app.post("/api/compress")
async def compress_image(
    file: UploadFile = File(...),
    quality: int = 75,
    fmt: str = "jpeg"
):
    from PIL import Image

    contents = await file.read()
    img = Image.open(io.BytesIO(contents))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    out = io.BytesIO()
    save_fmt = "JPEG" if fmt.lower() in ("jpeg", "jpg") else fmt.upper()
    save_kwargs = {}
    if save_fmt == "JPEG":
        save_kwargs = {"quality": quality, "optimize": True}
    elif save_fmt == "PNG":
        save_kwargs = {"optimize": True}
    elif save_fmt == "WEBP":
        save_kwargs = {"quality": quality}

    img.save(out, format=save_fmt, **save_kwargs)
    out.seek(0)

    mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
    return StreamingResponse(out, media_type=mime.get(save_fmt, "image/jpeg"))