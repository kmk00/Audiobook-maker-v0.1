# Audiobook Maker

Audiobook Maker to lokalny system do tworzenia wielogłosowych audiobooków i dubbingu mangi. Łączy interfejs Vue z API FastAPI, biblioteką postaci i usługami GPU uruchamianymi w kontenerach. Tekst może być syntezowany głosem narratora lub przypisanych postaci, a wynik może zostać uzupełniony o napisy SRT oraz timeline FCPXML dla DaVinci Resolve.

## Najważniejsze możliwości

- Tworzenie i katalogowanie postaci wraz z avatarem, tagami, kategorią oraz ustawieniami głosu.
- Synteza z użyciem Qwen3 TTS, OmniVoice oraz Higgs TTS 3; obsługiwane są projektowanie głosu i/lub klonowanie zależnie od modelu.
- Pięć sposobów przygotowania materiału: Builder, Long Text, Re:Zero Mode, Dubbing mangi i Multi-files.
- Import tekstu z plików TXT, PDF i EPUB.
- Dzielenie długich wypowiedzi na fragmenty, grupowanie generacji według postaci oraz końcowe odtworzenie pierwotnej kolejności.
- Opcjonalne napisy SRT i timeline FCPXML z kartami postaci.
- OCR dymków mangi (angielski/japoński), ręczna korekta obszarów i przypisywanie głosów.

## Szybki start

Wymagania:

- Docker Desktop z włączoną obsługą Linux containers;
- zgodny sterownik NVIDIA oraz NVIDIA Container Toolkit / obsługa GPU w Dockerze;
- karta NVIDIA z wystarczającą pamięcią VRAM (projekt był testowany na RTX 5070 Ti 16 GB), 32 GB RAM i dużo wolnego miejsca na modele;
- połączenie z Internetem przy pierwszym uruchomieniu, aby pobrać obrazy i wagi modeli.

Uruchom z katalogu głównego projektu:

```bash
docker compose up --build
```

Po uruchomieniu:

- aplikacja: `http://localhost:3000`
- dokumentacja interaktywna API: `http://localhost:8000/docs`
- API: `http://localhost:8000`

Pierwsze uruchomienie usług AI może trwać długo, ponieważ modele są pobierane i ładowane do pamięci GPU. Zatrzymanie wszystkich usług: `docker compose down`.

> Usługi Qwen i OmniVoice współdzielą jedną kartę GPU. Generowanie jest wykonywane sekwencyjnie; nie uruchamiaj równoległych zadań, jeśli VRAM jest ograniczony.

## Praca z aplikacją

1. Otwórz **Postacie**, wybierz model, ustaw parametry głosu i wygeneruj odsłuch próbny.
2. Zapisz postać. Pliki referencyjne i avatar zostaną zapisane lokalnie w `backend/characters/`.
3. W widoku **Generowanie** wybierz postać z panelu po lewej i przygotuj scenariusz w wybranym trybie.
4. Włącz opcję generowania timeline'u, jeśli potrzebujesz plików do montażu.
5. Rozpocznij generowanie. Interfejs odpyta API o stan zadania co 3 sekundy, a po zakończeniu pokaże odtwarzacz i linki do plików.

Szczegółowy opis interfejsu, modeli i przebiegów znajduje się w [dokumentacji użytkownika](docs/USER_GUIDE.md). Architektura, konfiguracja i API są opisane w [dokumentacji technicznej](docs/TECHNICAL_DOCUMENTATION.md).

## Struktura repozytorium

```text
frontend/                 aplikacja Vue 3 / Vite
backend/
  api/                    endpointy, OCR, synchronizacja i eksport timeline'u
  db/                     modele SQLAlchemy i SQLite
  providers/              adaptery API -> workery TTS
  workers/                kontenery Qwen, OmniVoice, Whisper i Higgs
  src/                    kontrakty TTS i manager providerów
docker-compose.yml        uruchomienie kompletnego stosu
docs/                     dokumentacja użytkownika i techniczna
```

## Dane lokalne

W trakcie działania backend tworzy bazę `backend/audiobookDatabase.db` oraz katalogi w `backend/`:

- `characters/` — próbki głosowe, avatary i odsłuchy postaci;
- `audiobooks/audio/temp/` — robocze fragmenty audio, czyszczone przy starcie i zakończeniu API;
- `audiobooks/output/` — wygenerowane audiobooki WAV;
- `audiobooks/timelines/` — pliki SRT i FCPXML;
- `audiobooks/nameplates/` — cache plansz z avatarem i nazwą.

To dane użytkownika — nie powinny być dodawane do kontroli wersji ani usuwane bez kopii zapasowej.

## Stan projektu i ograniczenia

Projekt jest przeznaczony do pracy lokalnej. Nie ma logowania, kontroli dostępu, trwałej kolejki zadań ani mechanizmu odzyskiwania zadań po restarcie API. Statusy generacji są przechowywane w pamięci procesu. Domyślny adres API jest wpisany w frontendzie jako `127.0.0.1:8000`, dlatego przy wdrożeniu zdalnym wymaga konfiguracji.

Nie ma też zautomatyzowanego zestawu testów w repozytorium. Przed zmianami w produkcji warto zweryfikować ręcznie generację dla każdego używanego modelu oraz import timeline'u w docelowej wersji DaVinci Resolve.

## Technologie

- **Frontend:** Vue 3, TypeScript, Vite, Vue Router, Pinia.
- **API:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, SQLite.
- **Audio i montaż:** FFmpeg, Pydub, Faster-Whisper, OpenTimelineIO, FCPXML.
- **OCR:** EasyOCR oraz Manga OCR.
- **TTS:** Qwen3 TTS, OmniVoice i Higgs Audio TTS 3.
