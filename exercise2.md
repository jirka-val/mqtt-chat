# Cviko 2 – postup testování

Agent (proxy) s frontou zpráv, více klientů, ACL.

```
GUI klient ──► lokální mosquitto :1884 ◄── agent ──► pcfeib425t.vsb.cz:1883
               (passwd + ACL)              1 spojení na server za každého uživatele
```

| Účet | Heslo | K čemu |
|---|---|---|
| `VAL0475-agent` | v `.env` | agent |
| `VAL0475` | `monster` | klient A (přes agenta) |
| `VAL0475-2` | `monster` | klient C (přes agenta) / testy ACL |
| `VAL0475-test` | `mobilni` / `Systemy` | klient B (napřímo na školu) |

> Pozor: když v okně PowerShellu označíš myší text, program v něm se zastaví (titulek „Vybrat“).
> Kopírovat Enterem nebo pravým tlačítkem, zrušit výběr Esc.

## Příprava

Školní VPN připojená. Každé okno PowerShellu otevřít v kořeni projektu:

```powershell
cd J:\DevProjects\mobilesystems
$env:PYTHONPATH = "src"
```

**Okno 1 – lokální mosquitto**
```powershell
mosquitto -c mosquitto/mosquitto.conf -v
```
Musí být vidět `Config loaded`, `'basic-auth'`, `'acl-check'` a `running`.

**Okno 2 – agent**
```powershell
.venv\Scripts\python.exe -m ultrachatagent.main
```
→ `[AGENT] pripojeno na lokalni broker localhost:1884`

**Okno 3 – klient A přes agenta**
```powershell
.venv\Scripts\python.exe -m ultrachatapp.main
```
Identita `VAL0475` → zaškrtnout **Pres agenta** → heslo `monster` → Pripojit
→ agent: `nova session pro 'VAL0475'`, `pripojeno na server`

**Okno 4 – klient B napřímo**
```powershell
.venv\Scripts\python.exe -m ultrachatapp.main
```
Identita `VAL0475-test`, agenta **nezaškrtávat**, `mobilni` / `Systemy`

Rychlá kontrola: A a B si napíšou zprávu všem a soukromou (příjemce `VAL0475` / `VAL0475-test`).

---

## Test 1: fronta zpráv (2b)

1. **Zavřít okno klienta A**
   → agent: `VAL0475: klient offline, zacinam ukladat do fronty`
2. Z klienta B poslat 2–3 zprávy všem a jednu soukromou pro `VAL0475`
   → agent u každé: `do fronty '...' (ve fronte N)`
3. Chvíli počkat a znovu spustit klienta A přes agenta (`VAL0475` / `monster`)
   → agent: `klient online, posilam frontu (N zprav)`
   → v klientovi A se zprávy objeví s **původním časem odeslání**

Varianta s pádem: místo zavření okna ukončit klienta Ctrl+C v okně 3 → mosquitto po chvíli
pošle jeho LWT `offline` a agent ukládá do fronty stejně.

## Test 2: více klientů (1b)

**Okno 5 – klient C přes agenta**
```powershell
.venv\Scripts\python.exe -m ultrachatapp.main
```
Identita `VAL0475-2` → zaškrtnout **Pres agenta** → heslo `monster`

- agent: `nova session pro 'VAL0475-2'` → agent drží 2 spojení na server
- klient B vidí `VAL0475` i `VAL0475-2` online
- z B soukromá zpráva pro `VAL0475-2` → přijde **jen C**, A ne
- zavřít C, z B psát → do fronty se ukládá jen pro `VAL0475-2`, A dostává normálně

Na testy ACL klienta C **zavřít**.

---

## Testy ACL (1b)

Běží okno 1 (mosquitto), 2 (agent), 3 (klient A), 4 (klient B).
Příkazy psát do nového okna PowerShellu v kořeni projektu.

### Test 3: podvrh (nejdůležitější)

