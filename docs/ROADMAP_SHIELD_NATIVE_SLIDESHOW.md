# Roadmap: Slideshow-Zielbild (Web vs. NVIDIA Shield)

Dieses Dokument definiert ein **realistisches Zielbild** für maximale Performance und erweiterte Effekte auf der **NVIDIA Shield** (native Android/Kotlin), während der **reine Webbrowser** bewusst **begrenzte** Ziele behält. Das **Photo-Tool** bleibt **Quelle der Rohdaten** (Projekte, Auswahl, Metadaten, Export-Pipeline); der **wesentliche strukturelle Bruch** zur Zukunft liegt vor allem im **Export** (Zielprofil „Web“ vs. „Shield/Native“) und im **Player**, nicht in der Bildverwaltung.

---

## 1. Leitprinzipien

1. **Eine Wahrheit im Photo-Tool** – Kuratierung, Ratings, Playlists, Sidecars, Export-Profile bleiben zentral.
2. **Gemeinsames, versioniertes Playlist-/Slide-Modell** – Ein JSON-Manifest (oder Folge kompatibler Dateien) beschreibt die Show; `schema_version` und optionale **Capability-Flags** erlauben Abwärtskompatibilität.
3. **Zwei Player-Spuren**
   - **Web** – breite Verfügbarkeit, mittlere GPU-/Audio-Tiefe; Features nur, die ohne native Engine zuverlässig laufen.
   - **Shield Native** – volle Nutzung von **HW-Video-Decode**, **OpenGL ES / Vulkan**, TV-**Remote**, optionalem **Prefetch** vom NAS.
4. **Export als Schalter** – Gleiche logische Show, unterschiedliche **Pakete**: Assets (Auflösungen, ggf. Video-Proxies), Manifest-Anreicherung, und Hinweise für den nativen Client (`target: web | shield`).
5. **Audio-Mixing / Mehrkanal / Dolby Atmos** – **bewusst ausgelagert** (eigenes Thema, ggf. andere Geräte-Tools oder spätere Spezifikation). Diese Roadmap verlangt nur: Manifest kann **optionale** Audio-Referenzen tragen; der Web-Player muss sie nicht vollständig interpretieren.

---

## 2. Rollen im Ökosystem

| Komponente | Aufgabe |
|------------|---------|
| **Photo-Tool (+ gui_poc)** | Rohdaten, Projekte, Export-Profile, Erzeugung von Medien + **kanonischem** Show-Manifest |
| **Export „Web“** | HTML/JS/CSS, `slides.json` (o. Ä.), Bilder; Feature-Umfang = **Web-tauglich** |
| **Export „Shield“** | Gleiches Manifest (oder Obermenge), ggf. zusätzliche **Renditions**, **Video-Proxies**, Checksums, optionale **Bundle-Struktur** für den Kotlin-Client |
| **Player Web** | Aktueller Browser-Stack; **Lite-Modus** / `effects_level` respektieren |
| **Player Shield (Kotlin)** | Maximale Performance, alle in der Roadmap als „native“ markierten Features |

---

## 3. Feature-Matrix: Web vs. Shield

Legende: **W** = Web (realistisch), **S** = Shield Native (Ziel), **(L)** = nur mit reduzierter Qualität / Lite-Modus auf Web.

| Feature | Web | Shield | Performance-Hinweis |
|---------|-----|--------|------------------------|
| Grundslideshow, Timing, Pause, Remote (Hub) | W | S | Web: Netzwerk + JS; Shield: native Events |
| Crossfade vs. harter Schnitt | W | S | Cuts günstiger |
| Pro-Slide Dauer / Faktoren | W | S | Nur Datenmodell + Scheduler |
| Ken Burns, Blur-Backdrop | (L) | S | Web: GPU-Last; Shield: Shader |
| Foto + Video gemischt | W (begrenzt) | S | Web: Codec-/Fullscreen-Themen; Shield: ExoPlayer |
| 360° equirektangular | optional (L) | S | Web schwierig; Shield GL/Engine |
| Viele parallele Effekte | vermeiden | S | Web: Presets „lite“ |

---

## 4. Phasen-Roadmap

### Phase A (jetzt / kurzfristig) – Fundament ohne native App

- Manifest-Schema: **`schema_version`**, globale **`effects_level`** oder pro-Slide-Overrides wo sinnvoll.
- Web-Export: dokumentierte **Obergrenzen** (welche Keys der Web-Player ignoriert oder downgradet).
- Kein Zwang, alle Shield-Features im Web nachzubauen.

### Phase B – Web innerhalb realistischer Grenzen

- Pro-Slide: **Dauer-Multiplikator / Stufen**, **Crossfade deaktivieren** (Hard Cut).
- **Lite / Full** im Web (z. B. Blur abgeschaltet, Ken Burns vereinfacht oder aus).
- Video in der Slideshow: nur wenn **messbar stabil** auf Zielbrowsern; sonst „Shield only“ im Manifest kennzeichnen.

### Phase C – Export-Profil „Shield“ (Daten + Paket)

- Export-Target **`shield`** (oder `native_android_tv`): Ausgabeordner-Layout, Manifest mit `target`, ggf. **zusätzliche Felder** (Video-URLs, 360-Typ, Transition-Typ).
- Photo-Tool liefert **dieselbe** Show-Logik; Unterschied = **generierte Dateien** und **Validierung** (z. B. „Video-Slide nur mit shield target“).

### Phase D – Kotlin-App auf Shield (MVP)

- HTTP(S) vom NAS: Manifest + Medien.
- Kern: **Image + Video**, **Timer**, **Cut/Fade**, **Remote**.
- Später: **Ken Burns / Blur** über GPU, **360**-Pfad.

### Phase E – Ausbaustufe nativ

- Erweiterte Übergänge, Preload, 360-Autorotation, robuste Fehlerbehandlung.
- Audio: **nur** soweit für MVP nötig (Stereo, Ducking); Mehrkanal/Atmos = **separates Projekt**.

---

## 5. Was bewusst nicht Teil dieser Roadmap ist

- **Dolby Atmos Object-Mapping** oder kanalbasiertes Authoring für Heimkino – Standardisierung und Tools sind ein **eigenes** Vorhaben; hier höchstens **Hooks** im Manifest (`audio_ref`, `spatial_profile: opaque`).
- **Identische** Feature-Parität Web ↔ Shield – Ziel ist **gemeinsame Show-Beschreibung**, nicht identisches Rendering.

---

## 6. Erfolgskriterien „maximal performant“

- Shield-Player hält **konstante Frametimes** bei typischer 4K-Foto- und1080p/4K-Video-Last (messbar auf Gerät).
- Web-Player bleibt auf schwachen Clients **benutzbar**, wenn `effects_level=lite` gesetzt ist.
- Ein Export aus dem Photo-Tool kann **beide** Targets erzeugen (zwei Jobs oder ein Job mit zwei Ausgaben), ohne die Datenbank duplizieren zu müssen.

---

## 7. Verwandte Dokumente im Repo

- `ARCHITECTURE.md` – Gesamtarchitektur Photo-Tool  
- `Phototool-Konzept.md` – Produktkonzept  
- `Spezifikation_Export_Projekt_*` / `gui_poc/WEB_GALLERY_EXPORT.md` – Export- und Web-Details  
- `slideshow-hub_doku.md` – Hub / Fernsteuerung (sofern weiterhin relevant)

---

*Stand: 2026-04 – lebendes Dokument; bei Schema-Änderungen `schema_version` im Manifest anheben.*
