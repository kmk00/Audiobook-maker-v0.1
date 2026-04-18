<script setup>
import { ref } from "vue";

const props = defineProps({
  activeCharacter: Object,
});

const longText = ref("");

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    longText.value = e.target.result;
  };
  reader.readAsText(file);
};

const generateAudiobook = () => {
  if (!props.activeCharacter) {
    alert("Wybierz postać z listy po lewej stronie przed generowaniem!");
    return;
  }

  if (longText.value.trim() === "") {
    alert("Wpisz tekst lub załaduj plik .txt!");
    return;
  }

  const payload = {
    mode: "long_text",
    character_id: props.activeCharacter.id,
    text: longText.value,
  };

  console.log("🚀 GOTOWY JSON Z LONG TEXT:", JSON.stringify(payload, null, 2));
  alert("Sprawdź konsolę! JSON z długim tekstem gotowy.");
};
</script>

<template>
  <div class="mode-container">
    <div class="editor-area">
      <div class="file-upload-section">
        <div class="file-upload-wrapper">
          <label for="text-upload" class="nav-btn file-label"> TXT </label>
          <input
            type="file"
            id="text-upload"
            accept=".txt"
            @change="handleFileUpload"
            hidden
          />
        </div>
        <div class="file-upload-wrapper">
          <label for="text-upload" class="nav-btn file-label"> PDF </label>
          <input
            type="file"
            id="text-upload"
            accept=".txt"
            @change="handleFileUpload"
            hidden
          />
        </div>
        <div class="file-upload-wrapper">
          <label for="text-upload" class="nav-btn file-label"> EPUB </label>
          <input
            type="file"
            id="text-upload"
            accept=".txt"
            @change="handleFileUpload"
            hidden
          />
        </div>
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

/* Skopiowane elementy paska z buildera */
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
