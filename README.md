# Audiobook Maker

Aplikacja desktopowa, umożliwiająca tworzenie profesjonalnych audiobooków z podziałem na role przy użyciu najnowocześniejszych modeli Text-to-Speech. Projekt kładzie nacisk na prywatność, wydajność lokalnego układu GPU oraz automatyzację procesu produkcji długich treści audio.

# O projekcie
Projekt powstał z potrzeby stworzenia narzędzia, które potrafi przekształcić całe książki (PDF, EPUB, TXT) w słuchowiska bez konieczności korzystania z płatnych i ograniczonych usług chmurowych. Aplikacja zarządza wieloma mikroserwisami AI, z których każdy operuje na innym modelu (XTTS, Qwen3, OmniVoice), oferując bezprecedensową jakość i spójność głosu.

# Główne funkcje

- Automatyczne parsowanie plików i generowanie wielogłosowych nagrań z zachowaniem podziału na Narratora i postacie.
- Tryb Builder Mode pozwala na precyzyjne układanie kwestii dialogowych blok po bloku.
- Tworzenie głosów dla postaci na podstawie opisów tekstowych, umożliwiając pełną personalizację.

# Technologie

### Modele AI
<!-- TABLE -->
| Technologia | Opis |
|-------------|------|
| XTTSv2      | Model Text-to-Speech do generowania naturalnego głosu |
| Qwen3     | Model Text-to-Speech do generowania naturalnego głosu |
| OmniVoice   | Model Text-to-Speech do generowania naturalnego głosu |
<!-- END TABLE -->

### Frontend
<!-- TABLE -->
| Narzędzie   | Opis |
|-------------|------|
| Vue.js      | Framework do tworzenia aplikacji frontendowych |
| Vite       | Narzędzie do budowy aplikacji frontendowych |
| Typescript | Język programowania dla aplikacji frontendowych |
| Pinia      | Biblioteka do zarządzania stanem aplikacji |
<!-- END TABLE -->

### Backend
<!-- TABLE -->
| Narzędzie   | Opis |
|-------------|------|
| Python     | Język programowania dla aplikacji backendowych |
| FastAPI    | Framework do tworzenia aplikacji backendowych |
| SQLAlchemy | Biblioteka do zarządzania bazą danych (ORM) |
| SQLite     | Lokalna baza danych |
<!-- END TABLE -->

### Audio Processing
<!-- TABLE -->
| Narzędzie   | Opis |
|-------------|------|
| FFmpeg     | Narzędzie do przetwarzania audio |
| Pydub      | Biblioteka do przetwarzania audio|
<!-- END TABLE -->

### Pozostałe

<!-- TABLE -->
| Narzędzie   | Opis |
|-------------|------|
| Miniconda     | Środowisko do zarządzania pakietami i wirtualnymi środowiskami Python |

### Wersje Python

<!-- TABLE -->
| Narzędzie   | Opis |
|-------------|------|
| Python 3.12.13     | Wersja języka Python dla modelu Omnivoice |
| Python 3.12.13     | Wersja języka Python dla API backendu |
| Python 3.10.201     | Wersja języka Python dla modelu XTTS |
| Python 3.12.13     | Wersja języka Python dla modelu Qwen3 |
<!-- END TABLE -->

# Specyfikacja Sprzętowa (Środowisko Testowe)

Projekt został zoptymalizowany pod kątem pracy na mocnych stacjach roboczych:

GPU: GPU: NVIDIA GeForce RTX 5070 Ti (16 GB VRAM)
RAM: 32 GB
CPU: AMD Ryzen 7 7800X3D
OS: Windows 10 


# Rozwiązania i optymalizacje

Zamiast przełączać modele przy każdej zmianie roli, system grupuje zadania według postaci. Najpierw generowane są wszystkie kwestie Narratora (jeden model w VRAM), potem Postaci A, itd. Na koniec system przywraca oryginalną chronologię. To podejście minimalizuje przeładowania GPU, znacznie przyspieszając proces produkcji audiobooka.

Długie teksty są dzielone na optymalne fragmenty (chunks), co zapobiega halucynacjom modeli i utracie spójności barwy głosu przy długich nagraniach.

Dzięki systemowi Background Tasks i odpytywaniu o status (Polling), użytkownik może generować setki stron tekstu bez obawy o timeout przeglądarki.

# Przykłady Wygenerowanych Treści

TODO: Dodać przykładowe nagrania audio wygenerowane przez aplikację, pokazujące różne głosy i role.


