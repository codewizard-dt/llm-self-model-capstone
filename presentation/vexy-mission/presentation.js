const slides = Array.from(document.querySelectorAll(".slide"));
const revealItems = Array.from(document.querySelectorAll("[data-reveal]"));
const progressBar = document.querySelector("#progressBar");
const currentSlide = document.querySelector("#currentSlide");
const currentLabel = document.querySelector("#currentLabel");
const startPresentation = document.querySelector("#startPresentation");
const editPresentation = document.querySelector("#editPresentation");
const pinComment = document.querySelector("#pinComment");
const speakerOwner = document.querySelector("#speakerOwner");
const toggleSuggestions = document.querySelector("#toggleSuggestions");
const copyEdits = document.querySelector("#copyEdits");
const copyReviewMarkdownButton = document.querySelector("#copyReviewMarkdown");
const copyReviewLinkButton = document.querySelector("#copyReviewLink");
const exportReviewPacketButton = document.querySelector("#exportReviewPacket");
const importReviewPacketButton = document.querySelector("#importReviewPacket");
const importReviewPacketFile = document.querySelector("#importReviewPacketFile");
const reviewToolsMenu = document.querySelector("#reviewToolsMenu");
const downloadEditedHtml = document.querySelector("#downloadEditedHtml");
const resetEdits = document.querySelector("#resetEdits");
const editStatus = document.querySelector("#editStatus");
const copyTeamHandoff = document.querySelector("#copyTeamHandoff");
const markSpeakerReadyButton = document.querySelector("#markSpeakerReady");
const speakerReadyList = document.querySelector("#speakerReadyList");
const reviewFocusTitle = document.querySelector("#reviewFocusTitle");
const reviewFocusCopy = document.querySelector("#reviewFocusCopy");
const reviewChecklist = document.querySelector("#reviewChecklist");
const reviewLauncherName = document.querySelector("#reviewLauncherName");
const pinModeBanner = document.querySelector("#pinModeBanner");
const cancelPinModeButton = document.querySelector("#cancelPinModeButton");
const reviewDrawer = document.querySelector("#reviewDrawer");
const closeReviewDrawer = document.querySelector("#closeReviewDrawer");
const commentList = document.querySelector("#commentList");
const suggestionPanel = document.querySelector("#suggestionPanel");
const suggestionBank = document.querySelector("#suggestionBank");
const pinComposer = document.querySelector("#pinComposer");
const pinCommentText = document.querySelector("#pinCommentText");
const pinComposerMeta = document.querySelector("#pinComposerMeta");
const savePinComment = document.querySelector("#savePinComment");
const cancelPinComment = document.querySelector("#cancelPinComment");
const editableNodes = Array.from(document.querySelectorAll("[data-edit-key]"));
const commentSurfaces = Array.from(document.querySelectorAll("[data-comment-surface]"));
const diagramChoiceCards = Array.from(document.querySelectorAll("[data-diagram-choice]"));
const activeDiagramBoards = Array.from(document.querySelectorAll("[data-active-diagram-owner]"));
const speakerPrivatePanels = Array.from(document.querySelectorAll("[data-private-owner]"));
const editStorageKey = "vexy-mission-presentation-edits-v2";
const changedEditKeysStorageKey = "vexy-mission-presentation-changed-edit-keys-v2";
const deprecatedReviewStorageKeys = [
  "vexy-mission-presentation-edits-v1",
  "vexy-mission-presentation-changed-edit-keys-v1"
];
const commentsStorageKey = "vexy-mission-presentation-comments-v2";
const diagramSelectionsStorageKey = "vexy-mission-presentation-diagram-selections-v2";
const speakerConfirmationsStorageKey = "vexy-mission-presentation-speaker-confirmations-v2";
const reviewDeckVersion = "vexy-mission-review-v2";
const urlHashReviewKey = "review";
const validSpeakerOwners = ["grace", "david", "erick", "jake"];
const maxReviewUrlLength = 12000;
const initialUrlParams = new URLSearchParams(window.location.search);
const reviewEnabledFromUrl = initialUrlParams.has("edit") || window.location.hash.includes(`${urlHashReviewKey}=`);
let audioUnlocked = false;
let activeIndex = 0;
let activeLockCleanup = null;
let pinMode = false;
let pendingPin = null;
let blockedByFactCheck = false;
let revealFrame = 0;

if (reviewEnabledFromUrl) {
  document.body.classList.add("review-enabled");
}

const speakerSuggestions = {
  unassigned:
    "Choose your name first. Then edit only your speaking section, pin exact comments, pick one diagram, and send back a review packet.",
  grace:
    "Grace should own the premise: Self-Modeling Machines, in Language; VEX V5 as the body; Raspberry Pi, AprilTag, and yellow ball as perception; grab, pull, throw as the primitive arc.",
  david:
    "David should avoid repeating Grace's hardware intro and instead explain the small learning loop, the Generational Loop, the research synthesis, and the honest future path.",
  erick:
    "Erick should make trusted motion concrete: bounded vocabulary, command limits, watchdogs, ack/fault states, and evidence for every robot action.",
  jake:
    "Jake should make the evidence packet feel inevitable: prediction, observation, telemetry, vision, gap, and update."
};

const noteSuggestionBank = {
  grace: [
    "Open by naming the premise: Self-Modeling Machines, in Language.",
    "Point to VEX V5, Raspberry Pi, AprilTag, and the yellow ball as the physical grounding.",
    "Close by saying grab, pull, and throw make the learning loop visible."
  ],
  david: [
    "Say the small loop is plan, execute, analyze telemetry, then start over.",
    "Explain the Generational Loop as the future body-redesign layer.",
    "Frame the novelty as combining self-modeling, LLM morphology, and hardware evidence."
  ],
  erick: [
    "Use the phrase trusted motion: bounded commands plus evidence.",
    "Name the real-world messiness: slip, drift, camera errors, and moving targets.",
    "Explain why strict command vocabulary lets the LLM reason without freelancing against motors."
  ],
  jake: [
    "Define the evidence packet: predicted, observed, telemetry, vision, gap, update.",
    "Say the gap is not embarrassment; it is the learning signal.",
    "Connect AprilTags and yellow-ball confidence to grounded observation."
  ]
};

