<script setup>
import { ref } from "vue";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "./LoadingOverlay.vue";

const props = defineProps({
  activeCharacter: Object,
});

const toaster = createToaster({ position: "top-right", duration: 3000 });
const isLoading = ref(false);
const loadingText = ref("");

const ocrLanguage = ref("ja");
const pages = ref([]);

const handleFileUpload = (event) => {
  const files = event.target.files;
  if (!files.length) return;

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    pages.value.push({
      id: Date.now() + Math.random(),
      file: file,
      url: URL.createObjectURL(file),
      blocks: [],
      audioUrl: null,
      status: "idle",
    });
  }
  event.target.value = "";
};

// --- ETAP 1: DETEKCJA DYMKÓW ---
const detectBubbles = async (pageIndex) => {
  const page = pages.value[pageIndex];
  page.status = "detecting";
  isLoading.value = true;
  loadingText.value = "Szukanie dymków na stronie...";

  const formData = new FormData();
  formData.append("file", page.file);
  formData.append("language", ocrLanguage.value);

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/audiobook_utils/detect-bubbles",
      {
        method: "POST",
        body: formData,
      },
    );

    if (!response.ok) throw new Error("Błąd podczas detekcji dymków.");
    const data = await response.json();

    page.blocks = data.blocks.map((b) => ({
      id: b.id,
      box: b.box,
      text: "",
      characterId: null,
      characterName: "Nieprzypisany",
      avatar: null,
    }));

    page.status = "review_boxes";
    toaster.success("Znaleziono dymki! Sprawdź je na obrazku po prawej.");
  } catch (error) {
    page.status = "idle";
    toaster.error("Błąd serwera: " + error.message);
  } finally {
    isLoading.value = false;
  }
};

// --- RYSOWANIE WŁASNYCH RAMEK ---
const isDrawing = ref(false);
const startPoint = ref({ x: 0, y: 0 });
const tempBox = ref(null);

const startDraw = (e) => {
  const rect = e.currentTarget.getBoundingClientRect();
  startPoint.value = {
    x: ((e.clientX - rect.left) / rect.width) * 100,
    y: ((e.clientY - rect.top) / rect.height) * 100,
  };
  isDrawing.value = true;
  tempBox.value = {
    x: startPoint.value.x,
    y: startPoint.value.y,
    width: 0,
    height: 0,
  };
};

const onDrawMove = (e) => {
  if (!isDrawing.value) return;
  const rect = e.currentTarget.getBoundingClientRect();
  const currentX = ((e.clientX - rect.left) / rect.width) * 100;
  const currentY = ((e.clientY - rect.top) / rect.height) * 100;

  tempBox.value.x = Math.min(startPoint.value.x, currentX);
  tempBox.value.y = Math.min(startPoint.value.y, currentY);
  tempBox.value.width = Math.abs(currentX - startPoint.value.x);
  tempBox.value.height = Math.abs(currentY - startPoint.value.y);
};

const stopDraw = (page) => {
  if (!isDrawing.value) return;
  isDrawing.value = false;

  if (tempBox.value.width > 2 && tempBox.value.height > 2) {
    page.blocks.push({
      id: "manual_" + Date.now(),
      box: { ...tempBox.value },
      text: "",
      characterId: null,
      characterName: "Nieprzypisany",
      avatar: null,
    });
  }
  tempBox.value = null;
};

const removeBox = (pageIndex, blockId) => {
  const page = pages.value[pageIndex];
  const index = page.blocks.findIndex((b) => b.id === blockId);
  if (index > -1) {
    page.blocks.splice(index, 1);
  }
};

