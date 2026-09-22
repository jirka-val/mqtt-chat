# UltraChat

MQTT chat klient (PyQt6 GUI) nad brokerem `pcfeib425t.vsb.cz` – veřejné i soukromé zprávy, online/offline stav uživatelů.

## Požadavky

- Python 3.12 (jiná 3.x verze bude pravděpodobně fungovat taky, ale testováno na 3.12)
- Připojení na `pcfeib425t.vsb.cz` (přes školní VPN)

## Instalace

Z kořene projektu:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Tyhle hodnoty se v GUI jen předvyplní do přihlašovacího formuláře, jde je tam při spuštění přepsat.

## Spuštění

Appka je v `src/ultrachatapp`, není nainstalovaná jako balíček, takže je potřeba nastavit `PYTHONPATH` na `src`:

```powershell
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m ultrachatapp.main
```

`$env:PYTHONPATH` platí jen pro aktuální okno PowerShellu – v novém okně to nastav znovu.

## Testování mezi dvěma klienty (veřejné/soukromé zprávy)

- Spusť appku dvakrát (dvě okna PowerShellu / dva procesy), pokaždé se **jinou identitou** v přihlašovacím formuláři (identita se používá i jako MQTT `client_id`, stejná identita ve dvou oknech způsobí, že broker jedno z připojení odpojí).
- Kliknutím na jméno v seznamu uživatelů (napravo) se jméno doplní do pole "Příjemce" pro soukromou zprávu.



## Struktura projektu

```
src/ultrachatapp/
    connection.py   - MQTTClient, obalka nad paho-mqtt (connect/publish/subscribe, LWT)
    topics.py        - skladani MQTT topicu podle zadani
    message.py        - format zpravy (timestamp + text)
    main.py             - vstupni bod, spousti GUI
    gui/
        app.py            - hlavni okno, propojuje GUI s MQTTClient
        login_view.py      - prihlasovaci obrazovka
        chat_view.py         - chat + odesilaci radek
        user_list_view.py     - seznam uzivatelu (online/offline)
        theme.py                - barvy, QSS styl
```
