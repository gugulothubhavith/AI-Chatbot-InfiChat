from __future__ import annotations
import os
import tempfile
import asyncio

try:
    import edge_tts
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
except ImportError:
    pass

class LocalTTSEngine:
    def __init__(self, default_voice: str = "en-IN-NeerjaNeural"):
        self.default_voice = default_voice
        pygame.mixer.init()

    async _generate_and_play(self, text: str, voice: str) -> None:
        communicate = edge_tts.Communicate(text, voice)
        
        # We need a temp file since pygame.mixer.Sound prefers a file path
        # for complex formats like mp3/ogg or wav, pygame.mixer.music handles mp3 best
        fd, temp_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        
        try:
            await communicate.save(temp_path)
            
            # Play the audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait until it finishes playing
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
                
        finally:
            pygame.mixer.music.unload()
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    def stream_tts(self, text: str, voice_id: str | None = None) -> None:
        """Stream/Play TTS audio using Edge TTS and Pygame."""
        # Clean text of markdown or special chars to avoid weird dictations
        clean_text = text.replace("*", "").replace("#", "")
        print(f"[TTS Local Audio Playing...]")
        
        voice = voice_id or self.default_voice
        try:
            asyncio.run(self._generate_and_play(clean_text, voice))
        except Exception as e:
            print(f"[TTS Error] {e}")
