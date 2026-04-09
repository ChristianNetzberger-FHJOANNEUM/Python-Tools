# Slideshow Remote Hub – Doku (Setup-Zusammenfassung)

Diese Datei fasst die **Erstellung, das Bauen und den Betrieb** des Slideshow Remote Hub zusammen, inklusive der **PowerShell-** und **SSH-Befehle**, die im Projektverlauf verwendet wurden.

Betroffene Komponenten im Repo:

- `slideshow_hub/` – FastAPI-App (WebSocket-Relay, `/remote`, `/api/rate`)
- `compose.slideshow-hub.yml` – optional: Docker Compose vom Repo-Root
- Exportierte Galerie: `slideshow`-Template mit optionalen Feldern **LAN remote** (`remote_hub_ws_base`, `remote_session_id`)

---

## 1. Kurzüberblick Architektur

| Dienst            | Typische Rolle                              | Beispiel-Port |
|-------------------|---------------------------------------------|---------------|
| Galerie (nginx)   | `index.html`, Bilder, `slides.json`         | **8080** → 80 |
| Slideshow Hub     | Fernbedienung, WebSocket, Bewertungs-API    | **8090**      |

- **HTTP Fernbedienung:** `http://<NAS-IP>:8090/remote` (Handy/Browser – **kein** `ws://` in die Adresszeile).
- **WebSocket-Basis** (für TV + Remote-UI, wird von JavaScript genutzt): `ws://<NAS-IP>:8090/ws` – Session wird angehängt, z. B. `/default`.
- **Healthcheck:** `http://<NAS-IP>:8090/health`

---

## 2. Entwicklung am PC **ohne** Docker

Voraussetzung: Repo-Root, z. B. `C:\_Git\Python-tools`, aktiviertes venv.

```powershell
cd C:\_Git\Python-tools
.\venv\Scripts\Activate.ps1
pip install -r slideshow_hub\requirements.txt
python -m uvicorn slideshow_hub.main:app --host 0.0.0.0 --port 8090
```

Optional mit Auto-Reload bei Codeänderungen:

```powershell
python -m uvicorn slideshow_hub.main:app --host 0.0.0.0 --port 8090 --reload
```

**Hinweis:** Befehl immer vom **Repo-Root** ausführen, damit `slideshow_hub` als Paket importierbar ist.

---

## 3. Docker: Image am PC bauen

Voraussetzung: **Docker Desktop** läuft (Engine aktiv, sonst Fehler `docker_engine` / Pipe).

### Skript (Build + `docker save`, optional SCP)

Vom Repo-Root:

```powershell
cd C:\_Git\Python-tools
.\slideshow_hub\update-hub.ps1
```

ARM64 (Standard): nichts weiter. Intel-NAS: `.\slideshow_hub\update-hub.ps1 -Platform linux/amd64`

Nur bauen, keine `.tar`: `.\slideshow_hub\update-hub.ps1 -NoSave`

Kopie auf die NAS (OpenSSH-`scp`):

```powershell
.\slideshow_hub\update-hub.ps1 -ScpTarget "christian@192.168.0.100:/volume1/data/docker-images/slideshow-hub.tar"
```

Am Ende werden die **SSH-Befehle** zum Container-Neustart ausgegeben (`-NoPrintNasCommands` unterbindet das).

---

Wechsel ins Repo-Root (manueller Ablauf):

```powershell
cd C:\_Git\Python-tools
```

### 3.1 Standard-Build (lokal meist **linux/amd64**)

```powershell
docker build -f slideshow_hub/Dockerfile -t slideshow-hub:local .
```

### 3.2 Build für **ARM64-NAS** (`aarch64`, z. B. UGreen DH4300+)

Auf der NAS prüfen:

```bash
uname -m
```

Wenn Ausgabe **`aarch64`**, Image **auf dem PC** für `linux/arm64` bauen:

```powershell
cd C:\_Git\Python-tools
docker buildx create --use 2>$null
docker buildx build --platform linux/arm64 -f slideshow_hub/Dockerfile -t slideshow-hub:local --load .
```

Architektur des lokalen Images prüfen (soll **arm64** sein, nicht amd64):