const speakerReviewLinks = [
  ["Grace", "grace"],
  ["David Taylor", "david"],
  ["Erick", "erick"],
  ["Jake", "jake"]
];

const speakerCoverageMap = {
  grace: [
    {
      topic: "VEX hardware and language self-model premise",
      tokens: ["self-modeling machines", "vex v5 brain", "smart ports", "raspberry pi", "apriltag", "yellow ball", "grab", "pull", "throw"]
    }
  ],
  david: [
    {
      topic: "learning loops and morphology redesign",
      tokens: ["small learning loop", "generational loop", "numerical self-modeling", "morphology", "redesign its own body", "sub-symbolic tensor"]
    }
  ],
  erick: [
    {
      topic: "trusted motion and bounded command contracts",
      tokens: ["trusted motion", "bounded commands", "strict contracts", "watchdog", "ack", "fault", "wheel slip", "motor drift"]
    }
  ],
  jake: [
    {
      topic: "evidence packet and prediction-observation gap",
      tokens: ["evidence packet", "predicted", "observed", "telemetry", "vision state", "gap", "learning signal"]
    }
  ]
};

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#039;"
    };
    return entities[character];
  });
}

function updateProgress(index) {
  const safeIndex = Math.max(0, Math.min(index, slides.length - 1));
  activeIndex = safeIndex;
  const percent = slides.length <= 1 ? 100 : (safeIndex / (slides.length - 1)) * 100;
  progressBar.style.width = `${percent}%`;
  if (currentSlide) currentSlide.textContent = String(safeIndex + 1).padStart(2, "0");
  if (currentLabel) currentLabel.textContent = slides[safeIndex].dataset.label || "Presentation";
  slides.forEach((slide, slideIndex) => slide.classList.toggle("is-active", slideIndex === safeIndex));
  revealActiveSlide(safeIndex);
  pauseInactiveVideos(safeIndex);
  playActiveVideo(safeIndex, { restart: audioUnlocked });
}

function revealActiveSlide(activeIndex) {
  slides[activeIndex]?.querySelectorAll("[data-reveal]").forEach((item) => {
    item.classList.add("is-visible");
  });
}

function currentSlideIndexFromViewport() {
  const probeY = window.innerHeight * 0.38;
  const index = slides.findIndex((slide) => {
    const rect = slide.getBoundingClientRect();
    return rect.top <= probeY && rect.bottom >= probeY;
  });
  return index === -1 ? activeIndex : index;
}

function revealSlideInViewport() {
  revealActiveSlide(currentSlideIndexFromViewport());
}

function pauseInactiveVideos(activeIndex) {
  slides.forEach((slide, slideIndex) => {
    if (slideIndex === activeIndex) return;
    slide.querySelectorAll("video").forEach((video) => video.pause());
  });
}

function playActiveVideo(activeIndex, options = {}) {
  const activeVideo = slides[activeIndex]?.querySelector("video");
  if (!activeVideo) {
    unlockScrollAfterVideo();
    return;
  }
  if (options.restart) {
    try {
      activeVideo.currentTime = 0;
    } catch {
      activeVideo.setAttribute("data-seek-blocked", "true");
    }
  }
  activeVideo.loop = !audioUnlocked && activeVideo.dataset.loopAfterCopy !== undefined;
  if (audioUnlocked) {
    activeVideo.muted = false;
  }
  activeVideo.play().catch(() => {
    activeVideo.setAttribute("data-play-blocked", "true");
  });
  if (audioUnlocked && activeVideo.dataset.videoLock !== undefined) {
    lockScrollForVideo(activeVideo);
  }
}

function clearAudienceUrlState() {
  if (!window.history?.replaceState) return;
  try {
    window.history.replaceState(null, "", window.location.pathname || "./");
  } catch {
    document.body.setAttribute("data-audience-url-cleanup-blocked", "true");
  }
}

function unlockAudio() {
  closeDrawer();
  disableEditMode();
  closeDrawer();
  document.body.classList.remove("review-enabled", "editing", "pinning");
  document.body.classList.remove("suggestions-open");
  if (pinModeBanner) pinModeBanner.hidden = true;
  if (pinComposer) pinComposer.hidden = true;
  reviewToolsMenu?.removeAttribute("open");
  clearAudienceUrlState();
  audioUnlocked = true;
  document.body.classList.add("presentation-started");
  document.querySelectorAll("[data-presentation-video]").forEach((video) => {
    video.muted = false;
    video.loop = false;
    video.controls = false;
  });
  if (document.documentElement.requestFullscreen) {
    document.documentElement.requestFullscreen().catch(() => {
      document.body.setAttribute("data-fullscreen-blocked", "true");
    });
  }
  playActiveVideo(activeIndex, { restart: true });
}

function lockScrollForVideo(video) {
  if (activeLockCleanup) activeLockCleanup();
  document.body.classList.add("video-locked");
  const unlock = () => {
    unlockScrollAfterVideo();
    if (video.dataset.loopAfterCopy !== undefined) {
      video.muted = true;
      video.loop = true;
      video.play().catch(() => {
        video.setAttribute("data-loop-blocked", "true");
      });
    }
  };
  video.addEventListener("ended", unlock, { once: true });
  activeLockCleanup = () => {
    video.removeEventListener("ended", unlock);
    activeLockCleanup = null;
  };
}

function readStoredEdits() {
  try {
    return JSON.parse(localStorage.getItem(editStorageKey) || "{}");
  } catch {
    return {};
  }
}

function readJsonStorage(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
  } catch {
    return fallback;
  }
}

function writeJsonStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value, null, 2));
}

