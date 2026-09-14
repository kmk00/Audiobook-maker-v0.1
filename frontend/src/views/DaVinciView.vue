<script setup>
import { ref, computed, onMounted, nextTick, watch } from "vue";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "../components/LoadingOverlay.vue";
import { useCharacterStore } from "../stores/characterStore";

const toaster = createToaster({ position: "top-right", duration: 3000 });
const characterStore = useCharacterStore();

// --- Krok 1: audio ---
const audioFile = ref(null);
const audioUrl = ref(null);
const language = ref("en");

const handleAudioUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;
  audioFile.value = file;
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
  audioUrl.value = URL.createObjectURL(file);
};

// --- Krok 2: skrypt (opcjonalny) ---
const rawInput = ref("");
const isParsed = ref(false);
const blocks = ref([]);
const blockRefs = ref([]);

const setBlockRef = (el, index) => {
  if (el) blockRefs.value[index] = el;
};

const parseText = () => {
  if (!rawInput.value.trim()) {
    toaster.warning("Wklej najpierw tekst skryptu!");
    return;
  }

  const newBlocks = [];
  let currentNarratorText = "";

  const pushNarrator = () => {
    if (currentNarratorText.trim()) {
      newBlocks.push({
        id: Date.now() + Math.random(),
        type: "narrator",
        characterNameOriginal: "Narrator",
        characterId: null,
        characterName: "Narrator",
        avatar: null,
        text: currentNarratorText.trim(),
      });
      currentNarratorText = "";
    }
  };

  const dialogRegex = /^([^:]+):\s*\[(.*?)\]?$/;

  rawInput.value.split("\n").forEach((line) => {
    const match = line.trim().match(dialogRegex);
    if (match) {
      pushNarrator();
      const charName = match[1].trim();
      let dialogText = match[2].trim();
      if (line.trim().endsWith("]") && dialogText.endsWith("]")) {
        dialogText = dialogText.slice(0, -1);
      }
      newBlocks.push({
        id: Date.now() + Math.random(),
        type: "dialogue",
        characterNameOriginal: charName,
        characterId: null,
        characterName: `${charName} (Nieprzypisany)`,
        avatar: null,
        text: dialogText,
      });
    } else {
      currentNarratorText += line + "\n";
    }
  });

  pushNarrator();
  blocks.value = newBlocks;
  isParsed.value = true;
  adjustAllTextareas();
  toaster.success("Skrypt został przeanalizowany!");
};

const resetParser = () => {
  if (
    confirm(
      "Czy na pewno chcesz zresetować skrypt? Utracisz wszystkie przypisania.",
    )
  ) {
    isParsed.value = false;
    blocks.value = [];
    rawInput.value = "";
  }
};

// --- Wybór postaci (lokalny "aktywny" wybór jak sidebar w GENEROWANIU) ---
const activeCharacter = ref(null);
const selectCharacter = (character) => {
  activeCharacter.value = character;
};

const detectedCharacters = computed(() => {
  const charMap = {};
  blocks.value.forEach((block, index) => {
    const name = block.characterNameOriginal;
    if (!charMap[name]) {
      charMap[name] = {
        name,
        count: 0,
        isAssigned: false,
        assignedName: null,
        assignedAvatar: null,
        firstOccurrenceIndex: index,
      };
    }
    charMap[name].count += 1;
    if (block.characterId) {
      charMap[name].isAssigned = true;
      charMap[name].assignedName = block.characterName;
      charMap[name].assignedAvatar = block.avatar;
    }
  });
  return Object.values(charMap).sort((a, b) => {
    if (a.name === "Narrator") return -1;
    if (b.name === "Narrator") return 1;
    return b.count - a.count;
  });
});

const assignCharacterToRole = (originalName) => {
  if (!activeCharacter.value) {
    toaster.warning("Najpierw wybierz postać z listy poniżej!");
    return;
  }
  let assignedCount = 0;
  blocks.value.forEach((block) => {
    if (block.characterNameOriginal === originalName) {
      block.characterId = activeCharacter.value.id;
      block.characterName = activeCharacter.value.name;
      block.avatar = activeCharacter.value.avatar_path;
      assignedCount++;
    }
  });
  toaster.success(
    `Przypisano ${activeCharacter.value.name} do ${assignedCount} kwestii roli: ${originalName}`,
  );
};

