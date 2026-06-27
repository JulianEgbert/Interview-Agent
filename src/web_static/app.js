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

let room = null;
let activeSession = null;
let challengeCatalog = [];

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
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

async function loadChallenges() {
  const response = await fetch("/api/challenges");
  const payload = await response.json();
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
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Could not start session.");

    activeSession = payload;
    renderChallenge(payload.challenge);
    renderWorkspaceLinks(payload.workspace);

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

loadChallenges().catch((error) => {
  console.error(error);
  setStatus(error.message, true);
});
