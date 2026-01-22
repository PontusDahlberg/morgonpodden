import os
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    os.makedirs("audio", exist_ok=True)

    from google_cloud_tts import GoogleCloudTTS

    tts = GoogleCloudTTS()
    print("TTS available:", tts.is_available())
    print("Configured Lisa voice name:", tts.voice_mapping.get("lisa", {}).get("name"))
    print("Configured Pelle voice name:", tts.voice_mapping.get("pelle", {}).get("name"))

    if not tts.is_available():
        print("GoogleCloudTTS not available (credentials/client init failed).")
        return 2

    jobs = [
        ("lisa", "Hej! Jag är Lisa. Det här är ett kort test av rösten.", "audio/test_lisa.mp3"),
        ("pelle", "Hej! Jag är Pelle. Det här är ett kort test av rösten.", "audio/test_pelle.mp3"),
    ]

    for voice, text, out_path in jobs:
        audio_bytes = tts.generate_audio(text, voice=voice)
        if not audio_bytes:
            print(f"No audio returned for {voice}")
            return 3

        with open(out_path, "wb") as f:
            f.write(audio_bytes)

        print("Wrote", out_path, "bytes=", len(audio_bytes))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
