import os
import sys

from dotenv import load_dotenv

from agent import Agent
from voice import VoiceIO

load_dotenv()

GOODBYE_WORDS = {"goodbye", "bye"}


def main():
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not anthropic_key:
        sys.exit("Missing ANTHROPIC_API_KEY in .env")

    voice = VoiceIO()
    agent = Agent(api_key=anthropic_key)
    agent.load()

    print("\nAria is ready. Say 'Hey Aria' to wake her up.\n")
    greeting = "Hey Levi! Say hey Aria whenever you need me." if not agent.history else "Hey, I'm back! Say hey Aria whenever you're ready."
    print(f"Aria: {greeting}")
    voice.speak(greeting)

    while True:
        try:
            voice.wait_for_wake_word()
            audio = voice.record()
            if audio is None:
                continue

            text = voice.transcribe(audio)
            if not text:
                continue
            print(f"You:  {text}")

            if any(w in text.lower() for w in GOODBYE_WORDS):
                farewell = "Goodbye! Talk to you soon."
                print(f"Aria: {farewell}")
                voice.speak(farewell)
                break

            if "clear history" in text.lower() or "forget everything" in text.lower():
                agent.reset()
                reply = "Got it, I've cleared our conversation history."
                print(f"Aria: {reply}")
                voice.speak(reply)
                continue

            reply = agent.chat(text)
            print(f"Aria: {reply}")
            voice.speak(reply)
            agent.save()

        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"[error] {e}")


if __name__ == "__main__":
    main()
