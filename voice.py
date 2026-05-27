import os
import tempfile
import numpy as np

import scipy.io.wavfile as wav
import sounddevice as sd
from faster_whisper import WhisperModel
from elevenlabs.client import ElevenLabs

SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
TTS_RATE = 22050


class VoiceIO:
    def __init__(self, elevenlabs_api_key: str, voice_id: str, whisper_model: str = "tiny"):
        print("Loading Whisper model...")
        self.whisper = WhisperModel(whisper_model, device="cpu", compute_type="int8")
        self.eleven = ElevenLabs(api_key=elevenlabs_api_key)
        self.voice_id = voice_id

    def record(self, silence_secs: float = 0.8, threshold: float = 0.015, max_secs: float = 30) -> np.ndarray | None:
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
        """Convert text to speech using ElevenLabs and play it via sounddevice."""
        audio_iter = self.eleven.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="pcm_22050",
            voice_settings={
                "stability": 0.35,
                "similarity_boost": 0.85,
                "style": 0.60,
                "use_speaker_boost": True,
            },
        )
        audio_bytes = b"".join(audio_iter)
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        # Use Microsoft Sound Mapper so playback follows the Windows default audio device
        sd.play(audio, samplerate=TTS_RATE, device="Microsoft Sound Mapper - Output")
        sd.wait()
