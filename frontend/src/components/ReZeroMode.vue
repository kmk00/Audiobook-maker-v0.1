<script setup>
import { ref, computed, nextTick, watch } from "vue";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "./LoadingOverlay.vue";
import { useAudiobookStore } from "../stores/audiobookStore";
import GenerateBottomBar from "./GenerateBottomBar.vue";

const props = defineProps({
  activeCharacter: Object,
});

const toaster = createToaster({ position: "top-right", duration: 3000 });
const audiobookStore = useAudiobookStore();

const isLoading = ref(false);
const loadingText = ref("");
const rawInput = ref("");
const isParsed = ref(false);
const blocks = ref([]);
const blockRefs = ref([]);

const setBlockRef = (el, index) => {
  if (el) {
    blockRefs.value[index] = el;
  }
};

const parseText = () => {
  if (!rawInput.value.trim()) {
    toaster.warning("Wklej najpierw tekst rozdziału!");
    return;
  }

  const newBlocks = [];
  const lines = rawInput.value.split("\n");
  let currentNarratorText = "";

  const pushNarrator = () => {
    if (currentNarratorText.trim()) {
      newBlocks.push({
        id: Date.now() + Math.random(),
        type: "narrator",
        characterNameOriginal: "Narrator",
        characterId: null,
        characterName: "Narrator (Nieprzypisany)",
        avatar: null,
        text: currentNarratorText.trim(),
      });
      currentNarratorText = "";
    }
  };

  const dialogRegex = /^([^:]+):\s*\[(.*?)\]?$/;

  lines.forEach((line) => {
    const match = line.trim().match(dialogRegex);
    if (match) {
      pushNarrator();
      const charName = match[1].trim();
      let dialogText = match[2].trim();
      if (line.trim().endsWith("]") && dialogText.endsWith("]")) {
        dialogText = dialogText.slice(0, -1);
      }

      const hasReadableText = /[\p{L}\p{N}]/u.test(dialogText);
      const isNonVerbal = !hasReadableText;

      newBlocks.push({
        id: Date.now() + Math.random(),
        type: "dialogue",
        characterNameOriginal: charName,
        characterId: null,
        characterName: `${charName} (Nieprzypisany)`,
        avatar: null,
        text: dialogText,
        isNonVerbal: isNonVerbal,
      });
    } else {
      currentNarratorText += line + "\n";
    }
  });

  pushNarrator();
  blocks.value = newBlocks;
  isParsed.value = true;
  adjustAllTextareas();
  toaster.success("Tekst został pomyślnie przeanalizowany!");
};

