import os
import urllib.request
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_kokoro_assets():
    models_dir = os.path.join(os.getcwd(), "data", "models")
    os.makedirs(models_dir, exist_ok=True)
    onnx_path = os.path.join(models_dir, "kokoro-v0_19.onnx")
    voices_path = os.path.join(models_dir, "voices-v1.0.bin")
    
    if not os.path.exists(onnx_path):
        logger.info("Downloading Kokoro ONNX model (approx 340MB)...")
        urllib.request.urlretrieve(
            "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx",
            onnx_path
        )
        logger.info("OK")
        
    if not os.path.exists(voices_path):
        logger.info("Downloading Kokoro advanced voices pack (v1.0)...")
        urllib.request.urlretrieve(
            "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
            voices_path
        )
        logger.info("OK")
        
    logger.info("Kokoro assets ready.")

if __name__ == "__main__":
    download_kokoro_assets()
