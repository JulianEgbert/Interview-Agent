import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    TurnHandlingOptions,
    cli,
    function_tool,
    inference,
    room_io,
)
from livekit.plugins import ai_coustics

from challenges import InterviewChallenge, select_challenge_from_env
from coding_workspace import (
    CandidateWorkspace,
    prepare_candidate_workspace,
    read_candidate_code,
    run_candidate_tests,
    write_evaluation_report,
)
from interview import build_interviewer_instructions, build_opening_message

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
RESET_WORKSPACE = os.getenv("INTERVIEWROOM_RESET_WORKSPACE", "").lower() in {
    "1",
    "true",
    "yes",
}


class Interviewer(Agent):
    def __init__(
        self, challenge: InterviewChallenge, workspace: CandidateWorkspace
    ) -> None:
        self.workspace = workspace
        super().__init__(
            llm=inference.LLM(model=LLM_MODEL),
            instructions=build_interviewer_instructions(
                challenge,
                workspace_path=(
                    str(workspace.solution_path) if workspace.solution_path else None
                ),
                function_name=(
                    workspace.coding_spec.function_name
                    if workspace.coding_spec
                    else None
                ),
                has_runnable_tests=workspace.has_runnable_tests,
            ),
        )

    @function_tool
    async def inspect_candidate_code(self, context: RunContext) -> str:
        """Read the candidate's current local solution file.

        Use this when the candidate asks for feedback on their code, says they
        have written an approach, or when you need code context before asking a
        debugging question. Summarize what you see instead of reciting the whole file.
        """

        return read_candidate_code(self.workspace)

    @function_tool
    async def run_candidate_tests(self, context: RunContext) -> str:
        """Run the local tests for the active coding challenge.

        Use this when the candidate asks you to check their solution, says they
        are done, or wants help debugging failing behavior. Do not provide the
        full solution after running tests; ask a targeted follow-up question.
        """

        return run_candidate_tests(self.workspace)

    @function_tool
    async def write_evaluation_report(
        self,
        context: RunContext,
        overall_score: int,
        problem_understanding: int,
        communication: int,
        algorithmic_reasoning: int,
        code_correctness: int,
        edge_case_handling: int,
        testing_approach: int,
        complexity_discussion: int,
        strengths: str,
        improvements: str,
        next_steps: str,
        transcript_moments: str = "",
    ) -> str:
        """Write a markdown interview scorecard to the candidate workspace.

        Use this at the end of the interview or when the candidate asks for a
        written evaluation. Score each dimension from zero to five. The report
        includes simple visual bars, latest local test results, strengths,
        improvements, notable moments, and next steps.
        """

        return write_evaluation_report(
            self.workspace,
            overall_score=overall_score,
            problem_understanding=problem_understanding,
            communication=communication,
            algorithmic_reasoning=algorithmic_reasoning,
            code_correctness=code_correctness,
            edge_case_handling=edge_case_handling,
            testing_approach=testing_approach,
            complexity_discussion=complexity_discussion,
            strengths=strengths,
            improvements=improvements,
            next_steps=next_steps,
            transcript_moments=transcript_moments,
        )


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def interview_room_agent(ctx: JobContext):
    challenge = select_challenge_from_env()
    workspace = prepare_candidate_workspace(challenge, reset=RESET_WORKSPACE)
    ctx.log_context_fields = {
        "room": ctx.room.name,
        "agent": AGENT_NAME,
        "challenge": challenge.id,
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
        agent=Interviewer(challenge, workspace),
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
    logger.info(
        "InterviewRoom agent joined room %s with challenge %s",
        ctx.room.name,
        challenge.id,
    )
    session.say(
        build_opening_message(
            challenge,
            workspace_path=str(workspace.solution_path)
            if workspace.solution_path
            else None,
        ),
        allow_interruptions=True,
    )


if __name__ == "__main__":
    cli.run_app(server)