const scrollToBlock = (index) => {
  const el = blockRefs.value[index];
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.classList.add("highlight-flash");
    setTimeout(() => el.classList.remove("highlight-flash"), 1500);
  }
};

const adjustAllTextareas = () => {
  nextTick(() => {
    document.querySelectorAll(".invisible-textarea").forEach((ta) => {
      ta.style.height = "auto";
      ta.style.height = ta.scrollHeight + "px";
    });
  });
};

watch(blocks, () => adjustAllTextareas(), { deep: true });

const getAvatarUrl = (path) => {
  if (!path) return "/emilia.png";
  const fixedPath = path.replace("characters/", "static_characters/");
  return `http://127.0.0.1:8000/${fixedPath}`;
};

// --- Krok 3: generowanie timeline'u ---
const isLoading = ref(false);
const loadingText = ref("");
const srtUrl = ref(null);
const fcpxmlUrl = ref(null);

const canGenerate = computed(() => !!audioFile.value);

const pollTaskStatus = (taskId) => {
  const poll = async () => {
    try {
      const res = await fetch(
        `http://127.0.0.1:8000/davinci/task-status/${taskId}`,
      );
      const data = await res.json();

      if (data.status === "completed") {
        isLoading.value = false;
        srtUrl.value = data.srt_url;
        fcpxmlUrl.value = data.fcpxml_url;
        toaster.success("Timeline gotowy! Pobierz SRT i FCPXML.");
      } else if (data.status === "error") {
        isLoading.value = false;
        toaster.error("Błąd: " + data.error);
      } else {
        loadingText.value = data.message || "Przetwarzanie na serwerze...";
        setTimeout(poll, 3000);
      }
    } catch (error) {
      isLoading.value = false;
      toaster.error("Błąd komunikacji z serwerem.");
    }
  };
  poll();
};

const buildTimeline = async () => {
  if (!audioFile.value) {
    toaster.warning("Wrzuć najpierw plik audio!");
    return;
  }

  srtUrl.value = null;
  fcpxmlUrl.value = null;
  isLoading.value = true;
  loadingText.value = "Wysyłanie audio na serwer...";

  const formData = new FormData();
  formData.append("audio", audioFile.value);
  formData.append("language", language.value);
  if (isParsed.value && blocks.value.length > 0) {
    const payload = blocks.value
      .filter((b) => b.text.trim() !== "")
      .map((b) => ({ character_id: b.characterId, text: b.text.trim() }));
    formData.append("blocks", JSON.stringify(payload));
  } else {
    formData.append("blocks", "[]");
  }

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/davinci/build-timeline",
      { method: "POST", body: formData },
    );
    if (!response.ok) {
      const err = await response.json().catch(() => null);
      throw new Error(err?.detail || "Błąd podczas wysyłania audio.");
    }
    const data = await response.json();
    loadingText.value = "Transkrypcja audio (Whisper)...";
    pollTaskStatus(data.task_id);
  } catch (error) {
    isLoading.value = false;
    toaster.error(error.message || "Wystąpił błąd.");
  }
};

onMounted(() => {
  characterStore.fetchCharacters();
});
</script>

