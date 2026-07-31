from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.core.deps import require_consent, get_db
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.chat import ChatMessage, ChatSession
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
    session_id: str | None = None


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
    user: User = Depends(require_consent),
    db: Session = Depends(get_db)
):
    """Generate image using Hugging Face Inference API with PIL placeholder fallback."""
    logger.info(f"Image generation request from {user.username}: {payload.prompt}")

    image_base64 = None
    model_used = None

    logger.info("Requesting image from Pollinations AI...")
    try:
        encoded_prompt = urllib.parse.quote(payload.prompt)
        width = payload.width if payload.width else 1024
        height = payload.height if payload.height else 1024
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model=flux&nologo=true"
        
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as p_client:
            response = await p_client.get(pollinations_url)
            if response.status_code == 200:
                image_base64 = base64.b64encode(response.content).decode('utf-8')
                model_used = "pollinations.ai/flux"
            else:
                logger.warning(f"Pollinations AI failed with status: {response.status_code}")
    except Exception as e:
        logger.error(f"Pollinations AI error: {e}")

    if image_base64:
        image_url = f"data:image/jpeg;base64,{image_base64}"
        
        session_id = payload.session_id
        if not session_id:
            import uuid
            new_session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=payload.prompt[:50]
            )
            db.add(new_session)
            session_id = new_session.id
            
        try:
            # User prompt
            user_msg = ChatMessage(
                session_id=session_id,
                role="user",
                content=payload.prompt
            )
            db.add(user_msg)
            
            # Assistant image response
            asst_msg = ChatMessage(
                session_id=session_id,
                role="assistant",
                content="Here is your generated image:",
                image=image_url,
                model=model_used
            )
            db.add(asst_msg)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save image to chat history: {e}")
            db.rollback()

        return JSONResponse(
            content={
                "image_url": image_url,
                "prompt": payload.prompt,
                "model": model_used,
                "session_id": session_id
            },
            headers={"X-Chat-Session-ID": str(session_id)}
        )

    # Fallback placeholder — never crash the frontend
    img_b64 = _make_placeholder_image(
        payload.prompt, payload.width, payload.height,
        "Image Generation Failed"
    )
    return {
        "image_url": f"data:image/png;base64,{img_b64}",
        "prompt": payload.prompt,
        "model": "placeholder",
        "warning": "Image generation service is currently unreachable.",
    }