function purgeDeprecatedReviewStorage() {
  deprecatedReviewStorageKeys.forEach((key) => localStorage.removeItem(key));
}

function markChangedEditKey(editKey) {
  if (!editKey) return;
  const changedKeys = new Set(readJsonStorage(changedEditKeysStorageKey, []));
  changedKeys.add(editKey);
  writeJsonStorage(changedEditKeysStorageKey, Array.from(changedKeys));
}

function ownerForNode(node) {
  return node?.dataset.owner || node?.closest("[data-owner]")?.dataset.owner || "all";
}

function collectEdits() {
  return editableNodes.reduce((edits, node) => {
    edits[node.dataset.editKey] = node.textContent.trim();
    return edits;
  }, {});
}

function factCheckSpeakerNoteOverlap(node) {
  const editKey = node?.dataset?.editKey || "";
  if (!editKey.endsWith("_notes")) return { blocked: false };
  const owner = ownerForNode(node);
  const text = node.textContent.toLowerCase();
  for (const [otherOwner, topicGroups] of Object.entries(speakerCoverageMap)) {
    if (otherOwner === owner) continue;
    for (const group of topicGroups) {
      const matchedTokens = group.tokens.filter((token) => text.includes(token));
      if (matchedTokens.length >= 2) {
        return {
          blocked: true,
          owner: otherOwner,
          topic: group.topic,
          matchedTokens
        };
      }
    }
  }
  return { blocked: false };
}

function renderFactCheckMessage(result) {
  return `Fact-check blocked save: this sounds like ${result.owner}'s section (${result.topic}). Move it to a suggestion or rewrite it for your own part.`;
}

function persistEdits(event) {
  const node = event?.currentTarget;
  const factCheck = factCheckSpeakerNoteOverlap(node);
  if (factCheck.blocked) {
    blockedByFactCheck = true;
    node.setAttribute("data-fact-check", "blocked");
    if (editStatus) editStatus.textContent = renderFactCheckMessage(factCheck);
    openReviewDrawer();
    return false;
  }
  blockedByFactCheck = false;
  node?.removeAttribute("data-fact-check");
  markChangedEditKey(node?.dataset?.editKey);
  localStorage.setItem(editStorageKey, JSON.stringify(collectEdits(), null, 2));
  if (editStatus) editStatus.textContent = "Saved in this browser only. Copy review link to send.";
  renderReviewFocus();
  return true;
}

function applyStoredEdits() {
  const edits = readStoredEdits();
  editableNodes.forEach((node) => {
    const saved = edits[node.dataset.editKey];
    if (typeof saved === "string" && saved.length) node.textContent = saved;
  });
}

function enableEditMode() {
  document.body.classList.add("editing");
  editableNodes.forEach((node) => {
    node.contentEditable = "true";
    node.spellcheck = true;
  });
  [copyEdits, copyReviewMarkdownButton, copyReviewLinkButton, exportReviewPacketButton, downloadEditedHtml, resetEdits].forEach((button) => {
    if (button) button.disabled = false;
  });
  if (editPresentation) {
    editPresentation.textContent = "Done editing";
    editPresentation.setAttribute("aria-pressed", "true");
  }
  if (editStatus) editStatus.textContent = "Editing copy";
  applySpeakerOwnerFilter();
  openReviewDrawer();
}

function disableEditMode() {
  document.body.classList.remove("editing", "pinning");
  pinMode = false;
  pendingPin = null;
  editableNodes.forEach((node) => {
    node.contentEditable = "false";
  });
  [copyEdits, copyReviewMarkdownButton, copyReviewLinkButton, exportReviewPacketButton, downloadEditedHtml, resetEdits].forEach((button) => {
    if (button) button.disabled = true;
  });
  if (editPresentation) {
    editPresentation.textContent = "Review / Edit";
    editPresentation.setAttribute("aria-pressed", "false");
  }
  if (pinComment) {
    pinComment.textContent = "Pin a spot";
    pinComment.setAttribute("aria-pressed", "false");
  }
  if (pinModeBanner) pinModeBanner.hidden = true;
  if (pinComposer) pinComposer.hidden = true;
  reviewToolsMenu?.removeAttribute("open");
  if (editStatus) editStatus.textContent = "View mode";
  applyPrivateSpeakerVisibility();
  closeDrawer();
}

function prepareReviewMode() {
  document.body.classList.remove("editing", "pinning");
  pinMode = false;
  pendingPin = null;
  editableNodes.forEach((node) => {
    node.contentEditable = "false";
  });
  [copyEdits, copyReviewMarkdownButton, copyReviewLinkButton, exportReviewPacketButton, downloadEditedHtml, resetEdits].forEach((button) => {
    if (button) button.disabled = true;
  });
  if (editPresentation) {
    editPresentation.textContent = "Review / Edit";
    editPresentation.setAttribute("aria-pressed", "false");
  }
  if (pinComment) {
    pinComment.textContent = "Pin a spot";
    pinComment.setAttribute("aria-pressed", "false");
  }
  if (pinModeBanner) pinModeBanner.hidden = true;
  if (pinComposer) pinComposer.hidden = true;
  reviewToolsMenu?.removeAttribute("open");
  closeDrawer();
  applyPrivateSpeakerVisibility();
  renderReviewFocus();
  updateSuggestionPanel();
}

function toggleEditMode() {
  if (document.body.classList.contains("editing")) {
    disableEditMode();
  } else {
    enableEditMode();
  }
}

function runFactCheckBeforeExport() {
  for (const node of editableNodes) {
    const factCheck = factCheckSpeakerNoteOverlap(node);
    if (factCheck.blocked) {
      blockedByFactCheck = true;
      node.setAttribute("data-fact-check", "blocked");
      if (editStatus) editStatus.textContent = renderFactCheckMessage(factCheck);
      openReviewDrawer();
      return false;
    }
  }
  blockedByFactCheck = false;
  return true;
}

