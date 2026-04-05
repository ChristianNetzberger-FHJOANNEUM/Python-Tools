# Photo Tool – Konzept & Ordnerstruktur

Dieses Dokument fasst die **Idee von Workspace, Medienordnern und Projekten** zusammen und schlägt eine **klare NAS-Struktur** für viele kommende Events/Treks vor. Ziel: Schnelles Wiederfinden, wenig Durcheinander zwischen Rohmedien und Tool-Daten.

---

## 1. Begriffe (kurz)

| Begriff | Bedeutung |
|--------|-----------|
| **Medienordner** | Ordner mit **Originaldateien** (Smartphone, Lumix, Insta360, …). Werden im GUI unter „Media“ / Workspace-Foldern **aktiviert** und gescannt. |
| **Workspace (GUI)** | Ein **logischer Arbeitsbereich**: eine Stelle auf der Festplatte/NAS, unter der Photo Tool **Datenbanken und Projekte** ablegt. **Kein Ersatz** für die Medienordner – die bleiben, wo die Kamera sie erzeugt hat. |
| **Projekt** | Auswahl/Filter auf Teilmenge der Medien (Slideshow, Fotobuch, …). Liegt unter dem Workspace in `gui_poc/projects/<projekt-id>/`. |
| **Export** | Erzeugte Ausgabe (z. B. HTML-Slideshow, Bilder in Auflösung X) – idealerweise **nicht** mitten in den Rohdaten-Ordnern, sondern unter `exports/` oder einem eigenen Zielpfad. |

**Wichtig:** Bewertungen, Labels, Projekt-Zuordnung u. a. werden auch als **Metadaten neben den Dateien** abgelegt (Sidecar-JSON). Dafür müssen die Medienordner auf dem NAS **beschreibbar** sein (oder du akzeptierst, dass Metadaten nur in der DB landen – Standard ist Sidecar + DB-Sync im Hybrid-Modell).

---

## 2. Wo soll der Workspace liegen? (Empfehlung)

### Prinzip

- **Rohmedien und Tool-Artefakte trennen**, aber **pro „Event“ / Trek / Jahr** zusammenhalten.
- Der Workspace soll **nicht innerhalb eines einzelnen Kamera-Ordners** liegen (z. B. nicht nur unter `…/Lumix/`), sondern **auf derselben Ebene wie alle Geräte-Ordner** – damit alle Quellen gleichberechtigt in **einem** Workspace-Projektpool landen.

### Konkret für `N:\NEPAL\2024`

**Empfohlene Struktur:**

```text
N:\NEPAL\2024\
├── PhotoTool-Workspace\      ← Workspace-Wurzel (einen dieser Namen wählen, _ konsistent)
│   ├── gui_poc\
│   │   ├── db\               ← workspace_media.db, Schemas, SQLite-Cache
│   │   └── projects\         ← ein Unterordner pro Projekt (Slideshow, Fotobuch, …)
│   ├── exports\              ← optional: zentrale Exporte (auch manuell so nutzbar)
│   └── README.txt            ← optional: Notizen (Trek, Datenquellen)
├── Smartphone\               ← Medienordner 1 (scannen im GUI)
├── Lumix\                    ← Medienordner 2
├── Insta360\                 ← Medienordner 3
└── …                          ← weitere Quellen
```

**Warum nicht den Workspace *in* einen Medienordner legen?**  
Damit bleibt klar: *Hier liegen Dateien von Gerät X*, *hier verwaltet das Tool Indizes und Projekte*. Vermeidet versehentliche Backups nur „Lumix“ ohne Projekte.

**Warum nicht die Ebene `N:\NEPAL\` ohne Jahr?**  
Kann man machen (`N:\NEPAL\PhotoTool-Workspace` mit Scan-Roots `2024\Smartphone` etc.), wird aber bei **vielen Jahren** unübersichtlich und eine DB wächst sehr groß. **Pro Jahr/Trek ein Workspace** ist meist die bessere Balance (klare Trennung, einfachere Archive).

---

## 3. Alternative: Workspace „neben“ dem Jahresordner

Wenn `2024` strikt nur Rohdaten enthalten soll:

```text
N:\NEPAL\
├── 2024\                     ← nur Medien
│   ├── Smartphone\
│   └── Lumix\
└── 2024-PhotoTool\           ← Workspace-Wurzel; im GUI Scan-Roots auf ..\2024\… setzen
    └── gui_poc\...
