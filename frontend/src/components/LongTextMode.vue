<script setup>
import { ref, nextTick, watch, onMounted } from "vue";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "../components/LoadingOverlay.vue";
import { useAudiobookStore } from "../stores/audiobookStore";

const toaster = createToaster({ position: "top-right", duration: 3000 });
const audiobookStore = useAudiobookStore();

const props = defineProps({
  activeCharacter: Object,
});

const isLoading = ref(false);
const loadingText = ref("");
const phraseToRemove = ref("");

const textSelection = ref({
  blockIndex: -1,
  start: 0,
  end: 0,
});

const adjustAllTextareas = () => {
  nextTick(() => {
    const textareas = document.querySelectorAll(".invisible-textarea");
    textareas.forEach((ta) => {
      ta.style.height = "auto";
      ta.style.height = ta.scrollHeight + "px";
    });
  });
};

watch(
  () => audiobookStore.longTextBlocks,
  () => {
    adjustAllTextareas();
  },
  { deep: true },
);

onMounted(() => {
  adjustAllTextareas();
});

const cleanupAndMergeBlocks = () => {
  const blocks = audiobookStore.longTextBlocks;

  for (let i = blocks.length - 1; i >= 0; i--) {
    if (blocks[i].text.length === 0) {
      blocks.splice(i, 1);
    }
  }

  for (let i = blocks.length - 1; i > 0; i--) {
    const current = blocks[i];
    const prev = blocks[i - 1];

    if (current.characterId === prev.characterId) {
      prev.text += current.text;
      blocks.splice(i, 1);
    }
  }

  if (blocks.length === 0) {
    audiobookStore.setLongText("");
  }

  adjustAllTextareas();
};

const handleSelect = (event, index) => {
  const start = event.target.selectionStart;
  const end = event.target.selectionEnd;

  if (start !== end) {
    textSelection.value = { blockIndex: index, start, end };
  } else {
    textSelection.value = { blockIndex: -1, start: 0, end: 0 };
  }
};

const handleKeyDown = (event, index) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();

    const start = event.target.selectionStart;
    const end = event.target.selectionEnd;

    if (start !== end) {
      textSelection.value = { blockIndex: index, start, end };
      assignSelectionToCharacter();
    } else {
      toaster.warning("Najpierw zaznacz fragment tekstu!");
    }
  }
};

const assignSelectionToCharacter = () => {
  if (!props.activeCharacter) {
    toaster.warning("Wybierz najpierw postać z lewego panelu!");
    return;
  }

  const { blockIndex, start, end } = textSelection.value;
  if (blockIndex === -1) return;

  const targetBlock = audiobookStore.longTextBlocks[blockIndex];
  const fullText = targetBlock.text;

  const textBefore = fullText.substring(0, start);
  const textSelected = fullText.substring(start, end);
  const textAfter = fullText.substring(end);

  if (textSelected.trim() === "") {
    toaster.warning("Zaznacz fragment zawierający tekst, a nie same odstępy!");
    return;
  }

  const newBlocks = [];

  if (textBefore.length > 0) {
    newBlocks.push({
      ...targetBlock,
      id: Date.now() + Math.random(),
      text: textBefore.replace(/\n+$/, "\n"),
    });
  }

  newBlocks.push({
    id: Date.now() + Math.random(),
    characterId: props.activeCharacter.id,
    characterName: props.activeCharacter.name,
    avatar: props.activeCharacter.avatar_path,
    text: textSelected,
  });

  if (textAfter.length > 0) {
    newBlocks.push({
      ...targetBlock,
      id: Date.now() + Math.random(),
      text: textAfter.replace(/^\n+/, "\n"),
    });
  }

  audiobookStore.longTextBlocks.splice(blockIndex, 1, ...newBlocks);
  textSelection.value = { blockIndex: -1, start: 0, end: 0 };

  cleanupAndMergeBlocks();
  toaster.success(`Przypisano do: ${props.activeCharacter.name}`);
};

