# Analizator Wydatkow

Aplikacja web do analizy wydatkow z CSV bankowego.
MVP skupia sie na imporcie CSV (ING Polska), auto-kategoryzacji, recznej korekcie i raportowaniu per kategoria.

## Co rozwiazuje

Bankowe kategorie czesto nie pasuja do realnych potrzeb budzetowych.
Aplikacja skraca proces: importujesz CSV, dostajesz propozycje kategorii, poprawiasz pojedyncze transakcje, widzisz podsumowanie wydatkow.

## Funkcje MVP

- Rejestracja i logowanie uzytkownika.
- Izolacja danych: kazdy uzytkownik widzi tylko swoje dane.
- Import CSV transakcji (MVP: format ING Polska).
- Auto-kategoryzacja transakcji na podstawie mapowan merchant -> kategoria.
- Uczenie na korektach: poprawki kategorii wplywaja na przyszle importy.
- CRUD kategorii (create/read/update/delete).
- Lista transakcji z filtrowaniem i sortowaniem.
- Podsumowanie wydatkow per kategoria z zakresem dat.

## Wymagania

- Python 3.12+
- PDM

## Uruchomienie lokalne

1. Zainstaluj zaleznosci:

```bash
pdm install
```

2. Przygotuj zmienne srodowiskowe:

- Skopiuj `.env.example` do `.env`.
- W PowerShell zaladuj `.env` do biezacej sesji:

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
  }
}
```

3. Wykonaj migracje:

```bash
pdm run python manage.py migrate
```

4. Uruchom aplikacje:

```bash
pdm run python manage.py runserver
```

5. Otworz:

- http://localhost:8000/

## Testy i checki jakosci

Uruchomienie testow:

```bash
pdm run python manage.py test
```

Wybrane testy aplikacji:

```bash
pdm run python manage.py test accounts.tests categories.tests transactions.tests
```

Lint:

```bash
pdm run ruff check .
```

Format:

```bash
pdm run ruff format .
```

Typecheck:

```bash
pdm run basedpyright
```

## Dokumentacja projektu (foundation)

- PRD: [context/foundation/prd.md](context/foundation/prd.md)
- Plan testow i ryzyk: [context/foundation/test-plan.md](context/foundation/test-plan.md)
- Roadmapa: [context/foundation/roadmap.md](context/foundation/roadmap.md)
- Stos technologiczny: [context/foundation/tech-stack.md](context/foundation/tech-stack.md)

## Ograniczenia MVP

- Import danych tylko przez CSV (brak bezposredniego polaczenia z bankiem).
- MVP targetuje format CSV ING Polska.
- Brak kont wspoldzielonych (model single-user per konto).

## Test