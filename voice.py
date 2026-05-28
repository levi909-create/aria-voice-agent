import os
import tempfile
import time
import winsound
import numpy as np

import asyncio
import miniaudio
import scipy.io.wavfile as wav
import sounddevice as sd
from faster_whisper import WhisperModel
import edge_tts

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
TTS_RATE = 22050


EDGE_VOICE = "en-US-AriaNeural"
EDGE_RATE  = "+20%"   # speak 20% faster
EDGE_VOL   = "+100%"  # maximum volume
_loop      = asyncio.new_event_loop()


class VoiceIO:
    def __init__(self, whisper_model: str = "tiny"):
        print("Loading Whisper model...")
        self.whisper = WhisperModel(whisper_model, device="cpu", compute_type="int8")

    def wait_for_wake_word(self) -> None:
        """Listen in 2-second bursts until wake word is heard."""
        WAKE_WORDS = {"aria", "hey aria", "area", "hey area", "haria"}
        print("Waiting for 'Hey Aria'...")
        while True:
            audio = sd.rec(int(2.0 * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
            sd.wait()
            audio = audio.flatten()
            if float(np.abs(audio).mean()) < 0.003:
                continue
            text = self.transcribe(audio).lower()
            if any(w in text for w in WAKE_WORDS):
                winsound.Beep(880, 120)
                time.sleep(0.15)
                return

    def record(self, silence_secs: float = 0.8, threshold: float = 0.008, max_secs: float = 30) -> np.ndarray | None:
        """Record from mic until silence is detected after speech."""
        print("\nListening... (speak now)")
        chunks: list[np.ndarray] = []
        silence_count = 0
        silence_limit = int(silence_secs * SAMPLE_RATE / BLOCK_SIZE)
        started = False

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=BLOCK_SIZE) as stream:
            while True:
                chunk, _ = stream.read(BLOCK_SIZE)
                level = float(np.abs(chunk).mean())

                if level > threshold:
                    started = True
                    silence_count = 0
                    chunks.append(chunk.copy())
                elif started:
                    chunks.append(chunk.copy())
                    silence_count += 1
                    if silence_count >= silence_limit:
                        break

                if chunks and len(chunks) * BLOCK_SIZE / SAMPLE_RATE >= max_secs:
                    break

        if not chunks:
            return None
        return np.concatenate(chunks, axis=0)

    def transcribe(self, audio: np.ndarray) -> str:
        """Convert audio to text using Whisper."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav.write(f.name, SAMPLE_RATE, (audio * 32767).astype(np.int16))
            path = f.name
        try:
            segments, _ = self.whisper.transcribe(path, language="en")
            return " ".join(s.text for s in segments).strip()
        finally:
            os.unlink(path)

    def speak(self, text: str):
        """Convert text to speech using Edge TTS and play via sounddevice."""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            path = f.name
        try:
            _loop.run_until_complete(
                edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE, volume=EDGE_VOL).save(path)
            )
            decoded = miniaudio.decode_file(path)
            audio = np.array(decoded.samples, dtype=np.int16).astype(np.float32) / 32768.0
            audio = np.clip(audio * 2.5, -1.0, 1.0)  # amplify
            sd.play(audio, samplerate=decoded.sample_rate, device="Microsoft Sound Mapper - Output")
            sd.wait()
        finally:
            os.unlink(path)
