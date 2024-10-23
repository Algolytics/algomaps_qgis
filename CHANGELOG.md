# CHANGELOG

## PL

### 0.1.4 (2024-10-24)

- Dodano sprawdzanie ról kolumn dla Batch
- Dodano dodatkowe pola wyjściowe dla Batch (z wyjątkiem danych finansowych)
- Dodano zaawansowane parsowanie CSV z niestandardowymi separatorami i znakami rozdzielenia tekstu
- Instalacja bibliotek Pythona po kliknięciu przycisku na pasku narzędzi i po zgodzie użytkownika, obsługa różnych odpowiedzi OS i pip
- Testy na różnych systemach operacyjnych i wersjach QGIS
- Wdrożenie do repozytorium wtyczek QGIS

### 0.1.3 (2024-10-02)

- Instalacja dodatkowych bibliotek Pythona podczas inicjalizacji wtyczki
- Dodano początkową wersję przetwarzania wsadowego (DQ-Client)
- Poprawki błędów dla starszych wersji QGIS

### 0.1.2 (2024-09-12)

- Naprawiono dodawanie adresów do warstwy, która miała inne pola wyjściowe
- Dodano interfejs użytkownika do przetwarzania wsadowego (Batch) i odczytu CSV

### 0.1.1 (2024-09-09)

- Dodano dodatkowe pola wyjściowe (nazwy symboliczne: identyfikatory TERYT, informacje o budynkach, obwody GUS, dane finansowe) dla geokodowania pojedynczych adresów

### 0.1.0 (2024-09-09)

- Geokodowanie pojedynczych adresów
- Dodano plik `config.json` i funkcjonalność zapisywania/resetowania ustawień

### 0.0.1 (2024-09-06)

- Inicjalizacja wtyczki

___

## EN

### 0.1.4 (2024-10-23)

- Added column roles checks for Batch
- Added additional output fields for Batch (except financial data)
- Added advanced CSV parsing with custom separators and quote characters
- Installation of Python libraries AFTER clicking the toolbar button and after user's consent, handling different OS and pip responses 
- Tested on multiple OS and QGIS versions
- QGIS plugin repository deployment

___

### 0.1.3 (2024-10-02)

- Installation of additional python libraries during the plugin initialization
- Added initial version of batch processing (DQ-Client)
- Bugfixes for older QGIS versions

### 0.1.2 (2024-09-12)

- Fix the concatenation of addresses to the layer that had other output fields 
- Add Batch processing UI and CSV reading

### 0.1.1 (2024-09-09)

- Added additional output fields (symbolic names: TERYT identifiers, building information, GUS identifiers, 
  financial data) for single address geocoding

### 0.1.0 (2024-09-09)

- Single address geocoding
- Added `config.json` file and settings save/reset fucntionality

### 0.0.1 (2024-09-06)

- Initialize the plugin