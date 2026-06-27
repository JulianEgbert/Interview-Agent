import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    TurnHandlingOptions,
    cli,
    inference,
    room_io,
)
from livekit.plugins import ai_coustics

from interview import OPENING_MESSAGE, build_interviewer_instructions

logger = logging.getLogger("interview-room")

load_dotenv(".env.local")

AGENT_NAME = os.getenv("INTERVIEWROOM_AGENT_NAME", "interview-room-agent")
LLM_MODEL = os.getenv("INTERVIEWROOM_LLM_MODEL", "openai/gpt-5.2-chat-latest")
STT_MODEL = os.getenv("INTERVIEWROOM_STT_MODEL", "deepgram/nova-3")
TTS_MODEL = os.getenv("INTERVIEWROOM_TTS_MODEL", "cartesia/sonic-3")
TTS_VOICE = os.getenv(
    "INTERVIEWROOM_TTS_VOICE",
    "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
)


class Interviewer(Agent):
    def __init__(self) -> None:
        super().__init__(
            llm=inference.LLM(model=LLM_MODEL),
            instructions=build_interviewer_instructions(),
        )


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def interview_room_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": AGENT_NAME,
    }

    session = AgentSession(
        stt=inference.STT(model=STT_MODEL, language="multi"),
        tts=inference.TTS(model=TTS_MODEL, voice=TTS_VOICE),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
        preemptive_generation=True,
    )

    await session.start(
        agent=Interviewer(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                ),
            ),
        ),
    )

    await ctx.connect()
    logger.info("InterviewRoom agent joined room %s", ctx.room.name)
    session.say(OPENING_MESSAGE, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
