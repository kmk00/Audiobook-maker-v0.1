import { defineStore } from "pinia";
import { ref } from "vue";

export const useAudiobookStore = defineStore("audiobook", () => {
  // --- STAN BUILDERA ---
  const conversation = ref([]);

  // --- STAN LONG TEXT ---
  const longTextBlocks = ref([
    {
      id: Date.now(),
      characterId: null,
      characterName: "Narrator / Brak przypisania",
      avatar: null,
      text: "",
    },
  ]);

  // Akcja do nadpisywania całego tekstu (np. po wgraniu pliku)
  const setLongText = (text: string) => {
    longTextBlocks.value = [
      {
        id: Date.now(),
        characterId: null,
        characterName: "Narrator / Brak przypisania",
        avatar: null,
        text: text,
      },
    ];
  };

  // --- AKCJE DLA BUILDERA ---
  const addBlock = (activeCharacter: any) => {
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

  const removeBlock = (index: number) => {
    conversation.value.splice(index, 1);
  };

  return {
    conversation,
    addBlock,
    removeBlock,
    longTextBlocks,
    setLongText,
  };
});
