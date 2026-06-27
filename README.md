# InterviewRoom

InterviewRoom is a LiveKit-powered mock software interview coach for students preparing for technical interviews.

The student joins a realtime interview room, speaks with an AI interviewer, shares their screen while coding, and receives structured feedback afterward. The goal is not just to give students more coding problems, but to help them practice the live interview behaviors that are hard to train alone: thinking out loud, asking clarifying questions, handling hints, explaining tradeoffs, testing edge cases, and recovering when stuck.

## Problem

Students can find many coding challenges online, but realistic interview practice is harder to access. A real technical interview includes time pressure, spoken reasoning, ambiguity, interviewer follow-up questions, and feedback on communication.

Most solo practice tools evaluate only the final answer. InterviewRoom evaluates the full interview process.

## Core Idea

InterviewRoom simulates a company-style software interview using:

- Live voice conversation with an AI interviewer.
- Screen sharing so the interviewer can follow the candidate's coding process.
- Publicly available or original coding challenges inspired by common interview patterns.
- Company-style interviewer personas, such as large tech, startup, backend, frontend, or behavioral interview styles.
- A post-interview scorecard with concrete feedback and a study plan.

## Target Users

- University students preparing for internships or new grad roles.
- Bootcamp graduates practicing technical interviews.
- Self-taught developers who do not have easy access to mock interview partners.
- Career centers or coding clubs that want scalable interview practice.

## LiveKit Fit

LiveKit is central to the product because the experience depends on realtime voice, video, and screen sharing.

LiveKit can power:

- Interview rooms with the student and AI interviewer as participants.
- Low-latency voice interaction.
- Screen sharing from the student's IDE or browser.
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

The student enters a LiveKit room and shares:

- Microphone.
- Camera, optional.
- Screen, showing their code editor or browser.

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
5. The student shares their screen and starts solving.
6. The interviewer asks follow-up questions and gives one small hint.
7. The student explains complexity and tests edge cases.
8. The session ends with a scorecard and personalized practice plan.

## Suggested Architecture

### Frontend

- Web app for interview setup and room entry.
- LiveKit client for voice, camera, and screen share.
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
- Optionally receives screen frames or editor state.
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

> Realistic realtime interview practice with voice, screen sharing, interviewer pressure, and feedback on the candidate's process.

## Stretch Goals

- Replay important interview moments.
- Detect long silences and missed clarification opportunities.
- Let students choose an interviewer personality.
- Add behavioral interview mode.
- Add a human mentor review mode.
- Compare multiple attempts over time.
- Generate a weekly practice plan.
- Support pair interviews or group practice rooms.
- Add an embedded code editor for easier screen-aware evaluation.

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
