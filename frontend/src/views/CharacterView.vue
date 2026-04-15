<template>
  <div class="character-view">
    <form class="character-form" action="">
      <label for="avatar"
        >Wybierz Avatar
        <input type="file" name="avatar" id="avatar" required />
      </label>

      <label for="character-name"
        >Nazwa Postaci

        <input type="text" name="character-name" id="character-name" required />
      </label>

      <label for="description"
        >Opis
        <textarea name="description" id="description"></textarea>
      </label>

      <label for="provider"
        >Wybierz Model

        <select name="provider" id="provider" required>
          <option value="">Wybierz Model</option>
          <option value="coqui_xtts_v2">XTTS_V2</option>
          <option value="qwen_design">QWEN DESIGN</option>
          <option value="qwen_custom">QWEN CUSTOM</option>
          <option value="qwen_base">QWEN BASE</option>
          <option value="omnivoice">OMNIVOICE</option>
        </select>
      </label>

      <label for="text-to-generate"
        >Tekst do wygenerowania

        <textarea name="text-to-generate" id="text-to-generate"></textarea>
      </label>

      <label for="voice-to-clone"
        >Wybierz głos do klonowania

        <input
          type="file"
          name="voice-to-clone"
          id="voice-to-clone"
          accept="audio/*"
        />
      </label>

      <label for="character-name"
        >Prompt dla głosu

        <input type="text" name="character-name" id="character-name" required />
      </label>

      <input type="submit" value="Wygeneruj głos" />
      <input type="submit" value="Zapisz Postać" />
    </form>
  </div>
</template>

<style scoped>
.character-view {
  max-width: 500px;
  margin: auto;
}

.character-form {
  display: flex;
  flex-direction: column;
  margin: 40px auto;
}

.character-form input,
.character-form textarea,
.character-form select {
  border-radius: 14px;
  padding: 10px 15px;
  border: 2px solid var(--col-brown);
  background-color: var(--col-light);
  text-decoration: none;
  color: var(--border-color);
  font-weight: bold;
  cursor: pointer;
  text-align: center;
  font-family: var(--font-bitroad);
  font-size: 1.2rem;
  letter-spacing: 1px;
}

.character-form label {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.character-form textarea {
  height: 200px;
  max-width: 100%;
  resize: none;
}

.character-form input[type="submit"] {
  padding: 10px 20px;
  border-radius: 14px;
  border: none;
  background-color: var(--col-brown);
  color: var(--col-light);
  font-weight: bold;
  cursor: pointer;
  text-align: center;
  font-family: var(--font-bitroad);
  font-size: 1.2rem;
  letter-spacing: 1px;
}

.character-form input[type="submit"]:hover {
  background-color: var(--col-orange);
}

.character-form input[type="submit"]:first-of-type {
  margin-top: 20px;
  margin-bottom: 20px;
}
</style>
