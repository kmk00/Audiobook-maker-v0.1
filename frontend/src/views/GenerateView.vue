<script setup>
import { ref, computed, onMounted } from "vue";
import { useCharacterStore } from "../stores/characterStore";

const characterStore = useCharacterStore();

const searchQuery = ref("");
const isSearchOpen = ref(false);
const activeCharacter = ref(null);
const conversation = ref([]);
const hoveredCharacter = ref(null);

const fetchCharacters = async () => {
  try {
    const response = await fetch("http://127.0.0.1:8000/characters/");
    if (response.ok) {
      characters.value = await response.json();
    } else {
      console.error("Błąd podczas pobierania postaci");
    }
  } catch (error) {
    console.error("Błąd sieci:", error);
  }
};

onMounted(() => {
  characterStore.fetchCharacters();
});

const filteredCharacters = computed(() => {
  if (!searchQuery.value) return characterStore.characters;
  return characterStore.characters.filter((char) =>
    char.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
});

const selectCharacter = (char) => {
  if (activeCharacter.value && activeCharacter.value.id === char.id) {
    activeCharacter.value = null;
  } else {
    activeCharacter.value = char;
  }
};

const toggleSearch = () => {
  isSearchOpen.value = !isSearchOpen.value;
  if (!isSearchOpen.value) searchQuery.value = "";
};

const addBlock = () => {
  if (!activeCharacter.value) {
    alert("Wybierz najpierw postać z listy po lewej stronie!");
    return;
  }

  conversation.value.push({
    id: Date.now(),
    characterId: activeCharacter.value.id,
    characterName: activeCharacter.value.name,
    avatar: activeCharacter.value.avatar_path,
    text: "",
  });
};

const removeBlock = (index) => {
  conversation.value.splice(index, 1);
};

const generateAudiobook = () => {
  if (conversation.value.length === 0) {
    alert("Dodaj przynajmniej jedną kwestię dialogową!");
    return;
  }

  const isEmpty = conversation.value.some((block) => block.text.trim() === "");
  if (isEmpty) {
    alert("Niektóre kwestie są puste. Uzupełnij je przed generowaniem.");
    return;
  }

  const payload = {
    blocks: conversation.value.map((block) => ({
      character_id: block.characterId,
      text: block.text,
    })),
  };

  console.log(
    "🚀 GOTOWY JSON DO WYSŁANIA NA BACKEND:",
    JSON.stringify(payload, null, 2),
  );

  // TODO: Tutaj w przyszłości dodamy fetch("http://127.0.0.1:8000/audiobook/generate", { ... })
  alert("Sprawdź konsolę! JSON z konwersacją gotowy do wysłania.");
};

const getAvatarUrl = (path) => {
  if (!path) return "/emilia.png";

  const fixedPath = path.replace("characters/", "static_characters/");

  return `http://127.0.0.1:8000/${fixedPath}`;
};

const displayCharacterName = computed(() => {
  if (
    activeCharacter.value &&
    hoveredCharacter.value &&
    activeCharacter.value.id !== hoveredCharacter.value.id
  ) {
    return `Zmień na: ${hoveredCharacter.value.name.toUpperCase()}`;
  }
  if (hoveredCharacter.value) {
    return hoveredCharacter.value.name.toUpperCase();
  }
  if (activeCharacter.value) {
    return activeCharacter.value.name.toUpperCase();
  }
  return "WYBIERZ POSTAĆ";
});
</script>

<template>
  <div class="generate-view">
    <aside class="sidebar">
      <p class="hovered-character-name">
        {{ displayCharacterName }}
      </p>

      <div class="characters-grid">
        <div
          class="diamond-avatar"
          v-for="char in filteredCharacters"
          :key="char.id"
          :class="{ active: activeCharacter && activeCharacter.id === char.id }"
          @click="selectCharacter(char)"
          @mouseover="hoveredCharacter = char"
          @mouseleave="hoveredCharacter = null"
        >
          <div class="decor-frame frame-1"></div>
          <div class="decor-frame frame-2"></div>

          <div class="avatar-inner">
            <img :src="getAvatarUrl(char.avatar_path)" :alt="char.name" />
          </div>
        </div>
      </div>

      <div class="sidebar-bottom">
        <transition name="slide-fade">
          <input
            v-if="isSearchOpen"
            type="text"
            class="search-input"
            placeholder="Szukaj postaci..."
            v-model="searchQuery"
          />
        </transition>
        <button class="toggle-search-btn diamond-btn" @click="toggleSearch">
          <span
            :style="{
              transform: isSearchOpen ? 'rotate(180deg)' : 'rotate(0)',
            }"
            >↑</span
          >
        </button>
      </div>
    </aside>

    <section class="editor-section">
      <div class="sub-nav">
        <div>
          <button class="nav-btn active">BUILDER</button>
          <button class="nav-btn">LONG TEXT</button>
        </div>
        <div>
          <button class="nav-btn">LEKTOR</button>
          <button class="nav-btn">POSTACIE</button>
        </div>
      </div>

      <div class="conversation-area">
        <div
          class="dialogue-block"
          v-for="(block, index) in conversation"
          :key="block.id"
        >
          <div class="character-tag">
            <div class="mini-diamond">
              <img :src="getAvatarUrl(block.avatar)" alt="" />
            </div>
            <span>{{ block.characterName }}</span>
          </div>

          <textarea
            v-model="block.text"
            placeholder="Wpisz kwestię dialogową..."
          ></textarea>

          <button class="delete-btn" @click="removeBlock(index)">🗑️</button>
        </div>

        <button class="add-block-btn" @click="addBlock">
          <div class="add-icon">+</div>
        </button>
      </div>

      <div class="generate-bottom-bar">
        <h2>WYGENERUJ AUDIOBOOK</h2>
        <button
          class="generate-action-btn diamond-btn large"
          @click="generateAudiobook"
        >
          <span>🎶</span>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.generate-view {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 480px;
  background-color: var(--col-lbrown);
  padding: 20px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.characters-grid {
  display: grid;
  margin-top: 30px;
  grid-template-columns: repeat(6, 1fr);
  grid-auto-rows: 95px;
  flex: 1;
  overflow-y: auto;
  padding-bottom: 80px;
  padding-top: 25px;
}

.diamond-avatar:nth-child(5n + 1) {
  grid-column: 1 / span 2;
  justify-self: center;
}
.diamond-avatar:nth-child(5n + 2) {
  grid-column: 3 / span 2;
  justify-self: center;
}
.diamond-avatar:nth-child(5n + 3) {
  grid-column: 5 / span 2;
  justify-self: center;
}

.diamond-avatar:nth-child(5n + 4) {
  grid-column: 2 / span 2;
  justify-self: center;
}
.diamond-avatar:nth-child(5n + 5) {
  grid-column: 4 / span 2;
  justify-self: center;
}

.diamond-avatar {
  width: 120px;
  height: 120px;
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;

  display: flex;
  justify-content: center;
  align-items: center;
}

.diamond-avatar:hover {
  transform: scale(1.05);
}

.diamond-avatar.active .avatar-inner {
  box-shadow: 0 0 15px var(--col-orange);
}

.decor-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: transparent;
  width: 90px;
  height: 90px;
  z-index: 1;
}