async function copyEditsJson() {
  if (!runFactCheckBeforeExport()) return;
  const json = JSON.stringify(collectEdits(), null, 2);
  await navigator.clipboard.writeText(json);
  if (editStatus) editStatus.textContent = "Copied edits JSON";
}

function downloadEditedHtmlSnapshot() {
  if (!runFactCheckBeforeExport()) return;
  persistEdits();
  const clone = document.documentElement.cloneNode(true);
  clone.querySelectorAll("[contenteditable]").forEach((node) => node.removeAttribute("contenteditable"));
  const html = `<!doctype html>\n${clone.outerHTML}`;
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "vexy-mission-presentation-edited.html";
  anchor.click();
  URL.revokeObjectURL(url);
  if (editStatus) editStatus.textContent = "Downloaded edited HTML";
}

function resetLocalEdits() {
  localStorage.removeItem(editStorageKey);
  localStorage.removeItem(changedEditKeysStorageKey);
  purgeDeprecatedReviewStorage();
  localStorage.removeItem(commentsStorageKey);
  localStorage.removeItem(diagramSelectionsStorageKey);
  localStorage.removeItem(speakerConfirmationsStorageKey);
  window.location.reload();
}

function openReviewDrawer() {
  reviewDrawer?.classList.add("is-open");
}

function closeDrawer() {
  reviewDrawer?.classList.remove("is-open");
}

function currentOwner() {
  return speakerOwner?.value || "unassigned";
}

function currentOwnerIsValidReviewer() {
  return validSpeakerOwners.includes(currentOwner());
}

function speakerNameForOwner(owner) {
  return speakerReviewLinks.find(([, speakerOwnerId]) => speakerOwnerId === owner)?.[0] || owner;
}

function renderReviewLauncher(owner = currentOwner()) {
  if (!reviewLauncherName) return;
  reviewLauncherName.textContent = validSpeakerOwners.includes(owner)
    ? `${speakerNameForOwner(owner)}'s`
    : "Choose your speaker";
}

function renderReviewFocus(owner = currentOwner()) {
  if (!reviewFocusTitle || !reviewFocusCopy || !reviewChecklist) return;
  const hasOwner = validSpeakerOwners.includes(owner);
  if (!hasOwner) {
    reviewFocusTitle.textContent = "Choose your speaker";
    reviewFocusCopy.textContent = "Pick your name to unlock only your notes, your diagram choices, and your review checklist.";
    reviewChecklist.innerHTML = [
      ["Choose speaker", "Use the Editing as menu or your direct review link."],
      ["Review notes", "Open your private notes and adjust only your section."],
      ["Pin exact fixes", "Use Pin a spot only when a slide needs a specific change."],
      ["Send back", "Mark ready, then copy a review link."]
    ]
      .map(([title, detail], index) => `
        <li class="${index === 0 ? "is-current" : ""}">
          <strong>${escapeHtml(title)}</strong>
          <span>${escapeHtml(detail)}</span>
        </li>
      `)
      .join("");
    return;
  }

  const name = speakerNameForOwner(owner);
  const changedKeys = readJsonStorage(changedEditKeysStorageKey, []);
  const comments = readJsonStorage(commentsStorageKey, []);
  const confirmations = readJsonStorage(speakerConfirmationsStorageKey, {});
  const ready = Boolean(confirmations[owner]);
  const notesChanged = changedKeys.includes(`${owner}_notes`);
  const ownerComments = comments.filter((comment) => comment.author === owner || comment.targetOwner === owner);
  const steps = [
    {
      title: "Speaker lane active",
      detail: `${name} can edit their private notes and diagram controls.`,
      complete: true
    },
    {
      title: "Private notes checked",
      detail: notesChanged ? "Private speaker notes were updated in this browser." : "Open the private notes panel and adjust only if needed.",
      complete: notesChanged || ready
    },
    {
      title: "Exact pins added",
      detail: ownerComments.length ? `${ownerComments.length} pinned comment${ownerComments.length === 1 ? "" : "s"} saved.` : "Use Pin a spot only for exact slide fixes.",
      complete: ownerComments.length > 0 || ready
    },
    {
      title: "Section marked ready",
      detail: ready ? "Ready confirmation is included in the review packet." : "Click Mark my section ready after reviewing.",
      complete: ready
    },
    {
      title: "Review link sent back",
      detail: ready ? "Copy review link and send it back to Grace." : "This becomes the final step after Ready check.",
      complete: false
    }
  ];
  const firstOpenIndex = steps.findIndex((step) => !step.complete);
  reviewFocusTitle.textContent = `${name}'s review lane`;
  reviewFocusCopy.textContent = ready
    ? "Ready is marked. The only thing left is to copy the review link and send it back."
    : "Move top to bottom: notes, exact pins if needed, ready check, then review link.";
  reviewChecklist.innerHTML = steps
    .map((step, index) => `
      <li class="${step.complete ? "is-complete" : ""} ${index === firstOpenIndex ? "is-current" : ""}">
        <strong>${escapeHtml(step.title)}</strong>
        <span>${escapeHtml(step.detail)}</span>
      </li>
    `)
    .join("");
}

function updateSuggestionPanel(owner = currentOwner()) {
  if (!suggestionPanel) return;
  const key = validSpeakerOwners.includes(owner) ? owner : "unassigned";
  suggestionPanel.innerHTML = `
    <h3>Speaker guidance</h3>
    <p>${escapeHtml(speakerSuggestions[key] || "Choose a speaker to see targeted copy suggestions.")}</p>
  `;
}

function renderSuggestionBank(owner = currentOwner()) {
  if (!suggestionBank) return;
  const suggestions = noteSuggestionBank[owner] || [];
  suggestionBank.innerHTML = `
    <h3>Add to speaker notes</h3>
    <p>${escapeHtml(validSpeakerOwners.includes(owner) ? "These suggestions append only to your private notes." : "Choose your name to see note suggestions.")}</p>
    <div class="suggestion-actions">
      ${suggestions
        .map(
          (suggestion) =>
            `<button type="button" data-note-suggestion="${escapeHtml(suggestion)}">${escapeHtml(suggestion)}</button>`
        )
        .join("")}
    </div>
  `;
}

