# Mini-Spec: Fullscreen Blind-Rating & Stern-Filter (Remote + TV)

**spec_version:** 1  
**Datum:** 2026-04-04  
**Ziel:** Implementierungs-Vorschrift ohne Interpretationsspielraum.  
**Bezugscode:** `slideshow_hub/static/remote.html`, `slideshow_hub/main.py` (`/api/rate`, WebSocket-Relay), `photo_tool/actions/export.py` (generierte TV-`index.html`, `cmd`-Handler).

---

## 1. Feature A — Fullscreen „Blind Rating“ auf der Remote

### 1.1 Bedienkonzept

- Nutzer aktiviert einen Modus **Fullscreen Rating** (Button in normaler Remote-UI).
- Bildschirm füllt die **Viewport-Fläche** (Querformat empfohlen); Inhalt ist ausschließlich:
  - **Linker Streifen** (ca. **28 %** der Viewport-Breite): vertikal halbiert in **obere** und **untere** Touch-Zone.
  - **Rechter Streifen** (ca. **28 %** der Viewport-Breite): ebenfalls **oben** / **unten**.
  - **Mitte** (~44 % Breite): **keine** Aktionen (optional neutraler Hintergrund oder schwache Markierung — kein Pflichtinhalt).
  - **Unten mittig:** schmale Leiste (**mind. 48 px** Höhe, `safe-area-inset-bottom` beachten) mit einem Button **„Beenden“** (Fullscreen-Modus verlassen, normale Remote-UI wieder sichtbar).

**Zuordnung (Daumen-Logik):**

| Zone (Quadrant) | Aktion |
|-----------------|--------|
| Links oben (LU) | Sterne **+1** (Couch-Rating), clamp 0…5 |
| Links unten (LD) | Sterne **−1**, clamp 0…5 |
| Rechts oben (RU) | Folie **weiter** (wie `cmd` `next`) |
| Rechts unten (RD) | Folie **zurück** (wie `cmd` `prev`) |

- **Ein Tap** = genau **eine** Aktion + genau **ein** TV-Feedback (siehe Abschnitt 3).
- **Kein** Long-Press / Repeat in v1 (explizit out-of-scope; kann v2).

### 1.2 Fullscreen-API vs. CSS-Vollbild

1. **Primär:** Normales **CSS-Fullscreen-Layout**: `position: fixed; inset: 0; z-index` hoch, Hintergrund und Zonen per `%` — funktioniert überall ohne Permission.
2. **Optional (nice-to-have):** Nach Tap auf **„Vollbild (optional)“** oder nach erstem Tap in den Zonen `Element.requestFullscreen()` auf dem Wrapper — **nur** wenn vorherige User-Geste (Browser-Policy); auf iOS eingeschränkt → Fallback bleibt CSS-Fullscreen.

### 1.3 Debounce / Fehlbedienung

- Pro Zone **mindestens 250 ms** nach einem erfolgreichen Tap **desselben** Quadranten erneut auswerten (verhindert Doppelfeuern durch `touchstart` + `click`).
- Pointer-Events: vorzugsweise **`pointerup`** (oder `touchend`) mit `preventDefault()` nur wenn nötig, Scrollen der Seite im Modus unterbinden (`touch-action: none` auf Overlay).

### 1.4 Abhängigkeiten

- WebSocket zum Hub wie heute; **kein** separater Kanal.
- Für Rating **±1** muss der Hub oder die Remote den **aktuellen** `couch_rating`-Wert kennen — siehe Abschnitt 2 (`rating_delta`).

---

## 2. API-Erweiterung — `/api/rate` mit `rating_delta`

**Zweck:** Blind-Zonen sollen ohne vorheriges `GET slides.json` auf der Remote ein **relatives** Rating setzen.

### 2.1 Request (JSON)

Bestehende Felder unverändert nutzbar. **Neu:**

| Feld | Typ | Bedeutung |
|------|-----|-----------|
| `rating_delta` | `integer`, optional | Nur **`1`** oder **`-1`** erlaubt. |

**Regeln:**

