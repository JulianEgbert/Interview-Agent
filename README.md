# InterviewRoom

InterviewRoom is a LiveKit-powered mock software interview coach for students preparing for technical interviews.

The student joins a realtime interview room, speaks with an AI interviewer, codes in a local workspace the agent can inspect, and receives structured feedback afterward. The goal is not just to give students more coding problems, but to help them practice the live interview behaviors that are hard to train alone: thinking out loud, asking clarifying questions, handling hints, explaining tradeoffs, testing edge cases, and recovering when stuck.

## Prototype

This repo now contains a first LiveKit Agents prototype for the hackathon:

- `src/agent.py`: LiveKit voice agent entrypoint.
- `src/interview.py`: InterviewRoom prompt, opening message, and rubric.
- `src/challenges.py` and `src/challenges/local.json`: Local challenge catalog and selector.
- `src/coding_workspace.py`: Local Python workspace setup, code inspection, and test runner.
- `src/web_app.py` and `src/web_static/`: Local browser interview room for LiveKit Cloud demos.
- `candidate_workspace/`: Generated local coding folders for candidate solutions.
- `tests/test_interview.py`: Fast local tests for the prototype behavior.
- `Dockerfile`: Starter deployment container from the LiveKit Python agent template.

The first demo path can pick from a local catalog of coding, backend, and frontend challenges. The agent joins a LiveKit room, speaks first, asks the candidate to clarify assumptions, nudges them through the problem, and can produce a concise scorecard when the candidate is finished.

### Setup

Create a LiveKit Cloud project, then copy the environment template:

```bash
cp .env.example .env.local
```

Fill in:

```bash
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
```

If you are already authenticated with the LiveKit CLI, you can also write credentials with:

```bash
lk app env --write --destination .env.local
```

Install dependencies:

```bash
uv sync
```

### Run Locally

Talk to the interviewer in the terminal:

```bash
uv run python src/agent.py console
```

Run the agent for LiveKit Agent Console or a frontend:

```bash
uv run python src/agent.py dev
```

Run the local browser interview room in a second terminal:

```bash
uv run python src/web_app.py
```

Open:

```text
http://localhost:8765
```

The web page creates a LiveKit Cloud room, generates a short-lived participant token on the local Python server, dispatches the local agent into the room, and lets the candidate use their microphone from the browser. After the session starts, the solution link opens the generated `solution.py` file through VS Code's URL handler when VS Code is installed.

For a shareable hackathon demo link, keep the agent and web server running locally, then put the web server behind an HTTPS tunnel such as ngrok or cloudflared:

```bash
INTERVIEWROOM_WEB_HOST=0.0.0.0 uv run python src/web_app.py
```

Then point the tunnel at port `8765` and share the HTTPS URL. Browser microphone access works on `localhost` or HTTPS origins; a plain LAN `http://<your-ip>:8765` URL may not get device permissions.

Run tests:

```bash
uv run pytest
```

### Project Showcase Page

This repository also includes a static landing page for GitHub Pages:

- `docs/index.html`
- `docs/styles.css`
- `docs/assets/interviewroom-hero.png`

To publish it, enable GitHub Pages for the repository branch and choose the
`/docs` folder as the Pages source. No frontend build step is required.

### Challenge Selection

By default, each interview picks a random challenge from `src/challenges/local.json`.

To force one specific challenge:

```bash
INTERVIEWROOM_CHALLENGE_ID=minimum-meeting-rooms uv run python src/agent.py console
```

To filter the random choice:

```bash
INTERVIEWROOM_CHALLENGE_TYPE=coding INTERVIEWROOM_CHALLENGE_DIFFICULTY=new-grad uv run python src/agent.py console
```

Supported filters are:

- `INTERVIEWROOM_CHALLENGE_ID`
- `INTERVIEWROOM_CHALLENGE_TYPE`
- `INTERVIEWROOM_CHALLENGE_DIFFICULTY`
- `INTERVIEWROOM_CHALLENGE_CATEGORY`
- `INTERVIEWROOM_CHALLENGE_TAGS`, comma-separated
- `INTERVIEWROOM_CHALLENGE_SEED`, useful for repeatable demos

### Current Scope

This prototype supports realtime voice through LiveKit and gives the candidate a local browser room for starting the interview. For coding challenges with local test specs, it also creates a local `candidate_workspace/<challenge-id>/solution.py` file. The interviewer can inspect that file and run local tests when the candidate asks for a check or reaches a debugging checkpoint.

When the page is shared through a tunnel, remote candidates can join the room and speak with the interviewer. The code-inspection and test-running tools still read the host machine's local `candidate_workspace`, so a browser-based editor with LiveKit data events is the natural next step for fully remote coding.

### Local Coding Loop

For the most coding-focused demo, force a coding challenge:

```bash
INTERVIEWROOM_CHALLENGE_ID=minimum-meeting-rooms uv run python src/agent.py console
```

The agent creates:

```text
candidate_workspace/minimum-meeting-rooms/solution.py
```

Edit that file while talking through your approach. Then say something like:

> I have an implementation. Can you check it?

or:

> Can you run the tests?

The agent can read the current solution and run the local challenge tests, then respond as an interviewer without giving away the full answer.

At the end of the interview, ask for a written evaluation:

> Can you write my evaluation report?

The agent creates:

```text
candidate_workspace/<challenge-id>/evaluation.md
```

The report includes simple score bars, local test results, strengths,
improvement areas, notable moments, and next steps.

## Problem

Students can find many coding challenges online, but realistic interview practice is harder to access. A real technical interview includes time pressure, spoken reasoning, ambiguity, interviewer follow-up questions, and feedback on communication.