const detectedCharacters = computed(() => {
  const charMap = {};

  blocks.value.forEach((block, index) => {
    if (block.isNonVerbal) return;

    const name = block.characterNameOriginal;
    if (!charMap[name]) {
      charMap[name] = {
        name: name,
        type: block.type,
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

const unassignedUnknowns = computed(() => {
  return blocks.value
    .map((block, index) => ({ block, index }))
    .filter(
      (item) =>
        item.block.characterId === null &&
        (item.block.isNonVerbal ||
          item.block.characterNameOriginal.includes("?") ||
          item.block.characterNameOriginal.toLowerCase() === "voice"),
    );
});

const assignCharacterToRole = (originalName) => {
  if (!props.activeCharacter) {
    toaster.warning(
      "Wybierz postać z lewego panelu bocznego, by ją przypisać!",
    );
    return;
  }

  let assignedCount = 0;
  blocks.value.forEach((block) => {
    if (block.characterNameOriginal === originalName) {
      block.characterId = props.activeCharacter.id;
      block.characterName = props.activeCharacter.name;
      block.avatar = props.activeCharacter.avatar_path;
      assignedCount++;
    }
  });

  toaster.success(
    `Przypisano ${props.activeCharacter.name} do ${assignedCount} kwestii roli: ${originalName}`,
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

const resetParser = () => {
  if (
    confirm(
      "Czy na pewno chcesz zresetować i wkleić nowy tekst? Utracisz wszystkie przypisania.",
    )
  ) {
    isParsed.value = false;
    blocks.value = [];
    rawInput.value = "";
  }
};

// const pollTaskStatus = async (taskId) => {
//   try {
//     const res = await fetch(`http://127.0.0.1:8000/tts/task-status/${taskId}`);
//     const data = await res.json();

//     if (data.status === "completed") {
//       isLoading.value = false;
//       generatedAudioUrl.value = data.file_url;
//       toaster.success("Rozdział wygenerowany pomyślnie!");
//     } else if (data.status === "error") {
//       isLoading.value = false;
//       toaster.error("Błąd podczas generowania: " + data.error);
//     } else {
//       loadingText.value = data.message || "Trwa przetwarzanie na serwerze...";
//       setTimeout(() => pollTaskStatus(taskId), 3000);
//     }
//   } catch (error) {
//     isLoading.value = false;
//     toaster.error("Błąd komunikacji z serwerem sprawdzającym status.");
//   }
// };

// const generateAudiobook = async () => {
//   const validBlocks = blocks.value.filter((b) => b.text.trim() !== "");

//   if (validBlocks.length === 0) {
//     toaster.warning("Brak tekstu do wygenerowania!");
//     return;
//   }

//   const unassignedCount = validBlocks.filter((b) => !b.characterId).length;
//   if (unassignedCount > 0) {
//     if (
//       !confirm(
//         `Masz ${unassignedCount} nieprzypisanych kwestii (Zostaną przeczytane przez domyślnego Narratora). Chcesz kontynuować?`,
//       )
//     ) {
//       return;
//     }
//   }

//   const payload = {
//     mode: "rezero",
//     blocks: validBlocks.map((block) => ({
//       character_id: block.characterId,
//       text: block.text.trim(),
//     })),
//   };

//   isLoading.value = true;
//   loadingText.value = "Zlecanie zadania na serwer... Czekaj!";
//   generatedAudioUrl.value = null;

//   try {
//     const response = await fetch(
//       "http://127.0.0.1:8000/tts/generate-audiobook",
//       {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//       },
//     );

//     if (!response.ok) {
//       const err = await response.json();
//       throw new Error(err.detail || "Błąd podczas zlecania audiobooka.");
//     }

//     const data = await response.json();
//     pollTaskStatus(data.task_id);
//   } catch (error) {
//     isLoading.value = false;
//     toaster.error(error.message || "Wystąpił błąd.");
//   }
// };

const adjustAllTextareas = () => {
  nextTick(() => {
    const textareas = document.querySelectorAll(".invisible-textarea");
    textareas.forEach((ta) => {
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
</script>

<template>
  <div class="mode-container">
    <LoadingOverlay v-if="isLoading" :text="loadingText" />

    <div v-if="!isParsed" class="paste-screen">
      <h2 class="paste-title">Wklej surowy rozdział Re:Zero</h2>
      <p class="paste-subtitle">
        Aplikacja automatycznie rozpozna kwestie w formacie
        <b>Postać: [Dialog]</b>.
      </p>
      <textarea
        v-model="rawInput"
        class="raw-textarea"
        placeholder="Reinhard: […How surprising.]&#10;As if having listened in on Otto’s inner thoughts, Reinhard muttered those words..."
      ></textarea>
      <button class="nav-btn parse-btn" @click="parseText">
        ANALIZUJ TEKST
      </button>
    </div>

    <div v-else class="parsed-screen">
      <div class="editor-area">
        <div class="editor-header">
          <h3>Skrypt Rozdziału</h3>
          <button class="nav-btn small-btn" @click="resetParser">
            Resetuj / Wklej Nowy
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
                class="mini-avatar-container"
              >
                <div class="decor-frame mini-frame-1"></div>
                <div class="decor-frame mini-frame-2"></div>
                <div class="mini-diamond-inner">
                  <img :src="getAvatarUrl(block.avatar)" alt="" />
                </div>
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
                  title="Przypisz aktywną postać tylko do tej kwestii"
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
              :class="[
                'invisible-textarea',
                { 'spacer-textarea': block.text.trim() === '' },
              ]"
              @input="adjustAllTextareas"
            ></textarea>
          </div>
        </div>
      </div>

      <div class="casting-panel">
        <h3>OBSADA ({{ detectedCharacters.length }})</h3>
        <p class="casting-desc">
          Zaznacz postać z lewego paska i przypisz ją do wybranej roli.
        </p>

        <div class="detected-list">
          <div
            class="detected-item"
            v-for="char in detectedCharacters"
            :key="char.name"
            :class="{ 'is-assigned': char.isAssigned }"
          >
            <div class="detected-info">
              <strong>{{ char.name }}</strong>
              <span class="line-count">{{ char.count }} bloków tekstu</span>
            </div>

            <div class="detected-actions">
              <div
                v-if="char.isAssigned"
                class="assigned-badge"
                :title="`Przypisano lektora: ${char.assignedName}`"
              >
                <img
                  :src="getAvatarUrl(char.assignedAvatar)"
                  class="micro-avatar"
                />
                ✔ Zrobione
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

        <div v-if="unassignedUnknowns.length > 0" class="unknowns-section">
          <h4 class="unknown-title">⚠️ Wymaga uwagi:</h4>
          <div class="unknown-list">
            <button
              v-for="item in unassignedUnknowns"
              :key="item.index"
              class="unknown-jump-btn"
              @click="scrollToBlock(item.index)"
            >
              Skocz do: {{ item.block.characterNameOriginal }}
              <span
                v-if="item.block.isNonVerbal"
                style="color: #d35400; font-weight: bold"
                >[Niewerbalne]</span
              >
              (Linia {{ item.index + 1 }})
            </button>
          </div>
        </div>
      </div>
    </div>

    <GenerateBottomBar :blocks="blocks" mode="rezero" />
  </div>
</template>

<style scoped>
.generate-btn {
  width: 30px;
  height: 30px;
}
.mode-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.paste-screen {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 40px;
  align-items: center;
  justify-content: center;
}
.paste-title {
  font-family: var(--font-bitroad);
  color: var(--col-brown);
  margin-bottom: 5px;
}
.paste-subtitle {
  color: var(--col-dark);
  margin-bottom: 20px;
  font-family: var(--font-breite);
}
.raw-textarea {
  width: 80%;
  height: 60%;
  border-radius: 14px;
  border: 3px solid var(--col-brown);
  padding: 20px;
  font-family: var(--font-breite);
  font-size: 1.1rem;
  resize: none;
  background-color: var(--col-lbrown);
  box-shadow: inset 0 4px 10px rgba(0, 0, 0, 0.05);
  margin-bottom: 30px;
}
.parse-btn {
  font-size: 1.2rem;
  padding: 15px 40px;
  background-color: var(--col-orange);
  color: var(--col-light);
  border-color: var(--col-dark);
}

.parsed-screen {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 20px;
  gap: 20px;
}

.editor-area {
  flex: 2;
  display: flex;
  flex-direction: column;
  background-color: var(--col-light);
  overflow: hidden;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 0 10px;
}
.editor-header h3 {
  margin: 0;
  font-family: var(--font-bitroad);
  color: var(--col-brown);
}

.casting-panel {
  flex: 1;
  background-color: var(--col-lbrown);
  border: 3px solid var(--col-brown);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}
.casting-panel h3 {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  margin: 0 0 5px 0;
}
.casting-desc {
  font-size: 0.85rem;
  color: var(--col-brown);
  margin-bottom: 20px;
}

.detected-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.detected-item {
  background-color: var(--col-light);
  border: 2px solid var(--col-brown);
  border-radius: 10px;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.3s;
}
.detected-item.is-assigned {
  background-color: rgba(60, 42, 33, 0.1);
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
  gap: 5px;
  font-size: 0.8rem;
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

.unknowns-section {
  margin-top: 30px;
  border-top: 2px dashed var(--col-orange);
  padding-top: 15px;
}
.unknown-title {
  color: var(--col-orange);
  font-family: var(--font-bitroad);
  margin-bottom: 10px;
}
.unknown-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.unknown-jump-btn {
  background-color: #ffe8d6;
  border: 1px solid var(--col-orange);
  color: var(--col-dark);
  text-align: left;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  font-family: var(--font-breite);
}
.unknown-jump-btn:hover {
  background-color: var(--col-orange);
  color: white;
}

.seamless-textarea-container {
  flex: 1;
  width: 100%;
  background-color: var(--col-lbrown);
  border: 3px solid var(--col-brown);
  border-radius: 14px;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
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

.inline-speaker-tag {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  background-color: var(--col-light);
  color: var(--col-brown);
  padding: 3px 10px;
  border-radius: 6px;
  font-family: var(--font-bitroad);
  font-size: 0.85rem;
  font-weight: 800;
  margin-bottom: 2px;
}
.narrator-tag {
  background-color: transparent;
  border: 1px dashed var(--col-brown);
}
.assigned-mark {
  color: var(--col-orange);
  margin-left: 5px;
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

.mini-avatar-container {
  width: 60px;
  height: 60px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}
.decor-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: transparent;
  z-index: 1;
}
.mini-frame-1 {
  width: 45px;
  height: 45px;
  border: 2px solid var(--col-brown);
  transform: translate(-50%, -50%) rotate(60deg);
}
.mini-frame-2 {
  width: 45px;
  height: 45px;
  border: 2px solid var(--col-lbrown);
  transform: translate(-50%, -50%) rotate(75deg);
}
.mini-diamond-inner {
  position: relative;
  width: 45px;
  height: 45px;
  transform: rotate(45deg);
  background: var(--col-brown);
  border: 2px solid var(--col-light);
  overflow: hidden;
  box-sizing: border-box;
  z-index: 2;
}
.mini-diamond-inner img {
  width: 100%;
  height: 100%;
  transform: rotate(-45deg) scale(1.4);
  object-fit: cover;
  position: absolute;
  top: 0;
  left: 0;
}
.speaker-wrapper {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
}
.remove-speaker-btn {
  background: none;
  border: none;
  color: var(--col-dark);
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0;
}
.invisible-textarea {
  width: 100%;
  background: transparent;
  border: none;
  resize: none;
  font-family: var(--font-breite), sans-serif;
  font-size: 1.2rem;
  color: var(--col-dark);
  overflow: hidden;
  padding: 0;
  margin: 0;
  line-height: 1.5;
}
.invisible-textarea:focus {
  outline: none;
}
.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
  color: var(--col-brown);
  font-weight: bold;
  cursor: pointer;
}
.generate-bottom-bar {
  height: 120px;
  background-color: var(--col-dark);
  color: var(--col-light);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 0 50px;
  gap: 20px;
  flex-shrink: 0;
}
.generate-bottom-bar h2 {
  font-family: var(--font-bitroad);
  letter-spacing: 2px;
}
.diamond-btn {
  width: 40px;
  height: 40px;
  transform: rotate(45deg);
  background-color: var(--col-brown);
  border: none;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
}
.diamond-btn span {
  transform: rotate(-45deg);
  color: var(--col-light);
  font-weight: bold;
}
.diamond-btn.large {
  width: 60px;
  height: 60px;
  border: 2px solid var(--col-light);
  background: transparent;
}
.spacer-textarea {
  height: 12px !important;
  min-height: 0;
  opacity: 0.3;
  pointer-events: none;
}
.result-player {
  height: 40px;
  border-radius: 20px;
  outline: none;
  border: 2px solid var(--col-orange);
}
</style>