const unassignBlock = (index) => {
  audiobookStore.longTextBlocks[index].characterId = null;
  audiobookStore.longTextBlocks[index].characterName =
    "Narrator / Brak przypisania";
  audiobookStore.longTextBlocks[index].avatar = null;
  cleanupAndMergeBlocks();
};

const removePhrase = () => {
  if (!phraseToRemove.value) return;

  const escapedPhrase = phraseToRemove.value.replace(
    /[.*+?^${}()|[\]\\]/g,
    "\\$&",
  );
  const regex = new RegExp(escapedPhrase, "gi");

  audiobookStore.longTextBlocks.forEach((block) => {
    let newText = block.text.replace(regex, "");

    newText = newText.replace(/ {2,}/g, " ").replace(/\n{3,}/g, "\n\n");
    block.text = newText;
  });

  cleanupAndMergeBlocks();
  toaster.success(`Usunięto wszystkie wystąpienia: "${phraseToRemove.value}"`);
  phraseToRemove.value = "";
};

const uploadAndExtractText = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  isLoading.value = true;
  loadingText.value = `Wyciąganie tekstu z pliku ${file.name}...`;

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/audiobook_utils/extract-text",
      {
        method: "POST",
        body: formData,
      },
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Błąd serwera.");
    }

    const extractedText = data.text ? String(data.text) : "";
    audiobookStore.setLongText(extractedText);

    if (extractedText !== "") {
      toaster.success("Tekst pomyślnie załadowany!");
    } else {
      toaster.warning("Plik jest pusty.");
    }
  } catch (error) {
    toaster.error(error.message || "Błąd ładowania pliku.");
  } finally {
    isLoading.value = false;
    event.target.value = "";
  }
};

const generateAudiobook = () => {
  const validBlocks = audiobookStore.longTextBlocks.filter(
    (b) => b.text.trim() !== "",
  );

  if (validBlocks.length === 0) {
    toaster.warning("Brak tekstu do wygenerowania!");
    return;
  }

  const payload = {
    mode: "longtext",
    blocks: validBlocks.map((block) => ({
      character_id: block.characterId,
      text: block.text.trim(),
    })),
  };

  console.log("🚀 GOTOWY JSON Z LONG TEXT:", JSON.stringify(payload, null, 2));
  toaster.success("JSON z długim tekstem gotowy. Sprawdź konsolę!");
};

const getAvatarUrl = (path) => {
  if (!path) return "/emilia.png";
  const fixedPath = path.replace("characters/", "static_characters/");
  return `http://127.0.0.1:8000/${fixedPath}`;
};
</script>

