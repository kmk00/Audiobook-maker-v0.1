# Podręcznik użytkownika

## Biblioteka postaci

Widok **Postacie** służy do definiowania profili głosowych. Każdy profil zawiera nazwę (unikalną), dostawcę TTS, opcjonalny opis, kategorię, tagi, avatar oraz ustawienia specyficzne dla modelu. Kategoria i tagi pozwalają później filtrować postacie w widoku generowania.

Najpierw wprowadź krótki tekst testowy i użyj **Wygeneruj głos**. Po akceptacji odsłuchu wybierz **Zapisz postać**. Odsłuch tymczasowy zostanie przeniesiony do katalogu postaci, a pliki tymczasowe zostaną usunięte.

| Model | Zastosowanie | Wymagane dane |
|---|---|---|
| `qwen_design` | Projektowanie nowego głosu na podstawie instrukcji | Język i prompt opisujący głos |
| `qwen_custom` | Synteza jednym z gotowych timbrów Qwen | Timbre, opcjonalna instrukcja |
| `qwen_base` | Klonowanie głosu | Próbka audio i dokładna transkrypcja próbki |
| `omnivoice` | Projektowanie lub klonowanie głosu | Atrybuty/prompt albo próbka audio; przy klonowaniu warto podać transkrypcję |
| `higgs_tts_3` | Wielojęzyczna synteza ekspresyjna | Opcjonalna próbka i transkrypcja; opcjonalne tagi emocji/prozodii |

Próbki głosowe powinny być czyste, zawierać pojedynczego mówcę i odpowiadać dokładnie podanej transkrypcji. Jakość próbki ma bezpośredni wpływ na klonowanie.

## Generowanie audiobooka

W panelu po lewej wybierz postać. Jej avatar będzie podświetlony. Możesz wyszukiwać po nazwie, kategorii i tagach; tryb usuwania usuwa postać razem z przypisanym katalogiem plików po potwierdzeniu.

| Tryb | Przeznaczenie |
|---|---|
| **Builder** | Ręczne budowanie kolejnych kwestii; wybierasz postać i dodajesz jej blok tekstu. |
| **Long Text** | Długi tekst jednego narratora lub tekst rozdzielony na większe bloki. Obsługuje import TXT/PDF/EPUB. |
| **Re:Zero Mode** | Parser scenariusza: linie w formie `Postać: [Wypowiedź]` rozdziela od narracji i pozwala przypisać wykryte role. |
| **Dubbing** | Praca z obrazami mangi: wykrycie dymków, ręczna korekta, OCR i przypisanie postaci do każdej kwestii. |
| **Multi-files** | Przetwarzanie wielu plików/partii materiału w jednym widoku. |

Nieprzypisane bloki są czytane przez domyślny narrator oparty na OmniVoice. Gdy część bloków jest przypisana, a część nie, aplikacja ostrzega przed startem. Pusty blok jest pomijany.

### Długie teksty i kolejność

Backend dzieli każdy blok na części do 1200 znaków, preferując granice zdań i nowe linie. Następnie zadania są grupowane według postaci, aby ograniczyć przeładowywanie modeli na GPU. Po syntezie fragmenty są sortowane z powrotem według oryginalnej kolejności scenariusza i łączone z przerwą 600 ms.

To oznacza, że wynik zachowuje kolejność wejściową, choć kolejność rzeczywistego generowania na GPU może być inna.

## Napisy i DaVinci Resolve

Po zaznaczeniu opcji timeline'u aplikacja transkrybuje każdy fragment przez worker Whisper, wykorzystując rozpoznanie przede wszystkim do ustalenia czasu. Treść napisów pochodzi z oryginalnego scenariusza, nie z wyniku rozpoznawania mowy.

Wyniki:

- **WAV** — gotowy audiobook;
- **SRT** — napisy zdanie po zdaniu; kwestie postaci mają nazwę nad tekstem;
- **FCPXML** — ścieżka wideo z kartami postaci (avatar + nazwa). Narrator pozostawia przerwę bez karty.

W DaVinci Resolve zaimportuj FCPXML jako nowy timeline/projekt, dodaj WAV na pozycję `00:00`, a plik SRT zaimportuj jako oddzielną ścieżkę napisów. FCPXML celowo nie zawiera audio ani napisów, co zmniejsza problemy z importem połączeń klipów.

## Dubbing mangi

1. Dodaj obraz strony i wybierz język OCR (`en` lub `ja`).
2. Uruchom wykrywanie dymków. Wynik możesz zmienić: usuwać ramki i dorysować własne.
3. Zatwierdź ramki, aby odczytać tekst. Dla japońskiego używany jest Manga OCR, dla angielskiego EasyOCR.
4. Popraw rozpoznany tekst, ustaw kolejność i przypisz postacie.
5. Wygeneruj dźwięk dla strony.

Wykrywanie automatyczne jest punktem startowym: jakość zależy od kontrastu, kroju pisma, efektów dźwiękowych i układu strony. Sprawdzenie każdej ramki przed OCR jest zalecane.

## Najczęstsze problemy

| Objaw | Co sprawdzić |
|---|---|
| Brak połączenia z API | Czy `api` działa, a strona jest otwarta pod `localhost:3000`. |
| Błąd połączenia z modelem | Czy odpowiedni worker (`worker-qwen`, `worker-omnivoice` lub `worker-higgs`) zakończył ładowanie. |
| Błąd przy timeline | Czy działa `worker-whisper`, czy FFmpeg jest dostępny w kontenerze API i czy na dysku jest miejsce. |
| Brak FCPXML | Jest tworzony tylko, gdy występuje co najmniej jedna kwestia przypisana do postaci. |
| Niska jakość klonowania | Użyj czystszej próbki, jednej osoby mówiącej i prawidłowej transkrypcji referencji. |
| Brak pamięci GPU | Zakończ inne procesy GPU, zmniejsz równoległość i poczekaj aż worker zwolni/zmieni model. |