// --- ETAP 2: TRANSKRYPCJA ZATWIERDZONYCH RAMEK ---
const transcribeBubbles = async (pageIndex) => {
  const page = pages.value[pageIndex];
  if (page.blocks.length === 0) {
    toaster.warning("Brak ramek do transkrypcji!");
    return;
  }

  page.status = "transcribing";
  isLoading.value = true;
  loadingText.value = "Czytanie tekstu (OCR)...";

  const formData = new FormData();
  formData.append("file", page.file);
  formData.append("language", ocrLanguage.value);

  const boxesData = page.blocks.map((b) => ({ id: b.id, box: b.box }));
  formData.append("boxes_data", JSON.stringify(boxesData));

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/audiobook_utils/transcribe-bubbles",
      {
        method: "POST",
        body: formData,
      },
    );

    if (!response.ok) throw new Error("Błąd podczas transkrypcji tekstu.");
    const data = await response.json();

    data.transcriptions.forEach((trans) => {
      const block = page.blocks.find((b) => b.id === trans.id);
      if (block) block.text = trans.text;
    });

    page.status = "ready";
    toaster.success("Tekst gotowy do reżyserii!");
  } catch (error) {
    page.status = "review_boxes";
    toaster.error("Błąd serwera: " + error.message);
  } finally {
    isLoading.value = false;
  }
};

// --- PRZESUWANIE POZYCJI STRZAŁKAMI I RĘCZNIE ---
const moveBlockUp = (pageIndex, blockIdx) => {
  if (blockIdx === 0) return;
  const blocks = pages.value[pageIndex].blocks;
  const item = blocks.splice(blockIdx, 1)[0];
  blocks.splice(blockIdx - 1, 0, item);
};

const moveBlockDown = (pageIndex, blockIdx) => {
  const blocks = pages.value[pageIndex].blocks;
  if (blockIdx === blocks.length - 1) return;
  const item = blocks.splice(blockIdx, 1)[0];
  blocks.splice(blockIdx + 1, 0, item);
};

const updateBlockPosition = (pageIndex, oldIndex, event) => {
  const blocks = pages.value[pageIndex].blocks;
  let newIndex = parseInt(event.target.value, 10) - 1;

  // Weryfikacja: jeśli ktoś wpisze litery, wracamy do poprzedniej wartości
  if (isNaN(newIndex)) {
    event.target.value = oldIndex + 1;
    return;
  }

  // Ograniczenia granic (nie mniej niż 0, nie więcej niż długość tablicy)
  if (newIndex < 0) newIndex = 0;
  if (newIndex >= blocks.length) newIndex = blocks.length - 1;

  // Wymuszenie zaktualizowania inputa w przypadku wpisania np. "999" (zmieni na maksa)
  event.target.value = newIndex + 1;

  // Jeśli pozycja się nie zmieniła, nic nie robimy
  if (oldIndex === newIndex) return;

  // Przesunięcie elementu w tablicy
  const item = blocks.splice(oldIndex, 1)[0];
  blocks.splice(newIndex, 0, item);
};

// --- PRZYPISANIE POSTACI ---
const assignCharacterToBlock = (pageIndex, blockId) => {
  if (!props.activeCharacter) {
    toaster.warning("Wybierz najpierw postać z lewego panelu bocznego!");
    return;
  }

  const block = pages.value[pageIndex].blocks.find((b) => b.id === blockId);
  if (!block) return;

  if (block.characterId === props.activeCharacter.id) {
    block.characterId = null;
    block.characterName = "Nieprzypisany";
    block.avatar = null;
    return;
  }

  block.characterId = props.activeCharacter.id;
  block.characterName = props.activeCharacter.name;
  block.avatar = props.activeCharacter.avatar_path;
};

const getAvatarUrl = (path) => {
  if (!path) return "/emilia.png";
  return `http://127.0.0.1:8000/${path.replace("characters/", "static_characters/")}`;
};

// --- ETAP 3: GENEROWANIE AUDIO ---
const generateAudioForPage = async (pageIndex) => {
  const page = pages.value[pageIndex];
  const validBlocks = page.blocks.filter((b) => b.text.trim() !== "");

  if (validBlocks.length === 0) {
    toaster.warning("Ta strona nie ma przypisanego żadnego tekstu!");
    return;
  }

  const payload = {
    mode: "manga",
    page_id: page.id,
    blocks: validBlocks.map((block) => ({
      character_id: block.characterId,
      text: block.text.trim(),
    })),
  };

  page.status = "generating";
  isLoading.value = true;
  loadingText.value = `Generowanie dubbingu strony ${pageIndex + 1}...`;

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/tts/generate-audiobook",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) throw new Error("Błąd podczas wysyłania zadań.");

    const data = await response.json();
    await pollTaskStatus(data.task_id, pageIndex);
  } catch (error) {
    page.status = "ready";
    isLoading.value = false;
    toaster.error(error.message);
  }
};