<template>
  <div class="mode-container">
    <LoadingOverlay v-if="isLoading" :text="loadingText" />

    <div class="assign-bar" v-if="textSelection.blockIndex !== -1">
      <p v-if="!activeCharacter" class="warning-text">
        Wybierz postać z listy, aby przypisać tekst!
      </p>
      <div class="assign-actions" v-else>
        <span class="shortcut-hint">Zaznacz i kliknij <b>Ctrl + S</b></span>
        <button class="nav-btn assign-btn" @click="assignSelectionToCharacter">
          PRZYPISZ ZAZNACZENIE DO:
          <span class="highlight-name">{{
            activeCharacter.name.toUpperCase()
          }}</span>
        </button>
      </div>
    </div>

    <div class="editor-area">
      <div class="file-upload-section">
        <div class="file-upload-wrapper">
          <label for="txt-upload" class="nav-btn file-label"> TXT </label>
          <input
            type="file"
            id="txt-upload"
            accept=".txt"
            @change="uploadAndExtractText"
            hidden
          />
        </div>
        <div class="file-upload-wrapper">
          <label for="pdf-upload" class="nav-btn file-label"> PDF </label>
          <input
            type="file"
            id="pdf-upload"
            accept=".pdf"
            @change="uploadAndExtractText"
            hidden
          />
        </div>
        <div class="file-upload-wrapper">
          <label for="epub-upload" class="nav-btn file-label"> EPUB </label>
          <input
            type="file"
            id="epub-upload"
            accept=".epub"
            @change="uploadAndExtractText"
            hidden
          />
        </div>
      </div>

      <div
        class="cleanup-toolkit"
        v-if="audiobookStore.longTextBlocks[0]?.text !== ''"
      >
        <input
          type="text"
          v-model="phraseToRemove"
          placeholder="Wpisz tekst do usunięcia (np. 'Page|1', link, tytuł książki)..."
          @keydown.enter.prevent="removePhrase"
          class="cleanup-input"
        />
        <button class="nav-btn cleanup-btn" @click="removePhrase">🧹</button>
      </div>

      <div class="seamless-textarea-container">
        <div
          class="text-segment-wrapper"
          v-for="(block, index) in audiobookStore.longTextBlocks"
          :key="block.id"
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
              v-if="block.characterId && block.text.trim() !== ''"
            >
              <span class="speaker-name">{{
                block.characterName.toUpperCase()
              }}</span>
              <button
                class="remove-speaker-btn"
                title="Usuń przypisanie"
                @click="unassignBlock(index)"
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
            @select="handleSelect($event, index)"
            @keyup="handleSelect($event, index)"
            @mouseup="handleSelect($event, index)"
            @keydown="handleKeyDown($event, index)"
            @input="adjustAllTextareas"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="generate-bottom-bar">
      <h2>WYGENERUJ AUDIOBOOK (LONG TEXT)</h2>
      <button
        class="generate-action-btn diamond-btn large"
        @click="generateAudiobook"
      >
        <span>🎶</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Zostaw tu wszystkie swoje style bez zmian (identyczne jak w Twoim kodzie) */
.mode-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  position: relative;
}
.assign-bar {
  background-color: var(--col-orange);
  padding: 10px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  z-index: 10;
}
.assign-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
.shortcut-hint {
  font-family: var(--font-breite);
  font-size: 0.9rem;
  color: var(--col-light);
  opacity: 0.9;
}
.warning-text {
  margin: 0;
  font-family: var(--font-bitroad);
  color: var(--col-light);
  font-size: 1.1rem;
}
.assign-btn {
  background-color: var(--col-dark) !important;
  color: var(--col-light);
  border-color: var(--col-light) !important;
  font-size: 1.1rem;
}
.assign-btn:hover {
  background-color: var(--col-light) !important;
  color: var(--col-orange);
}
.highlight-name {
  color: var(--col-orange);
}
.editor-area {
  flex: 1;
  padding: 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow: hidden;
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
}
.inline-speaker-tag {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background-color: var(--col-light);
  color: var(--col-brown);
  padding: 3px 10px;
  border-radius: 6px;
  font-family: var(--font-bitroad);
  font-size: 0.85rem;
  font-weight: 800;
  margin-bottom: 2px;
  user-select: none;
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
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.8;
  transition: opacity 0.2s;
}
.remove-speaker-btn:hover {
  opacity: 1;
  color: var(--col-dark);
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
.file-upload-section {
  display: flex;
  justify-content: flex-end;
  gap: 20px;
}
.file-upload-wrapper {
  display: flex;
  justify-content: flex-end;
}
.file-label {
  display: inline-block;
  cursor: pointer;
  transition: all 0.2s;
}
.file-label:hover {
  background-color: var(--col-brown);
  color: var(--col-light);
}
.cleanup-toolkit {
  display: flex;
  gap: 10px;
  background-color: rgba(213, 206, 163, 0.3);
  padding: 10px;
  border-radius: 10px;
  border: 1px dashed var(--col-brown);
}
.cleanup-input {
  flex: 1;
  padding: 5px 10px;
  border: 1px solid var(--col-brown);
  border-radius: 8px;
  font-family: var(--font-breite), sans-serif;
  font-size: 1rem;
}
.cleanup-btn {
  background-color: var(--col-brown);
  color: var(--col-light);
  font-size: 1.2rem;
  padding: 5px 15px;
}
.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
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
</style>
