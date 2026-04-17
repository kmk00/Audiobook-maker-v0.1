import { defineStore } from "pinia";
import { ref } from "vue";

export const useAudiobookStore = defineStore("audiobook", () => {
  // --- STAN BUILDERA ---
  const conversation = ref([]);

  // --- STAN LONG TEXT ---
  const longText = ref("");

  // --- AKCJE DLA BUILDERA ---
  const addBlock = (activeCharacter) => {
    if (!activeCharacter) {
      alert("Wybierz najpierw postać z listy po lewej stronie!");
      return;
    }

    conversation.value.push({
      id: Date.now(),
      characterId: activeCharacter.id,
      characterName: activeCharacter.name,
      avatar: activeCharacter.avatar_path,
      text: "",
    });
  };

  const removeBlock = (index) => {
    conversation.value.splice(index, 1);
  };

  return {
    conversation,
    longText,
    addBlock,
    removeBlock,
  };
});
