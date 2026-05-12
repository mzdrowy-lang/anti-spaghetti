# Anti-Spaghetti

Podręczny notatnik-składnica zbudowany w Pythonie z PyQt6. Ciemny, minimalistyczny interfejs do szybkiego zapisywania fragmentów tekstu — prompty, klucze API, przepisy, notatki.

## Funkcje

- Tworzenie, edycja i usuwanie notatek
- Drag & drop do zmiany kolejności notatek w sidebarze
- Wyszukiwanie po nazwie i treści notatki (z debounce)
- Automatyczny zapis co 5 sekund + zapis przy zamknięciu
- Potwierdzenie usunięcia notatki
- Kopiowanie treści do schowka (z wizualnym feedbackiem)
- Pasek dolny z licznikiem słów/tokens i czasem ostatniej edycji
- Dwa motywy: Klasyczny i Ciemny
- Ciemny pasek tytułowy na Windows 10/11
- Skróty klawiszowe (patrz tabela poniżej)
- Kontekstowe menu edytora (wytnij/kopiuj/wklej)
- Atomowy zapis pliku (ochrona przed uszkodzeniem danych)
- Migracja struktury danych (automatyczne dodawanie timestampów)
- Font fallback (Intel One Mono → Consolas)
- Ochrona PIN z PBKDF2 (bezpieczne haszowanie)
- Nawigacja między notatkami (Ctrl+Tab / Ctrl+Shift+Tab)
- Wizualne potwierdzenie zapisu
- Kopie zapasowe uszkodzonych plików danych
- Obsługa klawisza Escape w dialogach

## Wymagania

- Python 3.10+
- PyQt6
- QtAwesome

## Instalacja

```bash
git clone https://github.com/TWOJ_USER/anti-spaghetti.git
cd anti-spaghetti
pip install -r requirements.txt
```

## Opcjonalnie: Font

Skopiuj pliki `.ttf` fontu Intel One Mono do folderu `fonts/` obok `main.py`. Aplikacja automatycznie go załaduje. Jeśli font nie jest dostępny, użyje Consolas jako fallback.

## Uruchomienie

```bash
python main.py
```

## Skróty klawiszowe

| Skrót | Akcja |
|-------|-------|
| Ctrl+S | Zapisz |
| Ctrl+N | Nowa notatka |
| Ctrl+F | Szukaj |
| Ctrl+D | Usuń aktywną notatkę |
| Ctrl+Tab | Następna notatka |
| Ctrl+Shift+Tab | Poprzednia notatka |
| Ctrl++ | Zwiększ czcionkę |
| Ctrl+- | Zmniejsz czcionkę |
| Escape | Zamknij dialog |

## Dane

Notatki są zapisywane w pliku `notes.json` obok `main.py`. Konfiguracja motywu w `.config`.

## Bezpieczeństwo

PIN jest hashowany algorytmem PBKDF2 z losowym solą (100 000 iteracji). W przypadku uszkodzenia pliku danych, aplikacja automatycznie tworzy kopię zapasową.

## Licencja

MIT License — zobacz [LICENSE](LICENSE).