```powershell
docker image inspect slideshow-hub:local --format "{{.Os}}/{{.Architecture}}"
```

**Warnung ignorieren nicht:** Lädt man ein **amd64**-Image auf eine **arm64**-NAS, meldet `docker run` u. a. `platform (linux/amd64) does not match ... (linux/arm64/v8)` – der Container ist dann ungeeignet; neu bauen mit `--platform linux/arm64`.

---

## 4. Image exportieren (`.tar` für NAS)

Am PC, nach erfolgreichem Build:

```powershell
cd C:\_Git\Python-tools
docker save slideshow-hub:local -o slideshow-hub.tar
```

Die Datei `slideshow-hub.tar` per SMB/USB auf die NAS kopieren (z. B. Ordner `docker-images` auf einer Freigabe).

**Gültigkeit der `.tar` am PC prüfen** (optional):

```powershell
docker load -i slideshow-hub.tar
```

Erwartung: Meldung `Loaded image: slideshow-hub:local`.

---

## 5. Auf der NAS (SSH): Image laden und Container starten

Einloggen (Beispiel):

```bash
ssh christian@192.168.0.100
```

Image laden (Pfad anpassen):

```bash
sudo docker load -i /volume1/data/docker-images/slideshow-hub.tar
```

Alten Container/Image bei Bedarf entfernen (vor erneutem Import):

```bash
sudo docker stop slideshow-remote-hub 2>/dev/null
sudo docker rm slideshow-remote-hub 2>/dev/null
sudo docker rmi slideshow-hub:local 2>/dev/null
```

**Container** aus dem Image erstellen und starten:

```bash
sudo docker run -d --name slideshow-remote-hub --restart unless-stopped -p 8090:8090 slideshow-hub:local
```

Status und Health auf der NAS:

```bash
sudo docker ps
curl -s http://127.0.0.1:8090/health
```

Logs:

```bash
sudo docker logs slideshow-remote-hub --tail 50
```

**Wichtig:** `docker load` legt nur ein **Abbild** an; ein **Container** entsteht durch `docker run` oder die Docker-UI („Ausführen“ / „Erstellen“) mit Port **8090:8090**.

Der **obige** Einzeiler-`docker run` enthält **weder** Volume **noch** `SLIDESHUB_GALLERY_PATH_MAP` — Bewerten und „Manifest laden“ funktionieren dann nicht. Für Produktivbetrieb siehe **Abschnitt 5.1**.

### 5.1 Dauerhafte Konfiguration (Volumes & Env nach jedem Deployment)

**Problem:** In vielen NAS-Oberflächen legt man nach **Import eines neuen Images** einen **neuen** Container an. Dabei gehen **Volume-Zuordnung** und **Umgebungsvariablen** leicht verloren — dieselbe Prozedur wie beim ersten Mal.

**Empfehlung:** Konfiguration in einer **Compose-Datei** auf der NAS festhalten und den Hub **immer über Compose** starten/aktualisieren (nicht nur „Image → Container“ per Mausklick).

1. **Repo-Datei** `compose.slideshow-hub.yml` auf den Docker-Host kopieren (z. B. `/volume1/docker/slideshow-hub/compose.yml`).
2. **Anpassen** (einmalig):
   - `SLIDESHUB_GALLERY_PATH_MAP`: Schlüssel = exakter Browser-**Origin** der Galerie (`http://IP:Port`), Wert = **Mount-Pfad im Container** (z. B. `/volume1/web` oder `/nas-web`).
   - `volumes`: **Links** = Ordner auf dem NAS-Host (Freigabe `web`), **rechts** = **derselbe** Pfad wie im JSON-Wert der Map.
3. **Image aktualisieren:** `docker load -i slideshow-hub.tar` (neues Tag `slideshow-hub:local`), dann im Compose-Ordner:

   ```bash
   cd /pfad/zum/compose-ordner
   sudo docker compose -f compose.yml up -d
   ```

   (Dateiname anpassen; unter DSM ggf. **Container Manager → Projekt** mit derselben YAML.)

**Synology DSM:** Abhängig von Version **„Projekt“** / **Stack** aus `docker-compose`-Datei — dort bleiben Volumes und Variablen am Projekt hängen, auch wenn das Image neu geladen wird.