- Wenn `rating_delta` gesetzt ist:
  - **`rating` (absolut) darf nicht gesetzt sein** → sonst **400** mit klarer Fehlermeldung.
  - Server liest **`slides[slide_index].couch_rating`** aus der **Disk**-`slides.json` (wie heute), interpretiert `null`/fehlt als **0**, berechnet `new = clamp(0, 5, alt + rating_delta)`, zurück schreiben wie bisher.
- Wenn `rating_delta` **nicht** gesetzt ist: bisheriges Verhalten (absolut `rating` oder nur `color`).
- Broadcast `type: "rated"` unverändert; Felder `couch_rating` = neuer Wert.

### 2.2 Response

Unverändert zu heute (`ok`, `slide_index`, `couch_rating`, `couch_color`).

---

## 3. WebSocket — TV-Feedback bei Blind-Tap

### 3.1 Nachricht (Remote → Hub → alle außer Sender)

**Einheitlich ein `cmd`**, damit der TV-Player keine zweite Parser-Stufe braucht (bestehend: `if (msg.type !== 'cmd')`).

```json
{
  "type": "cmd",
  "from": "remote",
  "action": "blind_tap",
  "quadrant": "LU"
}
```

**`quadrant`:** eines von **`LU` | `LD` | `RU` | `RD`** (kurz, eindeutig).

### 3.2 Semantik auf dem TV (Slideshow `index.html`)

1. **Visuelles Feedback (immer zuerst oder zeitgleich mit Aktion):**
   - Ein **kurzes Overlay** (ca. **400–600 ms** sichtbar): z. B. **konzentrischer Kreis** oder Ring (2–3 Farben), **zentriert** an einer **fixen Position** relativ zum Viewport (nicht zum Bildinhalt):
   - Normierte **Mittelpunkte** (x, y als Anteil der Viewport-Breite/-Höhe, von links/oben):

   | Quadrant | x | y |
   |----------|---|---|
   | LU | 0.14 | 0.22 |
   | LD | 0.14 | 0.78 |
   | RU | 0.86 | 0.22 |
   | RD | 0.86 | 0.78 |

   - Größe: ca. **12–18 %** der kleineren Viewport-Kante als Durchmesser.
   - `pointer-events: none`; `z-index` über dem Bild, unter permanenten kritischen Controls (oder darüber, wenn Controls ohnehin ausgeblendet).

2. **Keine doppelte Navigation/Rating auf dem TV:**  
   Die **fachliche** Aktion (next/prev/rating) führt die **Remote** aus (HTTP `rating_delta` bzw. `sendCmd('next'|'prev')`), **nicht** der TV durch Auswertung von `blind_tap`.  
   **Grund:** Einheitliche Persistenz (Hub schreibt JSON); TV bleibt „dumm“ für Blind-Tap außer **Animation**.

   **Alternative (nicht in v1):** TV wertet `blind_tap` auch aus → Risiko Doppel-Aktion mit Remote; **verboten** in v1.

3. **Reihenfolge auf der Remote** bei einem Tap:
   - `sendCmd('blind_tap', { quadrant: 'LU' })` — sofort (TV-Feedback).
   - Danach je nach Quadrant: `fetch POST /api/rate` mit `rating_delta` **oder** `sendCmd('next'|'prev')`.

### 3.3 Hub-Änderung

- Keine inhaltliche Filterung nötig: **alle** `cmd` wie bisher an andere Clients relayen; `blind_tap` ist nur ein weiteres `action`.

---

## 4. Feature B — Stern-Filter (phasenweise)

### 4.1 Phase B1 — nur Remote (ohne TV-Player-Logik)

**Ziel:** In der Remote nur Folien mit `couch_rating >= min_stars` durchklicken (`min_stars` ∈ {0,1,2,3,4,5}, **0** = kein Filter).

**Daten:**

- Remote lädt **`slides.json`** einmalig bei Verbindung / auf Knopf **„Filter anwenden“** / wenn sich Galerie-URL ändert (Cache invalidieren).
- Aus `slides[]`: Indexliste **`eligible_indices = [ i | (couch_rating ?? 0) >= min_stars ]`**, stabil nach Originalindex sortiert.

**Navigation:**

