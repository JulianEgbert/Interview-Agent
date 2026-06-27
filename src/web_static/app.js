import {
  Room,
  RoomEvent,
} from "https://esm.sh/livekit-client@2?bundle";

const challengeSelect = document.querySelector("#challengeSelect");
const participantName = document.querySelector("#participantName");
const connectButton = document.querySelector("#connectButton");
const disconnectButton = document.querySelector("#disconnectButton");
const micButton = document.querySelector("#micButton");
const statusEl = document.querySelector("#status");
const challengeTitle = document.querySelector("#challengeTitle");
const challengePrompt = document.querySelector("#challengePrompt");
const challengeMeta = document.querySelector("#challengeMeta");
const challengeExamples = document.querySelector("#challengeExamples");
const challengeConstraints = document.querySelector("#challengeConstraints");
const workspaceLinks = document.querySelector("#workspaceLinks");
const participantsEl = document.querySelector("#participants");
const audioTracks = document.querySelector("#audioTracks");
const roomSummary = document.querySelector("#roomSummary");
const refreshEvaluationButton = document.querySelector("#refreshEvaluationButton");
const evaluationStatus = document.querySelector("#evaluationStatus");
const evaluationContent = document.querySelector("#evaluationContent");

let room = null;
let activeSession = null;
let lastChallengeId = null;
let challengeCatalog = [];

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

async function readJsonResponse(response, fallbackMessage) {
  const body = await response.text();
  let payload = null;

  try {
    payload = body ? JSON.parse(body) : {};
  } catch {
    const status = `${response.status} ${response.statusText}`.trim();
    const detail = body ? ` (${body})` : "";
    throw new Error(`${fallbackMessage}: server returned ${status}${detail}`);
  }

  if (!response.ok) {
    throw new Error(payload.error || payload.message || fallbackMessage);
  }

  return payload;
}

function renderChallenge(challenge) {
  if (!challenge) {
    challengeTitle.textContent = "Random challenge";
    challengePrompt.textContent = "A challenge will be selected when the room starts.";
    challengeMeta.innerHTML = "";
    challengeExamples.innerHTML = "";
    challengeConstraints.innerHTML = "";
    return;
  }

  challengeTitle.textContent = challenge.title;
  challengePrompt.textContent = challenge.prompt;
  challengeMeta.innerHTML = "";
  challengeExamples.innerHTML = "";
  challengeConstraints.innerHTML = "";

  [
    challenge.type,
    challenge.difficulty,
    ...(challenge.categories || []),
    ...(challenge.tags || []),
  ].forEach((item) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = item;
    challengeMeta.appendChild(pill);
  });

  (challenge.examples || []).forEach((example) => {
    const item = document.createElement("li");
    item.textContent = example;
    challengeExamples.appendChild(item);
  });

  (challenge.constraints || []).forEach((constraint) => {
    const item = document.createElement("li");
    item.textContent = constraint;
    challengeConstraints.appendChild(item);
  });
}

function renderWorkspaceLinks(workspace) {
  workspaceLinks.innerHTML = "";
  if (!workspace?.links) return;

  [
    ["Open solution in VS Code", workspace.links.solution],
    ["Evaluation report", workspace.links.evaluation],
  ].forEach(([label, href]) => {
    if (!href) return;
    const link = document.createElement("a");
    link.href = href;
    if (href.startsWith("vscode://")) {
      link.target = "_self";
      link.title = "Open the generated solution file in VS Code";
    } else {
      link.target = "_blank";
      link.rel = "noreferrer";
    }
    link.textContent = label;
    workspaceLinks.appendChild(link);
  });
}

function setEvaluationStatus(message, isError = false) {
  evaluationStatus.textContent = message;
  evaluationStatus.classList.toggle("error", isError);
}

function renderRoomSummary() {
  if (!activeSession) {
    roomSummary.textContent = "No active room.";
    return;
  }

  roomSummary.textContent = `${activeSession.roomName} · agent ${activeSession.agentName}`;
}

