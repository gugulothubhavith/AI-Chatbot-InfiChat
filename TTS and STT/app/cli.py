from __future__ import annotations

from dotenv import load_dotenv

from .agent import IndianVoiceAgent
from .models import ChatTurn
from .stt_engine import LocalSTTEngine
from .tts_engine import LocalTTSEngine


def run_cli() -> None:
    load_dotenv()
    agent = IndianVoiceAgent()
    history: list[ChatTurn] = []

    print("Indian Conversational Voice AI Agent")
    voice_mode = input("Use Voice Mode (STT/TTS)? [y/N]: ").strip().lower() == 'y'
    
    stt = LocalSTTEngine() if voice_mode else None
    tts = LocalTTSEngine() if voice_mode else None

    print("Type your message (or follow STT prompts in Voice Mode). Enter 'exit' to quit.\n")

    while True:
        if voice_mode:
            user_input = stt.record_audio()
            print(f"You: {user_input}")
        else:
            user_input = input("You: ").strip()
            
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Agent: Thank you. Have a good day.")
            if voice_mode and tts:
                tts.stream_tts("Thank you. Have a good day.")
            break

        response = agent.respond(user_input, history=history)
        print(f"Agent: {response.reply}")
        print(f"(tone: {response.tone}, profile: {response.profile_name})\n")

        if voice_mode and tts:
            tts.stream_tts(response.reply)

        history.append(ChatTurn(role="user", text=user_input))
        history.append(ChatTurn(role="assistant", text=response.reply))


def main() -> None:
    run_cli()


if __name__ == "__main__":
    main()