- Remote hält **`fp`** „Position in eligible_indices“ (0 … length−1).
- „Weiter“ im Filtermodus: `next_idx = eligible_indices[fp + 1]` → `sendCmd('goto', { index: next_idx })`.
- „Zurück“: analog `fp - 1`.
- Bei eingehendem **`state`** vom TV (`index`): `fp = eligible_indices.indexOf(state.index)`; wenn **−1** (TV zeigt nicht-eligible Folie): entweder **fp auf nächsten eligible** setzen und `goto` schicken (Policy **„sanft korrigieren“**) oder **fp = 0** — in v1: **„korrigieren“**: springe zu nächstem `eligible` ≥ aktueller TV-Index (binary search / erste eligible ab `index`).

**Konflikt:** Wenn zwei Remotes oder TV-Tasten parallel bedienen — bestehende Session-Regel: **eine** Remote empfohlen; kein zusätzlicher Hub-Schutz in v1.

### 4.2 Phase B2 — TV-Slideshow „Autoplay nur ≥ Sterne“

**Ziel:** Auf dem TV `nextSlide()` (inkl. Timer) überspringt Folien unterhalb `min_couch_rating`.

**Konfiguration (v1-Vorschlag):**

- Query-Parameter der **`index.html`**, z. B. `?min_couch_stars=3`, **oder**
- Optional später: `slides.json` Manifestfeld `slideshow_min_couch_stars` (globale Vorgabe).

**Verhalten:**

- Hilfsfunktion `nextEligibleIndex(from, dir)` mit `dir ∈ {+1,-1}`, springt in `photos` bis Rating-Bedingung oder Anfang/Ende (Wrap optional: **gleich wie heute** `nextSlide` Wrap-Regel).
- **`goto` per Remote** bleibt möglich (inkl. zu „schwachen“ Folien); nur **automatisches** Weiter zählt filternd — **oder** konsistent alles filternd (Konfig-Flag `strict_filter: true|false`). v1-Default: **nur Autoplay** filtert; manuelles `goto` von Remote unverändert.

*Diese Phase berührt nur den Export-Generator (`export.py`), nicht den Hub.*

---

## 5. State & Synchronisation

- **`currentIndex`** auf der Remote kommt aus Hub-**`state`** (wie heute).
- Nach `rating_delta` antwortet Hub mit **`rated`**; Remote kann Statuszeile setzen — **kein** Pflichtupdate der lokalen `slides.json`-Cache für B1, aber empfohlen: nach erfolgreichem `rated` **einen** Slide-Eintrag im Cache patchen, damit Filterliste konsistent bleibt, bis nächser Reload.

---

## 6. Testing-Checkliste (manuell)

1. LU/LD: Sterne 0→1→…→5 und 5→4→…→0; `slides.json` auf NAS prüfen.
2. RU/RD: TV wechselt Folie; kein Rating-Schreiben.
3. `blind_tap`: auf dem TV erscheint Animation an erwarteter Seite; **keine** doppelte Folienänderung.
4. Mehrere schnelle Taps: Debounce greift.
5. iPad Safari: Overlay bedienbar; Beenden erreichbar (Safe Area).
6. B1: `min_stars=3`; nur Folien ≥3 per „Weiter“ in Remote; TV springt per `goto`.
7. Ohne WebSocket: Blind-Modus-Button ausgegraut oder Hinweis „verbinden“.

---

## 7. Out of Scope (v1)

- Farbe per Blind-Zonen.
- Haptik / Vibration.
- Mehrere gleichzeitige Fullscreen-Remotes pro Session absichern.
- Undo.

---

## 8. Implementierungsreihenfolge (empfohlen)

1. **`/api/rate`:** `rating_delta` (Hub).
2. **TV:** `blind_tap` + Overlay-Animation (`export.py`).
3. **Remote:** Fullscreen-Overlay + Zonen + Reihenfolge WS → HTTP/dedizierte cmds.
4. **Remote:** Phase B1 Filter (slides.json laden, eligible, `goto`).
5. **Export:** Phase B2 optional (Autoplay-Filter).

---

*Ende der Mini-Spec v1.*
