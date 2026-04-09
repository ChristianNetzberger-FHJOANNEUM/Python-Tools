# Plan: Sound-Archiv auf der NAS + Integration ins Photo Tool

**Ziel:** Zentrale, **lizenzsaubere** Ablage von gekauften und eigenen Audio-Assets; **keine Sackgasse** für spätere Features (Projekt-Pool, `slides.json`, Export, ggf. Import ins Tool).  
**Status:** Planungsgrundlage (nicht implementiert).

---

## 1. Leitlinien (Architektur)

| Prinzip | Bedeutung |
|--------|-----------|
| **Ein Kanon auf der NAS** | Eine **verbindliche** Ordnerstruktur unter einem Root (z. B. `…/sound-library/`). Alte verteilte Platten werden **nach und nach** hierhin **kopiert** (oder spiegeln nur noch als Backup). |
| **Paket = Herkunft + Lizenz** | Jedes **gekaufte Produkt** bleibt als **eigenes Unterpaket** mit **unverändertem** Vendor-Readme/License (keine Vermischung unkontrollierter Dateien). |
| **Workspace sieht nur „Köpfe“** | Das Photo Tool / Workspace verknüpft **Pfade** (oder Unterbäume) aus diesem Archiv – **kein** Duplikat der großen Bibliothek pro Projekt. |
| **Import ≠ Kopie zwangsläufig** | Phase 1: **Verlinken** (`music_roots` im Workspace). Phase 2: **Import-Assistent** (kopieren nach Kanon + Manifest-Eintrag + Stichworte). |

So schließen heutige Entscheidungen ** spätere** automatische Playlist, Sidecar-`music_track`-IDs und LAN-Player **nicht** aus.

---

## 2. Vorschlag Ordnerstruktur auf der NAS

```
sound-library/
  README.md                          # Kurz: Root-Zweck, Versionsstand
  _inventory/                        # Optional: CSV/JSON „was liegt wo“
    sources.yaml
  licensed/                          # Gekaufte Bibliotheken, Originalstruktur wo möglich
    <vendor>/
      <product-slug>/
        LICENSE.txt oder EULA.pdf    # Wie vom Anbieter mitgeliefert
        README.txt                   # Unverändert
        <original folders…>          # z.B. WAV/, Metadata/, stems/
  original/                          # Eigene Aufnahmen, keine Drittlizenz
    <jahr>-<thema>/
  staging/                           # Temporär: neue Käufe vor dem Einsortieren
  rejected/                          # Optional: Duplikate, falsche Formate
```

**Namenskonvention:** `vendor/product-slug` in **Kleinbuchstaben und Bindestrich**; **keine** Leerzeichen in Pfaden (vermeidet Quotes in JSON/YAML und Windows-Pfadchaos).

**SFX vs. Musik:** Entweder **pro Produkt** schon getrennt (viele Libraries liefern das so) oder bei großen Sammlungen zusätzlich:

```
licensed/<vendor>/<product>/categories/ambience|music|foley|ui/
```

Nur einpflegen, wenn es **ohne Bruch** der Vendor-Struktur geht.

---

## 3. Metadaten & Lizenz

- **Nie** Lizenzdateien löschen oder „alles in einen Topf“.  
- Optional: **`_inventory/sources.yaml`** mit Einträgen:

```yaml
- id: boomlibrary-nordic-2024
  path: licensed/boom-library/nordic-collection
  license: commercial-sync
  notes: "Kaufdatum, Shop, Rechnungs-Nr. intern"
```

- **Photo Tool** braucht später nur **`path`** + optional **`tags`** für die UI (Suche/Filter).

---

## 4. Integration ins bestehende Ökosystem

