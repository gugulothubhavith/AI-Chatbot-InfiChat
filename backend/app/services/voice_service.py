import os
import logging
import time
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback Local Whisper Config
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
DEVICE = "cpu"
COMPUTE_TYPE = "int8"

_CPU_COUNT = os.cpu_count() or 2

# CTranslate2 (faster-whisper's backend) parallelises a single transcription
# across `cpu_threads`, and serves concurrent transcribe() calls from separate
# Python threads across `num_workers`. Splitting the cores between the two is
# what lets several users transcribe at once instead of queueing: with
# num_workers=1 every request past the first waits for the one in flight.
WHISPER_NUM_WORKERS = max(1, int(os.getenv("WHISPER_NUM_WORKERS", str(min(4, _CPU_COUNT)))))
WHISPER_CPU_THREADS = max(1, int(os.getenv("WHISPER_CPU_THREADS", str(max(1, _CPU_COUNT // WHISPER_NUM_WORKERS)))))

_model_instance = None
_kokoro_model = None

# Guards for lazy singleton init. Without these, two parallel requests can both
# see the model as None and each load a full copy — doubling memory and load
# time on the first concurrent hit.
_model_lock = threading.Lock()
_kokoro_lock = threading.Lock()

# Transcription runs on its own thread pool rather than asyncio's shared
# default executor. Sized to num_workers, it bounds concurrent decodes to what
# CTranslate2 was built to serve, and keeps a burst of transcriptions from
# occupying every thread in the default pool that the rest of the app uses.
_transcribe_pool = ThreadPoolExecutor(
    max_workers=WHISPER_NUM_WORKERS, thread_name_prefix="whisper"
)

def get_local_model():
    global _model_instance
    if _model_instance is None:
        with _model_lock:
            # Double-checked: another thread may have loaded it while we waited.
            if _model_instance is None:
                from faster_whisper import WhisperModel
                logger.info(
                    "Loading local Whisper model: %s on %s "
                    "(num_workers=%d, cpu_threads=%d)...",
                    MODEL_SIZE, DEVICE, WHISPER_NUM_WORKERS, WHISPER_CPU_THREADS,
                )
                try:
                    _model_instance = WhisperModel(
                        MODEL_SIZE,
                        device=DEVICE,
                        compute_type=COMPUTE_TYPE,
                        num_workers=WHISPER_NUM_WORKERS,
                        cpu_threads=WHISPER_CPU_THREADS,
                    )
                except Exception as e:
                    logger.error(f"Failed to load local Whisper model: {e}")
                    raise e
    return _model_instance


def _find_models():
    """Locate the Kokoro ONNX and voices file correctly."""
    # 1. Try hardcoded path as fallback
    models_dir = "/models"
    onnx_path = os.path.join(models_dir, "kokoro-v0_19.onnx")
    voices_path = os.path.join(models_dir, "voices-v1.0.bin")
    
    if os.path.exists(onnx_path) and os.path.exists(voices_path):
        return onnx_path, voices_path
        
    # 2. Try current project directory for Docker or dev
    cwd_models = os.path.join(os.getcwd(), "models")
    if os.path.exists(cwd_models):
        onnx_path = os.path.join(cwd_models, "kokoro-v0_19.onnx")
        voices_path = os.path.join(cwd_models, "voices-v1.0.bin")
        if os.path.exists(onnx_path) and os.path.exists(voices_path):
            return onnx_path, voices_path

    # 4. Try project data directory (matches setup_windows.ps1)
    base_data_models = os.path.join(os.getcwd(), "data", "models")
    onnx_path = os.path.join(base_data_models, "kokoro-v0_19.onnx")
    voices_path = os.path.join(base_data_models, "voices-v1.0.bin")
    if os.path.exists(onnx_path):
        return onnx_path, voices_path
        
    return None, None

def get_kokoro_model():
    global _kokoro_model
    if _kokoro_model is None:
        with _kokoro_lock:
            if _kokoro_model is not None:
                return _kokoro_model
            from kokoro_onnx import Kokoro
            logger.info("Loading local Kokoro TTS model (ONNX)...")
            onnx_path, voices_path = _find_models()

            if not onnx_path or not os.path.exists(onnx_path):
                 logger.warning(f"Kokoro ONNX file not found at {onnx_path or 'anywhere'}! Returning None.")
                 return None

            logger.info(f"Loading Kokoro from {onnx_path}")
            _kokoro_model = Kokoro(onnx_path, voices_path)

            # Warm-up inference to initialize ORT sessions and cache
            try:
                logger.info("Warming up Kokoro model...")
                # create_stream in 0.5.0 is an async generator
                async def _warmup():
                    async for _ in _kokoro_model.create_stream("Hi", voice="af_sky", speed=1.0, lang="en-us"):
                        break

                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(_warmup())
                except RuntimeError:
                    # No loop running in this thread, or it's not the main thread
                    pass
            except Exception as e:
                logger.warning(f"Warmup failed (non-critical): {e}")

    return _kokoro_model

def preload_models():
    """Explicitly trigger model loading and warmup."""
    # Deferred for faster uvicorn reloads.
    # get_kokoro_model()
    # get_local_model()
    pass

async def transcribe_audio(file_path: str, language: str | None = None) -> str:
    """Transcribe audio locally with faster-whisper.

    Fully self-hosted: no cloud API, no key, no quota. Transcription is CPU-bound
    so it runs in a worker thread to avoid blocking the event loop.

    `language` is an ISO-639-1 hint (e.g. "en", "hi", "te"). Pass None to let
    faster-whisper auto-detect, which is required for the non-English voices —
    hardcoding "en" mistranscribed everything else.
    """
    def _transcribe_sync() -> str:
        model = get_local_model()
        logger.info(
            f"Transcribing {file_path} locally with {MODEL_SIZE} "
            f"(language={language or 'auto'})..."
        )
        # CTranslate2 admits num_workers concurrent decodes; the pool this runs
        # on is sized to match, so no extra locking is needed here.
        segments, _info = model.transcribe(
            file_path,
            beam_size=1,
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        return " ".join(s.text for s in segments).strip()

    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_transcribe_pool, _transcribe_sync)
    except Exception as e:
        logger.error(f"Local transcription failed: {e}")
        return "[Error: Voice Transcription failed]"

def _chunk_text(text: str, max_chars: int = 180):
    """
    Split text into small pieces to ensure fast first-audio response.
    Prioritizes splitting at punctuation, falling back to space-based splitting.
    """
    if not text:
        return []
        
    import re
    # 1. Initial split at sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    final_chunks = []
    for s in sentences:
        if not s: continue
        
        # 2. If already small enough, take it
        if len(s) <= max_chars:
            final_chunks.append(s)
            continue
            
        # 3. Sub-split by comma, semicolon, or colon
        subs = re.split(r'(?<=[,;:])\s+', s)
        for sub in subs:
            if len(sub) <= max_chars:
                final_chunks.append(sub)
            else:
                # 4. Force split at word boundaries for long text without punctuation
                words = sub.split(' ')
                current_chunk = []
                current_len = 0
                for w in words:
                    if not w: continue
                    if current_len + len(w) + 1 <= max_chars:
                        current_chunk.append(w)
                        current_len += len(w) + 1
                    else:
                        if current_chunk:
                            final_chunks.append(" ".join(current_chunk))
                        current_chunk = [w]
                        current_len = len(w)
                if current_chunk:
                    final_chunks.append(" ".join(current_chunk))
    
    return [c.strip() for c in final_chunks if c.strip()]

async def synthesize_speech_stream(text: str, voice_id: str = "af_sky"):
    """
    Synthesize speech using Kokoro's native create_stream.
    Each chunk is generated in a background thread to avoid blocking the event loop.
    """
    clean_text = text.replace("*", "").replace("#", "").strip()
    if not clean_text:
        return

    kokoro = get_kokoro_model()
    if kokoro is None:
        logger.warning("Kokoro model not loaded. Check paths. Yielding empty.")
        return

    t_start = time.time()
    chunks = _chunk_text(clean_text)
    logger.info(f"[TTS] Synthesizing {len(chunks)} chunks for {len(clean_text)} chars total")

    chunk_size = 1200  # ~12ms per chunk — stream first bytes ASAP


    try:
        is_first = True
        for chunk in chunks:
            # Initialize async streaming generator for this chunk
            async_stream = kokoro.create_stream(chunk, voice=voice_id, speed=1.0, lang="en-us")
            
            async for samples, sample_rate in async_stream:
                if samples is None:
                    break
                    
                pcm = samples.tobytes()

                if is_first:
                    t_first = time.time()
                    logger.info(f"[TTS TIMING] Time-to-first-audio chunk: {(t_first - t_start)*1000:.1f}ms")
                    is_first = False

                # Stream out the PCM in small chunks for immediate frontend playback
                for j in range(0, len(pcm), chunk_size):
                    yield pcm[j:j+chunk_size]

    except Exception as e:
        logger.error(f"[TTS ERROR] Streaming failed: {e}")
