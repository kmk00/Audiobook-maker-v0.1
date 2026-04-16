<script setup>
import { reactive, ref } from "vue";

const form = reactive({
  avatar: null,
  characterName: "dsadsa",
  description: "",
  provider: "xtts_v2",
  textToGenerate: "dsadsa",

  voiceToClone: null,

  xttsLanguage: "en",

  qwenLanguage: "English",
  voicePrompt: "",
  qwenTimbre: "Timbre 1",

  omnivoiceMode: "voice_design",
  omniGender: "male",
  omniAge: "young adult",
  omniPitch: "moderate pitch",
  omniStyle: "",
  omniAccent: "",
  omniDialect: "",
});

const canSave = ref(false);

const handleFileUpload = (field, event) => {
  form[field] = event.target.files[0];
};

const validateForm = () => {
  if (!form.provider) {
    console.error("Wybierz model przed wygenerowaniem głosu!");
    alert("Wybierz model!");
    return;
  }

  if (!form.characterName) {
    console.error("Podaj nazwę postaci!");
    alert("Podaj nazwę postaci!");
    return false;
  }
};

const validateXTTSForm = () => {
  console.log("XTTS form validation:", form);

  if (!form.textToGenerate) {
    console.error("Podaj tekst do wygenerowania głosu!");
    alert("Podaj tekst do wygenerowania głosu!");
    return false;
  }

  if (!form.xttsLanguage) {
    console.error("Wybierz język przed wygenerowaniem głosu!");
    alert("Wybierz język!");
    return false;
  }

  if (!form.voiceToClone) {
    console.error("Wybierz głos do sklonowania!");
    alert("Wybierz głos do sklonowania!");
    return false;
  }

  return true;
};

const validateQwenDesignForm = () => {
  console.log("QWEN form validation:", form);

  if (!form.textToGenerate) {
    console.error("Podaj tekst do wygenerowania głosu!");
    alert("Podaj tekst do wygenerowania głosu!");
    return false;
  }

  if (!form.qwenLanguage) {
    console.error("Wybierz język przed wygenerowaniem głosu!");
    alert("Wybierz język!");
    return false;
  }

  return true;
};

const validateQwenCustomForm = () => {
  console.log("QWEN form validation:", form);

  if (!form.textToGenerate) {
    console.error("Podaj tekst do wygenerowania głosu!");
    alert("Podaj tekst do wygenerowania głosu!");
    return false;
  }

  if (!form.qwenTimbre) {
    console.error("Wybierz Timbre przed wygenerowaniem głosu!");
    alert("Wybierz Timbre!");
    return false;
  }

  return true;
};

const validateQwenBaseForm = () => {
  console.log("QWEN base form validation:", form);

  if (!form.voiceToClone) {
    console.error("Wybierz głos do sklonowania!");
    alert("Wybierz głos do sklonowania!");
    return false;
  }

  if (!form.textToGenerate) {
    console.error("Podaj tekst do wygenerowania głosu!");
    alert("Podaj tekst do wygenerowania głosu!");
    return false;
  }

  return true;
};

const validateOmnivoiceForm = (mode) => {
  console.log("Omnivoice form validation:", form);

  if (!form.textToGenerate) {
    console.error("Podaj tekst do wygenerowania głosu!");
    alert("Podaj tekst do wygenerowania głosu!");
    return false;
  }

  if (mode === "voice_cloning" && !form.voiceToClone) {
    console.error("Wybierz głos do sklonowania!");
    alert("Wybierz głos do sklonowania!");
    return false;
  }

  if (
    mode === "voice_design" &&
    !form.omniGender &&
    !form.omniAge &&
    !form.omniPitch
  ) {
    console.error("Wybierz styl głosu!");
    alert("Wybierz styl głosu!");
    return false;
  }

  return true;
};