function applySuggestionToNotes(event) {
  const suggestion = event.target.closest("[data-note-suggestion]")?.dataset.noteSuggestion;
  const owner = currentOwner();
  if (!suggestion || !validSpeakerOwners.includes(owner)) return;
  const notesNode = document.querySelector(`[data-edit-key="${owner}_notes"]`);
  if (!notesNode) return;
  notesNode.textContent = `${notesNode.textContent.trim()}\n\n${suggestion}`;
  if (persistEdits({ currentTarget: notesNode })) {
    if (editStatus) editStatus.textContent = "Added suggestion to your private notes.";
    notesNode.closest("details")?.setAttribute("open", "");
  }
}

function renderSpeakerConfirmations() {
  if (!speakerReadyList) return;
  const confirmations = readJsonStorage(speakerConfirmationsStorageKey, {});
  speakerReadyList.innerHTML = speakerReviewLinks
    .map(([name, owner]) => {
      const confirmation = confirmations[owner];
      return `
        <span class="${confirmation ? "is-ready" : "is-waiting"}">
          <strong>${escapeHtml(name)}</strong>
          <em>${confirmation ? "Ready" : "Waiting"}</em>
        </span>
      `;
    })
    .join("");
}

function markSpeakerReady() {
  const owner = currentOwner();
  if (!validSpeakerOwners.includes(owner)) {
    if (editStatus) editStatus.textContent = "Choose your name before marking ready.";
    openReviewDrawer();
    return;
  }
  const confirmations = readJsonStorage(speakerConfirmationsStorageKey, {});
  confirmations[owner] = {
    deckVersion: reviewDeckVersion,
    owner,
    name: speakerNameForOwner(owner),
    confirmedAt: new Date().toISOString()
  };
  writeJsonStorage(speakerConfirmationsStorageKey, confirmations);
  renderSpeakerConfirmations();
  renderReviewFocus(owner);
  if (editStatus) editStatus.textContent = `${speakerNameForOwner(owner)} marked ready. Copy review link to send it back.`;
}

function applyPrivateSpeakerVisibility(owner = currentOwner()) {
  const editing = document.body.classList.contains("editing");
  renderReviewLauncher(owner);
  speakerPrivatePanels.forEach((panel) => {
    const panelOwner = panel.dataset.privateOwner;
    const visible = editing && (owner === panelOwner || owner === "all");
    panel.hidden = !visible;
    panel.toggleAttribute("data-owner-hidden", !visible);
    panel.setAttribute("aria-hidden", String(!visible));
    if (panel.matches("details")) {
      panel.open = visible;
    }
  });
  renderSuggestionBank(owner);
  renderReviewFocus(owner);
}

function applySpeakerOwnerFilter() {
  const owner = currentOwner();
  document.body.dataset.activeOwner = owner;
  editableNodes.forEach((node) => {
    const nodeOwner = ownerForNode(node);
    const canEdit = owner === "all" || (owner !== "unassigned" && nodeOwner === owner) || nodeOwner === "all";
    node.toggleAttribute("data-owner-locked", !canEdit);
    if (document.body.classList.contains("editing")) {
      node.contentEditable = canEdit ? "true" : "false";
    }
  });
  updateSuggestionPanel(owner);
  applyPrivateSpeakerVisibility(owner);
  renderReviewFocus(owner);
}

function buildReviewPacket() {
  return {
    deckVersion: reviewDeckVersion,
    url: window.location.href,
    exportedAt: new Date().toISOString(),
    activeOwner: currentOwner(),
    edits: collectEdits(),
    changedEditKeys: readJsonStorage(changedEditKeysStorageKey, []),
    comments: readJsonStorage(commentsStorageKey, []),
    diagramSelections: readJsonStorage(diagramSelectionsStorageKey, {}),
    speakerConfirmations: readJsonStorage(speakerConfirmationsStorageKey, {})
  };
}

function encodeReviewPacketToHash(packet) {
  const json = JSON.stringify(packet);
  const bytes = new TextEncoder().encode(json);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/u, "");
}

