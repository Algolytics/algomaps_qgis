# AlgoMaps QGIS plugin

Standaryzacja i geokodowanie adresów | Address standarization and geocoding

---

## PL

### Opis

Wtyczka pozwala na standaryzację i geokodowanie adresów w Polsce. Pozwala zarówno na standaryzację i geokodowanie
pojedynczego adresu jak i przetwarzanie wsadowe większego zbioru danych. Dane adresowe mogą być zapisane w różny sposób
i z błędami w pisowni.

Wynikiem pracy wtyczki jest warstwa punktowa ze zgeokodowanymi punktami adresowymi wraz z dołączonymi dodatkowymi
polami, w zależności od wybranych w Ustawieniach zmiennych.

Więcej informacji: https://algomaps.pl/

### Instalacja

1. Zainstaluj wtyczkę w programie QGIS (Wtyczki -> Zarządzanie wtyczkami -> Instaluj z pliku zip). Przy ostrzeżeniu
   bezpieczeństwa naciśnij  "Tak".
2. Włącz wtyczkę zaznaczając checkbox przy nazwie AlgoMaps (Wtyczki -> Zarządzanie wtyczkami -> Zainstalowane). Może to
   zająć parę chwil, w tym czasie okno QGIS może nie odpowiadać.
3. Uruchom QGIS ponownie.
4. Uruchom wtyczkę klikając jej ikonę na pasku narzędzi - powinien pojawić się dokowalny panel AlgoMaps.
5. Przejdź do zakładki "Ustawienia" i uzupełnij swoje dane przed rozpoczęciem korzystania z wtyczki:

Pojedynczy adres:

1. W swojej przeglądarce internetowej przejdź do https://developer.algolytics.pl/
2. Kliknij przycisk "Sign up", żeby założyć darmowe konto uprawniające do standaryzacji i geokodowania 1000 rekordów za
   darmo.
3. Wypełnij swoje dane oraz wprowadź kod CAPTCHA. Naciśnij "Sign up" na dole formularza.
4. Kliknij "Sign in" w prawym górnym rogu i zaloguj się na założone konto.
5. Kliknij zakładkę "Products" w prawym górnym rogu.
6. Wybierz "Trial Address Standarization API".
7. W sekcji "Your subscriptions" wpisz dowolną nazwę "np.: qgis" w pole tekstowe, zapoznaj się z zasadami "Terms of use"
   i naciśnij "Subscribe".