const generateVoice = () => {
  const payload = {
    provider: form.provider,
    text: form.textToGenerate,
  };

  switch (form.provider) {
    case "coqui_xtts_v2":
      if (!validateXTTSForm()) return;
      payload.language = form.xttsLanguage;
      payload.voiceToClone = form.voiceToClone?.name || null;
      console.log("--- WYSYŁANY OBIEKT DO BACKENDU XTTS ---", payload);
      canSave.value = true;
      break;

    case "qwen_design":
      if (!validateQwenDesignForm()) return;
      payload.language = form.qwenLanguage;
      payload.voicePrompt = form.voicePrompt;
      console.log("--- WYSYŁANY OBIEKT DO BACKENDU QWEN ---", payload);
      canSave.value = true;
      break;

    case "qwen_custom":
      if (!validateQwenCustomForm()) return;
      payload.timbre = form.qwenTimbre;
      payload.voicePrompt = form.voicePrompt;
      console.log("--- WYSYŁANY OBIEKT DO BACKENDU QWEN ---", payload);
      canSave.value = true;
      break;

    case "qwen_base":
      if (!validateQwenBaseForm()) return;
      payload.voiceToClone = form.voiceToClone?.name || null;
      payload.voicePrompt = form.voicePrompt;
      console.log("--- WYSYŁANY OBIEKT DO BACKENDU QWEN ---", payload);
      canSave.value = true;
      break;

    case "omnivoice":
      payload.mode = form.omnivoiceMode;

      if (!validateOmnivoiceForm(form.omnivoiceMode)) return;

      if (form.omnivoiceMode === "voice_design") {
        payload.attributes = {
          gender: form.omniGender,
          age: form.omniAge,
          pitch: form.omniPitch,
          style: form.omniStyle,
          englishAccent: form.omniAccent,
          chineseDialect: form.omniDialect,
        };
      } else {
        payload.voiceToClone = form.voiceToClone?.name || null;
      }

      console.log("--- WYSYŁANY OBIEKT DO BACKENDU OMNIVOICE ---", payload);
      canSave.value = true;
      break;
  }
};

const saveCharacter = () => {
  console.log("💾 Zapisywanie postaci ze wszystkimi danymi:", form);
};
</script>

