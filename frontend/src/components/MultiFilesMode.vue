<script setup>
import { ref } from "vue";
import { createToaster } from "@meforma/vue-toaster";

const props = defineProps({
  activeCharacter: Object,
});

const toaster = createToaster({ position: "top-right", duration: 3000 });

const filesQueue = ref([]);
const isProcessingQueue = ref(false);

const handleFileUpload = (event) => {
  const files = Array.from(event.target.files);
  if (!files.length) return;

  for (const file of files) {
    if (!file.name.toLowerCase().endsWith(".txt")) {
      toaster.warning(
        `Pominięto ${file.name} - obsługiwane są tylko pliki .txt`,
      );
      continue;
    }

    const fileItem = {
      id: Date.now() + Math.random(),
      file: file,
      name: file.name,
      text: "",
      status: "idle",
      progressMessage: "Oczekuje w kolejce",
      audioUrl: null,
      characterName: null,
      avatar: null,
    };

    const reader = new FileReader();
    reader.onload = (e) => {
      fileItem.text = e.target.result;
    };
    reader.readAsText(file);

    filesQueue.value.push(fileItem);
  }
  event.target.value = "";
};

const removeFile = (id) => {
  const index = filesQueue.value.findIndex((f) => f.id === id);
  if (index > -1) {
    filesQueue.value.splice(index, 1);
  }
};

const processSingleFile = async (fileItem) => {
  if (fileItem.status === "generating" || fileItem.status === "done") return;
  if (!fileItem.text.trim()) {
    fileItem.status = "error";
    fileItem.progressMessage = "Błąd: Plik jest pusty";
    return;
  }
  if (!props.activeCharacter) {
    toaster.warning(`Wybierz postać przed wygenerowaniem: ${fileItem.name}`);
    return;
  }

  fileItem.characterName = props.activeCharacter.name;
  fileItem.avatar = props.activeCharacter.avatar_path;

  fileItem.status = "generating";
  fileItem.progressMessage = "Zlecanie zadania na serwer...";

  const payload = {
    mode: "longtext",
    blocks: [
      {
        character_id: props.activeCharacter.id,
        text: fileItem.text.trim(),
      },
    ],
  };

  try {
    const response = await fetch(
      "http://127.0.0.1:8000/tts/generate-audiobook",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );

    if (!response.ok) throw new Error("Błąd zlecenia zadania.");

    const data = await response.json();
    await pollTaskStatus(data.task_id, fileItem);
  } catch (error) {
    fileItem.status = "error";
    fileItem.progressMessage = "Błąd: " + error.message;
  }
};

