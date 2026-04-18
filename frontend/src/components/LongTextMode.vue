<script setup>
import { ref } from "vue";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "../components/LoadingOverlay.vue";

const toaster = createToaster({ position: "top-right", duration: 3000 });

const props = defineProps({
  activeCharacter: Object,
});

const longText = ref("");
const isLoading = ref(false);
const loadingText = ref("");
const phraseToRemove = ref("");

// Funkcja do błyskawicznego usuwania śmieci (nagłówki, stopki itp.)
const removePhrase = () => {
  if (!phraseToRemove.value) return;

  const escapedPhrase = phraseToRemove.value.replace(
    /[.*+?^${}()|[\]\\]/g,
    "\\$&",
  );
  const regex = new RegExp(escapedPhrase, "gi");

  longText.value = longText.value.replace(regex, "");
  longText.value = longText.value
    .replace(/ {2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  toaster.success(`Usunięto wszystkie wystąpienia: "${phraseToRemove.value}"`);
  phraseToRemove.value = "";
};

const uploadAndExtractText = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  console.log(`Wybrany plik: ${file.name} | Rozmiar: ${file.size} bajtów`);

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
      throw new Error(
        data.detail || "Błąd podczas przetwarzania pliku na serwerze.",
      );
    }

    longText.value = data.text ? String(data.text) : "";

    console.log(`Wczytano znaków: ${longText.value.length}`);

    if (longText.value !== "") {
      toaster.success("Tekst pomyślnie załadowany!");
    } else {
      toaster.warning("Plik został przetworzony, ale jest pusty.");
    }
  } catch (error) {
    console.error("Błąd pobierania:", error);
    toaster.error(error.message || "Nie udało się załadować pliku.");
  } finally {
    isLoading.value = false;
    event.target.value = "";
  }
};

const generateAudiobook = () => {
  if (!props.activeCharacter) {
    toaster.warning(
      "Wybierz postać z listy po lewej stronie przed generowaniem!",
    );
    return;
  }

  if (longText.value.trim() === "") {
    toaster.warning("Wpisz tekst lub załaduj plik do przeczytania!");
    return;
  }

  const payload = {
    mode: "long_text",
    character_id: props.activeCharacter.id,
    text: longText.value,
  };

  console.log("🚀 GOTOWY JSON Z LONG TEXT:", JSON.stringify(payload, null, 2));
  toaster.success("Sprawdź konsolę! JSON z długim tekstem gotowy.");
};
</script>

<template>
  <div class="mode-container">
    <LoadingOverlay v-if="isLoading" :text="loadingText" />

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

      <div class="cleanup-toolkit" v-if="longText !== ''">
        <input
          type="text"
          v-model="phraseToRemove"
          placeholder="Wpisz tekst do usunięcia (np. 'Page|1', link, tytuł książki)..."
          @keydown.enter.prevent="removePhrase"
          class="cleanup-input"
        />
        <button class="nav-btn cleanup-btn" @click="removePhrase">
          🧹 USUŃ Z CAŁEGO TEKSTU
        </button>
      </div>

      <textarea
        v-model="longText"
        placeholder="Wpisz lub załaduj długi tekst do przeczytania przez jedną postać..."
        class="long-textarea"
      ></textarea>
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
.mode-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.editor-area {
  flex: 1;
  padding: 20px 40px;
  display: flex;
  flex-direction: column;
  gap: 20px;
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
  font-size: 0.9rem;
}

.long-textarea {
  flex: 1;
  width: 100%;
  background-color: var(--col-lbrown);
  border: 3px solid var(--col-brown);
  border-radius: 14px;
  padding: 20px;
  resize: none;
  font-family: var(--font-breite), sans-serif;
  font-size: 1.2rem;
  color: var(--col-dark);
}

.long-textarea:focus {
  outline: none;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}

.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
  font-weight: bold;
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
</style>