**Alternative ohne Compose:** Ein kleines Shell-Skript auf der NAS mit **vollständigem** `docker run … -e SLIDESHUB_GALLERY_PATH_MAP=… -v /…:/…:rw -p 8090:8090` — nur nicht verlieren und nach Image-Update erneut ausführen.

**Kurz:** Was persistent sein soll, gehört **nicht** nur in die UI eines einmal angelegten Containers, sondern in **deklarierte** Konfiguration (Compose oder Skript), die du bei jedem Deploy **wiederverwendest**.

### Pfad-Hinweis (UGreen / Synology)

Der Pfad zur `.tar` hängt vom Volume ab, z. B. `/volume1/data/docker-images/…`. Mit `ls` auf der NAS den exakten Ort prüfen.

---

## 6. Bekannte Stolpersteine

### 6.1 Docker-CLI ohne laufenden Desktop

Fehler z. B. an `npipe://.../docker_engine`: **Docker Desktop starten** und warten, bis die Engine läuft; dann `docker build` erneut.

### 6.2 `ws://` im Browser

**Nicht** `ws://192.168.0.100:8090/ws` in die Adresszeile eingeben → Fehler `ERR_UNKNOWN_URL_SCHEME`.  
Stattdessen: **`http://192.168.0.100:8090/remote`** – die Seite baut das WebSocket selbst.

### 6.3 Synology / NAS-UI: Import zeigt `.tar` nicht

Manche Dateiauswahl-Dialoge listen im Ordner-Root nur Unterordner. **Workaround:** `.tar` in einen Unterordner legen (z. B. `docker-images`) oder **ohne UI** laden:

```bash
sudo docker load -i /pfad/zur/slideshow-hub.tar
```

### 6.4 UI: „Nicht unterstütztes Architekturformat“

Image-Architektur passt nicht zur NAS-CPU → Abschnitt **3.2** (ARM64-Build) und neue `.tar`.

### 6.5 Remote zeigt „Nicht verbunden“

Auf `/remote` den Button **„Verbinden“** klicken.  
In den Logs sollte u. a. erscheinen: `WebSocket /ws/default` … `accepted`.

---

## 7. Couch-Bewertungen (`/api/rate`) und `SLIDESHUB_GALLERY_PATH_MAP`

Sterne/Farbe vom Handy schreiben **`couch_rating` / `couch_color`** in die **`slides.json`** der Galerie (nicht in Original-Sidecars). Der Hub muss den **gleichen Ordner** sehen wie nginx:

```bash
# Beispiel Docker (JSON in einfachen Anführungszeichen unter Linux):
-e 'SLIDESHUB_GALLERY_PATH_MAP={"http://192.168.0.100:8080":"/volume1/web"}'
```

Schlüssel = exakter **Origin** (`scheme://host:port`), Wert = **Wurzel** der Freigabe, unter der die URL-Pfade liegen (z. B. `…/mera-peak/slides.json` → `/volume1/web/mera-peak/slides.json`).

Der **POST-Body** kann optional **`session_id`** enthalten (wie WebSocket-Sitzung), damit die TV-Slideshow per Broadcast aktualisiert wird.

---

## 8. Handy / iPad / QR

- **URL im Browser:** `http://<NAS-IP>:8090/remote` (z. B. `http://192.168.0.100:8090/remote`).
- **QR-Code:** dieselbe **HTTP**-URL kodieren (nicht `ws://`).
- **Session** in `/remote` muss mit der **exportierten Slideshow** übereinstimmen.

---

## 9. Galerie-Export (Photo Tool)

Im Export (Slideshow) optional:

- **LAN remote – WebSocket-Basis:** z. B. `ws://192.168.0.100:8090/ws`
- **Session-ID:** z. B. `default`

**Bewertungen (`/api/rate`):** Der Hub muss die in `slides.json` stehenden **`source_path`**-Dateien auf dem **Hub-Host** (Container/NS) lesen/schreiben können – ggf. Volumes im Docker-Setup und Pfade anpassen (siehe Kommentar in `compose.slideshow-hub.yml`).

---

## 10. Debugging: TV reagiert nicht / Verbindungs-LEDs