```powershell
mosquitto_pub -h localhost -p 1884 -u VAL0475-2 -P monster -t "/mschat/all/VAL0475" -m "1700000000 podvrh"
```
**Kde se dívat:** v okně 1 (mosquitto) bude
```
Denied PUBLISH from VAL0475-2 (d0, q0, r0, m0, '/mschat/all/VAL0475', ... )
```
V agentovi ani v klientovi B se nic nestane.

### Test 4: totéž pod vlastním jménem

```powershell
mosquitto_pub -h localhost -p 1884 -u VAL0475-2 -P monster -t "/mschat/all/VAL0475-2" -m "1700000000 ahoj z konzole"
```
**Kde se dívat:** agent vypíše `-> server '/mschat/all/VAL0475-2'`, klient B zobrazí zprávu od `VAL0475-2`.
Datum bude z roku 2023 – `1700000000` je timestamp z listopadu 2023.

### Test 5: čtení cizí schránky

Klient A (`VAL0475` přes agenta) musí běžet.

```powershell
mosquitto_sub -h localhost -p 1884 -u VAL0475-2 -P monster -t "/inbox/VAL0475/#" -v
```
Příkaz zůstane viset a čekat. Z klienta B napsat zprávu všem.
**Výsledek:** klient A ji dostane, tohle okno nevypíše nic. Ukončit Ctrl+C.

Pro srovnání vlastní schránka zprávy vypisuje:
```powershell
mosquitto_sub -h localhost -p 1884 -u VAL0475-2 -P monster -t "/inbox/VAL0475-2/#" -v
```

### Test 6: špatné heslo

```powershell
mosquitto_sub -h localhost -p 1884 -u VAL0475-2 -P spatne -t "/inbox/VAL0475-2/#"
```
**Výsledek:** hned skončí s `not authorised`. To není ACL, ale `passwd` – ověření, **kdo jsi**.
ACL řeší, **co smíš**.

---

## Otázky k obhajobě

**Proč lokální mosquitto?**
Přihlašování (`passwd`) a oprávnění (`acl`) za nás řeší broker, agent jen přeposílá zprávy.

**Co je v `passwd`?**
Hashe hesel (`$7$` = PBKDF2-SHA512, sůl, 1000 iterací), heslo se z nich zpátky získat nedá.
Mění se přes `mosquitto_passwd`, po změně restartovat mosquitto.

**Co je v ACL?**
```
user VAL0475-agent
topic readwrite #                  ← agent smí všechno

pattern write /mschat/all/%u       ← %u = login připojeného uživatele
pattern write /mschat/user/+/%u
pattern write /mschat/status/%u
pattern read /inbox/%u/#
```

**Proč `/inbox/<login>/`?**
Agent publikuje za všechny uživatele. Kdyby klienti četli přímo `/mschat/...`,
viděli by i cizí soukromé zprávy. Takhle si každý čte jen svou schránku
(`/mschat/all/pepa` → `/inbox/VAL0475/mschat/all/pepa`), klient prefix zase odstraní.

**Jak agent pozná odesílatele?**
Z topicu (`/mschat/all/<odesilatel>`, `/mschat/user/<prijemce>/<odesilatel>`).
Je to bezpečné, protože ACL nikomu nedovolí psát pod cizím jménem.

**Jak agent pozná, že je klient offline?**
Ze stavu `/mschat/status/<login>` – klient při odhlášení pošle `offline`,
při pádu ho za něj pošle mosquitto (LWT).

**Proč se do fronty nedávají stavy?**
Jsou retained – broker si pamatuje poslední stav a klient ho dostane hned po připojení.

**Jak víc klientů?**
Agent má na lokální mosquitto jedno spojení, pro každého uživatele si založí `UserSession`
s vlastním spojením na školní server (`client_id` = identita, login `server` / `Broker`).

**Proč zprávy z fronty mají původní čas?**
Timestamp je součástí payloadu, agent zprávu jen přepošle beze změny.

**Slabina:** fronta je jen v paměti, po restartu agenta se ztratí.
