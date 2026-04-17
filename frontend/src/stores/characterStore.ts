import { defineStore } from "pinia";
import { ref } from "vue";

export const useCharacterStore = defineStore("characters", () => {
  const characters = ref([]);
  const isLoaded = ref(false);

  const fetchCharacters = async (force = false) => {
    if (isLoaded.value && !force) return;

    try {
      const response = await fetch("http://127.0.0.1:8000/characters/");
      if (response.ok) {
        characters.value = await response.json();
        isLoaded.value = true;
        console.log("Pinia: Characters loaded from API");
      } else {
        console.error("Error loading characters from API");
      }
    } catch (error) {
      console.error("Network error", error);
    }
  };

  return { characters, isLoaded, fetchCharacters };
});
