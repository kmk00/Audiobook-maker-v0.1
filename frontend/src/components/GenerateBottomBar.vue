<script setup>
import { useAudiobookGeneration } from "../composables/useAudiobookGeneration";
import LoadingOverlay from "./LoadingOverlay.vue";

const props = defineProps({
  blocks: { type: Array, required: true },
  mode: { type: String, required: true },
  title: { type: String, default: "WYGENERUJ AUDIOBOOK" },
});

const {
  isLoading,
  loadingText,
  generatedAudioUrl,
  srtUrl,
  fcpxmlUrl,
  generateTimeline,
  generateAudiobook,
} = useAudiobookGeneration();

const handleGenerate = () => generateAudiobook(props.mode, props.blocks);
</script>

<template>
  <LoadingOverlay v-if="isLoading" :text="loadingText" />

  <div class="generate-bottom-bar">
    <label
      class="timeline-checkbox"
      title="Wygeneruje dodatkowo napisy .srt i kartę postaci .fcpxml do DaVinci Resolve"
    >
      <input type="checkbox" v-model="generateTimeline" />
      <span>Timeline do DaVinci (napisy + karty postaci)</span>
    </label>

    <h2>{{ title }}</h2>

    <div v-if="generatedAudioUrl" class="result-cluster">
      <audio :src="generatedAudioUrl" controls class="result-player"></audio>

      <a
        v-if="srtUrl"
        :href="srtUrl"
        download
        class="nav-btn download-btn"
        title="Pobierz napisy (.srt)"
      >
        SRT
      </a>
      <a
        v-if="fcpxmlUrl"
        :href="fcpxmlUrl"
        download
        class="nav-btn download-btn"
        title="Pobierz timeline z kartami postaci (.fcpxml)"
      >
        FCPXML
      </a>
    </div>

    <button
      class="generate-action-btn diamond-btn large"
      @click="handleGenerate"
    >
      <span
        ><img class="generate-btn" src="../assets/generate.svg" alt=""
      /></span>
    </button>
  </div>
</template>

<style scoped>
.generate-btn {
  width: 30px;
  height: 30px;
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

.timeline-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-breite);
  font-size: 0.8rem;
  color: var(--col-light);
  cursor: pointer;
  margin-right: auto; /* odsuwa checkbox w lewo, reszta zostaje po prawej jak wcześniej */
  opacity: 0.85;
}
.timeline-checkbox input {
  accent-color: var(--col-orange);
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.result-cluster {
  display: flex;
  align-items: center;
  gap: 10px;
}
.result-player {
  height: 40px;
  border-radius: 20px;
  outline: none;
  border: 2px solid var(--col-orange);
}
.download-btn {
  font-size: 0.7rem;
  padding: 6px 12px;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  white-space: nowrap;
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
.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
  color: var(--col-brown);
  font-weight: bold;
  cursor: pointer;
}
</style>
