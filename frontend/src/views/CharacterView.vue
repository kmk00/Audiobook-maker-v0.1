<script setup>
import { reactive, ref, computed } from "vue";
import { onBeforeRouteLeave } from "vue-router";
import { useCharacterStore } from "../stores/characterStore";
import { createToaster } from "@meforma/vue-toaster";
import LoadingOverlay from "../components/LoadingOverlay.vue";

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
  characterName: "",
  category: "",
  tags: [],
  description: "",
  provider: "",
  textToGenerate: "",

  voiceToClone: null,
  xttsLanguage: "en",
  qwenLanguage: "English",
  voicePrompt: "",
  qwenTimbre: "Timbre 1",
  referenceTranscript: "",

  omnivoiceMode: "voice_design",
  omniGender: "male",
  omniAge: "young adult",
  omniPitch: "moderate pitch",
  omniStyle: "",
  omniAccent: "",
  omniDialect: "",

  breezeMode: "voice_design",
  breezeInstruction: "",
  breezeReferenceTranscript: "",
  breezeCfgScale: 4,

  higgsLanguage: "English",
  higgsReferenceTranscript: "",
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

  if (!form.referenceTranscript) {
    toaster.warning("Podaj transkrypcję głosu referencyjnego!");
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

const validateBreezeForm = (mode) => {
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  if (mode === "voice_design" && !form.breezeInstruction.trim()) {
    toaster.warning("Opis głosu (instruction) jest wymagany!");
    return false;
  }
  if (mode === "voice_cloning") {
    if (!form.voiceToClone) {
      toaster.warning("Wybierz głos do sklonowania!");
      return false;
    }
    if (!form.breezeReferenceTranscript.trim()) {
      toaster.warning("Podaj dokładną transkrypcję głosu referencyjnego!");
      return false;
    }
  }
  return true;
};

const validateHiggsForm = () => {
  if (!form.textToGenerate) {
    toaster.warning("Podaj tekst do wygenerowania głosu!");
    return false;
  }
  if (!form.higgsLanguage) {
    toaster.warning("Wybierz język!");
    return false;
  }
  if (form.voiceToClone && !form.higgsReferenceTranscript) {
    toaster.warning("Podaj tekst referencyjny dla wgranego głosu!");
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
      payload.ref_text = form.referenceTranscript;
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

    case "breeze_tts":
      if (!validateBreezeForm(form.breezeMode)) return;
      payload.mode = form.breezeMode;
      payload.cfg_scale = form.breezeCfgScale;
      if (form.breezeMode === "voice_design") {
        payload.voicePrompt = form.breezeInstruction;
      } else {
        payload.voiceToClone = form.voiceToClone?.name || null;
        payload.ref_text = form.breezeReferenceTranscript;
      }
      break;

    case "higgs_tts_3":
      if (!validateHiggsForm()) return;
      payload.language = form.higgsLanguage;
      payload.voiceToClone = form.voiceToClone?.name || null;
      payload.ref_text = form.higgsReferenceTranscript;
      payload.voicePrompt = form.voicePrompt;
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
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    tempAudioPath.value = data.audio_path;
    generatedAudioUrl.value = `http://127.0.0.1:8000${data.audio_path}`;
    canSave.value = true;

    toaster.success("Próbka głosu została pomyślnie wygenerowana!");
  } catch (error) {
    toaster.error("Błąd: " + error.message);
    console.error("[generateVoice]", error);
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
  if (form.provider === "breeze_tts" && form.breezeMode === "voice_design") {
    formData.append("voice_prompt", form.breezeInstruction);
  }
  if (form.category) formData.append("category", form.category);
  formData.append("tags", JSON.stringify(form.tags));

  let lang = "";
  if (form.provider === "coqui_xtts_v2") lang = form.xttsLanguage;
  if (form.provider === "qwen_design") lang = form.qwenLanguage;
  if (form.provider === "higgs_tts_3") lang = form.higgsLanguage;

  if (lang) formData.append("language", lang);

  const options = {};
  if (form.provider === "qwen_custom") {
    options.timbre = form.qwenTimbre;
  } else if (form.provider === "qwen_base") {
    options.voiceToClone = form.voiceToClone?.name || null;
    options.ref_text = form.referenceTranscript;
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
  } else if (form.provider === "breeze_tts") {
    options.mode = form.breezeMode;
    options.cfg_scale = form.breezeCfgScale;
    if (form.breezeMode === "voice_cloning") {
      options.ref_text = form.breezeReferenceTranscript;
    }
  } else if (form.provider === "higgs_tts_3") {
    options.voiceToClone = form.voiceToClone?.name || null;
    options.ref_text = form.higgsReferenceTranscript;
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
          <option value="omnivoice">1. OMNIVOICE</option>
          <option value="breeze_tts">2. BREEZE TTS</option>
        </select>
      </label>

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

      <template v-if="form.provider === 'breeze_tts'">
        <label for="breeze-mode">
          Tryb Breeze TTS
          <select id="breeze-mode" v-model="form.breezeMode">
            <option value="voice_design">Voice Design (Opis głosu)</option>
            <option value="voice_cloning">Voice Cloning (Z pliku)</option>
          </select>
        </label>

        <template v-if="form.breezeMode === 'voice_design'">
          <label for="breeze-instruction">
            Opis głosu (instruction)
            <textarea
              id="breeze-instruction"
              v-model="form.breezeInstruction"
              placeholder="np. A warm, thoughtful young woman with a clear voice and a calm, reflective delivery."
            ></textarea>
          </label>
          <p class="field-hint">
            Wolny opis naturalnym językiem (EN lub CN). Zalecany CFG: 4.
          </p>
        </template>

        <template v-if="form.breezeMode === 'voice_cloning'">
          <label for="breeze-voice-to-clone">
            Wybierz głos do sklonowania
            <input
              type="file"
              id="breeze-voice-to-clone"
              accept="audio/*"
              @change="handleFileUpload('voiceToClone', $event)"
            />
          </label>
          <label for="breeze-ref-transcript">
            Dokładna transkrypcja referencyjna (wymagana)
            <textarea
              id="breeze-ref-transcript"
              v-model="form.breezeReferenceTranscript"
              placeholder='np. "This is the exact transcript of the reference audio."'
            ></textarea>
          </label>
        </template>

        <label for="breeze-cfg">
          CFG Scale (siła podążania za instrukcją)
          <input
            type="number"
            id="breeze-cfg"
            v-model.number="form.breezeCfgScale"
            min="1"
            max="10"
            step="0.5"
          />
        </label>
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

.field-hint {
  margin: -12px 0 20px;
  font-size: 0.85rem;
  color: var(--col-brown);
  text-align: left;
}

#breeze-instruction,
#breeze-ref-transcript {
  height: 90px;
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