### Sichtbare Anzeigen (nach Deploy)

- **`/remote`:** Zwei LEDs – **Hub** (Verbindung zum Hub-Server) und **TV / Slideshow** (grün, wenn in den letzten ~5 s ein **`state`**-Frame von der Slideshow kam). **Gelb** bei „TV“ = Hub ok, aber **keine Slideshow** in derselben Session oder **alte `index.html`** ohne Hub-Code.
- **Exportierte Slideshow:** Unten rechts **„LAN-Remote“** mit Punkt (grün = WebSocket zum Hub offen, orange = Verbindungsaufbau, grau/rot = getrennt/Fehler) – nur wenn beim Export die Hub-**WebSocket-URL** gesetzt war.

Nach Änderungen an `remote.html` / Hub: **Docker-Image neu bauen**, `.tar` erneut auf die NAS, `docker load` + Container neu. Nach Änderungen nur an der **Slideshow**: **neu exportieren** und `index.html` (und ggf. Bilder) auf die NAS legen.

### Technische Checks

1. **`index.html` prüfen** (auf der NAS oder lokal geöffnet): Im Seitenquelltext nach `REMOTE_HUB_WS_BASE` bzw. der eingetragenen `ws://…`-URL suchen. Fehlt sie, war der Export **ohne** LAN-Remote oder nicht das Template **Slideshow**.
2. **Gleiche Session** wie auf `/remote` (z. B. `default`).
3. **Hub-Logs** beim Tippen auf Weiter/Zurück am Handy:

   ```bash
   sudo docker logs -f slideshow-remote-hub
   ```

   Es sollten weiterhin WebSocket-Verbindungen bzw. Nachrichten sichtbar sein (je nach Log-Level).
4. **TV-Browser:** Viele TVs haben keine Konsole; auf dem PC dieselbe Galerie-URL öffnen und **Entwicklertools → Konsole**. Slideshow mit Parameter **`?remoteDebug=1`** laden, z. B.  
   `http://192.168.0.100:8080/mera-peak/?remoteDebug=1`  
   Dann erscheinen `[remote-hub]`-Logs bei eingehenden **`cmd`**-Nachrichten.
5. **Beweis „Befehl wirkt“:** Auf `/remote` muss **„TV“ grün** sein und die **Folien-Anzeige** (`Folie x / y`) beim Tipp auf Weiter/Zurück **mitwechseln** – die Slideshow sendet nach jedem Bildwechsel **`state`**.

### Später: mehr Befehle auf der Remote

Aktuell umgesetzt: **weiter, zurück, Play/Pause**; die TV-Seite kann bereits **`goto`** (Index). Denkbar fürs iPad: Geschwindigkeit, Loop, Vollbild, Musik – durch neue **`cmd`-Typen** in `remote.html` und im exportierten Slideshow-Skript (analog zu `next`/`prev`/`toggle`).

---

## 11. Optional: Compose vom Repo-Root

Wenn das **gesamte Repo** auf der NAS liegt und dort gebaut werden soll:

```bash
docker compose -f compose.slideshow-hub.yml up -d --build
```

(Build-Kontext ist das Repo-Root, siehe `compose.slideshow-hub.yml`.)

---

## 12. Referenz: Schnellbefehle (PC + NAS)

| Schritt              | Wo  | Befehl |
|----------------------|-----|--------|
| Hub lokal testen     | PC  | `python -m uvicorn slideshow_hub.main:app --host 0.0.0.0 --port 8090` |
| Image ARM64 bauen    | PC  | `docker buildx build --platform linux/arm64 -f slideshow_hub/Dockerfile -t slideshow-hub:local --load .` |
| tar erzeugen         | PC  | `docker save slideshow-hub:local -o slideshow-hub.tar` |
| tar laden            | NAS | `sudo docker load -i /…/slideshow-hub.tar` |
| Container starten    | NAS | `sudo docker run -d --name slideshow-remote-hub --restart unless-stopped -p 8090:8090 slideshow-hub:local` |

---

*Stand: Zusammenfassung der im Projekt durchgeführten Schritte (Docker Desktop, ARM64-NAS `aarch64`, UGreen/Synology, Ports 8080/8090).*