function decodeReviewPacketFromHash(encodedPacket) {
  const normalized = encodedPacket.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
  const binary = atob(padded);
  const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

function readReviewPacketFromHash() {
  const hash = window.location.hash.replace(/^#/, "");
  if (!hash) return null;
  const params = new URLSearchParams(hash);
  const encodedPacket = params.get(urlHashReviewKey);
  if (!encodedPacket) return null;
  return decodeReviewPacketFromHash(encodedPacket);
}

function mergeCommentsById(existingComments, incomingComments) {
  const commentsById = new Map();
  existingComments.forEach((comment) => commentsById.set(comment.id, comment));
  incomingComments.forEach((comment) => commentsById.set(comment.id || `pin-${Date.now()}`, comment));
  return Array.from(commentsById.values());
}

function applyReviewPacketFromHash() {
  try {
    const packet = readReviewPacketFromHash();
    if (!packet) return false;
    const imported = importReviewPacket(packet);
    if (!imported) return false;
    if (speakerOwner && typeof packet.activeOwner === "string") {
      speakerOwner.value = packet.activeOwner;
    }
    applySpeakerOwnerFilter();
    if (editStatus) editStatus.textContent = "Imported review link";
    return true;
  } catch {
    document.body.setAttribute("data-review-link-error", "true");
    if (editStatus) editStatus.textContent = "Review link could not be imported";
    return false;
  }
}

function applyOwnerFromUrl() {
  const ownerFromUrl = new URLSearchParams(window.location.search).get("owner");
  if (!validSpeakerOwners.includes(ownerFromUrl)) return false;
  if (speakerOwner) {
    speakerOwner.value = ownerFromUrl;
  }
  applySpeakerOwnerFilter();
  return true;
}

function downloadBlob(filename, mimeType, content) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function exportReviewPacket() {
  if (!runFactCheckBeforeExport()) return;
  downloadBlob(
    "vexy-mission-review-packet.json",
    "application/json",
    JSON.stringify(buildReviewPacket(), null, 2)
  );
  if (editStatus) editStatus.textContent = "Exported review packet";
}

function reviewPacketToMarkdown(packet = buildReviewPacket()) {
  const commentLines = (packet.comments || [])
    .map(
      (comment, index) =>
        `${index + 1}. slideId=${comment.slideId}; slideLabel=${comment.slideLabel}; author=${comment.author}; targetOwner=${comment.targetOwner || "unknown"}; status=${comment.status}; xPct=${comment.xPct}; yPct=${comment.yPct}; videoTimeSec=${comment.videoTimeSec ?? "none"}; comment=${comment.comment}`
    )
    .join("\n");
  const editLines = Object.entries(packet.edits || {})
    .map(([key, value]) => `- ${key}: ${value}`)
    .join("\n");
  const diagramLines = Object.entries(packet.diagramSelections || {})
    .map(([speaker, choice]) => `- ${speaker}: ${choice}`)
    .join("\n");
  const confirmationLines = Object.values(packet.speakerConfirmations || {})
    .map((confirmation) => `- ${confirmation.name || confirmation.owner}: ready at ${confirmation.confirmedAt}`)
    .join("\n");
  const changedKeyLines = (packet.changedEditKeys || [])
    .map((key) => `- ${key}`)
    .join("\n");
  return `# Vexy Mission Review Packet\n\nDeck: ${packet.deckVersion}\nURL: ${packet.url}\nOwner: ${packet.activeOwner}\n\n## Changed Edit Keys\n${changedKeyLines || "No changed edit keys exported."}\n\n## Pinned Comments\n${commentLines || "No pinned comments yet."}\n\n## Diagram Choices\n${diagramLines || "No diagram choices exported."}\n\n## Speaker Confirmations\n${confirmationLines || "No speaker confirmations exported."}\n\n## Copy Edits\n${editLines || "No copy edits exported."}\n`;
}

async function copyReviewMarkdown() {
  if (!runFactCheckBeforeExport()) return;
  await navigator.clipboard.writeText(reviewPacketToMarkdown());
  if (editStatus) editStatus.textContent = "Copied review markdown";
}

async function copyReviewLink() {
  if (!runFactCheckBeforeExport()) return;
  persistEdits();
  const url = new URL(window.location.href);
  url.searchParams.set("edit", "1");
  url.hash = `${urlHashReviewKey}=${encodeReviewPacketToHash(buildReviewPacket())}`;
  if (url.toString().length > maxReviewUrlLength) {
    exportReviewPacket();
    if (editStatus) editStatus.textContent = "Review is too large for a link. Exported JSON instead.";
    return;
  }
  await navigator.clipboard.writeText(url.toString());
  if (editStatus) editStatus.textContent = "Copied review link. Send it back after reviewing.";
}

function speakerReviewUrl(owner) {
  const url = new URL(window.location.href);
  url.search = "";
  url.hash = "";
  url.searchParams.set("edit", "1");
  url.searchParams.set("owner", owner);
  return url.toString();
}

function buildTeamHandoffMessage() {
  const linkLines = speakerReviewLinks
    .map(([name, owner]) => `- ${name}: ${speakerReviewUrl(owner)}`)
    .join("\n");
  const audienceUrl = speakerReviewUrl("grace").replace(/[?]edit=1&owner=grace$/u, "");
  const speakerAssetsUrl = new URL("speaker-assets.html", audienceUrl).toString();
  return `Please review your Vexy section before rehearsal.\n\nOpen your link, edit your private speaker notes, add pinned comments where something should change, then click Copy review link and send it back.\n\n${linkLines}\n\nAudience view:\n${audienceUrl}\nSpeaker assets:\n${speakerAssetsUrl}`;
}

async function copyTeamHandoffMessage() {
  await navigator.clipboard.writeText(buildTeamHandoffMessage());
  if (editStatus) editStatus.textContent = "Copied team handoff message";
}

function importReviewPacket(packet) {
  if (packet?.deckVersion !== reviewDeckVersion) {
    if (editStatus) editStatus.textContent = "Review packet version does not match this deck";
    return false;
  }
  if (packet?.edits && typeof packet.edits === "object") {
    const existingEdits = readStoredEdits();
    const changedKeys = Array.isArray(packet.changedEditKeys) ? packet.changedEditKeys : Object.keys(packet.edits);
    changedKeys.forEach((key) => {
      if (Object.prototype.hasOwnProperty.call(packet.edits, key)) {
        existingEdits[key] = packet.edits[key];
      }
    });
    localStorage.setItem(editStorageKey, JSON.stringify(existingEdits, null, 2));
    const existingChangedKeys = new Set(readJsonStorage(changedEditKeysStorageKey, []));
    changedKeys.forEach((key) => existingChangedKeys.add(key));
    writeJsonStorage(changedEditKeysStorageKey, Array.from(existingChangedKeys));
  }
  if (Array.isArray(packet?.comments) && packet.comments.length) {
    writeJsonStorage(
      commentsStorageKey,
      mergeCommentsById(readJsonStorage(commentsStorageKey, []), packet.comments)
    );
  }
  if (packet?.diagramSelections && typeof packet.diagramSelections === "object") {
    writeJsonStorage(diagramSelectionsStorageKey, {
      ...readJsonStorage(diagramSelectionsStorageKey, {}),
      ...packet.diagramSelections
    });
  }
  if (packet?.speakerConfirmations && typeof packet.speakerConfirmations === "object") {
    writeJsonStorage(speakerConfirmationsStorageKey, {
      ...readJsonStorage(speakerConfirmationsStorageKey, {}),
      ...packet.speakerConfirmations
    });
  }
  applyStoredEdits();
  renderCommentPins();
  renderCommentList();
  applyDiagramSelections();
  renderSpeakerConfirmations();
  renderReviewFocus();
  if (editStatus) editStatus.textContent = "Imported review packet";
  return true;
}

function setPinMode(enabled) {
  pinMode = enabled;
  document.body.classList.toggle("pinning", pinMode);
  if (pinComment) {
    pinComment.textContent = pinMode ? "Pinning on" : "Pin a spot";
    pinComment.setAttribute("aria-pressed", String(pinMode));
  }
  if (pinModeBanner) {
    pinModeBanner.hidden = !pinMode;
  }
  if (!pinMode) {
    pendingPin = null;
    if (pinComposer) pinComposer.hidden = true;
    if (pinCommentText) pinCommentText.value = "";
  }
  if (editStatus) {
    editStatus.textContent = pinMode ? "Click the exact slide spot that needs a fix." : "Editing copy";
  }
  if (pinMode) openReviewDrawer();
}

function createPinComment(event) {
  if (!pinMode) return;
  if (!currentOwnerIsValidReviewer()) {
    if (editStatus) editStatus.textContent = "Choose your name before pinning a comment.";
    openReviewDrawer();
    return;
  }
  const surface = event.target.closest("[data-comment-surface]");
  if (!surface) return;
  if (event.target.closest("button, a, details, summary, input, select, textarea")) return;
  event.preventDefault();
  event.stopPropagation();
  const rect = surface.getBoundingClientRect();
  const xPct = Math.round(((event.clientX - rect.left) / rect.width) * 1000) / 10;
  const yPct = Math.round(((event.clientY - rect.top) / rect.height) * 1000) / 10;
  const video = surface.querySelector("video");
  pendingPin = {
    id: `pin-${Date.now()}`,
    deckVersion: reviewDeckVersion,
    slideId: surface.dataset.slideId || surface.id || "unknown-slide",
    slideLabel: surface.dataset.label || surface.getAttribute("aria-label") || "Slide",
    targetOwner: surface.dataset.owner || "all",
    xPct,
    yPct,
    author: currentOwner(),
    status: "open",
    videoTimeSec: video ? Math.round(video.currentTime * 10) / 10 : null
  };
  if (pinComposer) pinComposer.hidden = false;
  if (pinCommentText) {
    pinCommentText.value = "";
    pinCommentText.focus();
  }
  if (pinComposerMeta) {
    pinComposerMeta.textContent = `${pendingPin.slideLabel} · ${pendingPin.xPct}%, ${pendingPin.yPct}%`;
  }
  openReviewDrawer();
  if (editStatus) editStatus.textContent = "Write the pinned comment, then Save pin.";
}

function savePendingPinComment() {
  if (!pendingPin) return;
  const comment = pinCommentText?.value.trim();
  if (!comment) {
    if (editStatus) editStatus.textContent = "Write a comment before saving the pin.";
    return;
  }
  const comments = readJsonStorage(commentsStorageKey, []);
  comments.push({
    ...pendingPin,
    comment
  });
  writeJsonStorage(commentsStorageKey, comments);
  pendingPin = null;
  if (pinComposer) pinComposer.hidden = true;
  if (pinCommentText) pinCommentText.value = "";
  renderCommentPins();
  renderCommentList();
  renderReviewFocus();
  openReviewDrawer();
  setPinMode(false);
  if (editStatus) editStatus.textContent = "Pinned locally. Copy review link to send it back.";
}

function cancelPendingPinComment() {
  pendingPin = null;
  if (pinComposer) pinComposer.hidden = true;
  if (pinCommentText) pinCommentText.value = "";
  if (editStatus) editStatus.textContent = pinMode ? "Click the exact slide spot that needs a fix." : "Editing copy";
}

function renderCommentPins() {
  document.querySelectorAll(".pin-marker").forEach((pin) => pin.remove());
  const comments = readJsonStorage(commentsStorageKey, []);
  comments.forEach((comment, index) => {
    const surface = document.querySelector(`[data-slide-id="${comment.slideId}"]`);
    if (!surface) return;
    const marker = document.createElement("button");
    marker.className = "pin-marker";
    marker.type = "button";
    marker.style.left = `${comment.xPct}%`;
    marker.style.top = `${comment.yPct}%`;
    marker.textContent = String(index + 1);
    marker.title = comment.comment;
    marker.addEventListener("click", () => {
      openReviewDrawer();
      const item = document.querySelector(`[data-comment-id="${comment.id}"]`);
      item?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    });
    surface.append(marker);
  });
}

function renderCommentList() {
  if (!commentList) return;
  const comments = readJsonStorage(commentsStorageKey, []);
  commentList.innerHTML = comments.length
    ? comments
        .map(
          (comment, index) => `
            <article class="comment-card" data-comment-id="${escapeHtml(comment.id)}">
              <span>${index + 1} · ${escapeHtml(comment.slideLabel)}</span>
              <p>${escapeHtml(comment.comment)}</p>
              <small>${escapeHtml(comment.author)} · ${escapeHtml(comment.xPct)}%, ${escapeHtml(comment.yPct)}%${comment.videoTimeSec == null ? "" : ` · ${escapeHtml(comment.videoTimeSec)}s`}</small>
            </article>
          `
        )
        .join("")
    : "<p class=\"empty-comments\">No pinned comments yet. Turn on Pin comment, then click a slide.</p>";
}

function togglePinMode() {
  setPinMode(!pinMode);
}

function applyDiagramSelections() {
  const selections = readJsonStorage(diagramSelectionsStorageKey, {});
  const selectedByOwner = new Map();
  diagramChoiceCards.forEach((card) => {
    const owner = card.closest("[data-diagram-owner]")?.dataset.diagramOwner;
    const defaultChoice = card.closest(".diagram-choice-grid")?.querySelector(".is-selected")?.dataset.diagramChoice;
    const selected = selections[owner] || selectedByOwner.get(owner) || defaultChoice;
    if (owner && selected) selectedByOwner.set(owner, selected);
    card.classList.toggle("is-selected", card.dataset.diagramChoice === selected);
  });
  activeDiagramBoards.forEach((board) => {
    const owner = board.dataset.activeDiagramOwner;
    const selectedDiagram =
      selections[owner] ||
      selectedByOwner.get(owner) ||
      board.querySelector("[data-diagram-panel]")?.dataset.diagramPanel;
    board.dataset.selectedDiagram = selectedDiagram || "";
    board.querySelectorAll("[data-diagram-panel]").forEach((panel) => {
      const visible = panel.dataset.diagramPanel === selectedDiagram;
      panel.hidden = !visible;
      panel.classList.toggle("is-selected", visible);
      panel.setAttribute("aria-hidden", String(!visible));
    });
  });
}

function selectDiagramChoice(event) {
  const card = event.currentTarget;
  const owner = card.closest("[data-diagram-owner]")?.dataset.diagramOwner;
  if (!owner) return;
  const selections = readJsonStorage(diagramSelectionsStorageKey, {});
  selections[owner] = card.dataset.diagramChoice;
  writeJsonStorage(diagramSelectionsStorageKey, selections);
  applyDiagramSelections();
  if (editStatus) editStatus.textContent = `Selected ${card.textContent.trim()}`;
}

function unlockScrollAfterVideo() {
  document.body.classList.remove("video-locked");
  if (activeLockCleanup) activeLockCleanup();
}

const observer = new IntersectionObserver(
  (entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (!visible) return;
    updateProgress(slides.indexOf(visible.target));
  },
  { threshold: [0.35, 0.6, 0.8] }
);

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      revealObserver.unobserve(entry.target);
    });
  },
  { threshold: 0.18, rootMargin: "0px 0px -12% 0px" }
);

