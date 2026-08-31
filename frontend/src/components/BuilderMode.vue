<script setup>
import { useAudiobookStore } from "../stores/audiobookStore";
import GenerateBottomBar from "./GenerateBottomBar.vue";

// Odbieramy aktywną postać od rodzica
const props = defineProps({
  activeCharacter: Object,
});

const audiobookStore = useAudiobookStore();

const getAvatarUrl = (path) => {
  if (!path) return "/emilia.png";
  const fixedPath = path.replace("characters/", "static_characters/");
  return `http://127.0.0.1:8000/${fixedPath}`;
};
</script>

<template>
  <div class="mode-container">
    <div class="conversation-area">
      <div
        class="dialogue-block"
        v-for="(block, index) in audiobookStore.conversation"
        :key="block.id"
      >
        <div class="character-tag">
          <div class="mini-avatar-container">
            <div class="decor-frame mini-frame-1"></div>
            <div class="decor-frame mini-frame-2"></div>
            <div class="mini-diamond-inner">
              <img :src="getAvatarUrl(block.avatar)" alt="" />
            </div>
          </div>
          <span class="mini-name">{{ block.characterName }}</span>
        </div>
        <textarea
          v-model="block.text"
          placeholder="Wpisz kwestię dialogową..."
          class="dialogue-box"
        ></textarea>
        <button class="delete-btn" @click="audiobookStore.removeBlock(index)">
          <img src="/trash.svg" alt="" />
        </button>
      </div>

      <button
        class="add-block-btn"
        @click="audiobookStore.addBlock(activeCharacter)"
      >
        <img src="/plus-line.svg" alt="" />
      </button>
    </div>

    <GenerateBottomBar
      :blocks="audiobookStore.conversation"
      mode="builder"
      title="WYGENERUJ AUDIOBOOK (BUILDER)"
    />
  </div>
</template>

<style scoped>
.mode-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden; /* zapobiega rozpychaniu layoutu */
}

.conversation-area {
  flex: 1;
  padding: 20px 40px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 30px;
}

.dialogue-box {
  resize: none;
}

.dialogue-block {
  margin-top: 20px;
  width: 80%;
  background-color: var(--col-lbrown);
  border: 2px solid var(--col-brown);
  border-radius: 10px;
  position: relative;
  padding: 30px 20px 20px 20px;
}

.character-tag {
  position: absolute;
  top: -25px;
  left: -20px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 15px 5px 5px;
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

.mini-name {
  font-family: var(--font-bitroad);
  font-weight: bold;
  color: var(--col-brown);
  margin-top: -50px;
  margin-left: -20px;
}

.dialogue-block textarea {
  width: 100%;
  min-height: 180px;
  background: transparent;
  border: none;
  resize: none;
  font-family: var(--font-breite), sans-serif;
  font-size: 1.1rem;
  color: var(--col-dark);
}
.dialogue-block textarea:focus {
  outline: none;
}

.delete-btn {
  position: absolute;
  bottom: -38px;
  right: -37px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
}
.delete-btn img {
  width: 60px;
  height: 60px;
}
.delete-btn:hover {
  animation: shrink-grow-shake 0.5s ease-in-out;
}

.add-block-btn {
  width: 40%;
  background-image: url("../assets/border-dashed.svg");
  background-size: contain;
  background-repeat: no-repeat;
  border: none;
  background-position: center;
  padding: 10px;
  background-color: transparent;
  cursor: pointer;
  display: flex;
  justify-content: center;
}
.add-block-btn:hover img {
  animation: shrink-grow-shake 0.5s ease-in-out;
}

@keyframes shrink-grow-shake {
  0% {
    transform: scale(1) rotate(0deg);
  }
  40% {
    transform: scale(1.2) rotate(0deg);
  }
  45% {
    transform: scale(1.2) rotate(-5deg);
  }
  55% {
    transform: scale(1.2) rotate(5deg);
  }
  65% {
    transform: scale(1.2) rotate(-5deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
  }
}

</style>
