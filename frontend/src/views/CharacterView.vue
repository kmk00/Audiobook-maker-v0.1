<template>
  <div class="character-view">
    <div class="form-container">
      <div class="diamond-avatar large">
        <div class="avatar-inner">
          <img src="/emilia.png" alt="Emilia" />
        </div>
      </div>

      <input type="text" class="custom-input" value="EMILIA" />

      <textarea class="custom-input large-input" placeholder="OPIS"></textarea>

      <div class="toggle-buttons">
        <button class="nav-btn active">GENEROWANIE</button>
        <button class="nav-btn">KLONOWANIE</button>
      </div>

      <textarea
        class="custom-input large-input"
        placeholder="PROMPT"
      ></textarea>

      <button class="save-btn diamond-btn">
        <span>💾</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.character-view {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: repeating-linear-gradient(
    90deg,
    transparent,
    transparent 50px,
    rgba(0, 0, 0, 0.03) 50px,
    rgba(0, 0, 0, 0.03) 100px
  );
}

.form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  width: 500px;
}

.custom-input {
  width: 100%;
  padding: 15px;
  border: 2px solid var(--border-color);
  background-color: var(--btn-bg);
  border-radius: 10px;
  text-align: center;
  font-family: inherit;
}

.large-input {
  height: 100px;
  resize: none;
}

.toggle-buttons {
  display: flex;
  gap: 10px;
}

.nav-btn.active {
  background-color: #fff;
}

/* Ponowne użycie diamentu, ale większego */
.diamond-avatar.large {
  width: 100px;
  height: 100px;
  margin-bottom: 20px;
}
.avatar-inner {
  width: 100%;
  height: 100%;
  transform: rotate(45deg);
  border: 2px solid var(--border-color);
  overflow: hidden;
}
.avatar-inner img {
  width: 140%;
  height: 140%;
  transform: rotate(-45deg) translate(-15%, -15%);
}

.save-btn {
  width: 60px;
  height: 60px;
  transform: rotate(45deg);
  background-color: var(--border-color);
  border: none;
  cursor: pointer;
  margin-top: 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.save-btn span {
  transform: rotate(-45deg);
  color: white;
  font-size: 24px;
}
</style>
