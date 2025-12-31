const messageEl = document.getElementById("message");
const boardEl = document.getElementById("board");
const redThoughtsEl = document.getElementById("red-thoughts");
const blueThoughtsEl = document.getElementById("blue-thoughts");
const humanRow = document.getElementById("human-row");
const moveBtn = document.getElementById("move-btn");
const runBtn = document.getElementById("run-btn");
const resetBtn = document.getElementById("reset-btn");
const redModel = document.getElementById("red-model");
const blueModel = document.getElementById("blue-model");
const variantSelect = document.getElementById("variant");
const ratingsBody = document.getElementById("ratings-body");
const resultsBody = document.getElementById("results-body");

// Variable pour stocker le dernier état
let lastState = null;

const tabButtons = document.querySelectorAll(".tab-button");
const tabPanels = document.querySelectorAll(".tab-panel");

const showLoading = (player = null) => {
  if (player === "red") {
    messageEl.innerHTML = '<div class="status">🤔 <strong style="color: var(--bs-danger);">Joueur Rouge</strong> réfléchit...</div>';
  } else if (player === "blue") {
    messageEl.innerHTML = '<div class="status">🤔 <strong style="color: var(--bs-primary);">Joueur Bleu</strong> réfléchit...</div>';
  } else {
    messageEl.innerHTML = '<div class="status">🤔 Réflexion en cours...</div>';
  }
};

const apiPost = async (path, payload) => {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  return res.json();
};

const apiGet = async (path) => {
  const res = await fetch(path);
  return res.json();
};

const setHumanButtons = (validMoves) => {
  const allowed = new Set(validMoves);
  document.querySelectorAll(".btn-human").forEach((btn) => {
    const move = parseInt(btn.dataset.move, 10);
    btn.hidden = !allowed.has(move);
  });
};

const applyState = (state) => {
  // Sauvegarder l'état actuel
  lastState = state;
  
  boardEl.innerHTML = state.board_html;
  messageEl.innerHTML = state.message_html;
  redThoughtsEl.innerHTML = state.red_thoughts;
  blueThoughtsEl.innerHTML = state.blue_thoughts;

  humanRow.hidden = !state.show_human;
  setHumanButtons(state.valid_moves || []);

  moveBtn.disabled = !state.can_move;
  runBtn.disabled = !state.can_run;

  redModel.value = state.red_model || redModel.value;
  blueModel.value = state.blue_model || blueModel.value;
  variantSelect.value = state.variant || variantSelect.value;

  const dropdownsEnabled = !!state.dropdowns_enabled;
  redModel.disabled = !dropdownsEnabled;
  blueModel.disabled = !dropdownsEnabled;
  variantSelect.disabled = !dropdownsEnabled;
};

const renderTable = (tbody, rows) => {
  tbody.innerHTML = "";
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
};

const initGame = async () => {
  const state = await apiPost("/api/init", {
    red_model: redModel.value || DEFAULTS.red,
    blue_model: blueModel.value || DEFAULTS.blue,
    variant: variantSelect.value || DEFAULTS.variant,
  });
  applyState(state);
};

const loadLeaderboard = async () => {
  const data = await apiGet("/api/leaderboard");
  renderTable(ratingsBody, data.ratings || []);
  renderTable(resultsBody, data.results || []);
};

moveBtn.addEventListener("click", async () => {
  moveBtn.disabled = true;
  // Utiliser l'état précédent pour savoir qui va jouer
  if (lastState && lastState.current_player) {
    showLoading(lastState.current_player);
  } else {
    showLoading();
  }
  
  const state = await apiPost("/api/move");
  applyState(state);
});

runBtn.addEventListener("click", async () => {
  runBtn.disabled = true;
  moveBtn.disabled = true;
  resetBtn.disabled = true;
  
  // Récupérer l'état actuel (ne pas réinitialiser)
  let state = lastState;
  
  // Si pas d'état (première partie), initialiser
  if (!state) {
    state = await apiPost("/api/init", {
      red_model: redModel.value,
      blue_model: blueModel.value,
      variant: variantSelect.value,
    });
    applyState(state);
  }
  
  // Jouer tour par tour avec mise à jour visuelle
  while (!state.game_over) {
    // Forcer les boutons à rester désactivés pendant le jeu automatique
    runBtn.disabled = true;
    moveBtn.disabled = true;
    resetBtn.disabled = true;
    
    // Afficher qui réfléchit
    showLoading(state.current_player);
    
    await new Promise(resolve => setTimeout(resolve, 500)); // Pause de 500ms entre chaque coup
    state = await apiPost("/api/move");
    applyState(state);
    
    // Si c'est un joueur humain, on arrête
    if (state.show_human) {
      break;
    }
  }
  
  // Réactiver le bouton reset à la fin
  resetBtn.disabled = false;
});

resetBtn.addEventListener("click", async () => {
  const state = await apiPost("/api/reset", {
    red_model: redModel.value,
    blue_model: blueModel.value,
    variant: variantSelect.value,
  });
  applyState(state);
});

document.querySelectorAll(".btn-human").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const move = parseInt(btn.dataset.move, 10);
    const state = await apiPost("/api/human-move", { move });
    applyState(state);
  });
});

redModel.addEventListener("change", async () => {
  const state = await apiPost("/api/model", { player: "red", model: redModel.value });
  applyState(state);
});

blueModel.addEventListener("change", async () => {
  const state = await apiPost("/api/model", { player: "blue", model: blueModel.value });
  applyState(state);
});

variantSelect.addEventListener("change", async () => {
  const state = await apiPost("/api/variant", { variant: variantSelect.value });
  applyState(state);
});

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    tabButtons.forEach((btn) => btn.classList.remove("is-active"));
    tabPanels.forEach((panel) => panel.classList.remove("is-active"));
    button.classList.add("is-active");
    const target = document.getElementById(`tab-${button.dataset.tab}`);
    if (target) {
      target.classList.add("is-active");
    }
    if (button.dataset.tab === "leaderboard") {
      loadLeaderboard();
    }
  });
});

initGame();

// Script pour communiquer la hauteur au parent (blog)
const sendHeightToParent = () => {
  const height = document.documentElement.scrollHeight;
  window.parent.postMessage({ type: 'nim-resize', height }, '*');
};

// Envoi initial
sendHeightToParent();

// Observer les changements du DOM
const resizeObserver = new ResizeObserver(() => {
  sendHeightToParent();
});

resizeObserver.observe(document.body);