function renderParticipants() {
  participantsEl.innerHTML = "";
  if (!room) return;

  const participants = [
    room.localParticipant,
    ...Array.from(room.remoteParticipants.values()),
  ];

  participants.forEach((participant) => {
    const item = document.createElement("div");
    item.className = "participant";
    item.textContent = `${participant.name || participant.identity} (${participant.identity})`;
    participantsEl.appendChild(item);
  });
}

function attachAudioTrack(track, _publication, participant) {
  const element = track.attach();
  element.dataset.participant = participant.identity;
  audioTracks.appendChild(element);
}

function detachAudioTrack(track) {
  track.detach().forEach((element) => element.remove());
}

function createScoreBar(score) {
  const wrapper = document.createElement("div");
  wrapper.className = "score-bar";

  const label = document.createElement("div");
  label.className = "score-label";
  label.textContent = score?.scoreLabel || "Not scored";

  const track = document.createElement("div");
  track.className = "score-track";

  const fill = document.createElement("div");
  fill.className = "score-fill";
  fill.style.width = `${Math.max(0, Math.min(100, score?.percent || 0))}%`;
  track.appendChild(fill);

  wrapper.append(label, track);
  return wrapper;
}

function createFeedbackCard(title, body) {
  const card = document.createElement("article");
  card.className = "feedback-card";

  const heading = document.createElement("h3");
  heading.textContent = title;

  const text = document.createElement("p");
  text.textContent = body || "Not noted.";

  card.append(heading, text);
  return card;
}

function renderEvaluation(payload) {
  evaluationContent.innerHTML = "";

  if (!payload.available) {
    evaluationContent.className = "evaluation-content empty";
    const empty = document.createElement("p");
    empty.textContent = payload.message || "No evaluation report has been written yet.";
    evaluationContent.appendChild(empty);
    setEvaluationStatus("Evaluation is not available yet.");
    return;
  }

  evaluationContent.className = "evaluation-content";
  setEvaluationStatus(`Loaded ${payload.title}.`);

  const overview = document.createElement("div");
  overview.className = "score-overview";

  const scoreNumber = document.createElement("div");
  scoreNumber.className = "score-number";
  scoreNumber.textContent =
    payload.overallScore?.score == null
      ? "--"
      : `${payload.overallScore.score}/${payload.overallScore.maximum}`;

  const scoreCopy = document.createElement("div");
  const scoreTitle = document.createElement("h3");
  scoreTitle.textContent = "Overall score";
  const scoreMeta = document.createElement("p");
  scoreMeta.textContent = [
    payload.metadata?.Difficulty,
    payload.metadata?.Type,
  ].filter(Boolean).join(" · ");
  scoreCopy.append(scoreTitle, scoreMeta, createScoreBar(payload.overallScore));
  overview.append(scoreNumber, scoreCopy);

  const rubricGrid = document.createElement("div");
  rubricGrid.className = "rubric-grid";
  (payload.rubric || []).forEach((item) => {
    const row = document.createElement("div");
    row.className = "rubric-row";
    const label = document.createElement("span");
    label.textContent = item.label;
    row.append(label, createScoreBar(item));
    rubricGrid.appendChild(row);
  });

  const testCard = document.createElement("article");
  testCard.className = "test-result-card";
  const testTitle = document.createElement("h3");
  testTitle.textContent = "Local test result";
  const testResult = document.createElement("pre");
  testResult.textContent = payload.testResult || "No local test result was recorded.";
  testCard.append(testTitle, testResult);

  const feedbackGrid = document.createElement("div");
  feedbackGrid.className = "feedback-grid";
  feedbackGrid.append(
    createFeedbackCard("What went well", payload.sections?.whatWentWell),
    createFeedbackCard("What to improve", payload.sections?.whatToImprove),
    createFeedbackCard("Notable moments", payload.sections?.notableMoments),
    createFeedbackCard("Next steps", payload.sections?.recommendedNextSteps),
  );

  evaluationContent.append(overview, rubricGrid, testCard, feedbackGrid);
}

