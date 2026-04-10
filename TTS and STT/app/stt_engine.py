from __future__ import annotations
import os
import queue
import wave
import tempfile
import sys
from typing import Optional

try:
    import sounddevice as sd
    import numpy as np
    from faster_whisper import WhisperModel
except ImportError:
    pass

class LocalSTTEngine:
    def __init__(self, model_size: str = "large-v3"):
        # "large-v3" is the highest accuracy World No. 1 model. 
        # Note: requires ~3.2GB download and more RAM.
        self.samplerate = 16000
        self.channels = 1
        print(f"[STT] Loading local model '{model_size}' (this may take a moment on first run)...")
        # auto chooses CUDA/GPU if available, otherwise falls back to CPU
        self.model = WhisperModel(model_size, device="auto", compute_type="default")
        print("[STT] Model loaded.")

    def record_audio(self) -> str:
        """Records audio from the microphone until the user presses Enter."""
        print("\n[STT] Press Enter to start recording...")
        input()
        
        q = queue.Queue()
        def callback(indata, frames, time, status):
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())

        print("[STT] Recording... Press Enter to stop.")
        stream = sd.InputStream(samplerate=self.samplerate, channels=self.channels, callback=callback)
        
        with stream:
            input()  # Wait for Enter to stop

        print("[STT] Processing audio locally...")
        audio_data = []
        while not q.empty():
            audio_data.append(q.get())
        
        if not audio_data:
            return ""

        audio_np = np.concatenate(audio_data, axis=0)
        
        # Save to temp wav
        fd, temp_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2) # 16-bit
            wf.setframerate(self.samplerate)
            wf.writeframes((audio_np * 32767).astype(np.int16).tobytes())
            
        # Send to local faster-whisper
        try:
            segments, info = self.model.transcribe(temp_path, beam_size=5, language="en")
            text = "".join([segment.text for segment in segments])
            os.remove(temp_path)
            return text.strip()
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return f"Error: Local STT failed ({str(e)})"
