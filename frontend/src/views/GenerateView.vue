<template>
  <div class="generate-view">
    <aside class="sidebar">
      <div class="characters-grid">
        <div class="diamond-avatar" v-for="i in 8" :key="i">
          <div class="avatar-inner">
            <img src="/emilia.png" alt="Emilia" />
          </div>
          <span class="avatar-name">EMILIA</span>
        </div>
      </div>
      <button class="add-char-btn diamond-btn">↑</button>
    </aside>

    <section class="editor-section">
      <div class="sub-nav">
        <button class="nav-btn">BUILDER</button>
        <button class="nav-btn">LONG TEXT</button>
        <button class="nav-btn">LEKTOR</button>
        <button class="nav-btn">POSTACIE</button>
      </div>

      <div class="content-area">
        <h2>WKLEJ TEKST</h2>
        <textarea
          class="text-input"
          placeholder="Wklej swój tekst tutaj..."
        ></textarea>

        <h2>IMPORTUJ TEKST Z PLIKU</h2>
        <div class="import-buttons">
          <button class="import-btn">.TXT</button>
          <button class="import-btn">.PDF</button>
          <button class="import-btn">.EPUB</button>
        </div>
      </div>

      <button class="generate-action-btn diamond-btn">L</button>
    </section>
  </div>
</template>

<style scoped>
.generate-view {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 300px;
  background-color: #decfb1;
  border-right: 3px solid var(--border-color);
  padding: 20px;
  position: relative;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
}

/* Magia Diamentowych Avatarów */
.diamond-avatar {
  width: 80px;
  height: 80px;
  position: relative;
  margin: 0 auto;
}

.avatar-inner {
  width: 100%;
  height: 100%;
  transform: rotate(45deg);
  border: 2px solid var(--border-color);
  overflow: hidden;
  background: white;
}

.avatar-inner img {
  width: 140%;
  height: 140%;
  transform: rotate(-45deg) translate(-15%, -15%); /* Odkręcamy obrazek wewnątrz */
  object-fit: cover;
}

.avatar-name {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
}

.editor-section {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  position: relative;
  /* Dodanie pionowych pasów z tła */
  background: repeating-linear-gradient(
    90deg,
    transparent,
    transparent 50px,
    rgba(0, 0, 0, 0.03) 50px,
    rgba(0, 0, 0, 0.03) 100px
  );
}

.sub-nav {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-bottom: 40px;
}

.content-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.text-input {
  width: 80%;
  height: 150px;
  border: 2px solid var(--border-color);
  background-color: var(--btn-bg);
  border-radius: 10px;
  margin-bottom: 40px;
  resize: none;
}

.import-buttons {
  display: flex;
  gap: 20px;
}

.import-btn {
  padding: 10px 40px;
  border: 2px solid var(--border-color);
  background-color: var(--btn-bg);
  border-radius: 20px;
  cursor: pointer;
}
</style>