Most solo practice tools evaluate only the final answer. InterviewRoom evaluates the full interview process.

## Core Idea

InterviewRoom simulates a company-style software interview using:

- Live voice conversation with an AI interviewer.
- A local coding workspace the interviewer can inspect and test during the conversation.
- Publicly available or original coding challenges inspired by common interview patterns.
- Company-style interviewer personas, such as large tech, startup, backend, frontend, or behavioral interview styles.
- A post-interview scorecard with concrete feedback and a study plan.

## Target Users

- University students preparing for internships or new grad roles.
- Bootcamp graduates practicing technical interviews.
- Self-taught developers who do not have easy access to mock interview partners.
- Career centers or coding clubs that want scalable interview practice.

## LiveKit Fit

LiveKit is central to the product because the experience depends on realtime voice, room orchestration, and low-latency agent participation.

LiveKit can power:

- Interview rooms with the student and AI interviewer as participants.
- Low-latency voice interaction.
- Agent participation in a live room.
- Session recording or transcript generation for later review.
- Future human handoff, group practice, or mentor review flows.

## MVP

The hackathon MVP should focus on one polished end-to-end interview flow.

### 1. Interview Setup

The student selects:

- Interview type: coding, frontend, backend, systems-lite, or behavioral.
- Difficulty: intern, new grad, or mid-level.
- Interview style: collaborative, strict, silent, or pressure-testing.
- Company style: generic large tech, startup, product company, or enterprise.

For the first demo, we can narrow this to:

- Type: coding interview.
- Difficulty: new grad.
- Company style: large tech.
- Interviewer style: collaborative but probing.

### 2. Live Interview Room

The student enters a LiveKit room and uses:

- Microphone.
- Camera, optional.
- The generated local coding workspace.

The AI interviewer begins with a realistic opening:

> Hi, I am your interviewer today. We will spend about 35 minutes on one coding problem. Please ask clarifying questions and think out loud as you work.

### 3. AI Interviewer Behavior

The interviewer should:

- Present the problem clearly.
- Ask the student to restate assumptions.
- Encourage the student to think out loud.
- Notice long silence and gently prompt.
- Ask about edge cases.
- Ask for time and space complexity.
- Offer hints only when needed.
- Challenge incomplete solutions.
- Ask the student to test their code.
- Keep the tone realistic and supportive.

### 4. Challenge Library

Use original challenges inspired by common public interview patterns instead of copying proprietary company questions.

Example categories:

- Arrays and hash maps.
- Strings.
- Two pointers.
- Graph traversal.
- Trees.
- Basic dynamic programming.
- API or backend design.
- Frontend state and component design.

Example MVP problem:

> Given a list of calendar events with start and end times, determine the minimum number of meeting rooms required so that no meetings overlap in the same room.

### 5. Feedback Scorecard

At the end of the session, the app generates a scorecard:

- Problem understanding.
- Communication.
- Clarifying questions.
- Algorithmic reasoning.
- Code correctness.
- Edge case handling.
- Debugging process.
- Testing approach.
- Time and space complexity.
- Overall readiness.

The feedback should include:

- What went well.
- What to improve.
- Specific moments from the transcript.
- Recommended practice topics.
- A suggested next interview difficulty.

## Demo Flow

1. Open InterviewRoom.
2. Select "New Grad Coding Interview" and "Large Tech Style".
3. Join the LiveKit interview room.
4. The AI interviewer greets the student and gives a coding challenge.
5. The student opens the generated solution file and starts solving.
6. The interviewer asks follow-up questions and gives one small hint.
7. The student explains complexity and tests edge cases.
8. The session ends with a scorecard and personalized practice plan.

## Suggested Architecture

### Frontend

- Web app for interview setup and room entry.
- LiveKit client for realtime voice.
- Interview dashboard with problem statement, timer, and session status.
- Post-interview feedback page.

### Backend

- Room creation and LiveKit token generation.
- Interview session storage.
- Challenge selection.
- Transcript and event capture.
- Feedback generation.

### AI Agent

- Joins the LiveKit room as the interviewer.
- Listens to the student in realtime.
- Inspects the generated solution file and runs local tests through tools.
- Uses a structured interviewer prompt.
- Calls tools to load the selected challenge, track rubric events, and generate final feedback.

### Data Model

Possible core entities:

- `InterviewSession`
- `Candidate`
- `Challenge`
- `InterviewerPersona`
- `TranscriptTurn`
- `RubricEvent`
- `FeedbackReport`

## Key Product Differentiator

The product should not be positioned as another coding challenge platform.

The differentiator is:

> Realistic realtime interview practice with voice, live coding feedback, interviewer pressure, and feedback on the candidate's process.

## Stretch Goals

- Replay important interview moments.
- Detect long silences and missed clarification opportunities.
- Let students choose an interviewer personality.
- Add behavioral interview mode.
- Add a human mentor review mode.
- Compare multiple attempts over time.
- Generate a weekly practice plan.
- Support pair interviews or group practice rooms.
- Add an embedded code editor for fully remote coding sessions.

## Risks and Constraints

- Avoid claiming to reproduce exact company interviews.
- Avoid using copied proprietary coding challenge content.
- Be transparent that company styles are approximations.
- Keep feedback constructive and student-safe.
- For the MVP, prefer a narrow but polished flow over many shallow interview modes.

## Hackathon Success Criteria

By the end of the hackathon, the demo should show:

- A student joining a LiveKit room.
- An AI interviewer conducting a live voice interview.
- Screen sharing during problem solving.
- Realistic follow-up questions.
- A generated scorecard after the session.
- A clear explanation of why LiveKit makes the experience possible.