<template>
  <div class="davinci-view">
    <LoadingOverlay v-if="isLoading" :text="loadingText" />

    <div class="davinci-layout">
      <div class="main-column">
        <h2 class="view-title">Timeline do DaVinci Resolve</h2>
        <p class="view-desc">
          Wrzuć gotowy plik audio — dostaniesz napisy (SRT) z timestampami oraz
          FCPXML z kartami postaci (nameplates). Opcjonalnie dołącz skrypt w
          formacie <b>Postać: [Dialog]</b> — wtedy napisy powstaną z Twojego
          tekstu (dokładniejsze), a karty przypiszą się automatycznie.
        </p>

        <div class="panel">
          <h3 class="panel-title">1. PLIK AUDIO</h3>
          <label class="upload-box">
            <input type="file" accept="audio/*" @change="handleAudioUpload" />
            <span v-if="!audioFile">Kliknij i wybierz plik audio (mp3/wav…)</span>
            <span v-else class="file-name">{{ audioFile.name }}</span>
          </label>
          <audio
            v-if="audioUrl"
            :src="audioUrl"
            controls
            class="audio-preview"
          ></audio>

          <div class="language-row">
            <label for="lang">Język transkrypcji:</label>
            <select id="lang" v-model="language" class="lang-select">
              <option value="en">Angielski</option>
              <option value="pl">Polski</option>
              <option value="ja">Japoński</option>
              <option value="de">Niemiecki</option>
              <option value="fr">Francuski</option>
              <option value="es">Hiszpański</option>
            </select>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">2. SKRYPT (OPCJONALNIE)</h3>

          <div v-if="!isParsed">
            <textarea
              v-model="rawInput"
              class="raw-textarea"
              placeholder="Heinkel: [Allow me to be your Knight, Miss Flóre.]&#10;W paddingu między kwestiami zwykły tekst = narrator..."
            ></textarea>
            <button class="nav-btn parse-btn" @click="parseText">
              ANALIZUJ SKRYPT
            </button>
            <p class="hint">
              Bez skryptu napisy powstaną z transkrypcji Whispera, a całość
              zostanie oznaczona jako narrator (bez nameplates postaci).
            </p>
          </div>

          <div v-else class="parsed-editor">
            <div class="editor-header">
              <h4>Skrypt ({{ blocks.length }} bloków)</h4>
              <button class="nav-btn small-btn" @click="resetParser">
                Resetuj
              </button>
            </div>
            <div class="seamless-textarea-container">
              <div
                class="text-segment-wrapper"
                v-for="(block, index) in blocks"
                :key="block.id"
                :ref="(el) => setBlockRef(el, index)"
              >
                <div class="speaker-wrapper">
                  <div
                    v-if="block.characterId && block.text.trim() !== ''"
                    class="mini-diamond-inner"
                  >
                    <img :src="getAvatarUrl(block.avatar)" alt="" />
                  </div>
                  <div
                    class="inline-speaker-tag"
                    :class="{ 'narrator-tag': block.type === 'narrator' }"
                  >
                    <span class="speaker-name">
                      {{ block.characterName.toUpperCase() }}
                      <span v-if="block.characterId" class="assigned-mark">✔</span>
                    </span>
                    <button
                      v-if="!block.characterId && activeCharacter"
                      class="quick-assign-btn"
                      title="Przypisz wybraną postać tylko do tej kwestii"
                      @click="
                        block.characterId = activeCharacter.id;
                        block.characterName = activeCharacter.name;
                        block.avatar = activeCharacter.avatar_path;
                      "
                    >
                      +
                    </button>
                    <button
                      v-if="block.characterId"
                      class="remove-speaker-btn"
                      title="Usuń przypisanie"
                      @click="
                        block.characterId = null;
                        block.characterName = `${block.characterNameOriginal} (Nieprzypisany)`;
                        block.avatar = null;
                      "
                    >
                      ✖
                    </button>
                  </div>
                </div>
                <textarea
                  v-model="block.text"
                  class="invisible-textarea"
                  @input="adjustAllTextareas"
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">3. GENERUJ</h3>
          <button
            class="nav-btn generate-btn"
            :disabled="!canGenerate || isLoading"
            @click="buildTimeline"
          >
            BUDUJ TIMELINE (SRT + FCPXML)
          </button>

          <div v-if="srtUrl || fcpxmlUrl" class="results">
            <a v-if="srtUrl" :href="srtUrl" download class="nav-btn result-btn">
              ⬇ POBIERZ SRT
            </a>
            <a
              v-if="fcpxmlUrl"
              :href="fcpxmlUrl"
              download
              class="nav-btn result-btn"
            >
              ⬇ POBIERZ FCPXML (NAMEPLATES)
            </a>
          </div>
        </div>
      </div>

      <div class="side-column">
        <div class="casting-panel">
          <h3>OBSADA ({{ detectedCharacters.length }})</h3>
          <p class="casting-desc">
            Wybierz postać z listy poniżej, a następnie przypisz ją do roli ze
            skryptu.
          </p>

          <div
            v-if="isParsed && detectedCharacters.length"
            class="detected-list"
          >
            <div
              class="detected-item"
              v-for="char in detectedCharacters"
              :key="char.name"
              :class="{ 'is-assigned': char.isAssigned }"
            >
              <div class="detected-info">
                <strong>{{ char.name }}</strong>
                <span class="line-count">{{ char.count }} bloków</span>
              </div>
              <div class="detected-actions">
                <div v-if="char.isAssigned" class="assigned-badge">
                  <img
                    :src="getAvatarUrl(char.assignedAvatar)"
                    class="micro-avatar"
                  />
                  ✔
                </div>
                <button
                  v-else
                  class="nav-btn casting-btn"
                  @click="assignCharacterToRole(char.name)"
                >
                  Przypisz
                </button>
                <button
                  class="jump-btn"
                  @click="scrollToBlock(char.firstOccurrenceIndex)"
                  title="Skocz do pierwszej kwestii"
                >
                  🔍
                </button>
              </div>
            </div>
          </div>
          <p v-else class="casting-desc">
            Panel obsady aktywny po analizie skryptu.
          </p>

          <h4 class="chars-title">POSTACIE</h4>
          <div class="chars-grid">
            <button
              v-for="character in characterStore.characters"
              :key="character.id"
              class="char-diamond"
              :class="{ active: activeCharacter?.id === character.id }"
              :title="character.name"
              @click="selectCharacter(character)"
            >
              <img :src="getAvatarUrl(character.avatar_path)" alt="" />
            </button>
          </div>
          <p v-if="activeCharacter" class="active-char-name">
            Wybrano: <b>{{ activeCharacter.name }}</b>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.davinci-view {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px;
  position: relative;
}
.davinci-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}
.main-column {
  flex: 2;
  min-width: 0;
}
.view-title {
  font-family: var(--font-bitroad);
  color: var(--col-brown);
  margin-bottom: 5px;
}
.view-desc {
  color: var(--col-dark);
  font-family: var(--font-breite);
  margin-bottom: 20px;
}

