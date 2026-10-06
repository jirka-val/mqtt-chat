# Cviko 3 – postup testování

Offline režim na straně klienta – frontu zpráv, seznam uživatelů a „všichni offline“ řeší klient sám.

```
klient A ──► proxy :1885 ──► pcfeib425t.vsb.cz:1883 ◄── klient B
             (Ctrl+C = výpadek)
```

Proxy (`tools/proxy.py`) jen přeposílá spojení na školní server. Když ho ukončíš, klientovi A
spadne spojení jako při výpadku sítě, klient B zůstane připojený a vidí, co se děje.

| Klient | Host / port | Identita | Login |
|---|---|---|---|
| A | `localhost` / `1885` | `VAL0475` | `mobilni` / `Systemy` |
| B | `pcfeib425t.vsb.cz` / `1883` | `VAL0475-test` | `mobilni` / `Systemy` |

„Pres agenta“ se **nezaškrtává**. Agent z cvika 2 nesmí běžet – připojoval by se na školu
jako `VAL0475` a s klientem A by se navzájem odpojovali.

> Pozor: když v okně PowerShellu označíš myší text, program v něm se zastaví (titulek „Vybrat“).
> Kopírovat Enterem nebo pravým tlačítkem, zrušit výběr Esc.

## Příprava

Školní VPN připojená. Každé okno PowerShellu:

```powershell
cd J:\DevProjects\mobilesystems
$env:PYTHONPATH = "src"
```

**Okno 1 – proxy**
```powershell
.venv\Scripts\python.exe tools/proxy.py
```
→ `[PROXY] localhost:1885 -> pcfeib425t.vsb.cz:1883, vypadek = Ctrl+C`

**Okno 2 – klient A**
```powershell
.venv\Scripts\python.exe -m ultrachatapp.main
```
Host `localhost`, port `1885`, identita `VAL0475`, `mobilni` / `Systemy`
→ proxy: `nove spojeni`, hlavička chatu: `VAL0475 - online`

**Okno 3 – klient B**
```powershell
.venv\Scripts\python.exe -m ultrachatapp.main
```
Výchozí host a port, identita `VAL0475-test`, `mobilni` / `Systemy`

Rychlá kontrola: A a B si napíšou zprávu všem a soukromou.

---

## Test 1: fronta zpráv při výpadku (2b)

1. **Okno 1 – Ctrl+C** (proxy skončí)
   → konzole A: `spojeni ztraceno ..., zpravy jdou do fronty`
   → hlavička A: `VAL0475 - offline`
2. **V A napsat 2 zprávy všem**
   → hlavička A: `offline (ve fronte 2)`, B nedostane nic
3. Chvíli počkat (ať je vidět rozdíl v čase)
4. **Okno 1 – znovu spustit proxy**
   → A se do pár sekund sám připojí, konzole: `z fronty na '/mschat/all/VAL0475'`
   → hlavička A: `VAL0475 - online`
   → B dostane obě zprávy s **časem napsání**, ne odeslání

## Test 2: všichni offline (1b)

1. **Okno 1 – Ctrl+C**
2. Počkat **15 s**
   → konzole A: `server porad nedostupny, vsichni offline`
   → v seznamu uživatelů A jsou všichni šedí (offline), včetně B, který je ve skutečnosti online
3. **Okno 1 – znovu spustit proxy**
   → A se připojí, server pošle aktuální stavy → B a ostatní online uživatelé jsou zase zelení

## Test 3: soukromá zpráva pro odpojeného uživatele (1b)

**a) uživatel se odpojil, zatímco jsem byl offline**

1. **Okno 1 – Ctrl+C** (A offline)
2. V A napsat **soukromou zprávu pro `VAL0475-test`** a jednu **všem**
   → hlavička A: `offline (ve fronte 2)`
3. **Zavřít okno klienta B** (B se odhlásí, na serveru je offline)
4. **Okno 1 – znovu spustit proxy**
   → zpráva všem odejde, soukromá **zůstane ve frontě** – hlavička A: `online (ve fronte 1)`
5. **Znovu spustit klienta B** (`VAL0475-test`)
   → jakmile je B online, A pošle soukromou zprávu: konzole A `z fronty na '/mschat/user/VAL0475-test/VAL0475'`
   → B ji dostane s původním časem, hlavička A: `VAL0475 - online`

**b) uživatel je offline a já jsem online**

1. Zavřít klienta B, A je online
2. V A napsat soukromou zprávu pro `VAL0475-test`
   → hlavička A: `online (ve fronte 1)`
3. Spustit klienta B → zpráva mu přijde

## Test 4: pravidelné obnovení seznamu

Každých 30 s konzole A vypíše `obnovuji seznam uzivatelu` – klient znovu odebere stavy
a broker mu pošle všechny uložené (retained) stavy znovu.

---

## Otázky k obhajobě

**Čím se liší od cvika 2?**
Cviko 2: odpojený je klient, agent mu drží **příchozí** zprávy.
Cviko 3: odpojený je server, klient si drží **odchozí** zprávy.

**Proč ve klientovi a ne jako agent?**
Zadání to dovoluje („resp. to dělá klient sám“), méně procesů, funguje napřímo i přes agenta.

**Jak klient pozná výpadek?**
Paho zavolá `on_disconnect` – buď spojení spadne hned, nebo nepřijde odpověď na keepalive
(`PINGREQ` každých 10 s, mrtvé po 1.5× keepalive = 15 s).

**Kdo se stará o znovupřipojení?**
Paho samo (`reconnect_delay_set(1, 5)` – zkouší po 1 až 5 s), pak se zavolá normální `on_connect`.

**Proč mají zprávy z fronty původní čas?**
Payload (timestamp + text) se vytvoří při napsání, do fronty jde hotový.

**Jak se obnovuje seznam uživatelů?**
Opakovaný subscribe – podle MQTT broker při novém subscribe znovu pošle všechny retained zprávy.

**Proč se fronta posílá až v `on_subscribe` a ne v `on_connect`?**
Zpráva napsaná těsně po výpadku (než ho klient pozná) nejde do naší fronty, ale do paho,
které si ji drží nepotvrzenou. Po připojení ji paho pošle znovu – ale až **po** `on_connect`.
Kdyby se fronta posílala v `on_connect`, předběhla by ji a pořadí by se prohodilo.
Potvrzení subscribe přijde vždy až potom.

**Proč se po připojení maže cache stavů?**
Během výpadku se mohl někdo odpojit. Soukromé zprávy proto čekají na aktuální stav ze serveru,
ne na starý z cache.

**Jak funguje „všichni offline“?**
Při výpadku se spustí časovač 15 s. Když se klient nepřipojí, pošle GUI pro všechny z cache
stav `offline` – stejnou cestou, jakou chodí stavy ze serveru. Cache se nemění,
po připojení přijdou správné stavy.

**Proč je v seznamu uživatelů časovač 100 ms?**
Server pošle ~150 stavů najednou, seznam se překreslí jen jednou po poslední.
Bez toho GUI při každém obnovení na ~10 s zamrzlo.

**Proč fronta a seznam používají zámek / signál?**
GUI, paho a časovače běží v různých vláknech. Fronta má zámek, do GUI se posílá
přes Qt signál (widgety se smí měnit jen z hlavního vlákna).

**Slabiny:** fronta je jen v paměti; při nedostupném serveru už při přihlášení offline režim
nenaskočí; soukromá zpráva pro identitu, která se nikdy nepřipojí, zůstane ve frontě navždy.
