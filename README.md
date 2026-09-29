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



## Cviko 2 – agent (proxy) s frontou zpráv

```
GUI klient ──► lokální mosquitto :1884 ◄── agent (Python) ──► pcfeib425t.vsb.cz:1883
               (passwd + ACL)              1 spojení na server za každého uživatele
```

- Klient se přihlásí na lokální mosquitto vlastním loginem (login = identita).
- Klient **publikuje** do normálních topiců `/mschat/...`, ACL mu dovolí jen ty se svou identitou.
- Klient **čte** jen svůj inbox `/inbox/<login>/#` – tam mu agent přeposílá zprávy ze serveru
  (`/mschat/all/pepa` → `/inbox/jirka/mschat/all/pepa`).
- Agent pro každého uživatele drží vlastní spojení na hlavní broker (client_id = identita).
  Když je klient offline (poznáno z `/mschat/status/<login>`, včetně LWT), agent zprávy ukládá do fronty
  a po jeho přihlášení je všechny pošle. Timestamp je v payloadu, takže zůstane původní čas.

### Instalace mosquitta

Stáhnout z https://mosquitto.org/download/ (Windows installer), nebo `winget install EclipseFoundation.Mosquitto`.
Pak přidat `C:\Program Files\mosquitto` do PATH (nebo volat plnou cestou).

### Uživatelé (mosquitto_passwd)

Z kořene projektu – první příkaz soubor vytvoří (`-c`), další už jen přidávají:

```powershell
mosquitto_passwd -c mosquitto/passwd VAL0475-agent
mosquitto_passwd mosquitto/passwd VAL0475
mosquitto_passwd mosquitto/passwd pepa
```

Heslo agenta dej do `.env`:

```
AGENT_LOCAL_USERNAME=VAL0475-agent
AGENT_LOCAL_PASSWORD=heslo_agenta
# volitelne, vychozi hodnoty:
# AGENT_UPSTREAM_USERNAME=server
# AGENT_UPSTREAM_PASSWORD=Broker
```

### Spuštění (3 okna PowerShellu, z kořene projektu)

```powershell
# 1) lokalni broker
mosquitto -c mosquitto/mosquitto.conf -v

# 2) agent
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m ultrachatagent.main

# 3) klient - v loginu zaskrtnout "Pres agenta", identita = login z passwd
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe -m ultrachatapp.main
```

Test fronty: přihlas se přes agenta, zavři okno klienta, nech někoho (třeba druhého klienta napřímo)
poslat zprávy, pak se znovu přihlas – zprávy přijdou z fronty.

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
src/ultrachatagent/
    main.py         - vstupni bod agenta, nacte .env
    agent.py        - spojeni na lokalni mosquitto, rozdeluje zpravy podle uzivatele
    user_session.py - spojeni jednoho uzivatele na hlavni broker + fronta zprav
mosquitto/
    mosquitto.conf  - konfigurace lokalniho brokeru (port 1884)
    acl             - kdo smi cist/psat jake topicy
    passwd          - hesla (generuje mosquitto_passwd, neni v gitu)
```
