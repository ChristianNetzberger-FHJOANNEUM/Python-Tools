<#
.SYNOPSIS
    Baut das Slideshow-Hub-Docker-Image und erzeugt slideshow-hub.tar (optional: Kopie per SCP auf die NAS).

.DESCRIPTION
    Voraussetzung: Docker Desktop läuft, Aufruf vom Repo-Root wird empfohlen:
        .\slideshow_hub\update-hub.ps1
    Oder aus diesem Ordner:
        cd C:\_Git\Python-tools\slideshow_hub
        .\update-hub.ps1

.PARAMETER Platform
    Docker --platform (Standard: linux/arm64 für typische ARM-NAS wie UGreen aarch64).
    Für Intel-NAS: -Platform linux/amd64

.PARAMETER TarPath
    Ausgabepfad für docker save (Standard: <RepoRoot>\slideshow-hub.tar)

.PARAMETER NoSave
    Nur bauen, kein docker save

.PARAMETER ScpTarget
    Optional: Ziel für scp, z.B. christian@192.168.0.100:/volume1/data/docker-images/slideshow-hub.tar
    Benötigt OpenSSH-Client (Windows optional feature).

.PARAMETER PrintNasCommands
    Nach dem Save die empfohlenen SSH-Befehle zum Container-Neustart ausgeben (Standard: true)
#>
[CmdletBinding()]
param(
    [string]$Platform = "linux/arm64",
    [string]$ImageTag = "slideshow-hub:local",
    [string]$TarPath = "",
    [switch]$NoSave,
    [string]$ScpTarget = "",
    [switch]$NoPrintNasCommands
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

if (-not $TarPath) {
    $TarPath = Join-Path $RepoRoot "slideshow-hub.tar"
}

Write-Host "Repo-Root: $RepoRoot"
Write-Host "Platform:  $Platform"
Write-Host "Image:     $ImageTag"

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    throw "docker nicht gefunden. Docker Desktop starten und PATH pruefen."
}

# Optional: Buildx-Builder (Fehler ignorieren, z. B. wenn Builder schon existiert)
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
docker buildx create --use 2>$null | Out-Null
$ErrorActionPreference = $prevEap

Write-Host "`n=== docker buildx build ===" -ForegroundColor Cyan
docker buildx build --platform $Platform -f slideshow_hub/Dockerfile -t $ImageTag --load .
if ($LASTEXITCODE -ne 0) { throw "docker build fehlgeschlagen" }

Write-Host "`n=== Image-Architektur ===" -ForegroundColor Cyan
docker image inspect $ImageTag --format "{{.Os}}/{{.Architecture}}"

if (-not $NoSave) {
    Write-Host "`n=== docker save ===" -ForegroundColor Cyan
    docker save $ImageTag -o $TarPath
    if ($LASTEXITCODE -ne 0) { throw "docker save fehlgeschlagen" }
    $len = (Get-Item $TarPath).Length
    Write-Host "Geschrieben: $TarPath ($([math]::Round($len/1MB, 2)) MB)" -ForegroundColor Green

    if ($ScpTarget) {
        Write-Host "`n=== scp ===" -ForegroundColor Cyan
        $scp = Get-Command scp -ErrorAction SilentlyContinue
        if (-not $scp) { throw "scp nicht gefunden (OpenSSH-Client installieren)" }
        scp $TarPath "${ScpTarget}"
        if ($LASTEXITCODE -ne 0) { throw "scp fehlgeschlagen" }
        Write-Host "Kopiert nach: $ScpTarget" -ForegroundColor Green
    }
}

if (-not $NoPrintNasCommands) {
    Write-Host @"

=== Naechste Schritte auf der NAS (SSH) ===
  sudo docker stop slideshow-remote-hub
  sudo docker rm slideshow-remote-hub
  sudo docker rmi $ImageTag
  sudo docker load -i /volume1/data/docker-images/slideshow-hub.tar
  sudo docker run -d --name slideshow-remote-hub --restart unless-stopped -p 8090:8090 \
    -e 'SLIDESHUB_GALLERY_PATH_MAP={"http://192.168.0.100:8080":"/volume1/web"}' \
    $ImageTag

(Pfad zu .tar und JSON-Mapping an die NAS anpassen. Volume: Galerieordner auf dem Host mounten, falls Hub und nginx getrennt sind.)

"@ -ForegroundColor Yellow
}
