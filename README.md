# Anti-Spaghetti 🍝

Podręczny notatnik-składnica zbudowany w Pythonie z PyQt6. Ciemny, minimalistyczny interfejs do szybkiego zapisywania fragmentów tekstu — prompty, klucze API, przepisy, notatki.

## Funkcje

- **Tworzenie, edycja i usuwanie notatek** z automatycznym zapisem
- **Drag & drop** do zmiany kolejności notatek w sidebarze
- **Wyszukiwanie** po nazwie i treści notatki (z debounce 200ms)
- **Automatyczny zapis** co 5 sekund + zapis przy zamknięciu
- **Potwierdzenie usunięcia** notatki (zabezpieczenie przed przypadkowym usunięciem)
- **Kopiowanie treści** do schowka (z wizualnym feedbackiem)
- **Pasek stanu** z licznikiem tokenów i czasem ostatniej edycji
- **Dwa motywy**: Klasyczny i Ciemny
- **Ciemny pasek tytułowy** na Windows 10/11
- **Kontekstowe menu edytora** (wytnij/kopiuj/wklej)
- **Atomowy zapis pliku** (ochrona przed uszkodzeniem danych)
- **Migracja struktury danych** (automatyczne dodawanie timestampów)
- **Font fallback** (Intel One Mono → Consolas)
- **Ochrona PIN** z PBKDF2 (bezpieczne haszowanie, 100k iteracji)
- **File locking** zapobiega konfliktom między instancjami
- **Kopie zapasowe** uszkodzonych plików danych
- **23 testy automatyczne** (pytest)

## Skróty klawiszowe

| Skrót | Akcja |
|-------|-------|
| `Ctrl+S` | Zapisz |
| `Ctrl+N` | Nowa notatka |
| `Ctrl+F` | Szukaj |
| `Ctrl+D` | Usuń aktywną notatkę |
| `Ctrl+Tab` | Następna notatka |
| `Ctrl+Shift+Tab` | Poprzednia notatka |
| `Ctrl++` | Zwiększ czcionkę |
| `Ctrl+-` | Zmniejsz czcionkę |
| `Escape` | Zamknij dialog |
| Klik 2x nagłówek | Powrót do pustej kartki |

## Wymagania

- Python 3.10+
- PyQt6 >= 6.4.0
- QtAwesome >= 1.2.0

## Instalacja

```bash
git clone https://github.com/TWOJ_USER/anti-spaghetti.git
cd anti-spaghetti
pip install -r requirements.txt
```

### Opcjonalnie: Font

Skopiuj pliki `.ttf` fontu Intel One Mono do folderu `fonts/` obok `main.py`. Aplikacja automatycznie go załaduje. Jeśli font nie jest dostępny, użyje Consolas jako fallback.

## Uruchomienie

```bash
python main.py
```

## Uruchomienie testów

```bash
pytest -v
```

## Kanał komunikacyjny Hermes (opcjonalny)

Aplikacja zawiera serwer Flask do komunikacji między agentami:

```bash
python hermes_server.py &
curl -X POST http://localhost:5000/hermes -H "Content-Type: application/json" -d '{"prompt":"treść"}'
curl http://localhost:5000/hermes/outbox
```

## Dane

Notatki są zapisywane w pliku `notes.json` obok `main.py`. Konfiguracja motywu w `.config`.

## Bezpieczeństwo

- PIN hashowany algorytmem PBKDF2 z losowym solą (100 000 iteracji)
- Atomowy zapis pliku (tmp → replace, ochrona przed uszkodzeniem)
- File locking zapobiega konfliktom między instancjami
- Automatyczne tworzenie kopii zapasowych uszkodzonych plików

## Wersja

1.0.0 — zobacz [CHANGELOG](CHANGELOG.md) po szczegóły.

## Licencja

MIT License — zobacz [LICENSE](LICENSE).