const pollTaskStatus = async (taskId, pageIndex) => {
  try {
    const res = await fetch(`http://127.0.0.1:8000/tts/task-status/${taskId}`);
    const data = await res.json();
    const page = pages.value[pageIndex];

    if (data.status === "completed") {
      isLoading.value = false;
      page.audioUrl = data.file_url;
      page.status = "done";
      toaster.success(`Dubbing strony ${pageIndex + 1} gotowy!`);
    } else if (data.status === "error") {
      isLoading.value = false;
      page.status = "ready";
      toaster.error("Błąd generowania: " + data.error);
    } else {
      loadingText.value = data.message || "Nagrywanie w studiu...";
      setTimeout(() => pollTaskStatus(taskId, pageIndex), 3000);
    }
  } catch (error) {
    isLoading.value = false;
    pages.value[pageIndex].status = "ready";
    toaster.error("Błąd komunikacji z serwerem.");
  }
};
</script>

<template>
  <div class="mode-container">
    <LoadingOverlay v-if="isLoading" :text="loadingText" />

    <div class="manga-header">
      <h2>MANGA DUBBING STUDIO</h2>

      <div class="header-actions">
        <div class="lang-switch">
          <label>Język OCR:</label>
          <select v-model="ocrLanguage" class="nav-btn">
            <option value="ja">Japoński (manga-ocr)</option>
            <option value="en">Angielski (EasyOCR)</option>
          </select>
        </div>

        <div class="upload-btn-wrapper">
          <label for="manga-upload" class="nav-btn file-label"
            >+ DODAJ STRONĘ MANGI</label
          >
          <input
            type="file"
            id="manga-upload"
            accept="image/*"
            @change="handleFileUpload"
            hidden
          />
        </div>
      </div>
    </div>

    <div class="pages-scroll-container">
      <div v-if="pages.length === 0" class="empty-state">
        <p>Wgraj zdjęcie komiksu, aby rozpocząć!</p>
      </div>

      <div class="page-card" v-for="(page, pageIdx) in pages" :key="page.id">
        <div class="page-card-header">
          <h3>Edytor Strony ({{ page.blocks.length }} kwestii)</h3>
          <div class="page-actions">
            <button
              v-if="page.status === 'idle'"
              class="nav-btn action-btn"
              @click="detectBubbles(pageIdx)"
            >
              1. ZNAJDŹ DYMKI
            </button>
            <button
              v-if="page.status === 'review_boxes'"
              class="nav-btn action-btn highlight"
              @click="transcribeBubbles(pageIdx)"
            >
              2. ZATWIERDŹ I CZYTAJ TEKST
            </button>
            <button
              v-if="page.status === 'ready' || page.status === 'done'"
              class="nav-btn play-btn"
              @click="generateAudioForPage(pageIdx)"
            >
              3. 🎙️ GENERUJ DUBBING
            </button>
            <button
              class="nav-btn delete-btn"
              title="Usuń stronę"
              @click="pages.splice(pageIdx, 1)"
            >
              ✖
            </button>
          </div>
        </div>

        <div class="manga-workspace">
          <div
            class="script-panel"
            v-if="page.status === 'ready' || page.status === 'done'"
          >
            <p class="panel-desc">
              Ustal kolejność czytania klikając w strzałki lub wpisując numer.
            </p>

            <transition-group name="list" tag="div" class="script-list">
              <div
                class="script-item"
                v-for="(block, blockIdx) in page.blocks"
                :key="block.id"
              >
                <!-- KONTROLKI KOLEJNOŚCI -->
                <div class="order-controls">
                  <div class="move-controls">
                    <button
                      class="move-btn"
                      title="Przesuń wyżej"
                      :disabled="blockIdx === 0"
                      @click="moveBlockUp(pageIdx, blockIdx)"
                    >
                      ▲
                    </button>
                    <button
                      class="move-btn"
                      title="Przesuń niżej"
                      :disabled="blockIdx === page.blocks.length - 1"
                      @click="moveBlockDown(pageIdx, blockIdx)"
                    >
                      ▼
                    </button>
                  </div>

                  <input
                    type="number"
                    class="order-input"
                    title="Kolejność czytania (wpisz i kliknij poza polem)"
                    :value="blockIdx + 1"
                    @change="updateBlockPosition(pageIdx, blockIdx, $event)"
                    min="1"
                    :max="page.blocks.length"
                  />
                </div>

                <button
                  class="script-assign-btn"
                  :class="{ assigned: block.characterId }"
                  title="Kliknij, by przypisać postać z lewego menu"
                  @click="assignCharacterToBlock(pageIdx, block.id)"
                >
                  <img
                    v-if="block.avatar"
                    :src="getAvatarUrl(block.avatar)"
                    class="assigned-micro-avatar"
                  />
                  <span v-else>+</span>
                </button>

                <textarea
                  v-model="block.text"
                  class="script-textarea"
                  placeholder="Tekst..."
                ></textarea>
              </div>
            </transition-group>
          </div>

          <div
            class="script-panel instruction-panel"
            v-if="page.status === 'review_boxes'"
          >
            <h4 style="color: var(--col-orange)">TRYB EDYCJI RAMEK</h4>
            <p>
              1. <b>Narysuj własną ramkę</b>: Złap i przeciągnij myszką
              bezpośrednio na zdjęciu mangi po prawej stronie.
            </p>
            <p>
              2. <b>Usuń ramkę</b>: AI znalazło śmieć? Kliknij czerwony [X] na
              dymku.
            </p>
            <p>
              3. Po sprawdzeniu kliknij przycisk "Zatwierdź i czytaj tekst" u
              góry.
            </p>
          </div>

          <div class="image-panel">
            <div
              class="image-wrapper"
              @mousedown="
                page.status === 'review_boxes' ? startDraw($event) : null
              "
              @mousemove="
                page.status === 'review_boxes' ? onDrawMove($event) : null
              "
              @mouseup="page.status === 'review_boxes' ? stopDraw(page) : null"
              @mouseleave="
                page.status === 'review_boxes' ? stopDraw(page) : null
              "
            >
              <img :src="page.url" class="manga-image" draggable="false" />

              <div
                v-if="tempBox"
                class="bounding-box temp-box"
                :style="{
                  left: tempBox.x + '%',
                  top: tempBox.y + '%',
                  width: tempBox.width + '%',
                  height: tempBox.height + '%',
                }"
              ></div>

              <div
                v-for="(block, blockIdx) in page.blocks"
                :key="block.id"
                class="bounding-box"
                :class="{
                  'review-mode': page.status === 'review_boxes',
                  'ready-mode':
                    page.status === 'ready' || page.status === 'done',
                  'assigned-box': block.characterId !== null,
                }"
                :style="{
                  left: block.box.x + '%',
                  top: block.box.y + '%',
                  width: block.box.width + '%',
                  height: block.box.height + '%',
                }"
                @click.stop="
                  page.status === 'ready' || page.status === 'done'
                    ? assignCharacterToBlock(pageIdx, block.id)
                    : null
                "
              >
                <div class="box-badge">{{ blockIdx + 1 }}</div>

                <button
                  v-if="page.status === 'review_boxes'"
                  class="remove-box-btn"
                  title="Usuń tę ramkę"
                  @click.stop="removeBox(pageIdx, block.id)"
                >
                  ✖
                </button>

                <div class="box-avatars">
                  <div
                    v-if="
                      (page.status === 'ready' || page.status === 'done') &&
                      block.avatar
                    "
                    class="box-avatar-indicator"
                  >
                    <img :src="getAvatarUrl(block.avatar)" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="page.audioUrl" class="page-audio-player">
          <p class="audio-label">Gotowy Dubbing Strony:</p>
          <audio :src="page.audioUrl" controls class="result-player"></audio>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mode-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  padding: 20px 40px;
}

