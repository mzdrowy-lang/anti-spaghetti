# Changelog

Wszystkie istotne zmiany w projekcie Anti-Spaghetti będą dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl-PL/1.0.0/),
a projekt stosuje [Semantic Versioning](https://semver.org/lang/pl/).

## [1.0.0] - 2026-05-12

### Dodane
- Podręczny notatnik-składnica z ciemnym interfejsem
- Tworzenie, edycja i usuwanie notatek
- Drag & drop do zmiany kolejności notatek w sidebarze
- Wyszukiwanie po nazwie i treści notatki (z debounce)
- Automatyczny zapis co 5 sekund + zapis przy zamknięciu
- Potwierdzenie usunięcia notatki
- Kopiowanie treści do schowka (z wizualnym feedbackiem)
- Pasek dolny z licznikiem słów/tokenów i czasem ostatniej edycji
- Dwa motywy: Klasyczny i Ciemny
- Ciemny pasek tytułowy na Windows 10/11
- Skróty klawiszowe: Ctrl+S, Ctrl+N, Ctrl+F, Ctrl+D, Ctrl+Tab, Ctrl+Shift+Tab
- Kontekstowe menu edytora (wytnij/kopiuj/wklej)
- Atomowy zapis pliku (ochrona przed uszkodzeniem danych)
- Migracja struktury danych (automatyczne dodawanie timestampów)
- Font fallback (Intel One Mono → Consolas)
- Ochrona PIN z PBKDF2 (bezpieczne haszowanie)
- Nawigacja między notatkami (Ctrl+Tab / Ctrl+Shift+Tab)
- Wizualne potwierdzenie zapisu
- Kopie zapasowe uszkodzonych plików danych
- Obsługa klawisza Escape w dialogach
- File locking (zapobiega konfliktom instancji)
- 23 testy automatyczne (pytest)

### Bezpieczeństwo
- PIN hashowany algorytmem PBKDF2 z losowym solą (100 000 iteracji)
- Dialogi błędów zamiast cichego kasowania danych
- Automatyczne tworzenie kopii zapasowych uszkodzonych plików

### Naprawione
- Zduplikowane importy z PyQt6.QtCore
- Błędne obliczanie liczby tokenów (zaokrąglanie w dół)
- Brak resetu flagi _dirty po ręcznym zapisie
- Brak walidacji klucza "content" w danych JSON
- Brak aktualizacji tytułu okna przy zmianie notatki
- Niespójne wcięcia w słowniku SIZES
- SHA-256 bez salt → PBKDF2

### Techniczne
- QTextEdit → QPlainTextEdit (wydajność)
- Debounce aktualizacji liczników (100ms)
- Optymalizacja timera auto-zapisu
- Nowoczesne pakowanie (pyproject.toml)

## [1.0.0-beta] - 2026-05-12

### Dodane
- Wersja początkowa aplikacji
