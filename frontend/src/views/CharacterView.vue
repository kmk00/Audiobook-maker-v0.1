<script setup>
import { reactive, ref, computed } from "vue";
import { onBeforeRouteLeave } from "vue-router";
import { useCharacterStore } from "../stores/characterStore";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "../components/LoadingOverlay.vue"; // IMPORT LOADERA

const characterStore = useCharacterStore();

const isLoading = ref(false);
const loadingText = ref("");
const canSave = ref(false);
const isSaved = ref(false);
const generatedAudioUrl = ref(null);
const tempAudioPath = ref(null);
const tagInput = ref("");

const toaster = createToaster({
  position: "top-right",
  duration: 3000,
});

const form = reactive({
  avatar: null,
  characterName: "dsadsa",
  category: "",
  tags: [],
  description: "",
  provider: "",
  textToGenerate: "Please tell me a secret, but be honest.",

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

const availableTags = computed(() => {
  const allTags = new Set();
  characterStore.characters.forEach((char) => {
    if (char.tags && Array.isArray(char.tags)) {
      char.tags.forEach((tag) => allTags.add(tag));
    }
  });
  return Array.from(allTags);
});

const suggestedTags = computed(() => {
  if (!tagInput.value) return [];
  const lowerInput = tagInput.value.toLowerCase();
  return availableTags.value.filter(
    (tag) => tag.toLowerCase().includes(lowerInput) && !form.tags.includes(tag),
  );
});

const addTag = (specificTag = null) => {
  const newTag = specificTag || tagInput.value.trim();
  if (newTag && !form.tags.includes(newTag)) {
    form.tags.push(newTag);
  }
  tagInput.value = "";
};

const removeTag = (index) => {
  form.tags.splice(index, 1);
};

const handleFileUpload = (field, event) => {
  form[field] = event.target.files[0];
};

const availableCategories = computed(() => {
  const categories = new Set();
  characterStore.characters.forEach((char) => {
    if (char.category) {
      categories.add(char.category);
    }
  });
  return Array.from(categories);
});

const suggestedCategories = computed(() => {
  const input = form.category.trim().toLowerCase();
  if (!input) return [];

  return availableCategories.value.filter(
    (cat) => cat.toLowerCase().includes(input) && cat.toLowerCase() !== input,
  );
});

const selectCategory = (name) => {
  form.category = name;
};

const validateForm = () => {
  if (!form.provider) {
    toaster.warning("Wybierz model przed wygenerowaniem głosu!");
    return false;
  }
  if (!form.characterName) {
    toaster.warning("Podaj nazwę postaci!");
    return false;
  }
  return true;
};

const validateXTTSForm = () => {
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  if (!form.xttsLanguage) {
    toaster.warning("Wybierz język!");
    return false;
  }
  if (!form.voiceToClone) {
    toaster.warning("Wybierz głos do sklonowania!");
    return false;
  }
  return true;
};

const validateQwenDesignForm = () => {
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  if (!form.qwenLanguage) {
    toaster.warning("Wybierz język!");
    return false;
  }
  return true;
};

const validateQwenCustomForm = () => {
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  if (!form.qwenTimbre) {
    toaster.warning("Wybierz Timbre!");
    return false;
  }
  return true;
};

const validateQwenBaseForm = () => {
  if (!form.voiceToClone) {
    toaster.warning("Wybierz głos do sklonowania!");
    return false;
  }
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  return true;
};

const validateOmnivoiceForm = (mode) => {
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  if (mode === "voice_cloning" && !form.voiceToClone) {
    toaster.warning("Wybierz głos do sklonowania!");
    return false;
  }
  if (
    mode === "voice_design" &&
    !form.omniGender &&
    !form.omniAge &&
    !form.omniPitch
  ) {
    toaster.warning("Wybierz styl głosu!");
    return false;
  }
  return true;
};

const generateVoice = async () => {
  if (!validateForm()) return;

  const payload = {
    provider: form.provider,
    text: form.textToGenerate,
  };

  switch (form.provider) {
    case "coqui_xtts_v2":
      if (!validateXTTSForm()) return;
      payload.language = form.xttsLanguage;
      payload.voiceToClone = form.voiceToClone?.name || null;
      break;
    case "qwen_design":
      if (!validateQwenDesignForm()) return;
      payload.language = form.qwenLanguage;
      payload.voicePrompt = form.voicePrompt;
      break;
    case "qwen_custom":
      if (!validateQwenCustomForm()) return;
      payload.timbre = form.qwenTimbre;
      payload.voicePrompt = form.voicePrompt;
      break;
    case "qwen_base":
      if (!validateQwenBaseForm()) return;
      payload.voiceToClone = form.voiceToClone?.name || null;
      payload.voicePrompt = form.voicePrompt;
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
      break;
  }

  const formData = new FormData();
  formData.append("text", form.textToGenerate);
  formData.append("provider", form.provider);
  if (form.voiceToClone) formData.append("voiceToClone", form.voiceToClone);
  formData.append("options", JSON.stringify(payload));

  loadingText.value = "Generowanie próbki głosu...";
  isLoading.value = true;

  try {
    const response = await fetch("http://127.0.0.1:8000/tts/generate", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    tempAudioPath.value = data.audio_path;
    generatedAudioUrl.value = `http://127.0.0.1:8000${data.audio_path}`;
    canSave.value = true;

    toaster.success("Próbka głosu została pomyślnie wygenerowana!");
  } catch (error) {
    toaster.error("Błąd podczas generowania głosu.");
  } finally {
    isLoading.value = false;
  }
};

const saveCharacter = async () => {
  const formData = new FormData();
  formData.append("name", form.characterName);
  formData.append("provider", form.provider);

  if (form.description) formData.append("description", form.description);
  if (form.voicePrompt) formData.append("voice_prompt", form.voicePrompt);
  if (form.category) formData.append("category", form.category);
  formData.append("tags", JSON.stringify(form.tags));

  let lang = "";
  if (form.provider === "coqui_xtts_v2") lang = form.xttsLanguage;
  if (form.provider === "qwen_design") lang = form.qwenLanguage;
  if (lang) formData.append("language", lang);

  const options = {};
  if (form.provider === "qwen_custom") {
    options.timbre = form.qwenTimbre;
  } else if (form.provider === "omnivoice") {
    options.mode = form.omnivoiceMode;
    if (form.omnivoiceMode === "voice_design") {
      options.gender = form.omniGender;
      options.age = form.omniAge;
      options.pitch = form.omniPitch;
      options.style = form.omniStyle;
      options.accent = form.omniAccent;
      options.dialect = form.omniDialect;
    }
  }
  formData.append("provider_options", JSON.stringify(options));
  if (tempAudioPath.value) {
    formData.append("temp_preview_path", tempAudioPath.value);
  }

  if (form.voiceToClone) {
    formData.append("voice_file", form.voiceToClone);
  }
  if (form.avatar) {
    formData.append("avatar_file", form.avatar);
  }

  loadingText.value = "Zapisywanie postaci w bazie...";
  isLoading.value = true;

  try {
    const response = await fetch("http://127.0.0.1:8000/characters/", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Błąd zapisu postaci na serwerze");
    }

    const savedCharacter = await response.json();
    characterStore.characters.push(savedCharacter);
    isSaved.value = true;

    toaster.success(`Postać "${savedCharacter.name}" została zapisana!`);
  } catch (error) {
    toaster.error("Nie udało się zapisać postaci: " + error.message);
  } finally {
    isLoading.value = false;
  }
};

onBeforeRouteLeave(async (to, from, next) => {
  if (tempAudioPath.value && !isSaved.value) {
    try {
      await fetch(`http://127.0.0.1:8000/tts/temp`, {
        method: "DELETE",
      });
    } catch (error) {
      console.error("Network error", error);
    }
  }
  next();
});
</script>

<template>
  <div class="character-view">
    <LoadingOverlay v-if="isLoading" :text="loadingText" />

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

      <label for="category" class="category-wrapper">
        Kategoria (np. Tytuł książki)
        <input
          type="text"
          id="category"
          v-model="form.category"
          placeholder="Zostaw puste, jeśli brak"
          autocomplete="off"
        />

        <div
          class="suggestions-box category-suggestions"
          v-if="suggestedCategories.length"
        >
          <p>Istniejące kategorie:</p>
          <div class="suggestions-list">
            <span
              class="suggestion-pill"
              v-for="cat in suggestedCategories"
              :key="cat"
              @click="selectCategory(cat)"
            >
              {{ cat }}
            </span>
          </div>
        </div>
      </label>

      <div class="custom-label">
        <span style="margin-bottom: 5px">Tagi postaci</span>
        <div class="tags-container">
          <div class="selected-tags" v-if="form.tags.length">
            <span
              class="tag-pill"
              v-for="(tag, index) in form.tags"
              :key="index"
            >
              {{ tag }}
              <button class="remove-tag-btn" @click.prevent="removeTag(index)">
                ×
              </button>
            </span>
          </div>

          <input
            type="text"
            v-model="tagInput"
            @keydown.enter.prevent="addTag()"
            @keydown.space.prevent="addTag()"
            placeholder="Wpisz tag i wciśnij Enter/Spację..."
          />

          <div class="suggestions-box" v-if="suggestedTags.length">
            <p>Podpowiedzi:</p>
            <div class="suggestions-list">
              <span
                class="suggestion-pill"
                v-for="tag in suggestedTags"
                :key="tag"
                @click="addTag(tag)"
              >
                + {{ tag }}
              </span>
            </div>
          </div>
        </div>
      </div>

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
          <!-- <option value="qwen_base">4. QWEN BASE</option> -->
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

      <div
        v-if="generatedAudioUrl"
        style="margin-bottom: 20px; text-align: center"
      >
        <p style="font-family: var(--font-bitroad); color: var(--col-brown)">
          Podgląd wygenerowanego głosu:
        </p>
        <audio
          :src="generatedAudioUrl"
          controls
          style="border-radius: 14px; border: 2px solid var(--col-brown)"
        ></audio>
      </div>

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

.category-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
}

.category-suggestions {
  margin-top: 5px;
  border-style: solid;
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

.tags-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: 5px;
}

.tag-pill {
  background-color: var(--col-brown);
  color: var(--col-light);
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.remove-tag-btn {
  background: none;
  border: none;
  color: var(--col-orange);
  cursor: pointer;
  font-weight: bold;
  padding: 0;
  font-size: 1.1rem;
}

.suggestions-box {
  background-color: rgba(0, 0, 0, 0.05);
  border: 1px dashed var(--col-brown);
  border-radius: 10px;
  padding: 10px;
  font-size: 0.9rem;
}

.character-form label,
.custom-label {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.suggestions-box p {
  margin: 0 0 8px 0;
  color: var(--col-brown);
}

.suggestions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-pill {
  background-color: transparent;
  color: var(--col-brown);
  border: 1px solid var(--col-brown);
  padding: 4px 10px;
  border-radius: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-pill:hover {
  background-color: var(--col-brown);
  color: var(--col-light);
}
</style>