async function loadEvaluation() {
  const challengeId = activeSession?.challenge?.id || lastChallengeId;
  if (!challengeId) {
    renderEvaluation({
      available: false,
      message: "Start an interview before loading an evaluation.",
    });
    return;
  }

  setEvaluationStatus("Checking for evaluation report...");
  try {
    const response = await fetch(
      `/api/evaluation/${encodeURIComponent(challengeId)}`,
    );
    const payload = await readJsonResponse(response, "Could not load evaluation");
    renderEvaluation(payload);
  } catch (error) {
    console.error(error);
    evaluationContent.innerHTML = "";
    const message = error.message.includes("404") && error.message.includes("Not found")
      ? "Evaluation endpoint was not found. Restart the local web server so the updated API is active."
      : error.message;
    setEvaluationStatus(message, true);
  }
}

async function loadChallenges() {
  const response = await fetch("/api/challenges");
  const payload = await readJsonResponse(response, "Could not load challenges");
  challengeCatalog = payload.challenges;
  challengeSelect.innerHTML = "";

  const randomOption = document.createElement("option");
  randomOption.value = "";
  randomOption.textContent = "Random challenge";
  challengeSelect.appendChild(randomOption);

  challengeCatalog.forEach((challenge) => {
    const option = document.createElement("option");
    option.value = challenge.id;
    option.textContent = `${challenge.title} · ${challenge.type} · ${challenge.difficulty}`;
    challengeSelect.appendChild(option);
  });

  renderChallenge(null);
  challengeSelect.addEventListener("change", () => {
    renderChallenge(
      challengeCatalog.find((item) => item.id === challengeSelect.value),
    );
  });
  setStatus("Ready. Start the agent with dev mode, then start the interview.");
}

async function startInterview() {
  connectButton.disabled = true;
  setStatus("Creating room and token...");

  try {
    const response = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        challengeId: challengeSelect.value,
        participantName: participantName.value,
      }),
    });
    const payload = await readJsonResponse(response, "Could not start session");

    activeSession = payload;
    lastChallengeId = payload.challenge.id;
    renderChallenge(payload.challenge);
    renderWorkspaceLinks(payload.workspace);
    refreshEvaluationButton.disabled = false;
    loadEvaluation();

    room = new Room({ adaptiveStream: true, dynacast: true });
    room.on(RoomEvent.ParticipantConnected, renderParticipants);
    room.on(RoomEvent.ParticipantDisconnected, renderParticipants);
    room.on(RoomEvent.TrackSubscribed, attachAudioTrack);
    room.on(RoomEvent.TrackUnsubscribed, detachAudioTrack);
    room.on(RoomEvent.Disconnected, () => {
      setStatus("Disconnected.");
      connectButton.disabled = false;
      disconnectButton.disabled = true;
      micButton.disabled = true;
      room = null;
      activeSession = null;
      micButton.textContent = "Toggle mic";
      renderRoomSummary();
      renderParticipants();
    });

    await room.connect(payload.livekitUrl, payload.token);
    await room.localParticipant.setMicrophoneEnabled(true);

    disconnectButton.disabled = false;
    micButton.disabled = false;
    micButton.textContent = "Mute mic";
    setStatus(`Connected to ${payload.roomName}. The agent should join automatically.`);
    renderRoomSummary();
    renderParticipants();
  } catch (error) {
    console.error(error);
    setStatus(error.message, true);
    connectButton.disabled = false;
  }
}

async function leaveInterview() {
  if (room) {
    await room.disconnect();
  }
}

async function toggleMic() {
  if (!room) return;
  const enabled = room.localParticipant.isMicrophoneEnabled;
  await room.localParticipant.setMicrophoneEnabled(!enabled);
  micButton.textContent = enabled ? "Unmute mic" : "Mute mic";
  setStatus(`Microphone ${enabled ? "muted" : "enabled"}.`);
}

connectButton.addEventListener("click", startInterview);
disconnectButton.addEventListener("click", leaveInterview);
micButton.addEventListener("click", toggleMic);
refreshEvaluationButton.addEventListener("click", loadEvaluation);

loadChallenges().catch((error) => {
  console.error(error);
  setStatus(error.message, true);
});
