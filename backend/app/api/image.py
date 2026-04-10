from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.core.deps import get_current_user
from app.models.user import User
from app.core.config import settings
import httpx
import base64
import logging
import urllib.parse
from io import BytesIO
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)
from app.core.security import limiter

router = APIRouter(prefix="/image", tags=["Image"])


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512


def _make_placeholder_image(prompt: str, width: int, height: int, reason: str) -> str:
    """Return a base64 PNG placeholder when generation fails."""
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    for x in range(0, width, 32):
        draw.line([(x, 0), (x, height)], fill=(25, 33, 55), width=1)
    for y in range(0, height, 32):
        draw.line([(0, y), (width, y)], fill=(25, 33, 55), width=1)
    draw.rectangle([4, 4, width - 4, height - 4], outline=(99, 102, 241), width=2)
    draw.text((width // 2, height // 2 - 30), "Image Service Offline", fill=(156, 163, 175), anchor="mm")
    short_prompt = (prompt[:50] + "...") if len(prompt) > 50 else prompt
    draw.text((width // 2, height // 2 + 10), f'"{short_prompt}"', fill=(209, 213, 219), anchor="mm")
    draw.text((width // 2, height // 2 + 50), reason, fill=(99, 102, 241), anchor="mm")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.post("/generate")
@limiter.limit("10/minute")
async def image_generate(
    request: Request,
    payload: ImageGenerateRequest,
    user: User = Depends(get_current_user)
):
    """Generate image using Hugging Face Inference API with PIL placeholder fallback."""
    logger.info(f"Image generation request from {user.username}: {payload.prompt}")

    api_key = getattr(settings, "HUGGINGFACE_API_KEY", None)
    model_id = getattr(settings, "HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
    
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
    
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        logger.warning("No Hugging Face API key provided. Image generation may fail.")
        
    image_base64 = None
    model_used = None

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            logger.info(f"Requesting Hugging Face ({model_id})...")
            try:
                response = await client.post(api_url, headers=headers, json={"inputs": payload.prompt})
                logger.info(f"Hugging Face status: {response.status_code}")
                content_type = response.headers.get("content-type", "")
                if response.status_code == 200 and content_type.startswith("image/"):
                    image_base64 = base64.b64encode(response.content).decode()
                    model_used = model_id
                else:
                    logger.warning(f"Hugging Face returned {response.status_code} ({response.text[:200]}). Trying fallback...")
            except Exception as e:
                logger.warning(f"Hugging Face error: {e}. Trying fallback...")
                
            if not image_base64:
                # Fallback to Airforce API
                logger.info("Requesting Airforce API fallback...")
                encoded_prompt = urllib.parse.quote(payload.prompt)
                airforce_url = f"https://api.airforce/v1/imagine?prompt={encoded_prompt}"
                airforce_res = await client.get(airforce_url)
                logger.info(f"Airforce status: {airforce_res.status_code}")
                af_content_type = airforce_res.headers.get("content-type", "")
                
                if airforce_res.status_code == 200 and af_content_type.startswith("image/"):
                    image_base64 = base64.b64encode(airforce_res.content).decode()
                    model_used = "airforce-imagine"
                else:
                    logger.warning(f"Airforce API returned {airforce_res.status_code} ({af_content_type})")
                    
    except Exception as e:
        logger.warning(f"Image APIs total failure: {e}")

    if image_base64:
        return {
            "image_url": f"data:image/jpeg;base64,{image_base64}",
            "prompt": payload.prompt,
            "model": model_used,
        }

    # Fallback placeholder — never crash the frontend
    img_b64 = _make_placeholder_image(
        payload.prompt, payload.width, payload.height,
        "Pollinations.ai unreachable"
    )
    return {
        "image_url": f"data:image/png;base64,{img_b64}",
        "prompt": payload.prompt,
        "model": "placeholder",
        "warning": "Image generation service is currently unreachable.",
    }
