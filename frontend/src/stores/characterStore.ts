import { defineStore } from "pinia";
import { ref } from "vue";

export const useCharacterStore = defineStore("characters", () => {
  const characters = ref<any[]>([]);
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

  const updateCharacter = async (id: number, formData: FormData) => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/characters/${id}`, {
        method: "PUT",
        body: formData,
      });
      if (response.ok) {
        const updated = await response.json();
        const index = characters.value.findIndex((c: any) => c.id === id);
        if (index !== -1) {
          characters.value[index] = updated;
        }
        return updated;
      }
      const error = await response.json().catch(() => null);
      throw new Error(error?.detail || "Błąd podczas aktualizacji postaci");
    } catch (error) {
      console.error("Error updating character", error);
      throw error;
    }
  };

  return { characters, isLoaded, fetchCharacters, updateCharacter };
});