| Schicht | Heute / nahe Zukunft |
|---------|----------------------|
| **Workspace (PC + gemountete NAS)** | Neue Konfiguration: **`audio_library_roots`** (Liste absoluter UNC/Pfade auf `sound-library/...`). Analog zu **Medienordnern** für Fotos. |
| **Projekt** | **„Audio-Pool“** = Schnittmenge oder explizite **Unterbäume** / **Allowlist** (Ordner oder Tags). Kein Kopieren der WAVs ins Projekt. |
| **Export** | Weiterhin **Kopieren** der für die Show benötigten Dateien nach `music/` (wie heute) – **Quelle** ist dann immer **ein Pfad unter sound-library oder Staging**. |
| **`slides.json` / Sidecar** | Später: Referenz **relativ zur Galerie** *oder* **logische ID** aus einem projektinternen Manifest (Mapping ID → absoluter Pfad beim Export auflösen). |

Damit bleibt die **NAS** die **Wahrheit für Assets**; die **exportierte Galerie** bleibt **portabel** (lokal kopiert).

---

## 5. Importfunktion (Wunsch) – sinnvolle Stufen

**Stufe A – Manuell (sofort, ohne Code)**  
- Neue Käufe nach `staging/` legen; Checkliste (Lizenz gelesen); dann nach `licensed/vendor/product/` **verschieben**; Eintrag in `sources.yaml`.

**Stufe B – Photo Tool / Skript „Ordner registrieren“**  
- Dialog: Quellordner (externe Platte oder ZIP entpackt) → Ziel unter `licensed/<vendor>/<product>/`.  
- **Validierung:** erlaubte Extensions (`.wav`, `.flac`, `.mp3`, …), Maximalgröße optional, **keine** EXE etc.  
- **Kopieren oder robuster Move**; **Hash-Deduplikation** optional (gleiche Datei zweimal gekauft).

**Stufe C – Tiefere Integration**  
- **Vorschau** im Tool, **Tags** (Genre, BPM, Länge aus Mediainfo), **Sterne** nur für **Arbeitsorganisation** (nicht Lizenz-relevant).  
- Export eines **kleinen JSON-Katalogs** pro Root für schnelle Suche ohne NAS-Scan bei jedem Klick.

**Lizenz-Hinweis:** Import „bestimmter Dateien“ sollte **nie** automatisch aus dem Web ziehen, wenn die Lizenz **nur für vorhandene Pakete** gilt – immer **explizite Quelle** (Ordner, den der Nutzer wählt).

---

## 6. Migration von verteilten Festplatten (phasiert)

1. **Inventar:** Liste aller bisherigen `…/Soundeffekte/…` Pfade (nicht verschieben, nur dokumentieren).  
2. **Priorisierung:** Was wird zuerst für aktuelle Projekte gebraucht?  
3. **Kopieren** (nicht nur Link) in `sound-library/licensed/...`, damit die NAS **Backup/Versionierung** fahren kann.  
4. Alte Platten danach als **Cold Storage**; NAS als **einzige Arbeitsquelle**.

---

## 7. Abgrenzung Multitrack / Atmos

- Das Archiv hält **Dateien** (Mono/Stereo/Multichannel-Stems wie vom Vendor geliefert).  
- **Echtzeit-Mischpult / Atmos** bleibt **separater Playback-Pfad** (wie in Diskussionen festgehalten); das Archiv **liefert** nur **Rohmaterial**.  
- **Resolve-Exports** (eine Videodatei mit Mehrkanal-Ton) landen sinnvoll bei **Video-Assets** (zweites Archiv oder `sound-library/video/` / Projektrohmaterial) – kann im gleichen Plan verlinkt werden.

---

## 8. Nächste sinnvolle Repo-Schritte (wenn ihr implementieren wollt)

1. Workspace-Konfig um **`audio_library_roots`** erweitern (read-only Scan → Liste in UI).  
2. Export-Modal: Pfadwahl **„aus Bibliothek“** (Datei-Picker über bekannte Roots).  
3. Später: Import-Assistent + `sources.yaml` Generator.

---

*Dokument als Diskussions- und Architekturanker; bei konkreter UI/Schema-Änderung anpassen.*
