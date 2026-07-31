import base64
import os
import logging
import urllib.parse
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import httpx
from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


async def generate_image(prompt: str, user: User) -> dict:
    """Generate image using Hugging Face (default), SDXL, or mock fallback."""

    # 1. Try NVIDIA API or Hugging Face Inference API
    try:
        api_key = getattr(settings, "DEFAULT_CHAT_API_KEY", None)
        model_id = getattr(settings, "IMAGE_GENERATION_MODEL", "black-forest-labs/flux-1-schnell")
        
        if api_key:
            is_nvidia = api_key.startswith("nvapi")
            
            if is_nvidia:
                url = "https://integrate.api.nvidia.com/v1/images/generations"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_id,
                    "prompt": prompt,
                    "response_format": "b64_json"
                }
                logger.info(f"Generating image via NVIDIA API (model={model_id})...")
            else:
                url = f"https://api.airforce/v1/imagine?prompt={urllib.parse.quote(prompt)}"
                headers = {}
                payload = {}
                logger.info(f"Generating image via fallback...")

            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    if is_nvidia:
                        data = response.json()
                        image_base64 = data["data"][0]["b64_json"]
                        provider = "nvidia"
                    else:
                        image_base64 = base64.b64encode(response.content).decode()
                        provider = "huggingface"
                        
                    return {
                        "status": "success",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                        "provider": provider,
                    }
                else:
                    logger.warning(f"API returned status {response.status_code} ({response.text[:200]}). Falling back...")
        else:
            logger.warning("No API KEY set. Skipping primary provider.")
    except Exception as e:
        logger.warning(f"Image generation failed: {e}. Falling back...")



    # 3. Try Local/External SDXL
    sdxl_url = getattr(settings, "SDXL_URL", None)
    if sdxl_url:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{sdxl_url}/api/generate",
                    json={
                        "prompt": prompt,
                        "negative_prompt": "blurry, low quality, distorted",
                        "steps": 25,
                    },
                )
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "image_url": f"data:image/png;base64,{result['image']}",
                        "provider": "sdxl",
                    }
        except Exception as e:
            logger.warning(f"SDXL connection failed: {e}. Using mock fallback...")

    # 3. Mock fallback — generate a placeholder image using PIL
    logger.info("Using mock image fallback (PIL-generated placeholder).")
    try:
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), color=(15, 23, 42))  # dark blue-gray
        draw = ImageDraw.Draw(img)

        # Gradient-style background stripes
        for i in range(0, height, 4):
            alpha = int(255 * (i / height) * 0.3)
            draw.line([(0, i), (width, i)], fill=(30 + alpha // 4, 40 + alpha // 3, 80 + alpha // 2))

        # Border frame
        draw.rectangle([20, 20, width - 20, height - 20], outline=(99, 102, 241), width=3)

        # Label text
        label = "Image Generation Offline"
        draw.text((width // 2, height // 2 - 40), label, fill=(156, 163, 175), anchor="mm")
        prompt_short = (prompt[:60] + "...") if len(prompt) > 60 else prompt
        draw.text((width // 2, height // 2 + 20), f'"{prompt_short}"', fill=(209, 213, 219), anchor="mm")
        draw.text((width // 2, height // 2 + 80), "Image Generation Failed", fill=(99, 102, 241), anchor="mm")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode()

        return {
            "status": "success",
            "image_url": f"data:image/png;base64,{img_b64}",
            "provider": "mock",
            "warning": "Image generation service unreachable. Showing placeholder.",
        }
    except Exception as e:
        logger.error(f"Mock image generation failed: {e}")
        return {"status": "error", "message": "Image generation failed. Please try again later."}