.manga-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 3px solid var(--col-brown);
  margin-bottom: 20px;
}

.manga-header h2 {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  margin: 0;
  letter-spacing: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 20px;
}
.lang-switch {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-bitroad);
  font-weight: bold;
  color: var(--col-brown);
}

.file-label {
  background-color: var(--col-brown);
  color: var(--col-light);
  padding: 10px 20px;
  cursor: pointer;
}
.file-label:hover {
  background-color: var(--col-orange);
}

.pages-scroll-container {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 30px;
  padding-right: 10px;
}
.pages-scroll-container::-webkit-scrollbar {
  width: 8px;
}
.pages-scroll-container::-webkit-scrollbar-thumb {
  background-color: var(--col-brown);
  border-radius: 10px;
}

.empty-state {
  margin: auto;
  font-family: var(--font-breite);
  color: var(--col-brown);
  font-size: 1.2rem;
  opacity: 0.6;
}

.page-card {
  background-color: var(--col-lbrown);
  border: 3px solid var(--col-brown);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.page-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-card-header h3 {
  font-family: var(--font-bitroad);
  color: var(--col-brown);
  margin: 0;
  font-size: 1.3rem;
}
.page-actions {
  display: flex;
  gap: 10px;
}

.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 6px;
}
.action-btn {
  background-color: var(--col-light);
  color: var(--col-brown);
}
.action-btn:hover {
  background-color: var(--col-brown);
  color: var(--col-light);
}
.action-btn.highlight {
  background-color: var(--col-orange);
  color: var(--col-light);
  border-color: var(--col-orange);
}
.play-btn {
  background-color: var(--col-dark);
  color: var(--col-light);
  border-color: var(--col-dark);
}
.play-btn:hover {
  background-color: var(--col-orange);
  border-color: var(--col-orange);
}
.delete-btn {
  background-color: transparent;
  border: none;
  color: #d32f2f;
  font-size: 1.2rem;
  padding: 0 10px;
}
.delete-btn:hover {
  transform: scale(1.2);
}