.panel {
  background-color: var(--col-lbrown);
  border: 3px solid var(--col-brown);
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 20px;
}
.panel-title {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  margin: 0 0 15px 0;
}

.upload-box {
  display: block;
  border: 2px dashed var(--col-brown);
  border-radius: 10px;
  padding: 25px;
  text-align: center;
  cursor: pointer;
  color: var(--col-brown);
  font-family: var(--font-breite);
  background-color: var(--col-light);
}
.upload-box:hover {
  border-color: var(--col-orange);
}
.upload-box input {
  display: none;
}
.file-name {
  color: var(--col-orange);
  font-weight: bold;
}
.audio-preview {
  width: 100%;
  margin-top: 15px;
  border-radius: 20px;
  outline: none;
}
.language-row {
  margin-top: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-breite);
  color: var(--col-dark);
}
.lang-select {
  padding: 5px 10px;
  border-radius: 6px;
  border: 2px solid var(--col-brown);
  background: var(--col-light);
  font-family: var(--font-breite);
}

.raw-textarea {
  width: 100%;
  height: 200px;
  border-radius: 14px;
  border: 3px solid var(--col-brown);
  padding: 15px;
  font-family: var(--font-breite);
  font-size: 1.05rem;
  resize: vertical;
  background-color: var(--col-light);
  margin-bottom: 15px;
  box-sizing: border-box;
}
.parse-btn {
  font-size: 1rem;
  padding: 10px 25px;
  background-color: var(--col-orange);
  color: var(--col-light);
  border-color: var(--col-dark);
}
.hint {
  font-size: 0.85rem;
  color: var(--col-brown);
  margin-top: 10px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.editor-header h4 {
  margin: 0;
  font-family: var(--font-bitroad);
  color: var(--col-brown);
}
.seamless-textarea-container {
  max-height: 400px;
  overflow-y: auto;
  background-color: var(--col-light);
  border: 2px solid var(--col-brown);
  border-radius: 10px;
  padding: 15px;
}
.text-segment-wrapper {
  display: flex;
  flex-direction: column;
  transition: background-color 0.5s ease;
}
.highlight-flash {
  background-color: rgba(255, 165, 0, 0.3);
  border-radius: 8px;
}
.speaker-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}
.inline-speaker-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  background-color: var(--col-lbrown);
  color: var(--col-brown);
  padding: 3px 10px;
  border-radius: 6px;
  font-family: var(--font-bitroad);
  font-size: 0.8rem;
  font-weight: 800;
  margin-bottom: 2px;
}
.narrator-tag {
  background-color: transparent;
  border: 1px dashed var(--col-brown);
}
.assigned-mark {
  color: var(--col-orange);
}
.quick-assign-btn {
  background: var(--col-brown);
  color: var(--col-light);
  border: none;
  border-radius: 4px;
  cursor: pointer;
  padding: 0 5px;
  font-weight: bold;
}
.remove-speaker-btn {
  background: none;
  border: none;
  color: var(--col-dark);
  cursor: pointer;
  font-size: 0.8rem;
}
.mini-diamond-inner {
  width: 36px;
  height: 36px;
  transform: rotate(45deg);
  background: var(--col-brown);
  border: 2px solid var(--col-light);
  overflow: hidden;
  flex-shrink: 0;
}
.mini-diamond-inner img {
  width: 100%;
  height: 100%;
  transform: rotate(-45deg) scale(1.4);
  object-fit: cover;
}
.invisible-textarea {
  width: 100%;
  background: transparent;
  border: none;
  resize: none;
  font-family: var(--font-breite), sans-serif;
  font-size: 1.1rem;
  color: var(--col-dark);
  overflow: hidden;
  padding: 0;
  margin: 0;
  line-height: 1.5;
}
.invisible-textarea:focus {
  outline: none;
}