slides.forEach((slide) => observer.observe(slide));
revealItems.forEach((item) => revealObserver.observe(item));
purgeDeprecatedReviewStorage();
applyStoredEdits();
const importedReviewFromHash = applyReviewPacketFromHash();
const importedOwnerFromUrl = applyOwnerFromUrl();
updateProgress(0);
applyPrivateSpeakerVisibility();

startPresentation?.addEventListener("click", unlockAudio);
editPresentation?.addEventListener("click", toggleEditMode);
pinComment?.addEventListener("click", togglePinMode);
cancelPinModeButton?.addEventListener("click", () => setPinMode(false));
speakerOwner?.addEventListener("change", applySpeakerOwnerFilter);
toggleSuggestions?.addEventListener("click", () => {
  updateSuggestionPanel();
  openReviewDrawer();
});
copyEdits?.addEventListener("click", copyEditsJson);
copyReviewMarkdownButton?.addEventListener("click", copyReviewMarkdown);
copyReviewLinkButton?.addEventListener("click", copyReviewLink);
copyTeamHandoff?.addEventListener("click", copyTeamHandoffMessage);
markSpeakerReadyButton?.addEventListener("click", markSpeakerReady);
exportReviewPacketButton?.addEventListener("click", exportReviewPacket);
importReviewPacketButton?.addEventListener("click", () => importReviewPacketFile?.click());
importReviewPacketFile?.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) return;
  importReviewPacket(JSON.parse(await file.text()));
});
downloadEditedHtml?.addEventListener("click", downloadEditedHtmlSnapshot);
resetEdits?.addEventListener("click", resetLocalEdits);
closeReviewDrawer?.addEventListener("click", closeDrawer);
savePinComment?.addEventListener("click", savePendingPinComment);
cancelPinComment?.addEventListener("click", cancelPendingPinComment);
suggestionBank?.addEventListener("click", applySuggestionToNotes);
editableNodes.forEach((node) => node.addEventListener("input", persistEdits));
commentSurfaces.forEach((surface) => surface.addEventListener("click", createPinComment));
diagramChoiceCards.forEach((card) => card.addEventListener("click", selectDiagramChoice));