const pollTaskStatus = async (taskId, fileItem) => {
  return new Promise((resolve) => {
    const checkStatus = async () => {
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/tts/task-status/${taskId}`,
        );
        const data = await res.json();

        if (data.status === "completed") {
          fileItem.status = "done";
          fileItem.progressMessage = "Gotowe!";
          fileItem.audioUrl = data.file_url;
          toaster.success(`Plik ${fileItem.name} został wygenerowany!`);
          resolve();
        } else if (data.status === "error") {
          fileItem.status = "error";
          fileItem.progressMessage = "Błąd: " + data.error;
          resolve();
        } else {
          fileItem.progressMessage = data.message || "Nagrywanie w studiu...";
          setTimeout(checkStatus, 3000);
        }
      } catch (error) {
        fileItem.status = "error";
        fileItem.progressMessage = "Utracono połączenie z serwerem.";
        resolve();
      }
    };

    checkStatus();
  });
};

const generateAll = async () => {
  const pendingFiles = filesQueue.value.filter(
    (f) => f.status === "idle" || f.status === "error",
  );

  if (pendingFiles.length === 0) {
    toaster.info("Nie ma żadnych plików oczekujących na generowanie.");
    return;
  }

  isProcessingQueue.value = true;
  toaster.info(
    `Rozpoczynam sekwencyjne generowanie ${pendingFiles.length} plików...`,
  );

  for (const file of pendingFiles) {
    await processSingleFile(file);
  }

  isProcessingQueue.value = false;
  toaster.success("Zakończono przetwarzanie całej kolejki!");
};

const getAvatarUrl = (path) => {
  if (!path) return "/emilia.png";
  return `http://127.0.0.1:8000/${path.replace("characters/", "static_characters/")}`;
};
</script>

<template>
  <div class="mode-container">
    <div class="multifiles-header">
      <h2>MULTI-FILES STUDIO</h2>
      <div class="header-actions">
        <div class="upload-btn-wrapper">
          <label for="multi-upload" class="nav-btn file-label"
            >DODAJ PLIKI .TXT</label
          >
          <input
            type="file"
            id="multi-upload"
            accept=".txt"
            multiple
            @change="handleFileUpload"
            hidden
          />
        </div>
        <button
          class="nav-btn play-btn"
          @click="generateAll"
          :disabled="isProcessingQueue || filesQueue.length === 0"
        >
          <span v-if="isProcessingQueue">TRWA GENEROWANIE...</span>
          <span v-else>GENERUJ WSZYSTKO</span>
        </button>
      </div>
    </div>

    <div class="queue-scroll-container">
      <div v-if="filesQueue.length === 0" class="empty-state">
        <p>
          Wgraj wiele plików tekstowych (.txt), wybierz postać po lewej i
          wygeneruj je wszystkie naraz!
        </p>
      </div>

      <div class="queue-list" v-else>
        <div
          class="queue-item"
          v-for="(item, index) in filesQueue"
          :key="item.id"
          :class="`status-${item.status}`"
        >
          <div class="item-info">
            <div class="item-number">{{ index + 1 }}</div>
            <div class="item-details">
              <h4>{{ item.name }}</h4>
              <p class="status-msg">{{ item.progressMessage }}</p>
            </div>
          </div>

          <div class="item-actions">
            <div class="assigned-char" v-if="item.characterName">
              <img
                :src="getAvatarUrl(item.avatar)"
                :title="`Lektor: ${item.characterName}`"
              />
            </div>

            <audio
              v-if="item.audioUrl"
              :src="item.audioUrl"
              controls
              class="mini-player"
            ></audio>

            <button
              v-if="item.status === 'idle' || item.status === 'error'"
              class="nav-btn small-play-btn"
              title="Generuj tylko ten plik"
              @click="processSingleFile(item)"
              :disabled="isProcessingQueue"
            >
              ▶
            </button>

            <div class="spinner" v-if="item.status === 'generating'"></div>

            <button
              class="remove-btn"
              title="Usuń plik z listy"
              @click="removeFile(item.id)"
              :disabled="item.status === 'generating'"
            >
              ✖
            </button>
          </div>
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

.multifiles-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 3px solid var(--col-brown);
  margin-bottom: 20px;
}

.multifiles-header h2 {
  font-family: var(--font-bitroad);
  color: var(--col-dark);
  margin: 0;
  letter-spacing: 2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-btn {
  padding: 10px 20px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
  font-weight: bold;
  cursor: pointer;
  transition: all 0.2s;
  border-radius: 8px;
}

.file-label {
  background-color: var(--col-brown);
  color: var(--col-light);
  display: inline-block;
}
.file-label:hover {
  background-color: var(--col-orange);
}

.play-btn {
  background-color: var(--col-orange);
  color: var(--col-light);
  border-color: var(--col-orange);
}
.play-btn:hover:not(:disabled) {
  background-color: var(--col-dark);
  border-color: var(--col-dark);
}
.play-btn:disabled {
  background-color: #ccc;
  border-color: #999;
  cursor: not-allowed;
  opacity: 0.7;
}

.queue-scroll-container {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
}
.queue-scroll-container::-webkit-scrollbar {
  width: 8px;
}
.queue-scroll-container::-webkit-scrollbar-thumb {
  background-color: var(--col-brown);
  border-radius: 10px;
}

.empty-state {
  margin: auto;
  text-align: center;
  margin-top: 100px;
  font-family: var(--font-breite);
  color: var(--col-brown);
  font-size: 1.2rem;
  opacity: 0.6;
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--col-lbrown);
  border: 2px solid var(--col-brown);
  padding: 15px;
  border-radius: 10px;
  transition: all 0.3s;
}

.queue-item.status-idle {
  border-color: var(--col-brown);
}
.queue-item.status-generating {
  border-color: var(--col-orange);
  background-color: rgba(255, 165, 0, 0.1);
}
.queue-item.status-done {
  border-color: #2e7d32;
  background-color: rgba(46, 125, 50, 0.1);
}
.queue-item.status-error {
  border-color: #d32f2f;
  background-color: rgba(211, 47, 47, 0.1);
}

.item-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.item-number {
  background-color: var(--col-brown);
  color: var(--col-light);
  font-weight: bold;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-family: var(--font-bitroad);
}

.item-details h4 {
  margin: 0 0 5px 0;
  font-family: var(--font-breite);
  color: var(--col-dark);
}

.status-msg {
  margin: 0;
  font-size: 0.85rem;
  color: var(--col-brown);
  font-weight: bold;
}
.status-generating .status-msg {
  color: var(--col-orange);
}
.status-done .status-msg {
  color: #2e7d32;
}
.status-error .status-msg {
  color: #d32f2f;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.assigned-char {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid var(--col-brown);
  overflow: hidden;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}
.assigned-char img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mini-player {
  height: 36px;
  width: 250px;
  outline: none;
}

.small-play-btn {
  padding: 5px 12px;
  background-color: var(--col-light);
  color: var(--col-dark);
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.small-play-btn:hover {
  background-color: var(--col-orange);
  color: white;
  border-color: var(--col-orange);
}

.remove-btn {
  background: transparent;
  border: none;
  color: #d32f2f;
  font-size: 1.4rem;
  cursor: pointer;
  transition: transform 0.2s;
}
.remove-btn:hover:not(:disabled) {
  transform: scale(1.2);
}
.remove-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 4px solid rgba(255, 165, 0, 0.3);
  border-top: 4px solid var(--col-orange);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