.manga-workspace {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.script-panel {
  flex: 1;
  background-color: var(--col-light);
  border: 2px solid var(--col-brown);
  border-radius: 8px;
  padding: 15px;
  max-height: 800px;
  overflow-y: auto;
}
.script-panel::-webkit-scrollbar {
  width: 6px;
}
.script-panel::-webkit-scrollbar-thumb {
  background-color: var(--col-brown);
  border-radius: 10px;
}

.panel-desc {
  font-family: var(--font-breite);
  color: var(--col-brown);
  font-size: 0.9rem;
  margin-top: 0;
  margin-bottom: 15px;
  text-align: center;
}
.instruction-panel {
  font-family: var(--font-breite);
  font-size: 1rem;
  color: var(--col-dark);
  line-height: 1.6;
  padding: 30px;
}

.script-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.list-move {
  transition: transform 0.3s ease;
}

.script-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: var(--col-lbrown);
  border: 2px solid var(--col-brown);
  padding: 8px;
  border-radius: 8px;
  transition:
    opacity 0.2s,
    background-color 0.2s;
}

/* KONTROLKI KOLEJNOŚCI */
.order-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.move-controls {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.move-btn {
  background: var(--col-light);
  border: 1px solid var(--col-brown);
  border-radius: 4px;
  color: var(--col-brown);
  cursor: pointer;
  font-size: 0.6rem;
  padding: 3px 6px;
  transition: all 0.2s;
}

.move-btn:hover:not(:disabled) {
  background-color: var(--col-brown);
  color: var(--col-light);
}

.move-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  border-color: rgba(60, 42, 33, 0.3);
}

.order-input {
  width: 40px;
  height: 30px;
  text-align: center;
  background-color: var(--col-brown);
  color: var(--col-light);
  font-weight: bold;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  /* Pozbycie się natywnych strzałek w niektórych przeglądarkach */
  -moz-appearance: textfield;
}
.order-input::-webkit-outer-spin-button,
.order-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
.order-input:focus {
  outline: 2px solid var(--col-orange);
  background-color: var(--col-dark);
}