if (reviewEnabledFromUrl) {
  prepareReviewMode();
}
if (importedReviewFromHash && editStatus) {
  editStatus.textContent = "Imported review link";
} else if (importedOwnerFromUrl && editStatus) {
  editStatus.textContent = `Reviewing as ${speakerOwner.options[speakerOwner.selectedIndex].text}. Click Review / Edit to change your section.`;
}

renderCommentPins();
renderCommentList();
applyDiagramSelections();
renderSpeakerConfirmations();
renderReviewFocus();
updateSuggestionPanel();

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && pinMode) {
    event.preventDefault();
    setPinMode(false);
    return;
  }
  if (!["ArrowDown", "ArrowUp", "PageDown", "PageUp"].includes(event.key)) return;
  if (document.body.classList.contains("video-locked")) {
    event.preventDefault();
    return;
  }
  const activeIndex = slides.findIndex((slide) => {
    const rect = slide.getBoundingClientRect();
    return rect.top <= window.innerHeight * 0.35 && rect.bottom >= window.innerHeight * 0.35;
  });
  const currentIndex = activeIndex === -1 ? 0 : activeIndex;
  const delta = event.key === "ArrowDown" || event.key === "PageDown" ? 1 : -1;
  const next = slides[Math.max(0, Math.min(currentIndex + delta, slides.length - 1))];
  event.preventDefault();
  next.scrollIntoView({ behavior: "smooth", block: "start" });
});

window.addEventListener(
  "scroll",
  () => {
    window.cancelAnimationFrame(revealFrame);
    revealFrame = window.requestAnimationFrame(revealSlideInViewport);
  },
  { passive: true }
);

window.addEventListener(
  "wheel",
  (event) => {
    if (!document.body.classList.contains("video-locked")) return;
    event.preventDefault();
  },
  { passive: false }
);

window.addEventListener(
  "touchmove",
  (event) => {
    if (!document.body.classList.contains("video-locked")) return;
    event.preventDefault();
  },
  { passive: false }
);
