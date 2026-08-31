import { ref } from "vue";
import { createToaster } from "@meforma/vue-toaster";

const toaster = createToaster({ position: "top-right", duration: 3000 });
const API_BASE = "http://127.0.0.1:8000";

/**
 * useAudiobookGeneration
 *
 * Współdzielona logika generowania audiobooka + opcjonalnego timeline'u do
 * DaVinci (SRT + FCPXML). Reużywalne w KAŻDYM trybie (ReZero, LongText,
 * czysty lektor, cokolwiek dojdzie w przyszłości) — jedyny kontrakt to
 * `blocks: [{ characterId, text }]`, który już masz wszędzie taki sam.
 */
export function useAudiobookGeneration() {
  const isLoading = ref(false);
  const loadingText = ref("");
  const generatedAudioUrl = ref(null);
  const srtUrl = ref(null);
  const fcpxmlUrl = ref(null);

  // v-model na checkboxie w UI, domyślnie włączone
  const generateTimeline = ref(true);

  const resetResults = () => {
    generatedAudioUrl.value = null;
    srtUrl.value = null;
    fcpxmlUrl.value = null;
  };

  const pollTaskStatus = (taskId: string) => {
    return new Promise((resolve) => {
      const poll = async () => {
        try {
          const res = await fetch(`${API_BASE}/tts/task-status/${taskId}`);
          const data = await res.json();

          if (data.status === "completed") {
            isLoading.value = false;
            generatedAudioUrl.value = data.file_url;
            srtUrl.value = data.srt_url || null;
            fcpxmlUrl.value = data.fcpxml_url || null;
            toaster.success("Audiobook wygenerowany pomyślnie!");
            resolve(data);
          } else if (data.status === "error") {
            isLoading.value = false;
            toaster.error("Błąd podczas generowania: " + data.error);
            resolve(data);
          } else {
            loadingText.value =
              data.message || "Trwa przetwarzanie na serwerze...";
            setTimeout(poll, 3000);
          }
        } catch (error) {
          isLoading.value = false;
          toaster.error("Błąd komunikacji z serwerem sprawdzającym status.");
          resolve(null);
        }
      };
      poll();
    });
  };

  /**
   * @param {string} mode - 'rezero' | 'longtext' | dowolny przyszły tryb
   * @param {Array<{characterId: number|null, text: string}>} blocks
   */
  const generateAudiobook = async (
    mode: string,
    blocks: { characterId: number | null; text: string }[],
  ) => {
    const validBlocks = blocks.filter((b) => b.text.trim() !== "");

    if (validBlocks.length === 0) {
      toaster.warning("Brak tekstu do wygenerowania!");
      return;
    }

    const droppedCount = blocks.length - validBlocks.length;
    if (droppedCount > 0) {
      toaster.warning(
        `${droppedCount} pustych kwestii zostanie pominiętych — uzupełnij je, aby dialogi nie zniknęły z audiobooka.`,
      );
    }

    const unassignedCount = validBlocks.filter((b) => !b.characterId).length;
    if (unassignedCount > 0 && unassignedCount < validBlocks.length) {
      // Ostrzeżenie tylko gdy to MIESZANKA (część przypisana, część nie) —
      // w trybie czysto-lektorskim wszystko jest "nieprzypisane" celowo,
      // więc pytanie o to byłoby mylące.
      if (
        !confirm(
          `Masz ${unassignedCount} nieprzypisanych kwestii (zostaną przeczytane przez domyślnego Narratora). Kontynuować?`,
        )
      ) {
        return;
      }
    }

    const payload = {
      mode,
      generate_timeline: generateTimeline.value,
      blocks: validBlocks.map((block) => ({
        character_id: block.characterId,
        text: block.text.trim(),
      })),
    };

    isLoading.value = true;
    loadingText.value = "Zlecanie zadania na serwer... Czekaj!";
    resetResults();

    try {
      const response = await fetch(`${API_BASE}/tts/generate-audiobook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Błąd podczas zlecania audiobooka.");
      }

      const data = await response.json();
      await pollTaskStatus(data.task_id);
    } catch (error) {
      isLoading.value = false;
      toaster.error(error instanceof Error ? error.message : "Wystąpił błąd.");
    }
  };

  return {
    isLoading,
    loadingText,
    generatedAudioUrl,
    srtUrl,
    fcpxmlUrl,
    generateTimeline,
    generateAudiobook,
  };
}
