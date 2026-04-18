<script setup>
import { ref, computed, onMounted } from "vue";
import { useCharacterStore } from "../stores/characterStore";
import BuilderMode from "../components/BuilderMode.vue";
import LongTextMode from "../components/LongTextMode.vue";

const characterStore = useCharacterStore();

const searchQuery = ref("");
const isSearchOpen = ref(false);
const activeCharacter = ref(null);
const hoveredCharacter = ref(null);

const currentMode = ref("builder");

onMounted(() => {
  characterStore.fetchCharacters();
});

const filteredCharacters = computed(() => {
  if (!searchQuery.value) return characterStore.characters;
  return characterStore.characters.filter((char) =>
    char.name.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
});

const groupedCharacters = computed(() => {
  const groups = {};

  filteredCharacters.value.forEach((char) => {
    const cat = char.category ? char.category.trim() : "Inne";
    if (!groups[cat]) {
      groups[cat] = [];
    }
    groups[cat].push(char);
  });

  return Object.keys(groups)
    .sort((a, b) => {
      if (a === "Inne") return 1;
      if (b === "Inne") return -1;
      return a.localeCompare(b);
    })
    .map((cat) => ({
      category: cat,
      characters: groups[cat],
    }));
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

      <div class="sidebar-scroll-area">
        <div
          v-for="group in groupedCharacters"
          :key="group.category"
          class="category-group"
        >
          <div class="category-header">
            <h3>{{ group.category.toUpperCase() }}</h3>
            <div class="category-line"></div>
          </div>

          <div class="characters-grid">
            <div
              class="diamond-avatar"
              v-for="char in group.characters"
              :key="char.id"
              :class="{
                active: activeCharacter && activeCharacter.id === char.id,
              }"
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
          <button
            :class="['nav-btn', { active: currentMode === 'builder' }]"
            @click="currentMode = 'builder'"
          >
            BUILDER
          </button>
          <button
            :class="['nav-btn', { active: currentMode === 'longtext' }]"
            @click="currentMode = 'longtext'"
          >
            LONG TEXT
          </button>
        </div>
      </div>
      <BuilderMode
        v-if="currentMode === 'builder'"
        :activeCharacter="activeCharacter"
      />
      <LongTextMode
        v-else-if="currentMode === 'longtext'"
        :activeCharacter="activeCharacter"
      />
    </section>
  </div>
</template>

<style scoped>
.generate-view {
  display: flex;
  height: 100%;
  padding-bottom: 78px;
}

.sidebar {
  width: 480px;
  background-color: var(--col-lbrown);
  padding: 20px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.sidebar-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 80px;
  margin-top: 20px;
  padding-right: 10px;
}

.sidebar-scroll-area::-webkit-scrollbar {
  width: 6px;
}
.sidebar-scroll-area::-webkit-scrollbar-thumb {
  background-color: var(--col-brown);
  border-radius: 10px;
}

.category-group {
  margin-bottom: 30px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.category-header h3 {
  font-family: var(--font-bitroad);
  color: var(--col-brown);
  margin: 0;
  font-size: 1.1rem;
  white-space: nowrap;
}

.category-line {
  flex: 1;
  height: 2px;
  background-color: var(--col-brown);
  opacity: 0.3;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  grid-auto-rows: 95px;
  padding-top: 15px;
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
  z-index: 1;
}
.frame-1 {
  width: 90px;
  height: 90px;
  border: 3px solid var(--col-brown);
  transform: translate(-50%, -50%) rotate(60deg);
}
.frame-2 {
  width: 90px;
  height: 90px;
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
  width: 100%;
  height: 100%;
  transform: rotate(-45deg) scale(1.4);
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
</style>