```

Technisch gleichwertig; du musst nur **absolute Pfade** der Quellen korrekt im GUI hinterlegen.

---

## 4. Was das Photo Tool unter der Workspace-Wurzel anlegt

Orientierung am aktuellen **Web-GUI**-Setup:

- **`gui_poc/db/`** – globale Mediendatenbank (`workspace_media.db`), Performance für große Sammlungen.
- **`gui_poc/projects/<id>/`** – **projekt-spezifische** Daten (`project.db` etc.).
- **Klassisches CLI-Workspace** (falls `photo-tool workspace init …` genutzt): eigene Struktur mit `config.yaml`, `cache/`, `db/index.sqlite` – kann parallel existieren; für den Alltag im **GUI** entscheidend ist die **`gui_poc`-Struktur unter der gewählten Workspace-Wurzel**.

---

## 5. Metadaten neben den Bildern (Sidecars)

Das System nutzt u. a. Dateien wie:

- `.{dateiname}.metadata.json` oder `{name}.metadata.json` – Nutzer-Metadaten (Ratings, …)
- `{name}.phototool.json` – Analyse-Daten

**Konsequenz:** Die freigeschalteten Medienordner auf der NAS sollten **Schreibrechte** für den PC/API haben, mit dem du das Tool bedienst. Sonst sind **Backups** der Nur-Lese-Kopie ohne diese JSON-Dateien unvollständig.

---

## 6. Typischer Ablauf (NAS: uGreen 4300)

1. **NAS-Freigabe mappen** (z. B. `N:`), Ordnerstruktur wie oben anlegen (`PhotoTool-Workspace` + bestehende Geräte-Ordner).
2. **Photo Tool starten** (siehe `gui_poc/README.md`): im Repo `venv` aktivieren, `cd gui_poc`, `python server.py` → Browser `http://localhost:8000`.
3. Beim ersten Mal **Workspace-Wurzel** auf `N:\NEPAL\2024\PhotoTool-Workspace` setzen (bzw. den gewählten Pfad).
4. **Medienordner** (`Smartphone`, `Lumix`, `Insta360`, …) **registrieren und aktivieren**, Scan abwarten.
5. **Projekte** anlegen: z. B. `Slideshow-Besta`, `Fotobuch-CEWE`, `Resolve-Short` – jeweils andere Filter/Ratings.
6. **Export:** Zielordner sinnvoll wählen (z. B. `PhotoTool-Workspace\exports\slideshow-besta\` oder separater `N:\NEPAL\2024\Exports\…`), damit Rohordner sauber bleiben.

---

## 7. Export-Profile (Merke)

| Profil (Beispiel) | Typische Nutzung |
|-------------------|------------------|
| Web / kompakt | Vercel, schnelle Veröffentlichung |
| `smart_tv_8k` | Lokaler 8K-TV / hochauflösende HTML-Slideshow auf NAS |
| Später ggf. Shield-optimiert (4K) | Wenn du NVIDIA Shield + TV-Upscale nutzt |

Musik, Splash-Text und Export-Einstellungen können im GUI im Export-Dialog gesetzt werden; viele Werte sind **session-übergreifend** in `localStorage` gespeichert (Browser).

---

## 8. Skalierung: viele Treks / Jahre

Empfehlung:

```text
N:\NEPAL\
├── 2024\
│   ├── PhotoTool-Workspace\
│   └── …Medien…
├── 2025\
│   ├── PhotoTool-Workspace\
│   └── …Medien…
└── …
```

Pro Jahr **ein** Workspace vermeidet eine „Mega-Datenbank“ und macht Archive/Zip/Backup pro Trek einfacher.

---

## 9. Backup-Checkliste

- [ ] Medienordner (Originalbilder/Videos)  
- [ ] `PhotoTool-Workspace` (mindestens `gui_poc/`)  
- [ ] Sidecar-JSONs **in** den Medienordnern (falls beschreibbar)  
- [ ] Export-Ordner, falls du sie nicht neu erzeugen willst  

---

## 10. One-Liner: Server starten

```powershell
cd C:\_Git\Python-tools
.\venv\Scripts\Activate.ps1
cd gui_poc
python server.py
```

Browser: **http://localhost:8000** (Port laut `server.py`; für Zugriff vom TV/Firewall ggf. Port freigeben).

---

## 11. uGreen NAS 4300 – Slideshow per Docker (nginx)

Ziel: **ohne PC** nur mit Browser am TV (Lesezeichen `http://<NAS-IP>:8080/`).

| Element | Bedeutung |
|--------|-----------|
| **Freigabe `web`** | Statische Dateien: Landing Page + je Slideshow ein Unterordner |
| **Docker-Projekt `slideshow-web`** | Image `nginx:alpine`, Host-Port **8080** → Container **80** |
| **Volume** | Host: Pfad der Freigabe `web` → Container: `/usr/share/nginx/html` (read-only möglich) |

**Ordner auf der NAS (Beispiel):**

```text
web/
├── index.html           ← Landing Page (Einstieg)
├── mera-peak/           ← eine exportierte Galerie
│   ├── index.html
│   ├── slides.json      ← Zuordnung Export → Original + Sidecar (für Handy-Bewertung / NAS-Helfer)
│   ├── images/
│   └── …
└── andere-slideshow/
    └── …
```

### `gallery/slides.json` (Manifest)

Wird bei **jedem Galerie-Export** mitgeschrieben (`…/gallery/slides.json` relativ zum gewählten Export-Ordner). Enthält pro Slide u. a.:

| Feld | Bedeutung |
|------|-----------|
| `index` | 0-basierter Index = gleiche Reihenfolge wie in der Slideshow |
| `export_image` | Relativpfad, z. B. `images/0000.jpg` |
| `thumbnail` | z. B. `thumbnails/0000.jpg` |
| `source_path` | **Absoluter Pfad zum Original** auf dem Rechner/NAS (zur Laufzeit des Exports) |
| `metadata_sidecar` | Pfad zur Datei `.{name}.metadata.json` (Photo Tool) |
| `rating`, `color`, `keywords` | Stand beim Export |

**Hinweis:** Ein zukünftiger **Helfer-Server** auf der NAS kann so Sterne/Farben zur **richtigen Originaldatei** schreiben, sofern `source_path` bzw. Sidecar-Pfade von der NAS aus erreichbar/schreibbar sind (gleiche Freigaben wie beim Bearbeiten im Photo Tool).

**Landing Page im Repository:** [`nas_landing_page/index.html`](nas_landing_page/index.html) – nach Ändern der Karten (`href`, Titel) per Dateimanager in die **Wurzel von `web`** kopieren (oder dort direkt bearbeiten).

**Hinweise:**

- Wenn die Seite **403** zeigt: im Ordner `web` (nicht nur Papierkorb-Ordner `#recycle`) mindestens **`index.html`** ablegen.
- Im Docker-Terminal des Containers: `ls /usr/share/nginx/html` muss dieselben Dateien zeigen wie die Freigabe `web`.
- Hersteller ist **uGreen (UGOS)**; einzelne UI-Bezeichnungen können an andere NAS-Oberflächen erinnern – fachlich zählen Freigabe, Docker und Pfad.

---

*Stand: abgestimmt auf das Repository Python-tools (Workspace-Modell `gui_poc` unter der gewählten Workspace-Wurzel). **NAS-Zielgerät:** uGreen 4300 + Docker/nginx für statische Slideshows. Bei Schema-Änderungen im Code dieses Dokument kurz aktualisieren.*