.generate-btn {
  font-size: 1.1rem;
  padding: 12px 30px;
  background-color: var(--col-orange);
  color: var(--col-light);
  border-color: var(--col-dark);
}
.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.results {
  margin-top: 20px;
  display: flex;
  gap: 15px;
}
.result-btn {
  background-color: var(--col-brown);
  color: var(--col-light);
  text-decoration: none;
}

.side-column {
  flex: 1;
  min-width: 300px;
}
.casting-panel {
  background-color: var(--col-lbrown);
  border: 3px solid var(--col-brown);
  border-radius: 14px;
  padding: 20px;
  position: sticky;
  top: 20px;
}
.casting-panel h3 {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  margin: 0 0 5px 0;
}
.casting-desc {
  font-size: 0.85rem;
  color: var(--col-brown);
  margin-bottom: 15px;
}
.detected-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}
.detected-item {
  background-color: var(--col-light);
  border: 2px solid var(--col-brown);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detected-item.is-assigned {
  border-color: var(--col-orange);
}
.detected-info strong {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  display: block;
}
.line-count {
  font-size: 0.8rem;
  color: var(--col-brown);
}
.detected-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.casting-btn {
  font-size: 0.8rem;
  padding: 4px 10px;
}
.jump-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
}
.assigned-badge {
  display: flex;
  align-items: center;
  color: var(--col-orange);
  font-weight: bold;
}
.micro-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  border: 1px solid var(--col-orange);
}
.chars-title {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  margin: 15px 0 10px 0;
}
.chars-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.char-diamond {
  width: 52px;
  height: 52px;
  transform: rotate(45deg);
  border: 2px solid var(--col-brown);
  background: var(--col-brown);
  overflow: hidden;
  cursor: pointer;
  padding: 0;
}
.char-diamond img {
  width: 100%;
  height: 100%;
  transform: rotate(-45deg) scale(1.4);
  object-fit: cover;
}
.char-diamond.active {
  border-color: var(--col-orange);
  box-shadow: 0 0 0 3px var(--col-orange);
}
.active-char-name {
  margin-top: 12px;
  font-family: var(--font-breite);
  color: var(--col-dark);
}
</style>