.box-badge {
  position: absolute;
  top: -10px;
  left: -10px;
  background-color: var(--col-dark);
  color: var(--col-light);
  font-weight: bold;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 0.7rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.script-assign-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px dashed var(--col-brown);
  background-color: var(--col-light);
  color: var(--col-brown);
  font-weight: bold;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 0;
  flex-shrink: 0;
}
.script-assign-btn:hover {
  border-style: solid;
  background-color: var(--col-orange);
  color: #fff;
  border-color: var(--col-orange);
}
.script-assign-btn.assigned {
  border: 2px solid var(--col-orange);
  padding: 2px;
}

.script-textarea {
  flex: 1;
  height: 40px;
  resize: none;
  border: 1px solid var(--col-brown);
  border-radius: 4px;
  padding: 5px;
  font-family: var(--font-breite);
}
.script-textarea:focus {
  outline: none;
  border-color: var(--col-orange);
}

.image-panel {
  flex: 1.5;
  display: flex;
  justify-content: center;
}

.image-wrapper {
  position: relative;
  width: 100%;
  max-width: 650px;
  border: 3px solid var(--col-brown);
  background-color: #fff;
  border-radius: 8px;
  overflow: visible;
  user-select: none;
}
.image-wrapper::after {
  content: "Kliknij i przeciągnij, by dodać własny dymek";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  text-align: center;
  background-color: rgba(60, 42, 33, 0.8);
  color: white;
  font-family: var(--font-breite);
  font-size: 0.8rem;
  padding: 2px;
  opacity: 0;
  transition: opacity 0.3s;
  pointer-events: none;
}
.image-wrapper:hover::after {
  opacity: 1;
}

.manga-image {
  width: 100%;
  height: auto;
  display: block;
  pointer-events: none;
}

.bounding-box {
  position: absolute;
  border-radius: 4px;
  transition:
    background-color 0.2s,
    border-color 0.2s;
  pointer-events: none;
}

.bounding-box.review-mode {
  border: 2px dashed rgba(211, 47, 47, 0.8);
  pointer-events: auto;
  background-color: rgba(211, 47, 47, 0.1);
}
.bounding-box.review-mode:hover {
  background-color: rgba(211, 47, 47, 0.3);
  border-style: solid;
  border-color: #d32f2f;
}

.bounding-box.ready-mode {
  border: 2px dashed rgba(60, 42, 33, 0.5);
  pointer-events: auto;
  cursor: pointer;
}
.bounding-box.ready-mode:hover {
  background-color: rgba(255, 165, 0, 0.3);
  border-style: solid;
  border-color: var(--col-orange);
}
.bounding-box.ready-mode.assigned-box {
  border-style: solid;
  border-color: var(--col-orange);
  background-color: rgba(255, 165, 0, 0.15);
}

.temp-box {
  background-color: rgba(255, 165, 0, 0.2);
  border: 3px solid var(--col-orange);
  pointer-events: none;
}

.remove-box-btn {
  position: absolute;
  top: -10px;
  right: -10px;
  background-color: #d32f2f;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  font-size: 0.7rem;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  z-index: 5;
}
.remove-box-btn:hover {
  transform: scale(1.1);
  background-color: red;
}

.box-avatars {
  position: absolute;
  bottom: -15px;
  right: -15px;
  z-index: 5;
  pointer-events: none;
}

.box-avatar-indicator {
  width: 35px;
  height: 35px;
  border-radius: 50%;
  border: 2px solid var(--col-orange);
  background-color: var(--col-light);
  overflow: hidden;
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}
.box-avatar-indicator img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.assigned-micro-avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.page-audio-player {
  display: flex;
  align-items: center;
  gap: 15px;
  background-color: var(--col-dark);
  padding: 10px 20px;
  border-radius: 10px;
  margin-top: 10px;
}
.audio-label {
  color: var(--col-orange);
  font-family: var(--font-bitroad);
  margin: 0;
}
.result-player {
  flex: 1;
  height: 40px;
  border-radius: 20px;
  outline: none;
}
</style>