8. Po przekierowaniu na stronę profilu użytkownika (https://developer.algolytics.pl/profile) odszukaj utworzoną właśnie
   subskrybcję w polu "Subscriptions".
9. Wyświetl klucz API (primary lub secondary) naciskając "Show".
10.	Skopiuj klucz (32-znakowy ciąg znaków i liczb).
11.	Powróć do QGIS i wklej klucz w pole "API key" w Ustawieniach wtyczki AlgoMaps.

Przetwarzanie wsadowe (batch):

1. Przejdź na stronę https://algomaps.pl/
2. Kliknij przycisk "Załóż darmowe konto".
3. Wypełnij swoje dane, zakceptuj regulamin i potwierdź "Nie jestem robotem". Kliknij "Utwórz konto".
4. Kliknij w link aktywacyjny w twojej skrzynce pocztowej (jeśli nie widzisz wiadomości sprawdź folder Spam).
5. Zaloguj się na swoje konto.
6. Wybierz "Moje konto" z listy.
7. Pierwszy 1000 przetwarzanych rekordów jest darmowy. Aby zwiększyć limit należy uzupełnić dane kontaktowe i doładować
   konto.
8. Skopiuj "Klucz dostępu do API".
9. Powróć do QGIS i wklej klucz do pola "DQ token" w Ustawieniach wtyczki AlgoMaps.
10.	W polu "DQ user" wpisz adres email swojego konta.

### Korzystanie z przetwarzania wsadowego (batch)

#### 

#### Funkcje (role) kolumn
Funkcja kolumny (lub inaczej jej "rola") określa jaki typ danych znajduje się w danej kolumnie pliku wejściowego. 
Każda kolumna w pliku wejściowym może mieć tylko jedną funkcję. Każda funkcja w pliku wejściowym może wystąpić tylko raz. 
Wyjątek stanowią funkcje `PRZEPISZ` i `POMIN`, które mogą występować wielokrotnie.

W przypadku gdy dany wiersz nie wykorzystuje danej funkcji (np. nie jest podany nr domu), wartość kolumny w danym 
wierszu powinna być pusta. 

Kolumny mogą mieć następujące funkcje:

- Zmienna neutralna  
  - `PRZEPISZ` – kopiuje zmienną do pliku wyjściowego
  - `POMIN` – nie kopiuje zmiennej do pliku wyjściowego
- Identyfikator  
  - `ID_REKORDU`
- Zmienna niesprecyzowana  
  - `DANE_OGOLNE` – zmienna zostanie przeanalizowana pod kątem wszystkich możliwych informacji adresowych
- Zmienna adresowa  
  - `KOD_POCZTOWY`  
  - `MIEJSCOWOSC`  
  - `ULICA_NUMER_DOMU_I_MIESZKANIA`
  - `ULICA`
  - `NUMER_DOMU`
  - `NUMER_MIESZKANIA`
  - `NUMER_DOMU_I_MIESZKANIA`
  - `WOJEWODZTWO`
  - `POWIAT`
  - `GMINA`

Reguły:  

- aby można było rozpocząć przetwarzanie, wymagana jest przynajmniej jedna z kolumn: `DANE_OGOLNE`, `KOD_POCZTOWY` lub `MIEJSCOWOSC`
- jeśli istnieje kolumna `ULICA`, to wszystkie informacje w `ULICA_NUMER_DOMU_I_MIESZKANIA` są ignorowane
- jeśli istnieje kolumna `NUMER_DOMU`, to wszystkie informacje na temat numeru domu i mieszkania z `ULICA_NUMER_DOMU_I_MIESZKANIA` oraz `NUMER_DOMU_I_MIESZKANIA` są ignorowane
- jeśli nie istnieje kolumna `NUMER_DOMU`, to kolumna `NUMER_MIESZKANIA` jest ignorowana
- jeśli nie istnieje kolumna `ULICA` i istnieje kolumna `ULICA_NUMER_DOMU_I_MIESZKANIA`, to kolumna `NUMER_DOMU_I_MIESZKANIA` jest ignorowana
- jeśli istnieje którakolwiek z kolumn (`KOD_POCZTOWY`, `MIEJSCOWOSC`, `ULICA_NUMER_DOMU_I_MIESZKANIA`, `ULICA`, `NUMER_DOMU`, `NUMER_DOMU_I_MIESZKANIA`), to kolumna `DANE_OGOLNE` jest ignorowana

Dopuszczalne jest wysłanie kilku kolumn o funkcjach zawierających tę samą informację (np. numer mieszkania), przy czym 
użytkownik powinien zadbać o to, aby taka informacja nie była powielona w wielu kolumnach. Funkcjonalność służy do tego,
aby możliwe było przeprocesowanie wierszy o tych samych informacjach rozłożonych w kolumnach o różnych funkcjach. 

### Dziennik zmian

TODO

---

## EN

### Description

The plugin allows for the standardization and geocoding of addresses in Poland. It supports both single address
standardization and geocoding as well as batch processing of larger data sets. Address data can be entered in various
formats and with spelling errors.

The output of the plugin is a point layer with geocoded address points, along with additional fields depending on the
selected variables in the Settings.

More information: https://algomaps.pl/

### Installation

1. Install the plugin in QGIS (Plugins -> Manage and Install Plugins -> Install from ZIP file). When the security
   warning appears, click "Yes".
2. Enable the plugin by checking the box next to AlgoMaps (Plugins -> Manage and Install Plugins -> Installed). This may
   take a moment, during which the QGIS window may become unresponsive.
3. Restart QGIS.
4. Launch the plugin by clicking its icon on the toolbar - a dockable AlgoMaps panel should appear.
5. Go to the "Settings" tab and enter your information before using the plugin:

Single address:

1. In your web browser, go to https://developer.algolytics.pl/
2. Click the "Sign up" button to create a free account that allows for the standardization and geocoding of 1000 records
   for free.
3. Fill in your details and enter the CAPTCHA code. Click "Sign up" at the bottom of the form.
4. Click "Sign in" in the top right corner and log in to your account.
5. Click the "Products" tab in the top right corner.
6. Choose "Trial Address Standardization API".
7. In the "Your subscriptions" section, enter any name (e.g., qgis) in the text field, review the "Terms of use," and
   click "Subscribe".
8. After being redirected to the user profile page (https://developer.algolytics.pl/profile), find the newly created
   subscription in the "Subscriptions" section.
9. Display the API key (primary or secondary) by clicking "Show".
10. Copy the key (a 32-character string of letters and numbers).
11. Return to QGIS and paste the key into the "DQ token" field in the AlgoMaps plugin settings.
12. In the "DQ user" field, enter the email address of your account.

Batch processing:

1. Go to https://algomaps.pl/
2. Click the "Create a free account" button.
3. Fill in your details, accept the terms and conditions, and confirm "I'm not a robot". Click "Create account".
4. Click the activation link in your email (if you don't see the message, check your Spam folder).
5. Log in to your account.
6. In the top right corner, click the button with your email address.
7. Select "My account" from the list.
8. The first 1000 records per month are free. To increase the limit, complete your contact information and top up your
   account.
9. Copy the "API access key".
10. Return to QGIS and paste the access key into the "API key" field.

### Changelog

TODO