.frame-1 {
  border: 3px solid var(--col-brown);
  transform: translate(-50%, -50%) rotate(60deg);
}

.frame-2 {
  border: 3px solid var(--col-lbrown);
  transform: translate(-50%, -50%) rotate(75deg);
}

.avatar-inner {
  position: relative;
  width: 95px;
  height: 95px;
  transform: rotate(45deg);

  background: var(--col-brown);

  border: 3px solid var(--col-light);
  overflow: hidden;
  transition: all 0.3s;
  box-sizing: border-box;
}

.avatar-inner img {
  width: 150%;
  height: 150%;
  transform: rotate(-45deg) translate(-15%, -15%);
  object-fit: cover;
}

.hovered-character-name {
  font-family: var(--font-bitroad);
  font-weight: bold;
  color: var(--col-dark);
  border: 2px solid var(--col-brown);
  width: 400px;
  min-height: 50px;
  border-radius: 10px;
  margin: auto;
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.sidebar-bottom {
  position: absolute;
  bottom: 20px;
  left: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.search-input {
  width: 80%;
  padding: 10px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  border-radius: 10px;
  font-family: var(--font-bitroad);
  text-align: center;
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

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}
.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1);
}
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.sub-nav {
  display: flex;
  padding: 20px;
  gap: 10px;
  justify-content: space-between;
}

.spacer {
  flex: 1;
}

.nav-btn {
  padding: 5px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  font-family: var(--font-bitroad);
  font-weight: bold;
  cursor: pointer;
}
.nav-btn.active {
  background-color: var(--col-lbrown);
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

.dialogue-block {
  width: 80%;
  background-color: var(--col-lbrown);
  border: 2px solid var(--col-brown);
  border-radius: 10px;
  position: relative;
  padding: 30px 20px 20px 20px;
}

.character-tag {
  position: absolute;
  top: -15px;
  left: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--col-light);
  padding: 5px 15px 5px 5px;
  border: 2px solid var(--col-brown);
  border-radius: 20px;
  font-weight: bold;
}

.mini-diamond {
  width: 25px;
  height: 25px;
  transform: rotate(45deg);
  border: 1px solid var(--col-brown);
  overflow: hidden;
}

.mini-diamond img {
  width: 150%;
  height: 150%;
  transform: rotate(-45deg) translate(-15%, -15%);
  object-fit: cover;
}

.dialogue-block textarea {
  width: 100%;
  min-height: 80px;
  background: transparent;
  border: none;
  resize: vertical;
  font-family: var(--font-breite), sans-serif;
  font-size: 1.1rem;
  color: var(--col-dark);
}

.dialogue-block textarea:focus {
  outline: none;
}

.delete-btn {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1.2rem;
  opacity: 0.6;
}

.delete-btn:hover {
  opacity: 1;
}

.add-block-btn {
  width: 40%;
  border: 2px dashed var(--col-brown);
  background: transparent;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  justify-content: center;
}
.add-block-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.add-icon {
  width: 40px;
  height: 40px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: bold;
  font-size: 1.2rem;
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

.diamond-btn.large {
  width: 60px;
  height: 60px;
  border: 2px solid var(--col-light);
  background: transparent;
}
</style>