<template>
  <div class="character-view">
    <form class="character-form" @submit.prevent>
      <label for="avatar">
        Wybierz Avatar
        <input
          type="file"
          id="avatar"
          accept="image/*"
          @change="handleFileUpload('avatar', $event)"
        />
      </label>

      <label for="character-name">
        Nazwa Postaci
        <input
          type="text"
          id="character-name"
          v-model="form.characterName"
          required
        />
      </label>

      <label for="description">
        Opis
        <textarea id="description" v-model="form.description"></textarea>
      </label>

      <label for="provider">
        Wybierz Model
        <select id="provider" v-model="form.provider" required>
          <option value="" disabled>Wybierz Model</option>
          <option value="coqui_xtts_v2">1. XTTS</option>
          <option value="qwen_design">2. QWEN DESIGN</option>
          <option value="qwen_custom">3. QWEN CUSTOM</option>
          <option value="qwen_base">4. QWEN BASE</option>
          <option value="omnivoice">5. OMNIVOICE</option>
        </select>
      </label>

      <template v-if="form.provider === 'coqui_xtts_v2'">
        <label for="xtts-lang">
          Język (XTTS)
          <select id="xtts-lang" v-model="form.xttsLanguage">
            <option value="en">English (en)</option>
            <option value="pl">Polish (pl)</option>
            <option value="de">German (de)</option>
            <option value="es">Spanish (es)</option>
            <option value="fr">French (fr)</option>
          </select>
        </label>
        <label for="voice-to-clone">
          Wybierz głos do sklonowania
          <input
            type="file"
            id="voice-to-clone"
            accept="audio/*"
            @change="handleFileUpload('voiceToClone', $event)"
          />
        </label>
      </template>

      <template v-if="form.provider === 'qwen_design'">
        <label for="qwen-lang">
          Język (Qwen)
          <select id="qwen-lang" v-model="form.qwenLanguage">
            <option value="English">English</option>
            <option value="Chinese">Chinese</option>
            <option value="Polish">Polish</option>
          </select>
        </label>
        <label for="voice-prompt">
          Voice Prompt (Instrukcje)
          <textarea
            id="voice-prompt"
            v-model="form.voicePrompt"
            placeholder="Np. old wise man speaking softly"
          ></textarea>
          <div class="prompt-examples">
            <p class="prompt-example">Ex.</p>
            <p class="prompt-example">gender: Male</p>
            <p class="prompt-example">
              pitch: Low male pitch with significant upward inflections for
              emphasis and excitement.
            </p>
            <p class="prompt-example">old wise man speaking softly</p>
            <p class="prompt-example">
              speed: Fast-paced delivery with deliberate pauses for dramatic
              effect.
            </p>
            <p class="prompt-example">
              volume: Loud and projecting, increasing notably during moments of
              praise and announcements.
            </p>
            <p class="prompt-example">age: Young adult to middle-aged adult.</p>
            <p class="prompt-example">
              clarity: Highly articulate and distinct pronunciation.
            </p>
            <p class="prompt-example">
              fluency: Very fluent speech with no hesitations.
            </p>
            <p class="prompt-example">accent: British English.</p>
            <p class="prompt-example">
              texture: Bright and clear vocal texture.
            </p>
            <p class="prompt-example">
              emotion: Enthusiastic and excited, especially when complimenting.
            </p>
            <p class="prompt-example">
              tone: Upbeat, authoritative, and performative.
            </p>
            <p class="prompt-example">
              personality: Confident, extroverted, and engaging.
            </p>
          </div>
        </label>
      </template>

      <template v-if="form.provider === 'qwen_custom'">
        <label for="qwen-timbre">
          Wybierz Timbre
          <select id="qwen-timbre" v-model="form.qwenTimbre">
            <option value="苏瑶 Serena">苏瑶 Serena (Chinese)</option>
            <option value="福伯 Uncle Fu">福伯 Uncle Fu (Chinese)</option>
            <option value="十三 Vivian">十三 Vivian (Chinese)</option>
            <option value="艾登 Aiden">艾登 Aiden (English)</option>
            <option value="甜茶 Ryan">甜茶 Ryan (English)</option>
            <option value="小野杏 Ono Anna">小野杏 Ono Anna (Japanese)</option>
            <option value="素熙 Sohee">素熙 Sohee (Korean)</option>
            <option value="晓东 Dylan">
              晓东 Dylan (Chinese Dialect - Beijing Dialect)
            </option>
            <option value="程川 Eric">
              程川 Eric (Chinese Dialect - Sichuan Dialect)
            </option>
          </select>
        </label>
        <label for="voice-prompt">
          Voice Prompt (Instrukcje)
          <input
            type="text"
            id="voice-prompt"
            v-model="form.voicePrompt"
            placeholder="Instrukcje generowania głosu..."
          />
        </label>
      </template>

      <template v-if="form.provider === 'qwen_base'">
        <label for="voice-to-clone">
          Wybierz głos do sklonowania
          <input
            type="file"
            id="voice-to-clone"
            accept="audio/*"
            @change="handleFileUpload('voiceToClone', $event)"
          />
        </label>
      </template>

      <template v-if="form.provider === 'omnivoice'">
        <label for="omni-mode">
          Tryb Omnivoice
          <select id="omni-mode" v-model="form.omnivoiceMode">
            <option value="voice_design">Voice Design (Atrybuty)</option>
            <option value="voice_cloning">Voice Cloning (Z pliku)</option>
          </select>
        </label>

        <template v-if="form.omnivoiceMode === 'voice_design'">
          <label
            >Gender
            <select v-model="form.omniGender">
              <option value="male">Male (男)</option>
              <option value="female">Female (女)</option>
            </select></label
          >
          <label
            >Age
            <select v-model="form.omniAge">
              <option value="child">Child (儿童)</option>
              <option value="teenager">Teenager (少年)</option>
              <option value="young adult">Young Adult (青年)</option>
              <option value="middle-aged">Middle-aged (中年)</option>
              <option value="elderly">Elderly (老年)</option>
            </select>
          </label>
          <label
            >Pitch
            <select v-model="form.omniPitch">
              <option value="very low pitch">Very Low</option>
              <option value="low pitch">Low</option>
              <option value="moderate pitch">Moderate</option>
              <option value="high pitch">High</option>
              <option value="very high pitch">Very High</option>
            </select>
          </label>
          <label
            >Style (Opcjonalnie)
            <select v-model="form.omniStyle">
              <option value="">Brak (Domyślny)</option>
              <option value="whisper">Whisper (Szept)</option>
            </select>
          </label>
          <label
            >English Accent (Dla j. angielskiego)
            <select v-model="form.omniAccent">
              <option value="">Brak akcentu</option>
              <option value="american accent">American</option>
              <option value="british accent">British</option>
              <option value="australian accent">Australian</option>
              <option value="indian accent">Indian</option>
            </select>
          </label>
          <label
            >Chinese Dialect (Dla j. chińskiego)
            <select v-model="form.omniDialect">
              <option value="">Brak dialektu</option>
              <option value="河南话">河南话</option>
              <option value="陕西话">陕西话</option>
              <option value="四川话">四川话</option>
            </select>
          </label>
        </template>

        <template v-if="form.omnivoiceMode === 'voice_cloning'">
          <label for="voice-to-clone">
            Wybierz głos do sklonowania
            <input
              type="file"
              id="voice-to-clone"
              accept="audio/*"
              @change="handleFileUpload('voiceToClone', $event)"
            />
          </label>
        </template>
      </template>

      <label v-if="form.provider" for="text-to-generate">
        Tekst do wygenerowania
        <textarea
          id="text-to-generate"
          v-model="form.textToGenerate"
          placeholder="Wpisz tekst..."
          required
        ></textarea>
      </label>

      <input type="submit" value="Wygeneruj głos" @click="generateVoice" />
      <input
        type="submit"
        value="Zapisz Postać"
        @click="saveCharacter"
        :disabled="!canSave"
      />
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

.prompt-examples p {
  display: flex;
  flex-direction: column;
  margin: 5px 30px;
  text-align: left;
  font-size: 0.9rem;
  color: var(--col-brown);
}

.character-form input[type="submit"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.character-form input[type="submit"]:disabled:hover {
  background-color: var(--col-brown);
}
</style>
