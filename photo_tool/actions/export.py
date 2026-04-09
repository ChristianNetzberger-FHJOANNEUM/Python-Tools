"""
Web gallery export functionality
Export filtered photo selections as standalone HTML galleries
"""

import json
import shutil
from pathlib import Path
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime, timezone

from PIL import Image

from ..util.logging import get_logger
from ..projects.rating_layers import RATING_LAYER_PROJECT
from ..projects.project_sidecar import ProjectSidecarManager
from .metadata import get_metadata, get_metadata_file
from .export_profiles import get_profile, optimize_image, generate_optimized_thumbnail, list_profiles

logger = get_logger("export")

# Bundled QR library (davidshimjs/qrcodejs, MIT) — same-origin load works on TVs that block CDN scripts.
_SPLASH_QR_VENDOR = Path(__file__).resolve().parent.parent / "web_vendor" / "qrcode.min.js"


def _ensure_splash_qr_vendor(gallery_dir: Path) -> None:
    """Copy local QR script next to index.html so Smart-TVs need no internet/CDN."""
    if not _SPLASH_QR_VENDOR.is_file():
        logger.warning(
            "Splash QR script missing (%s). Run repo setup or add web_vendor/qrcode.min.js — QR falls back to CDN.",
            _SPLASH_QR_VENDOR,
        )
        return
    dest_dir = gallery_dir / "vendor"
    dest_dir.mkdir(exist_ok=True)
    shutil.copy2(_SPLASH_QR_VENDOR, dest_dir / "qrcode.min.js")


def _audio_mime_type(relative_path: str) -> str:
    """Best MIME type for <source type> from export-relative audio path."""
    name = relative_path.lower().split("?", 1)[0]
    if name.endswith(".mp3"):
        return "audio/mpeg"
    if name.endswith((".m4a", ".aac")):
        return "audio/mp4"
    if name.endswith(".mp4"):
        return "audio/mp4"
    if name.endswith(".ogg"):
        return "audio/ogg"
    if name.endswith(".flac"):
        return "audio/flac"
    if name.endswith(".wav"):
        return "audio/wav"
    return "audio/mpeg"


# Slideshow: only load nearby slides as <img src> (saves TV/browser RAM). All predefined Smart-TV export profiles.
_SMART_TV_PROFILES_8K = frozenset({"smart_tv_8k"})
_SMART_TV_PROFILES_4K_FHD = frozenset({"smart_tv", "smart_tv_fullhd"})


def _slideshow_memory_window_for_profile(profile_key: str) -> int:
    """Neighbour radius for slide image src (0 = load all slides at once, web-style only).

    - smart_tv_8k: ±1 (3 images max; schärfstes Limit wegen Pixeldecode).
    - smart_tv (4K), smart_tv_fullhd: ±2 (5 images max).
    - Alle anderen Profile: 0 (bisheriges Verhalten, z. B. Web mit vielen parallelen Loads).
    """
    if profile_key in _SMART_TV_PROFILES_8K:
        return 1
    if profile_key in _SMART_TV_PROFILES_4K_FHD:
        return 2
    return 0


def _slide_manifest_entry(
    index: int,
    photo_entry: Dict[str, Any],
    photo_path: Path,
) -> Dict[str, Any]:
    """One row for gallery/slides.json — links export JPEG to original + sidecar paths."""
    sidecar = get_metadata_file(photo_path)
    return {
        "index": index,
        "export_image": photo_entry["src"],
        "thumbnail": photo_entry["thumbnail"],
        "source_path": str(photo_path.resolve()),
        "source_name": photo_path.name,
        "metadata_sidecar": str(sidecar.resolve()),
        "rating": photo_entry.get("rating", 0),
        "color": photo_entry.get("color"),
        "keywords": list(photo_entry.get("keywords") or []),
        "couch_rating": photo_entry.get("couch_rating"),
        "couch_color": photo_entry.get("couch_color"),
    }


_EXPORT_JPEG_SUFFIXES = frozenset({".jpg", ".jpeg"})


def _images_dir_has_export_jpegs(images_dir: Path) -> bool:
    """True if folder exists and has at least one .jpg/.jpeg (any case)."""
    if not images_dir.is_dir():
        return False
    for p in images_dir.iterdir():
        if p.is_file() and p.suffix.lower() in _EXPORT_JPEG_SUFFIXES:
            return True
    return False


def _sorted_export_jpegs(images_dir: Path) -> List[Path]:
    """Sorted JPEG paths in export images folder (case-insensitive extension)."""
    if not images_dir.is_dir():
        return []
    jpgs = [
        p for p in images_dir.iterdir()
        if p.is_file() and p.suffix.lower() in _EXPORT_JPEG_SUFFIXES
    ]
    return sorted(jpgs, key=lambda x: x.name.lower())


_MEDIA_PRUNE_SUFFIXES = frozenset({".jpg", ".jpeg", ".webp", ".png"})


def _empty_slideshow_media_dirs(images_dir: Path, thumbs_dir: Path) -> None:
    """Remove JPEG/WebP from images + thumbnails before a full re-export (avoids stale 0000..1622 when new set is smaller)."""
    for d in (images_dir, thumbs_dir):
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if p.is_file() and p.suffix.lower() in _MEDIA_PRUNE_SUFFIXES:
                try:
                    p.unlink()
                except OSError as exc:
                    logger.warning("Could not remove %s: %s", p, exc)


def _prune_unreferenced_gallery_media(gallery_dir: Path, photo_data: List[Dict[str, Any]]) -> None:
    """Drop files under images/ and thumbnails/ not referenced by the current photo_data (quick-update shrink or partial sync)."""
    if not photo_data:
        return
    allowed: set = set()
    for row in photo_data:
        for key in ("src", "src_webp", "thumbnail", "thumbnail_webp"):
            v = row.get(key)
            if isinstance(v, str) and "/" in v:
                allowed.add(Path(v).name.lower())
    for sub in ("images", "thumbnails"):
        d = gallery_dir / sub
        if not d.is_dir():
            continue
        for p in d.iterdir():
            if not p.is_file() or p.suffix.lower() not in _MEDIA_PRUNE_SUFFIXES:
                continue
            if p.name.lower() in allowed:
                continue
            try:
                p.unlink()
                logger.info("Pruned unreferenced gallery file %s/%s", sub, p.name)
            except OSError as exc:
                logger.warning("Could not prune %s: %s", p, exc)


def _merge_couch_from_existing_slides_json(
    gallery_dir: Path,
    slides_manifest: List[Dict[str, Any]],
    photo_data: List[Dict[str, Any]],
) -> None:
    """Preserve couch_* from previous slides.json when re-exporting (same source_path)."""
    manifest_path = gallery_dir / "slides.json"
    if not manifest_path.exists() or not slides_manifest:
        return
    try:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        old_slides = old.get("slides") or []
        by_src = {s.get("source_path"): s for s in old_slides if s.get("source_path")}
        for s in slides_manifest:
            o = by_src.get(s.get("source_path"))
            if not o:
                continue
            if "couch_rating" in o:
                s["couch_rating"] = o.get("couch_rating")
            if "couch_color" in o:
                s["couch_color"] = o.get("couch_color")
        for i, s in enumerate(slides_manifest):
            if i < len(photo_data):
                photo_data[i]["couch_rating"] = s.get("couch_rating")
                photo_data[i]["couch_color"] = s.get("couch_color")
    except Exception as e:
        logger.warning("Could not merge couch fields from existing slides.json: %s", e)


def _apply_project_to_couch_seed(
    project_dir: Path,
    mode: Literal["fill_empty", "replace_all"],
    photo_data: List[Dict[str, Any]],
    slides_manifest: List[Dict[str, Any]],
) -> None:
    """
    After _merge_couch_from_existing_slides_json: copy project-layer rating/color into
    couch_rating / couch_color per Spezifikation_Export_Projekt_nach_Couch_slides.md.
    """
    if mode not in ("fill_empty", "replace_all"):
        return
    if not project_dir.is_dir():
        logger.warning("project_to_couch: project_dir missing %s", project_dir)
        return
    psm = ProjectSidecarManager(project_dir)
    n = min(len(photo_data), len(slides_manifest))
    for i in range(n):
        s = slides_manifest[i]
        raw_path = s.get("source_path")
        if not raw_path:
            continue
        try:
            photo_path = Path(raw_path)
        except Exception:
            continue
        try:
            gm = get_metadata(photo_path)
            merged = psm.merge_metadata(gm, photo_path, active_rating_layer=RATING_LAYER_PROJECT)
        except Exception as e:
            logger.warning("project_to_couch: merge failed for %s: %s", photo_path.name, e)
            continue
        try:
            r = merged.get("rating")
            rating_v = int(r) if r is not None else 0
        except (TypeError, ValueError):
            rating_v = 0
        rating_v = max(0, min(5, rating_v))
        col = merged.get("color")
        color_v = col if col not in (None, "") else None

        if mode == "replace_all":
            photo_data[i]["couch_rating"] = rating_v
            photo_data[i]["couch_color"] = color_v
            s["couch_rating"] = rating_v
            s["couch_color"] = color_v
        else:
            if photo_data[i].get("couch_rating") is None:
                photo_data[i]["couch_rating"] = rating_v
                s["couch_rating"] = rating_v
            cc = photo_data[i].get("couch_color")
            if cc is None or cc == "":
                photo_data[i]["couch_color"] = color_v
                s["couch_color"] = color_v


# Progress tracking for export
_export_progress = {
    'status': 'idle',  # idle, running, complete, error
    'current': 0,
    'total': 0,
    'step': '',
    'message': ''
}


def export_gallery(
    photo_paths: List[Path],
    output_dir: Path,
    title: str = "Photo Gallery",
    template: str = "photoswipe",
    profile: str = "web",
    include_metadata: bool = True,
    generate_webp: bool = False,
    quick_update: bool = False,  # NEW: Skip image processing, only regenerate HTML
    music_files: Optional[List[str]] = None,
    music_autoplay: bool = False,  # NEW: Auto-start music on load
    music_ducking_volume: int = 30,  # NEW: Music volume during pause (0-100%)
    slideshow_enabled: bool = False,
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False,
    splash_title: Optional[str] = None,      # 🎬 Custom splash screen title
    splash_subtitle: Optional[str] = None,   # 🎬 Custom splash screen subtitle
    remote_hub_ws_base: Optional[str] = None,  # e.g. ws://nas:8090/ws — LAN remote control hub
    remote_session_id: str = "default",
    gallery_public_http_base: Optional[str] = None,  # http(s) URL of gallery folder if TV opens file:///… (Hub/slides.json)
    apply_edits: bool = True,  # NEW: Apply non-destructive edits during export
    project_dir: Optional[Path] = None,
    project_to_couch_mode: str = "off",
    # Legacy parameters (deprecated, use profile instead)
    max_image_size: Optional[int] = None,
    thumbnail_size: Optional[int] = None
) -> Path:
    """
    Export photos as standalone web gallery with optimization profiles
    
    Args:
        photo_paths: List of photo paths to include
        output_dir: Web root for this export (index.html, slides.json, images/, …)
        title: Gallery title
        template: Template name (photoswipe, simple, slideshow)
        profile: Export profile (smart_tv, web, web_optimized, archive)
        include_metadata: Include ratings, colors, keywords
        generate_webp: Generate WebP versions in addition to JPEG
        music_files: Optional list of music file paths for slideshow
        music_autoplay: Auto-start music on page load (default: False)
        slideshow_enabled: Enable slideshow mode
        slideshow_duration: Duration per photo in seconds (2-15)
        smart_tv_mode: Enable large buttons for Smart TV
        max_image_size: (Deprecated) Use profile instead
        thumbnail_size: (Deprecated) Use profile instead
        
    Returns:
        Path to generated gallery web root (same as output_dir when using flat layout)
        
    Profiles:
        - smart_tv: 4K quality for Samsung/LG TVs (3840×2160, Q92)
        - smart_tv_fullhd: Full HD for TVs (1920×1080, Q90)
        - web: Standard web gallery (1920×1280, Q85, ~650 KB/photo)
        - web_medium: Medium web gallery (1600×1067, Q83, ~400 KB/photo)
        - web_compact: Compact web gallery (1280×853, Q80, ~250 KB/photo)
        - web_mobile: Mobile-friendly gallery (1024×683, Q78, ~150 KB/photo)
        - web_optimized: Highly optimized (1600×1200, Q80, WebP)
        - archive: High quality archive (4000×4000, Q95)
    """
    
    global _export_progress
    
    # Get export profile
    try:
        export_profile = get_profile(profile)
        logger.info(f"Using export profile: {export_profile.name}")
        logger.info(f"Profile: {export_profile.description}")
    except ValueError as e:
        logger.error(f"Invalid profile: {e}")
        # Fallback to web profile
        export_profile = get_profile("web")
        logger.warning(f"Falling back to 'web' profile")
    
    logger.info(f"Exporting gallery with {len(photo_paths)} photos to {output_dir}")
    logger.info(f"Max resolution: {export_profile.max_width}×{export_profile.max_height}")
    logger.info(f"JPEG quality: {export_profile.jpeg_quality}")
    if generate_webp and export_profile.webp_quality:
        logger.info(f"WebP quality: {export_profile.webp_quality}")
    
    # Initialize progress
    _export_progress['status'] = 'running'
    _export_progress['current'] = 0
    _export_progress['total'] = len(photo_paths)
    _export_progress['step'] = 'setup'
    _export_progress['message'] = 'Creating directory structure...'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    # Scratch dir for edit pipeline (removed after export); never mixed with web assets
    temp_dir = output_dir / "_export_tmp"
    legacy_gallery_root = output_dir / "gallery"
    
    # Web root: flat under output_dir. Quick-update still accepts pre-change exports in output_dir/gallery/
    if quick_update:
        flat_images = output_dir / "images"
        legacy_images = legacy_gallery_root / "images"
        has_flat = _images_dir_has_export_jpegs(flat_images)
        has_legacy = _images_dir_has_export_jpegs(legacy_images)
        if has_flat:
            gallery_dir = output_dir
        elif has_legacy:
            gallery_dir = legacy_gallery_root
            logger.info("⚡ Quick update: using legacy layout %s", gallery_dir)
        else:
            logger.error(
                "Quick update: no JPEGs in %s or %s (output_dir=%s)",
                flat_images,
                legacy_images,
                output_dir.resolve(),
            )
            logger.error("Run a full export first, or disable Quick update, or fix export target path.")
            raise ValueError("Quick update requires existing images. Run full export first.")
    else:
        gallery_dir = output_dir
    
    gallery_dir.mkdir(parents=True, exist_ok=True)
    images_dir = gallery_dir / "images"
    thumbs_dir = gallery_dir / "thumbnails"
    music_dir = gallery_dir / "music"
    images_dir.mkdir(exist_ok=True)
    thumbs_dir.mkdir(exist_ok=True)
    
    # Copy music files to gallery directory
    music_file_list = []
    if music_files:
        music_dir.mkdir(exist_ok=True)
        logger.info(f"Copying {len(music_files)} music files...")
        for i, music_path in enumerate(music_files):
            if music_path.exists():
                # Copy with numbered filename to avoid conflicts
                ext = music_path.suffix
                music_filename = f"track{i+1:02d}{ext}"
                dest_path = music_dir / music_filename
                shutil.copy2(music_path, dest_path)
                # Store relative path for HTML
                music_file_list.append(f"music/{music_filename}")
                logger.info(f"  ✓ Copied {music_path.name} → {music_filename}")
            else:
                logger.warning(f"  ⚠️ Music file not found: {music_path}")
    
    # Initialize variables (used in both quick and normal mode)
    photo_data = []
    slides_manifest: List[Dict[str, Any]] = []
    total_original_size = 0
    total_jpeg_size = 0
    total_webp_size = 0
    
    index_path = gallery_dir / "index.html"
    
    try:
        if quick_update:
            logger.info("⚡ QUICK UPDATE MODE: Reusing existing images, regenerating HTML only")
            _export_progress['step'] = 'processing'
            existing_images = _sorted_export_jpegs(images_dir)
            logger.info(f"Found {len(existing_images)} existing images")
            for i, img_path in enumerate(existing_images):
                if i >= len(photo_paths):
                    break
                
                photo_path = photo_paths[i]
                _export_progress['current'] = i + 1
                _export_progress['message'] = f'Quick update: {photo_path.name}…'
                img_filename = img_path.name
                thumb_filename = img_filename
                
                try:
                    with Image.open(img_path) as img:
                        width, height = img.size
                except Exception:
                    width, height = 1920, 1280
                
                metadata = {}
                if include_metadata:
                    metadata = get_metadata(photo_path)
                
                photo_entry = {
                    'src': f"images/{img_filename}",
                    'thumbnail': f"thumbnails/{thumb_filename}",
                    'width': width,
                    'height': height,
                    'title': photo_path.name,
                    'rating': metadata.get('rating', 0),
                    'color': metadata.get('color'),
                    'keywords': metadata.get('keywords', []),
                    'couch_rating': None,
                    'couch_color': None,
                }
                
                webp_img = images_dir / img_path.stem
                webp_img = webp_img.with_suffix('.webp')
                if webp_img.exists():
                    photo_entry['src_webp'] = f"images/{webp_img.name}"
                
                webp_thumb = thumbs_dir / img_path.stem
                webp_thumb = webp_thumb.with_suffix('.webp')
                if webp_thumb.exists():
                    photo_entry['thumbnail_webp'] = f"thumbnails/{webp_thumb.name}"
                
                photo_data.append(photo_entry)
                slides_manifest.append(
                    _slide_manifest_entry(len(photo_data) - 1, photo_entry, photo_path)
                )
            
            logger.info(f"⚡ Quick update: Reusing {len(photo_data)} existing images")
        
        else:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)
            _empty_slideshow_media_dirs(images_dir, thumbs_dir)
            
            _export_progress['step'] = 'processing'
            for i, photo_path in enumerate(photo_paths):
                _export_progress['current'] = i + 1
                _export_progress['message'] = f'Processing {photo_path.name}...'
                try:
                    img_filename = f"{i:04d}.jpg"
                    thumb_filename = f"{i:04d}.jpg"
                    
                    img_path = images_dir / img_filename
                    thumb_path = thumbs_dir / thumb_filename
                    
                    source_for_export = photo_path
                    temp_edited_path = None
                    
                    if apply_edits:
                        try:
                            from .edits import get_edits, has_edits
                            from ..image_processing import apply_all_edits as apply_image_edits
                            
                            if has_edits(photo_path):
                                edits = get_edits(photo_path)
                                temp_edited_path = temp_dir / f"temp_edited_{i:04d}.jpg"
                                edited_img = apply_image_edits(photo_path, edits, output_format='pil')
                                edited_img.save(temp_edited_path, quality=95)
                                source_for_export = temp_edited_path
                                logger.info(f"  ✨ Applied edits to {photo_path.name}")
                        except ImportError:
                            logger.warning("Image editing module not available, exporting originals")
                        except Exception as e:
                            logger.warning(f"Error applying edits to {photo_path.name}: {e}")
                    
                    img_result = optimize_image(
                        source_path=source_for_export,
                        output_path=img_path,
                        profile=export_profile,
                        generate_webp=generate_webp
                    )
                    
                    thumb_result = generate_optimized_thumbnail(
                        source_path=source_for_export,
                        output_path=thumb_path,
                        profile=export_profile,
                        generate_webp=generate_webp
                    )
                    
                    if temp_edited_path and temp_edited_path.exists():
                        temp_edited_path.unlink()
                    
                    total_original_size += img_result['original_size']
                    total_jpeg_size += img_result['jpeg_size']
                    if img_result['webp_size']:
                        total_webp_size += img_result['webp_size']
                    
                    metadata = {}
                    if include_metadata:
                        metadata = get_metadata(photo_path)
                    
                    photo_entry = {
                        'src': f"images/{img_filename}",
                        'thumbnail': f"thumbnails/{thumb_filename}",
                        'width': img_result['width'],
                        'height': img_result['height'],
                        'title': photo_path.name,
                        'rating': metadata.get('rating', 0),
                        'color': metadata.get('color'),
                        'keywords': metadata.get('keywords', []),
                        'couch_rating': None,
                        'couch_color': None,
                    }
                    
                    if img_result['webp_path']:
                        photo_entry['src_webp'] = f"images/{i:04d}.webp"
                    if thumb_result['webp_path']:
                        photo_entry['thumbnail_webp'] = f"thumbnails/{i:04d}.webp"
                    
                    photo_data.append(photo_entry)
                    slides_manifest.append(
                        _slide_manifest_entry(len(photo_data) - 1, photo_entry, photo_path)
                    )
                    
                    logger.debug(
                        f"Processed {photo_path.name} - "
                        f"JPEG: {img_result['jpeg_size']//1024}KB"
                        + (f", WebP: {img_result['webp_size']//1024}KB" if img_result['webp_size'] else "")
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to process {photo_path}: {e}")
                    continue
        
        if photo_data:
            _prune_unreferenced_gallery_media(gallery_dir, photo_data)
        
        if slides_manifest:
            _merge_couch_from_existing_slides_json(gallery_dir, slides_manifest, photo_data)

        _ptc = (project_to_couch_mode or "off").strip().lower()
        if (
            slides_manifest
            and _ptc in ("fill_empty", "replace_all")
            and project_dir is not None
        ):
            pd = Path(project_dir)
            _apply_project_to_couch_seed(pd, _ptc, photo_data, slides_manifest)
        
        if template == "slideshow":
            _ensure_splash_qr_vendor(gallery_dir)
            mem_win = _slideshow_memory_window_for_profile(profile)
            html = _generate_slideshow_html(
                title=title,
                photo_data=photo_data,
                music_files=music_file_list,
                music_autoplay=music_autoplay,
                music_ducking_volume=music_ducking_volume,
                slideshow_duration=slideshow_duration,
                smart_tv_mode=smart_tv_mode,
                splash_title=splash_title,
                splash_subtitle=splash_subtitle,
                memory_window_radius=mem_win,
                remote_hub_ws_base=remote_hub_ws_base,
                remote_session_id=remote_session_id,
                gallery_public_http_base=gallery_public_http_base,
            )
        elif template == "photoswipe":
            html = _generate_photoswipe_html(title, photo_data)
        else:
            html = _generate_simple_html(title, photo_data)
        
        _export_progress['step'] = 'finalizing'
        _export_progress['message'] = 'Generating HTML...'
        
        index_path.write_text(html, encoding='utf-8')
        
        if slides_manifest:
            manifest_path = gallery_dir / "slides.json"
            manifest_body = {
                "manifest_version": 1,
                "title": title,
                "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "export_profile": profile,
                "template": template,
                "slide_count": len(slides_manifest),
                "slides": slides_manifest,
            }
            manifest_path.write_text(
                json.dumps(manifest_body, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            logger.info(f"Wrote manifest {manifest_path} ({len(slides_manifest)} slides)")
        
        _export_progress['status'] = 'complete'
        _export_progress['message'] = 'Export complete!'
        
        if total_original_size > 0:
            jpeg_ratio = (1 - total_jpeg_size / total_original_size) * 100
            logger.info(f"Compression stats:")
            logger.info(f"  Original: {total_original_size / 1024 / 1024:.1f} MB")
            logger.info(f"  JPEG: {total_jpeg_size / 1024 / 1024:.1f} MB ({jpeg_ratio:.1f}% reduction)")
            if total_webp_size > 0:
                webp_ratio = (1 - total_webp_size / total_original_size) * 100
                logger.info(f"  WebP: {total_webp_size / 1024 / 1024:.1f} MB ({webp_ratio:.1f}% reduction)")
        
        logger.info(f"Gallery exported successfully to {gallery_dir}")
        logger.info(f"Profile: {export_profile.name}")
        if music_file_list:
            logger.info(f"Music tracks: {len(music_file_list)}")
        logger.info(f"Open {index_path} in browser to view")
        
        return gallery_dir
    
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)


def _generate_photoswipe_html(title: str, photos: List[Dict[str, Any]]) -> str:
    """Generate PhotoSwipe template HTML"""
    
    photos_json = json.dumps(photos, indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- PhotoSwipe CSS -->
    <link rel="stylesheet" href="https://unpkg.com/photoswipe/dist/photoswipe.css">
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
        }}
        
        .header {{
            padding: 40px 30px;
            text-align: center;
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #4ade80, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1.1rem;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            padding: 40px 30px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        
        .gallery-item {{
            position: relative;
            cursor: pointer;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s ease;
            background: rgba(255,255,255,0.05);
        }}
        
        .gallery-item:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(74, 222, 128, 0.3);
        }}
        
        .gallery-item img {{
            width: 100%;
            height: 280px;
            object-fit: cover;
            display: block;
        }}
        
        .photo-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.9));
            padding: 20px 15px 15px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .gallery-item:hover .photo-overlay {{
            opacity: 1;
        }}
        
        .photo-title {{
            font-size: 0.9rem;
            color: #fff;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .stars {{
            color: #fbbf24;
            font-size: 0.9rem;
        }}
        
        .keywords {{
            margin-top: 8px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }}
        
        .keyword {{
            background: rgba(59, 130, 246, 0.3);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.75rem;
            color: #93c5fd;
        }}
        
        .color-badge {{
            position: absolute;
            top: 15px;
            left: 15px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 3px solid #fff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }}
        
        .footer {{
            text-align: center;
            padding: 40px 30px;
            color: #666;
            font-size: 0.9rem;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        .footer a {{
            color: #4ade80;
            text-decoration: none;
        }}
        
        @media (max-width: 768px) {{
            .gallery {{
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                padding: 20px 15px;
            }}
            
            h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="subtitle">{len(photos)} photos</div>
    </div>

    <div class="gallery" id="gallery">
        <!-- Generated by JavaScript -->
    </div>

    <div class="footer">
        Generated with <a href="https://github.com" target="_blank">Photo Tool</a> | {now}
    </div>

    <!-- PhotoSwipe JS -->
    <script type="module">
        import PhotoSwipeLightbox from 'https://unpkg.com/photoswipe/dist/photoswipe-lightbox.esm.js';
        import PhotoSwipe from 'https://unpkg.com/photoswipe/dist/photoswipe.esm.js';

        const photos = {photos_json};

        const colorHex = {{
            red: '#ef4444',
            yellow: '#fbbf24',
            green: '#4ade80',
            blue: '#3b82f6',
            purple: '#a855f7'
        }};

        // Generate gallery HTML
        const gallery = document.getElementById('gallery');
        
        photos.forEach((photo, index) => {{
            const item = document.createElement('a');
            item.href = photo.src;
            item.className = 'gallery-item';
            item.setAttribute('data-pswp-width', photo.width);
            item.setAttribute('data-pswp-height', photo.height);

            // Use <picture> for WebP support with JPEG fallback
            let imgHtml;
            if (photo.thumbnail_webp) {{
                imgHtml = `
                    <picture>
                        <source srcset="${{photo.thumbnail_webp}}" type="image/webp">
                        <img src="${{photo.thumbnail}}" alt="${{photo.title}}" loading="lazy">
                    </picture>
                `;
            }} else {{
                imgHtml = `<img src="${{photo.thumbnail}}" alt="${{photo.title}}" loading="lazy">`;
            }}
            
            let html = imgHtml;
            
            // Color badge
            if (photo.color) {{
                html += `<div class="color-badge" style="background: ${{colorHex[photo.color]}}"></div>`;
            }}

            // Overlay with metadata
            let overlayContent = `<div class="photo-title">${{photo.title}}</div>`;
            
            if (photo.rating > 0) {{
                const stars = '★'.repeat(photo.rating) + '☆'.repeat(5 - photo.rating);
                overlayContent += `<div class="stars">${{stars}}</div>`;
            }}
            
            if (photo.keywords && photo.keywords.length > 0) {{
                overlayContent += '<div class="keywords">';
                photo.keywords.forEach(kw => {{
                    overlayContent += `<span class="keyword">${{kw}}</span>`;
                }});
                overlayContent += '</div>';
            }}
            
            html += `<div class="photo-overlay">${{overlayContent}}</div>`;

            item.innerHTML = html;
            gallery.appendChild(item);
        }});

        // Initialize PhotoSwipe
        const lightbox = new PhotoSwipeLightbox({{
            gallery: '#gallery',
            children: 'a',
            pswpModule: PhotoSwipe,
            preload: [1, 2]
        }});
        
        lightbox.init();
    </script>
</body>
</html>'''


def _generate_simple_html(title: str, photos: List[Dict[str, Any]]) -> str:
    """Generate simple grid template HTML (no dependencies)"""
    
    photos_html = ""
    for photo in photos:
        stars = "★" * photo.get('rating', 0) + "☆" * (5 - photo.get('rating', 0))
        keywords_html = " ".join([f'<span class="keyword">{k}</span>' for k in photo.get('keywords', [])])
        
        photos_html += f'''
        <div class="gallery-item">
            <a href="{photo['src']}" target="_blank">
                <img src="{photo['thumbnail']}" alt="{photo['title']}">
            </a>
            <div class="photo-info">
                <div class="photo-title">{photo['title']}</div>
                {f'<div class="stars">{stars}</div>' if photo.get('rating', 0) > 0 else ''}
                {f'<div class="keywords">{keywords_html}</div>' if keywords_html else ''}
            </div>
        </div>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: system-ui, sans-serif;
            background: #0a0a0a;
            color: #fff;
            padding: 30px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
        }}
        .gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        .gallery-item {{
            background: #1a1a1a;
            border-radius: 8px;
            overflow: hidden;
        }}
        .gallery-item img {{
            width: 100%;
            height: 250px;
            object-fit: cover;
        }}
        .photo-info {{
            padding: 12px;
        }}
        .photo-title {{
            font-size: 0.9rem;
            margin-bottom: 5px;
        }}
        .stars {{
            color: gold;
            font-size: 0.9rem;
        }}
        .keywords {{
            margin-top: 8px;
        }}
        .keyword {{
            background: rgba(59, 130, 246, 0.3);
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 0.75rem;
            margin-right: 4px;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="gallery">
        {photos_html}
    </div>
</body>
</html>'''


def _generate_slideshow_html(
    title: str,
    photo_data: List[Dict[str, Any]],
    music_files: Optional[List[str]] = None,
    music_autoplay: bool = False,
    music_ducking_volume: int = 30,  # 🎚️ Music volume during pause (0-100%)
    slideshow_duration: int = 5,
    smart_tv_mode: bool = False,
    splash_title: str = None,  # 🆕 Custom splash title
    splash_subtitle: str = None,  # 🆕 Custom splash subtitle (date)
    memory_window_radius: int = 0,  # TV: only load nearby slides; 0 = legacy (all imgs)
    remote_hub_ws_base: Optional[str] = None,
    remote_session_id: str = "default",
    gallery_public_http_base: Optional[str] = None,
) -> str:
    """Generate fullscreen slideshow template with music support (based on working GUI slideshow)"""
    
    photos_json = json.dumps(photo_data, indent=2)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Convert music file paths to HTML-friendly format
    music_html = ""
    music_controls_html = ""
    if music_files:
        music_sources = '\n'.join(
            f'            <source src="{music}" type="{_audio_mime_type(music)}">'
            for music in music_files
        )
        music_html = f'''
        <audio id="bgMusic" loop preload="auto">
{music_sources}
        </audio>'''
        music_controls_html = '''
                    <button class="slideshow-btn" onclick="event.stopPropagation(); toggleMusic();" title="Music (M)">
                        <span id="musicIcon">🎵</span> Music
                    </button>'''
    
    button_padding = "16px 32px" if smart_tv_mode else "12px 24px"
    button_font = "1.2rem" if smart_tv_mode else "1rem"
    
    # Splash screen configuration
    splash_bg = "splash.jpg"  # Try custom splash first
    splash_fallback = photo_data[0]['src'] if photo_data else ''
    
    # Use custom titles if provided, otherwise use defaults
    if not splash_title:
        splash_title = title
    if not splash_subtitle:
        splash_subtitle = f"{len(photo_data)} photos{' • Background music' if music_files else ''}"

    hub_ws = (remote_hub_ws_base or "").strip()
    remote_hub_literal = json.dumps(hub_ws) if hub_ws else "null"
    remote_session_literal = json.dumps((remote_session_id or "default").strip() or "default")
    pub_http = (gallery_public_http_base or "").strip()
    gallery_public_literal = json.dumps(pub_http) if pub_http else "null"
    hub_disabled_banner = ""
    if not hub_ws:
        hub_disabled_banner = """
    <div class=\"hub-disabled-banner\" role=\"status\">
        <strong>LAN-Remote aus:</strong> Slideshow im Photo Tool erneut exportieren und dabei die
        <strong>WebSocket-Adresse des Hubs</strong> eintragen (z.&nbsp;B. <code style=\"color:#fda\">ws://NAS-IP:8090/ws</code>),
        dieselbe <strong>Sitzung</strong> wie auf dem Handy. Ohne diese URL: kein Handy-Steuerung, keine Galerie-URL, keine Bewertung-Sync.
    </div>"""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, must-revalidate, max-age=0" />
    <meta http-equiv="Pragma" content="no-cache" />
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            color: #fff;
            overflow: hidden;
        }}
        
        .slideshow {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #000;
            display: flex;
            flex-direction: column;
            z-index: 3000;
        }}
        
        .slideshow.hide-controls {{
            cursor: none;
        }}
        
        .slideshow-header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: linear-gradient(to bottom, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 70%, transparent 100%);
            backdrop-filter: blur(10px);
            z-index: 100;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }}
        
        .slideshow.hide-controls .slideshow-header {{
            opacity: 0;
            transform: translateY(-100%);
            /* pointer-events: none; -- REMOVED: Allow clicks to show controls */
        }}
        
        .slideshow-title {{
            font-size: 1.2rem;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .slideshow-main {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }}
        
        .slideshow-image-container {{
            position: absolute;
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 1s ease-in-out;
        }}
        
        .slideshow-image-container.active {{
            opacity: 1;
        }}
        
        .slideshow-image {{
            max-width: 100%;
            max-height: 100%;
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        
        .slideshow-footer {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 20px 30px;
            background: linear-gradient(to top, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 70%, transparent 100%);
            backdrop-filter: blur(10px);
            z-index: 100;
            transition: opacity 0.3s ease, transform 0.3s ease;
        }}
        
        .slideshow.hide-controls .slideshow-footer {{
            opacity: 0;
            transform: translateY(100%);
            /* pointer-events: none; -- REMOVED: Allow clicks to show controls */
        }}
        
        .slideshow-progress {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }}

        /* Große vertikale Klick-/Touch-Fläche — der sichtbare Balken bleibt schlank */
        .slideshow-progress-bar-hit {{
            flex: 1;
            min-height: 40px;
            padding: 14px 0;
            display: flex;
            align-items: center;
            cursor: pointer;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}
        
        .slideshow-progress-bar {{
            flex: 1;
            height: 10px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 5px;
            overflow: hidden;
            position: relative;
        }}

        .slideshow-progress-bar-hit:hover .slideshow-progress-bar {{
            background: rgba(255, 255, 255, 0.3);
        }}
        
        .footer-qr-wrap {{
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            gap: 2px;
            margin-left: 4px;
            max-width: 96px;
        }}
        .footer-qr-wrap .footer-qr-mount img,
        .footer-qr-wrap .footer-qr-mount canvas {{
            display: block;
            border-radius: 6px;
            background: #fff;
            padding: 2px;
            max-width: 88px;
            max-height: 88px;
        }}
        .footer-qr-link {{
            font-size: 0.58rem;
            color: #c4b5fd;
            max-width: 96px;
            line-height: 1.15;
            text-align: center;
            word-break: break-all;
        }}
        
        .slideshow-progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #8b5cf6, #ec4899);
            border-radius: 3px;
            transition: width 0.3s ease;
        }}
        
        .slideshow-progress-text {{
            color: #888;
            font-size: 0.9rem;
            min-width: 80px;
            text-align: right;
        }}
        
        .slideshow-controls {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
        }}
        
        .slideshow-btn {{
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #fff;
            padding: {button_padding};
            border-radius: 8px;
            font-size: {button_font};
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .slideshow-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }}
        
        .slideshow-btn:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}
        
        .slideshow-btn.primary {{
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
        }}
        
        .slideshow-btn.primary:hover {{
            background: linear-gradient(135deg, #7c3aed, #db2777);
        }}
        
        /* Couch / Tool rating readout (independent of .hide-controls) */
        .slideshow-rating-hud {{
            position: absolute;
            bottom: 110px;
            right: 24px;
            z-index: 200;
            min-width: 132px;
            max-width: min(90vw, 300px);
            background: rgba(0, 0, 0, 0.74);
            backdrop-filter: blur(10px);
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 1rem;
            line-height: 1.35;
            color: #fff;
            pointer-events: none;
            box-shadow: 0 4px 28px rgba(0, 0, 0, 0.5);
            transition: opacity 0.22s ease, transform 0.22s ease;
        }}
        .slideshow-rating-hud.slideshow-rating-hud--off {{
            opacity: 0;
            transform: translateY(10px);
            visibility: hidden;
        }}
        .slideshow-rating-hud .rh-stars {{
            color: #fbbf24;
            letter-spacing: 1px;
        }}
        .slideshow-rating-hud .rh-color {{
            display: inline-block;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            margin-left: 12px;
            vertical-align: middle;
            border: 2px solid rgba(255, 255, 255, 0.45);
        }}
        
        .slideshow-settings {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .slideshow-setting {{
            display: flex;
            align-items: center;
            gap: 10px;
            color: #ccc;
            font-size: 0.9rem;
        }}
        
        .slideshow-setting select {{
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
        }}
        
        .slideshow-setting input[type="checkbox"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
        }}
        
        /* 🎬 Splash Screen - 2/3 Photo + 1/3 UI Layout */
        .splash-screen {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: #000;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            opacity: 1;
            transition: opacity 0.5s ease;
        }}
        
        .splash-screen.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .splash-background {{
            position: relative;
            flex: 2;  /* 2/3 of screen height */
            background-size: cover;
            background-position: center;
            filter: brightness(0.7);
            overflow: hidden;
        }}
        
        .splash-background img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .splash-content {{
            flex: 1;  /* 1/3 of screen height */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 16px 20px 20px;
            background: linear-gradient(to bottom, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.95) 100%);
            gap: clamp(14px, 2.5vh, 24px);
        }}

        .splash-start-row {{
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: center;
            gap: clamp(18px, 4vw, 40px);
            flex-wrap: wrap;
            flex-shrink: 0;
        }}
        
        .splash-title {{
            font-size: 2.5rem;
            font-weight: bold;
            text-align: center;
            text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
            line-height: 1.2;
        }}
        
        .splash-subtitle {{
            font-size: 1.4rem;
            color: #ccc;
            text-align: center;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.8);
            margin-top: 0;
        }}

        .splash-minstars-row {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
            flex-shrink: 0;
            margin-top: 4px;
        }}
        .splash-minstars-row label {{
            font-size: 0.95rem;
            color: #ddd;
            text-shadow: 0 1px 8px rgba(0, 0, 0, 0.85);
        }}
        .splash-minstars-row select {{
            background: rgba(255, 255, 255, 0.12);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.28);
            padding: 10px 16px;
            border-radius: 10px;
            font-size: 1rem;
            cursor: pointer;
            min-width: 220px;
        }}
        
        .splash-play-btn {{
            background: linear-gradient(135deg, #8b5cf6, #ec4899);
            border: none;
            color: #fff;
            width: 140px;
            height: 140px;
            border-radius: 50%;
            font-size: 4rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 15px 50px rgba(139, 92, 246, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .splash-play-btn:hover {{
            transform: scale(1.1);
            box-shadow: 0 20px 70px rgba(139, 92, 246, 0.8);
        }}
        
        .splash-play-btn:active {{
            transform: scale(0.95);
        }}

        .splash-qr-wrap {{
            display: none;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 6px;
            flex-shrink: 0;
            max-width: min(200px, 38vw);
        }}

        .splash-qr-mount {{
            min-width: 160px;
            min-height: 160px;
            max-width: min(220px, 42vw);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .splash-qr-mount img,
        .splash-qr-mount canvas {{
            display: block;
            border-radius: 10px;
            background: #fff;
            padding: 4px;
        }}

        .splash-qr-hint {{
            font-size: 0.68rem;
            color: #888;
            text-align: center;
            max-width: 200px;
            line-height: 1.25;
        }}

        .splash-qr-link {{
            font-size: 0.72rem;
            color: #c4b5fd;
            word-break: break-all;
            max-width: 200px;
            text-align: center;
        }}
        
        @media (max-width: 768px) {{
            .splash-title {{
                font-size: 1.8rem;
            }}
            
            .splash-subtitle {{
                font-size: 1.1rem;
            }}
            
            .splash-play-btn {{
                width: 120px;
                height: 120px;
                font-size: 3.5rem;
            }}
            
            .splash-content {{
                padding: 30px 20px;
                gap: 25px;
            }}
        }}

        /* LAN-Remote-Hub Status (nur wenn Export Hub-URL gesetzt hat) */
        .remote-hub-led-wrap {{
            position: fixed;
            bottom: 16px;
            right: 16px;
            z-index: 10000;
            display: none;
            align-items: center;
            gap: 8px;
            background: rgba(0, 0, 0, 0.55);
            padding: 8px 12px;
            border-radius: 10px;
            font-size: 0.8rem;
            color: #ddd;
            pointer-events: none;
        }}
        .remote-hub-led-wrap .led {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            flex-shrink: 0;
        }}
        .led-muted {{ background: #555; }}
        .led-wait {{ background: #f90; box-shadow: 0 0 8px #f90; animation: remoteLedPulse 1.2s ease-in-out infinite; }}
        .led-ok {{ background: #3c3; box-shadow: 0 0 8px #3c3; }}
        .led-err {{ background: #c33; box-shadow: 0 0 6px #c33; }}
        @keyframes remoteLedPulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.45; }}
        }}
        .remote-hub-led-text {{ max-width: 200px; line-height: 1.25; }}
        .hub-disabled-banner {{
            position: fixed;
            top: 12px;
            left: 12px;
            right: 12px;
            z-index: 10001;
            background: rgba(120, 30, 30, 0.92);
            color: #fff;
            padding: 12px 14px;
            border-radius: 10px;
            font-size: 0.88rem;
            line-height: 1.45;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }}
        .hub-disabled-banner code {{ font-size: 0.85rem; }}
    </style>
</head>
<body>
{hub_disabled_banner}
    <div id="fileGalleryHttpHint" class="hub-disabled-banner" style="display:none;background:rgba(100,65,20,0.93);border:1px solid rgba(255,200,120,0.35);">
        <strong>file:// / lokaler Pfad:</strong> Beim Export im Photo-Tool die <strong>öffentliche http(s)-URL dieser Galerie</strong> eintragen (NAS, Ordner mit <code>index.html</code>), sonst kann das Handy <code>slides.json</code> nicht per Hub laden.
    </div>
    <div id="remoteHubLedWrap" class="remote-hub-led-wrap" aria-live="polite">
        <span class="remote-hub-led-label">LAN-Remote</span>
        <span id="remoteHubLed" class="led led-muted" title="Hub-Verbindung"></span>
        <span id="remoteHubLedText" class="remote-hub-led-text"></span>
    </div>
    <!-- 🎬 Splash Screen with Custom Photo -->
    <div class="splash-screen" id="splashScreen">
        <div class="splash-background">
            <img src="{splash_bg}" 
                 onerror="this.src='{splash_fallback}'" 
                 alt="Welcome">
        </div>
        <div class="splash-content">
            <div class="splash-title">{splash_title}</div>
            <div class="splash-start-row">
                <button class="splash-play-btn" onclick="startSlideshow()" title="Start Slideshow">
                    ▶️
                </button>
                <div id="splashQrWrap" class="splash-qr-wrap">
                    <div id="splashQrMount" class="splash-qr-mount" aria-label="QR Fernbedienung"></div>
                    <a id="splashQrFallbackLink" class="splash-qr-link" href="#" target="_blank" rel="noopener"></a>
                    <div class="splash-qr-hint">QR scannen oder Link (WLAN)</div>
                </div>
            </div>
            <div class="splash-minstars-row">
                <label for="splashMinStars">Autoplay: Mindest-Sterne (effektiv Couch → sonst Projekt)</label>
                <select id="splashMinStars" aria-label="Mindest-Sterne für Autoplay und Fortschritt"></select>
            </div>
            <div class="splash-subtitle">{splash_subtitle}</div>
        </div>
    </div>
    
    <div class="slideshow" id="slideshow" onmousemove="showControlsTemporarily()" style="display: none;">
        <div class="slideshow-header">
            <div class="slideshow-title">
                <span>🎬</span>
                <span>{title}</span>
                <span style="color: #888; font-size: 0.9rem; margin-left: 10px;" id="counter">
                    1 / {len(photo_data)}
                </span>
            </div>
            <div style="display: flex; gap: 10px;">
                <button class="slideshow-btn" onclick="event.stopPropagation(); toggleFullscreen();" id="fullscreenBtn">
                    ⛶ Fullscreen
                </button>
            </div>
        </div>
        
        <div class="slideshow-main">
            <!-- Images will be added by JavaScript -->
        </div>
        
        <div id="ratingHud" class="slideshow-rating-hud slideshow-rating-hud--off" aria-live="polite"></div>
        
        <div class="slideshow-footer">
            <div class="slideshow-progress">
                <div class="slideshow-progress-bar-hit" id="progressBarHit" title="Folie wählen (große Klickfläche)">
                    <div class="slideshow-progress-bar">
                        <div class="slideshow-progress-fill" id="progressBar"></div>
                    </div>
                </div>
                <div class="slideshow-progress-text" id="progressText">1 / {len(photo_data)}</div>
                <div id="footerQrWrap" class="footer-qr-wrap" aria-label="QR Remote">
                    <div id="footerQrMount" class="footer-qr-mount"></div>
                    <a id="footerQrLink" class="footer-qr-link" href="#" target="_blank" rel="noopener"></a>
                </div>
            </div>
            
            <div class="slideshow-controls">
                <button class="slideshow-btn" onclick="event.stopPropagation(); prevSlide();" id="prevBtn">
                    ⏮️ Prev
                </button>
                
                <button class="slideshow-btn primary" onclick="event.stopPropagation(); togglePlay();" id="playBtn">
                    ⏸️ Pause
                </button>
                
                <button class="slideshow-btn" onclick="event.stopPropagation(); nextSlide();" id="nextBtn">
                    Next ⏭️
                </button>
                
                <div class="slideshow-settings">
                    <div class="slideshow-setting">
                        <span>Speed:</span>
                        <select id="speedSelect" onchange="event.stopPropagation(); changeSpeed();">
                            <option value="2">2s</option>
                            <option value="3">3s</option>
                            <option value="5" selected>5s</option>
                            <option value="7">7s</option>
                            <option value="10">10s</option>
                        </select>
                    </div>
                    
                    <div class="slideshow-setting">
                        <input type="checkbox" id="loopCheck" onchange="event.stopPropagation(); toggleLoop();" checked>
                        <label for="loopCheck">Loop</label>
                    </div>
                    
                    <div class="slideshow-setting">
                        <span>Min ⭐:</span>
                        <select id="footerMinStars" onchange="event.stopPropagation(); onFooterMinStarsChange();" title="Nur Slides mit effektiver Bewertung ≥ Schwelle im Autoplay; Fortschritt zeigt Trefferanzahl."></select>
                    </div>
                </div>
                
{music_controls_html}
            </div>
        </div>
    </div>
    
{music_html}
    
    <script>
        const photos = {photos_json};

        function effectiveRating(photo) {{
            if (!photo) return 0;
            const cr = photo.couch_rating;
            if (cr !== undefined && cr !== null) return Math.max(0, Math.min(5, Number(cr)));
            return Math.max(0, Math.min(5, Number(photo.rating || 0)));
        }}

        function effectiveColor(photo) {{
            if (!photo) return null;
            const cc = photo.couch_color;
            if (cc !== undefined && cc !== null && cc !== '') return cc;
            return photo.color != null ? photo.color : null;
        }}

        let currentIndex = 0;
        let isPlaying = true;
        let isLooping = true;
        let isFullscreen = false;
        let hideControlsTimeout = null;
        let slideInterval = null;
        let slideDuration = {slideshow_duration * 1000};

        function parseMinCouchStarsFromUrl() {{
            try {{
                const raw = new URLSearchParams(location.search).get('min_couch_stars');
                if (raw == null || raw === '') return 0;
                const n = parseInt(raw, 10);
                if (isNaN(n)) return 0;
                return Math.max(0, Math.min(5, n));
            }} catch (e) {{ return 0; }}
        }}

        let minCouchStarsAutoplay = parseMinCouchStarsFromUrl();

        function slideEligibleForAutoplay(i) {{
            if (minCouchStarsAutoplay <= 0) return true;
            const p = photos[i];
            if (!p) return false;
            return effectiveRating(p) >= minCouchStarsAutoplay;
        }}

        function getEligibleSlideIndices() {{
            if (minCouchStarsAutoplay <= 0) {{
                const a = [];
                for (let i = 0; i < photos.length; i++) a.push(i);
                return a;
            }}
            const out = [];
            for (let i = 0; i < photos.length; i++) {{
                if (slideEligibleForAutoplay(i)) out.push(i);
            }}
            return out;
        }}

        function progressMetrics() {{
            const elig = getEligibleSlideIndices();
            const filtered = minCouchStarsAutoplay > 0;
            const total = elig.length;
            if (photos.length === 0) {{
                return {{ pct: 0, line: '0 / 0', filtered }};
            }}
            if (!filtered) {{
                const t = photos.length;
                const pos = currentIndex + 1;
                return {{ pct: (pos / t) * 100, line: `${{pos}} / ${{t}}`, filtered }};
            }}
            if (total === 0) {{
                return {{ pct: 0, line: `0 / 0 (≥${{minCouchStarsAutoplay}}⭐)`, filtered }};
            }}
            const posIn = elig.indexOf(currentIndex);
            if (posIn < 0) {{
                return {{ pct: 0, line: `— / ${{total}}`, filtered }};
            }}
            return {{ pct: ((posIn + 1) / total) * 100, line: `${{posIn + 1}} / ${{total}}`, filtered }};
        }}

        function fillMinStarsSelectOptions(selectEl) {{
            if (!selectEl) return;
            selectEl.innerHTML = '';
            const opts = [
                [0, 'Alle Slides (kein Sterne-Filter)'],
                [1, '⭐ 1+'],
                [2, '⭐ 2+'],
                [3, '⭐ 3+'],
                [4, '⭐ 4+'],
                [5, '⭐ 5'],
            ];
            for (let j = 0; j < opts.length; j++) {{
                const o = document.createElement('option');
                o.value = String(opts[j][0]);
                o.textContent = opts[j][1];
                selectEl.appendChild(o);
            }}
        }}

        function syncMinStarsWidgets() {{
            const v = String(Math.max(0, Math.min(5, minCouchStarsAutoplay)));
            const s = document.getElementById('splashMinStars');
            const f = document.getElementById('footerMinStars');
            if (s) s.value = v;
            if (f) f.value = v;
        }}

        function setMinCouchStarsAutoplay(n) {{
            let v = parseInt(n, 10);
            if (isNaN(v)) v = 0;
            v = Math.max(0, Math.min(5, v));
            minCouchStarsAutoplay = v;
            syncMinStarsWidgets();
            updateDisplay();
            if (isPlaying) startAutoplay();
        }}

        function onFooterMinStarsChange() {{
            const el = document.getElementById('footerMinStars');
            if (!el) return;
            setMinCouchStarsAutoplay(el.value);
        }}

        function nextSlideFilteredForAutoplay() {{
            if (minCouchStarsAutoplay <= 0) {{
                nextSlide();
                return;
            }}
            for (let k = currentIndex + 1; k < photos.length; k++) {{
                if (slideEligibleForAutoplay(k)) {{
                    currentIndex = k;
                    updateDisplay();
                    return;
                }}
            }}
            if (isLooping) {{
                for (let k = 0; k < currentIndex; k++) {{
                    if (slideEligibleForAutoplay(k)) {{
                        currentIndex = k;
                        updateDisplay();
                        return;
                    }}
                }}
            }}
        }}

        const RATING_HUD_LS_KEY = 'photoSlideshowRatingHudVisible';
        const COLOR_LABEL_HEX = {{ "red": "#e11", "yellow": "#f5c518", "green": "#22bb44", "blue": "#2563eb", "purple": "#a855f7" }};
        let ratingHudVisible = localStorage.getItem(RATING_HUD_LS_KEY) === '1';

        function setRatingHudVisible(on) {{
            ratingHudVisible = !!on;
            localStorage.setItem(RATING_HUD_LS_KEY, ratingHudVisible ? '1' : '0');
            applyRatingHudVisibility();
        }}

        function applyRatingHudVisibility() {{
            const hud = document.getElementById('ratingHud');
            if (!hud) return;
            hud.classList.toggle('slideshow-rating-hud--off', !ratingHudVisible);
            if (ratingHudVisible) syncRatingHudContent();
        }}

        function syncRatingHudContent() {{
            const hud = document.getElementById('ratingHud');
            if (!hud || !ratingHudVisible) return;
            const p = photos[currentIndex];
            if (!p) {{ hud.innerHTML = ''; return; }}
            const r = effectiveRating(p);
            const c = effectiveColor(p);
            let html = '';
            if (r > 0) {{
                html += '<span class="rh-stars">' + '★'.repeat(r) + '☆'.repeat(5 - r) + '</span>';
            }} else {{
                html += '<span class="rh-stars" style="opacity:0.5">—</span>';
            }}
            if (c && COLOR_LABEL_HEX[c]) {{
                html += '<span class="rh-color" style="background:' + COLOR_LABEL_HEX[c] + '" title="' + c + '"></span>';
            }}
            hud.innerHTML = html;
        }}

        const REMOTE_HUB_WS_BASE = {remote_hub_literal};
        const REMOTE_SESSION_ID = {remote_session_literal};
        const GALLERY_PUBLIC_HTTP_BASE = {gallery_public_literal};
        const TV_INSTANCE_ID = (typeof crypto !== 'undefined' && crypto.randomUUID)
            ? crypto.randomUUID()
            : ('tv-' + String(Date.now()) + '-' + String(Math.random()).slice(2, 10));
        let TV_STATE_SEQ = 0;
        let remoteWs = null;
        let remoteReconnectTimer = null;
        const REMOTE_HUB_DEBUG = typeof URLSearchParams !== 'undefined' &&
            new URLSearchParams(location.search).get('remoteDebug') === '1';

        function remoteHubLog() {{
            if (REMOTE_HUB_DEBUG && typeof console !== 'undefined' && console.log) {{
                console.log.apply(console, ['[remote-hub]'].concat([].slice.call(arguments)));
            }}
        }}

        function showBlindTapFeedback(quadrant) {{
            const map = {{ LU: [0.14, 0.22], LD: [0.14, 0.78], RU: [0.86, 0.22], RD: [0.86, 0.78] }};
            const pos = map[quadrant];
            if (!pos) return;
            let el = document.getElementById('blindTapFlash');
            if (!el) {{
                el = document.createElement('div');
                el.id = 'blindTapFlash';
                el.setAttribute('aria-hidden', 'true');
                document.body.appendChild(el);
            }}
            const vmin = Math.min(window.innerWidth, window.innerHeight);
            const d = Math.round(vmin * 0.15);
            el.style.cssText = 'pointer-events:none;position:fixed;z-index:9998;border-radius:50%;'
                + 'left:' + Math.round(pos[0] * window.innerWidth - d / 2) + 'px;'
                + 'top:' + Math.round(pos[1] * window.innerHeight - d / 2) + 'px;'
                + 'width:' + d + 'px;height:' + d + 'px;'
                + 'background:radial-gradient(circle,rgba(124,58,237,0.9) 0%,rgba(34,187,68,0.55) 40%,transparent 72%);'
                + 'opacity:1;transform:scale(1);transition:none;box-shadow:0 0 24px rgba(124,58,237,0.4);';
            requestAnimationFrame(function () {{
                el.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
                el.style.opacity = '0';
                el.style.transform = 'scale(1.4)';
            }});
            setTimeout(function () {{
                el.style.transition = 'none';
                el.style.opacity = '0';
                el.style.transform = 'scale(1)';
            }}, 520);
        }}

        /** TV: aktuelle couch_* aus slides.json (NAS) — eingebettetes photos-Array ist nur Export-Snapshot. */
        async function mergeCouchRatingsFromSlidesJson() {{
            let url = '';
            try {{
                const u = new URL(window.location.href);
                if (u.protocol === 'http:' || u.protocol === 'https:') {{
                    url = new URL('slides.json', u.href).href;
                }} else if (GALLERY_PUBLIC_HTTP_BASE) {{
                    const base = String(GALLERY_PUBLIC_HTTP_BASE).trim().replace(/\\/+$/, '') + '/';
                    url = new URL('slides.json', base).href;
                }}
            }} catch (e) {{
                return;
            }}
            if (!url) return;
            try {{
                const res = await fetch(url, {{ cache: 'no-store' }});
                if (!res.ok) {{
                    remoteHubLog('slides.json HTTP', res.status);
                    return;
                }}
                const data = await res.json();
                const slides = data.slides || [];
                const n = Math.min(photos.length, slides.length);
                for (let i = 0; i < n; i++) {{
                    const s = slides[i];
                    if (!s || typeof s !== 'object') continue;
                    if ('couch_rating' in s) {{
                        const v = s.couch_rating;
                        if (v === null || v === undefined || v === '') {{
                            photos[i].couch_rating = null;
                        }} else {{
                            const num = Number(v);
                            if (!isNaN(num)) photos[i].couch_rating = Math.max(0, Math.min(5, num));
                        }}
                    }}
                    if ('couch_color' in s) {{
                        const c = s.couch_color;
                        photos[i].couch_color = c === '' || c == null ? null : c;
                    }}
                }}
                remoteHubLog('merged couch_* from slides.json for', n, 'slides');
            }} catch (e) {{
                remoteHubLog('slides.json merge failed', e);
            }}
        }}

        function syncRemoteHubLedWrap() {{
            const wrap = document.getElementById('remoteHubLedWrap');
            if (!wrap) return;
            wrap.style.display = REMOTE_HUB_WS_BASE ? 'flex' : 'none';
        }}

        function setRemoteHubLed(kind, text) {{
            const led = document.getElementById('remoteHubLed');
            const el = document.getElementById('remoteHubLedText');
            if (!led) return;
            const cls = ({{ connecting: 'led-wait', open: 'led-ok', closed: 'led-muted', error: 'led-err' }})[kind] || 'led-muted';
            led.className = 'led ' + cls;
            if (el != null && text != null) el.textContent = text;
        }}

        function remoteHubWsUrl() {{
            if (!REMOTE_HUB_WS_BASE) return null;
            const base = String(REMOTE_HUB_WS_BASE).replace(/\\/+$/, '');
            const sid = encodeURIComponent(REMOTE_SESSION_ID || 'default');
            return base + '/' + sid;
        }}

        function getGalleryBaseUrl() {{
            try {{
                const u = new URL(window.location.href);
                const fileOrOpaque = u.protocol === 'file:' || !u.origin || u.origin === 'null';
                if (fileOrOpaque) {{
                    if (GALLERY_PUBLIC_HTTP_BASE) {{
                        return String(GALLERY_PUBLIC_HTTP_BASE).trim().replace(/\\/+$/, '') + '/';
                    }}
                    return '';
                }}
                let p = u.pathname || '/';
                if (p.endsWith('/index.html')) {{
                    p = p.slice(0, -10);
                }}
                if (!p.endsWith('/')) {{
                    const i = p.lastIndexOf('/');
                    p = i >= 0 ? p.slice(0, i + 1) : '/';
                }}
                if (!p.endsWith('/')) p += '/';
                return u.origin + p;
            }} catch (e) {{
                return '';
            }}
        }}

        function hubHttpOriginFromWs(wsBase) {{
            if (!wsBase) return '';
            try {{
                const u = new URL(String(wsBase).trim());
                const proto = u.protocol === 'wss:' ? 'https:' : 'http:';
                return proto + '//' + u.host;
            }} catch (e) {{
                return '';
            }}
        }}

        function buildRemoteInviteUrl() {{
            if (!REMOTE_HUB_WS_BASE) return '';
            const root = hubHttpOriginFromWs(REMOTE_HUB_WS_BASE);
            if (!root) return '';
            const g = getGalleryBaseUrl();
            if (!g) return '';
            const p = new URLSearchParams();
            p.set('session', REMOTE_SESSION_ID || 'default');
            p.set('gallery', g);
            const hubWs = String(REMOTE_HUB_WS_BASE).trim().replace(/\\/+$/, '');
            if (hubWs) p.set('hubWs', hubWs);
            return root + '/remote?' + p.toString();
        }}

        function splashQrVendorScriptUrl() {{
            try {{
                return new URL('vendor/qrcode.min.js', window.location.href).href;
            }} catch (e) {{
                return 'vendor/qrcode.min.js';
            }}
        }}

        function styleQrMountPreferCanvas(mount) {{
            if (!mount) return;
            setTimeout(function () {{
                const c = mount.querySelector('canvas');
                const im = mount.querySelector('img');
                if (c) {{
                    c.style.display = 'block';
                    c.style.maxWidth = '100%';
                    c.style.height = 'auto';
                }}
                if (im && c) {{
                    im.style.display = 'none';
                }} else if (im && (!im.complete || im.naturalWidth === 0)) {{
                    im.style.display = 'none';
                }}
            }}, 0);
        }}

        /** Splash (groß) + Leiste (kompakt): gleiche Invite-URL — TV-Cache/Resume: Leiste einblenden → scannen. */
        function renderRemoteQrCodes() {{
            const wrap = document.getElementById('splashQrWrap');
            const mount = document.getElementById('splashQrMount');
            const link = document.getElementById('splashQrFallbackLink');
            const footerWrap = document.getElementById('footerQrWrap');
            const footerMount = document.getElementById('footerQrMount');
            const footerLink = document.getElementById('footerQrLink');
            if (!wrap || !mount) return;
            const invite = buildRemoteInviteUrl();
            if (!invite) {{
                wrap.style.display = 'none';
                if (footerWrap) footerWrap.style.display = 'none';
                remoteHubLog('QR skipped (no invite)', REMOTE_HUB_WS_BASE, getGalleryBaseUrl());
                return;
            }}
            wrap.style.display = 'flex';
            if (footerWrap) footerWrap.style.display = 'flex';
            if (link) {{
                link.href = invite;
                link.textContent = 'Remote öffnen · Link';
            }}
            if (footerLink) {{
                footerLink.href = invite;
                footerLink.textContent = 'Remote / Handy';
            }}
            const hintEl = wrap.querySelector('.splash-qr-hint');
            if (hintEl) {{
                hintEl.textContent = 'QR scannen oder Link (WLAN)';
            }}
            const setQrLoadFailed = function () {{
                mount.innerHTML = '';
                if (footerMount) footerMount.innerHTML = '';
                if (link) {{
                    link.textContent = 'Remote öffnen · Link (QR-Skript fehlt — Datei vendor/qrcode.min.js prüfen oder Link antippen)';
                }}
                if (footerLink) {{
                    footerLink.textContent = 'Link öffnen';
                }}
                if (hintEl) {{
                    hintEl.textContent = 'Mit neu exportierter Galerie liegt das Skript unter gleichem Ordner wie index.html (vendor/). Sonst Link nutzen.';
                }}
                if (footerWrap) footerWrap.style.display = 'flex';
            }};
            const draw = function () {{
                try {{
                    if (typeof QRCode === 'undefined') return;
                    mount.innerHTML = '';
                    new QRCode(mount, {{
                        text: invite,
                        width: 200,
                        height: 200,
                        colorDark: '#1a1a2e',
                        colorLight: '#ffffff',
                        correctLevel: QRCode.CorrectLevel.M
                    }});
                    styleQrMountPreferCanvas(mount);
                    if (footerMount) {{
                        footerMount.innerHTML = '';
                        new QRCode(footerMount, {{
                            text: invite,
                            width: 88,
                            height: 88,
                            colorDark: '#1a1a2e',
                            colorLight: '#ffffff',
                            correctLevel: QRCode.CorrectLevel.L
                        }});
                        styleQrMountPreferCanvas(footerMount);
                    }}
                }} catch (e) {{
                    console.warn('QR', e);
                    setQrLoadFailed();
                }}
            }};
            if (typeof QRCode !== 'undefined') {{
                draw();
                return;
            }}
            const scr = document.createElement('script');
            scr.src = splashQrVendorScriptUrl();
            scr.async = true;
            scr.onload = draw;
            scr.onerror = function () {{
                const scr2 = document.createElement('script');
                scr2.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
                scr2.async = true;
                scr2.onload = draw;
                scr2.onerror = setQrLoadFailed;
                document.head.appendChild(scr2);
            }};
            document.head.appendChild(scr);
        }}

        function sendRemoteState() {{
            if (!remoteWs || remoteWs.readyState !== WebSocket.OPEN) return;
            try {{
                const pm = progressMetrics();
                const elig = getEligibleSlideIndices();
                remoteWs.send(JSON.stringify({{
                    type: 'state',
                    index: currentIndex,
                    total: photos.length,
                    playing: isPlaying,
                    gallery_base: getGalleryBaseUrl(),
                    tv_instance: TV_INSTANCE_ID,
                    state_seq: ++TV_STATE_SEQ,
                    min_couch_stars: minCouchStarsAutoplay,
                    eligible_total: elig.length,
                    progress_line: pm.line,
                    autoplay_filter_active: minCouchStarsAutoplay > 0
                }}));
            }} catch (e) {{}}
        }}

        function connectRemoteHub() {{
            const url = remoteHubWsUrl();
            syncRemoteHubLedWrap();
            if (!url) return;
            setRemoteHubLed('connecting', 'verbinde…');
            if (remoteReconnectTimer) {{
                clearTimeout(remoteReconnectTimer);
                remoteReconnectTimer = null;
            }}
            try {{
                remoteHubLog('connecting', url);
                remoteWs = new WebSocket(url);
            }} catch (e) {{
                remoteHubLog('connect error', e);
                setRemoteHubLed('error', 'WebSocket-Fehler');
                remoteReconnectTimer = setTimeout(connectRemoteHub, 3000);
                return;
            }}
            remoteWs.onopen = function () {{
                setRemoteHubLed('open', 'Hub verbunden');
                try {{
                    remoteWs.send(JSON.stringify({{ type: 'hello', role: 'tv' }}));
                }} catch (err) {{}}
                sendRemoteState();
            }};
            remoteWs.onmessage = function (ev) {{
                try {{
                    const msg = JSON.parse(ev.data);
                    if (msg.type === 'rated' && msg.ok && msg.slide_index != null) {{
                        const ri = msg.slide_index;
                        if (ri >= 0 && ri < photos.length) {{
                            if (msg.couch_rating !== undefined) photos[ri].couch_rating = msg.couch_rating;
                            if (msg.couch_color !== undefined) photos[ri].couch_color = msg.couch_color;
                            updateDisplay();
                        }}
                        return;
                    }}
                    if (msg.type === 'hello' && msg.role === 'remote') {{
                        sendRemoteState();
                        return;
                    }}
                    if (msg.type !== 'cmd') return;
                    if (msg.from === 'tv') return;
                    remoteHubLog('cmd', msg.action, msg);
                    const act = msg.action;
                    if (act === 'next') {{ pauseAutoplayForManualNavigation(); nextSlide(); }}
                    else if (act === 'prev') {{ pauseAutoplayForManualNavigation(); prevSlide(); }}
                    else if (act === 'toggle') {{ togglePlay(); }}
                    else if (act === 'goto' && msg.index != null) {{
                        const idx = parseInt(msg.index, 10);
                        if (!isNaN(idx) && idx >= 0 && idx < photos.length) {{
                            pauseAutoplayForManualNavigation();
                            currentIndex = idx;
                            updateDisplay();
                        }}
                    }}
                    else if (act === 'hide_chrome' || act === 'hide_controls') {{
                        clearTimeout(hideControlsTimeout);
                        slideshow.classList.add('hide-controls');
                    }}
                    else if (act === 'show_chrome' || act === 'show_controls') {{
                        showControlsTemporarily();
                    }}
                    else if (act === 'toggle_chrome' || act === 'toggle_controls') {{
                        toggleControlsVisibility();
                    }}
                    else if (act === 'toggle_rating_hud') {{ setRatingHudVisible(!ratingHudVisible); }}
                    else if (act === 'show_rating_hud') {{ setRatingHudVisible(true); }}
                    else if (act === 'hide_rating_hud') {{ setRatingHudVisible(false); }}
                    else if (act === 'blind_tap' && msg.quadrant) {{
                        showBlindTapFeedback(String(msg.quadrant).toUpperCase());
                    }}
                }} catch (e) {{}}
            }};
            remoteWs.onerror = function () {{
                setRemoteHubLed('error', 'Hub nicht erreichbar');
            }};
            remoteWs.onclose = function () {{
                remoteWs = null;
                setRemoteHubLed('closed', 'getrennt, neu …');
                remoteReconnectTimer = setTimeout(connectRemoteHub, 3000);
            }};
        }}
        
        // 🎚️ Music ducking configuration
        const MUSIC_DUCKING_VOLUME = {music_ducking_volume / 100.0};  // Convert 0-100% to 0.0-1.0
        const MUSIC_FULL_VOLUME = 1.0;
        
        const slideshow = document.getElementById('slideshow');
        const slideshowMain = document.querySelector('.slideshow-main');
        const playBtn = document.getElementById('playBtn');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const progressBar = document.getElementById('progressBar');
        const progressBarHit = document.getElementById('progressBarHit');
        const progressText = document.getElementById('progressText');
        const counter = document.getElementById('counter');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        const speedSelect = document.getElementById('speedSelect');
        const bgMusic = document.getElementById('bgMusic');
        
        /** 0 = legacy (all slides keep <img src>); >0 = only load neighbors to save 4K/8K GPU RAM */
        const MEMORY_WINDOW_RADIUS = {memory_window_radius};
        
        function slideImageUrl(i) {{
            const p = photos[i];
            if (!p) return '';
            return p.src_webp || p.src;
        }}
        
        function absMediaUrl(rel) {{
            try {{ return new URL(rel, window.location.href).href; }} catch (e) {{ return rel; }}
        }}
        
        function releaseOffWindowImages() {{
            if (MEMORY_WINDOW_RADIUS <= 0) return;
            const keep = new Set();
            for (let d = -MEMORY_WINDOW_RADIUS; d <= MEMORY_WINDOW_RADIUS; d++) {{
                const i = currentIndex + d;
                if (i >= 0 && i < photos.length) keep.add(i);
            }}
            imageContainers.forEach((container, i) => {{
                const img = container.querySelector('img');
                if (!img) return;
                if (keep.has(i)) {{
                    const url = slideImageUrl(i);
                    const want = absMediaUrl(url);
                    if (!img.getAttribute('src') || img.src !== want) {{
                        img.src = url;
                    }}
                }} else {{
                    img.removeAttribute('src');
                }}
            }});
        }}
        
        // Create slide containers; TV/high-res exports defer src until releaseOffWindowImages()
        photos.forEach((photo, i) => {{
            const container = document.createElement('div');
            container.className = 'slideshow-image-container' + (i === 0 ? ' active' : '');
            
            const img = document.createElement('img');
            img.alt = photo.title || `Photo ${{i + 1}}`;
            img.className = 'slideshow-image';
            if (MEMORY_WINDOW_RADIUS <= 0) {{
                img.src = slideImageUrl(i);
            }}
            container.appendChild(img);
            slideshowMain.appendChild(container);
        }});
        
        const imageContainers = document.querySelectorAll('.slideshow-image-container');
        
        function updateDisplay() {{
            releaseOffWindowImages();
            imageContainers.forEach((container, i) => {{
                container.classList.toggle('active', i === currentIndex);
            }});
            
            const pm = progressMetrics();
            progressBar.style.width = pm.pct + '%';
            progressText.textContent = pm.line;
            counter.textContent = pm.line;
            if (progressBarHit) {{
                progressBarHit.title = pm.filtered && minCouchStarsAutoplay > 0
                    ? `Nur ≥${{minCouchStarsAutoplay}}⭐ — ${{pm.line}} (Klick springt zwischen Treffern)`
                    : 'Folie wählen (große Klickfläche)';
            }}
            
            prevBtn.disabled = currentIndex === 0 && !isLooping;
            nextBtn.disabled = currentIndex === photos.length - 1 && !isLooping;
            sendRemoteState();
            syncRatingHudContent();
        }}
        
        function nextSlide() {{
            if (currentIndex < photos.length - 1) {{
                currentIndex++;
            }} else if (isLooping) {{
                currentIndex = 0;
            }}
            updateDisplay();
        }}
        
        function prevSlide() {{
            if (currentIndex > 0) {{
                currentIndex--;
            }} else if (isLooping) {{
                currentIndex = photos.length - 1;
            }}
            updateDisplay();
        }}
        
        function togglePlay() {{
            isPlaying = !isPlaying;
            playBtn.textContent = isPlaying ? '⏸️ Pause' : '▶️ Play';

            if (isPlaying) {{
                startAutoplay();
                // 🎚️ Restore full music volume when playing
                const bgMusic = document.getElementById('bgMusic');
                if (bgMusic) {{
                    bgMusic.volume = MUSIC_FULL_VOLUME;
                }}
            }} else {{
                stopSlideshow();
                // 🎚️ Duck music volume when paused
                const bgMusic = document.getElementById('bgMusic');
                if (bgMusic) {{
                    bgMusic.volume = MUSIC_DUCKING_VOLUME;
                }}
            }}
            sendRemoteState();
        }}
        
        function startAutoplay() {{
            stopSlideshow();
            slideInterval = setInterval(() => {{
                const idxBefore = currentIndex;
                nextSlideFilteredForAutoplay();
                if (!isLooping) {{
                    if (minCouchStarsAutoplay <= 0) {{
                        if (currentIndex === photos.length - 1) {{
                            stopSlideshow();
                            isPlaying = false;
                            playBtn.textContent = '▶️ Play';
                        }}
                    }} else {{
                        const elig = getEligibleSlideIndices();
                        if (elig.length === 0) {{
                            stopSlideshow();
                            isPlaying = false;
                            playBtn.textContent = '▶️ Play';
                        }} else {{
                            const p = elig.indexOf(currentIndex);
                            const atLastElig = p === elig.length - 1;
                            if (atLastElig && currentIndex === idxBefore) {{
                                stopSlideshow();
                                isPlaying = false;
                                playBtn.textContent = '▶️ Play';
                            }}
                        }}
                    }}
                }}
            }}, slideDuration);
        }}
        
        function stopSlideshow() {{
            if (slideInterval) {{
                clearInterval(slideInterval);
                slideInterval = null;
            }}
        }}

        /** Remote next/prev/goto while autoplay was on otherwise advances in the background and state desyncs from what you see. */
        function pauseAutoplayForManualNavigation() {{
            stopSlideshow();
            isPlaying = false;
            playBtn.textContent = '▶️ Play';
            const bm = document.getElementById('bgMusic');
            if (bm) bm.volume = MUSIC_DUCKING_VOLUME;
        }}
        
        function changeSpeed() {{
            slideDuration = parseInt(speedSelect.value) * 1000;
            if (isPlaying) {{
                startAutoplay();
            }}
        }}
        
        function toggleLoop() {{
            isLooping = document.getElementById('loopCheck').checked;
            updateDisplay();
        }}
        
        function jumpToSlide(index) {{
            if (index >= 0 && index < photos.length) {{
                currentIndex = index;
                updateDisplay();
                // Restart slideshow if playing
                if (isPlaying) {{
                    startAutoplay();
                }}
            }}
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                slideshow.requestFullscreen().then(() => {{
                    isFullscreen = true;
                    fullscreenBtn.textContent = '⛶ Exit Fullscreen';
                }}).catch(err => {{
                    console.log('Fullscreen error:', err);
                }});
            }} else {{
                document.exitFullscreen().then(() => {{
                    isFullscreen = false;
                    fullscreenBtn.textContent = '⛶ Fullscreen';
                }});
            }}
        }}
        
        function showControlsTemporarily() {{
            slideshow.classList.remove('hide-controls');
            
            clearTimeout(hideControlsTimeout);
            // Only auto-hide if slideshow is playing
            if (isPlaying) {{
                hideControlsTimeout = setTimeout(() => {{
                    slideshow.classList.add('hide-controls');
                }}, 3000);
            }}
        }}
        
        // 📱 Mobile-friendly: Toggle controls visibility on tap (without affecting playback)
        function toggleControlsVisibility() {{
            const isHidden = slideshow.classList.contains('hide-controls');
            
            if (isHidden) {{
                // Show controls
                showControlsTemporarily();
            }} else {{
                // Hide controls immediately if playing, keep visible if paused
                if (isPlaying) {{
                    slideshow.classList.add('hide-controls');
                    clearTimeout(hideControlsTimeout);
                }}
            }}
        }}
        
        function toggleMusic() {{
            if (bgMusic) {{
                if (bgMusic.paused) {{
                    bgMusic.play();
                    document.getElementById('musicIcon').textContent = '🎵';
                }} else {{
                    bgMusic.pause();
                    document.getElementById('musicIcon').textContent = '🔇';
                }}
            }}
        }}
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {{
            showControlsTemporarily();
            
            switch(e.key) {{
                case 'ArrowLeft':
                    prevSlide();
                    break;
                case 'ArrowRight':
                    nextSlide();
                    break;
                case ' ':
                    e.preventDefault();
                    togglePlay();
                    break;
                case 'f':
                case 'F':
                    toggleFullscreen();
                    break;
                case 'm':
                case 'M':
                    if (bgMusic) toggleMusic();
                    break;
                case 'Escape':
                    if (isFullscreen) {{
                        document.exitFullscreen();
                    }}
                    break;
            }}
        }});
        
        // Handle fullscreen changes
        document.addEventListener('fullscreenchange', () => {{
            isFullscreen = !!document.fullscreenElement;
            fullscreenBtn.textContent = isFullscreen ? '⛶ Exit Fullscreen' : '⛶ Fullscreen';
        }});
        
        // 📱 Touch event handling for mobile devices
        slideshowMain.addEventListener('click', (e) => {{
            toggleControlsVisibility();
        }});
        
        slideshowMain.addEventListener('touchend', (e) => {{
            e.preventDefault();  // Prevent double-firing with click
            toggleControlsVisibility();
        }});
        
        function progressPointerX(e, rect) {{
            let clientX = e.clientX;
            if (e.changedTouches && e.changedTouches.length) {{
                clientX = e.changedTouches[0].clientX;
            }} else if (e.touches && e.touches.length) {{
                clientX = e.touches[0].clientX;
            }}
            return clientX - rect.left;
        }}

        function onProgressBarSeek(e) {{
            if (!progressBarHit || photos.length === 0) return;
            e.stopPropagation();
            const rect = progressBarHit.getBoundingClientRect();
            const w = rect.width;
            if (w <= 0) return;
            const x = Math.max(0, Math.min(w, progressPointerX(e, rect)));
            const percent = x / w;
            let targetIndex;
            if (minCouchStarsAutoplay > 0) {{
                const elig = getEligibleSlideIndices();
                if (!elig.length) return;
                const slot = Math.min(elig.length - 1, Math.floor(percent * elig.length));
                targetIndex = elig[slot];
            }} else {{
                targetIndex = Math.floor(percent * photos.length);
            }}
            jumpToSlide(Math.max(0, Math.min(photos.length - 1, targetIndex)));
            showControlsTemporarily();
        }}

        if (progressBarHit) {{
            progressBarHit.addEventListener('click', onProgressBarSeek);
            progressBarHit.addEventListener('touchend', function (e) {{
                e.preventDefault();
                onProgressBarSeek(e);
            }}, {{ passive: false }});
        }}
        
        // 📺 TV Remote / Keyboard Control
        document.addEventListener('keydown', (e) => {{
            // Prevent default browser behavior for arrow keys
            if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Enter', ' ', 'Escape'].includes(e.key)) {{
                e.preventDefault();
            }}
            
            switch(e.key) {{
                case 'ArrowRight':  // Next photo
                case 'MediaTrackNext':
                    nextSlide();
                    showControlsTemporarily();
                    break;
                    
                case 'ArrowLeft':   // Previous photo
                case 'MediaTrackPrevious':
                    prevSlide();
                    showControlsTemporarily();
                    break;
                    
                case 'Enter':       // Play/Pause (Samsung OK button)
                case ' ':           // Spacebar
                case 'MediaPlayPause':
                    togglePlay();
                    showControlsTemporarily();
                    break;
                    
                case 'ArrowUp':     // Speed up
                    if (slideDuration > 2000) {{
                        slideDuration = Math.max(2000, slideDuration - 1000);
                        document.getElementById('speedSelect').value = slideDuration / 1000;
                        if (isPlaying) {{
                            startAutoplay();  // Restart with new speed
                        }}
                        showControlsTemporarily();
                    }}
                    break;
                    
                case 'ArrowDown':   // Slow down
                    if (slideDuration < 15000) {{
                        slideDuration = Math.min(15000, slideDuration + 1000);
                        document.getElementById('speedSelect').value = slideDuration / 1000;
                        if (isPlaying) {{
                            startAutoplay();  // Restart with new speed
                        }}
                        showControlsTemporarily();
                    }}
                    break;
                    
                case 'Escape':      // Exit fullscreen
                case 'Back':        // Samsung Back button
                    if (document.fullscreenElement) {{
                        document.exitFullscreen();
                    }}
                    break;
                    
                case 'm':           // Toggle music
                case 'M':
                case 'MediaStop':
                    if (bgMusic) {{
                        toggleMusic();
                        showControlsTemporarily();
                    }}
                    break;
                    
                case 'f':           // Toggle fullscreen
                case 'F':
                    toggleFullscreen();
                    break;
                    
                case 'l':           // Toggle loop
                case 'L':
                    toggleLoop();
                    showControlsTemporarily();
                    break;
            }}
        }});
        
        let slideshowBootPromise = null;

        // 🎬 Splash Screen: Start slideshow on button click
        async function startSlideshowFromSplash() {{
            if (slideshowBootPromise) await slideshowBootPromise;
            const splashSel = document.getElementById('splashMinStars');
            if (splashSel) minCouchStarsAutoplay = Math.max(0, Math.min(5, parseInt(splashSel.value, 10) || 0));
            syncMinStarsWidgets();
            // Hide splash screen
            const splashScreen = document.getElementById('splashScreen');
            splashScreen.classList.add('hidden');
            
            // Show slideshow
            const slideshow = document.getElementById('slideshow');
            slideshow.style.display = 'flex';
            
            // 🖥️ Auto-enter fullscreen (if supported)
            if (document.documentElement.requestFullscreen) {{
                document.documentElement.requestFullscreen().catch(err => {{
                    console.log('Fullscreen request failed:', err);
                }});
            }}
            
            // Start playing
            isPlaying = true;
            playBtn.textContent = '⏸️ Pause';
            startAutoplay();
            
            // 🎵 Start music (user gesture from splash unlocks autoplay policy)
            if (bgMusic) {{
                bgMusic.volume = MUSIC_FULL_VOLUME;
                try {{ bgMusic.load(); }} catch (e) {{}}
                const tryPlay = () => bgMusic.play().catch(e => console.log('Music playback blocked:', e));
                if (bgMusic.readyState >= 2) {{
                    tryPlay();
                }} else {{
                    bgMusic.addEventListener('canplay', function startMusic() {{
                        tryPlay();
                        bgMusic.removeEventListener('canplay', startMusic);
                    }}, {{ once: true }});
                    bgMusic.addEventListener('canplaythrough', function startMusicFull() {{
                        tryPlay();
                        bgMusic.removeEventListener('canplaythrough', startMusicFull);
                    }}, {{ once: true }});
                }}
            }}
            
            // Hide controls after 3 seconds
            setTimeout(() => {{
                slideshow.classList.add('hide-controls');
            }}, 3000);
            sendRemoteState();
        }}
        
        // Make startSlideshow globally accessible for splash button
        window.startSlideshow = startSlideshowFromSplash;
        
        async function runSlideshowBoot() {{
            await mergeCouchRatingsFromSlidesJson();
            fillMinStarsSelectOptions(document.getElementById('splashMinStars'));
            fillMinStarsSelectOptions(document.getElementById('footerMinStars'));
            syncMinStarsWidgets();
            updateDisplay();
            applyRatingHudVisibility();
            renderRemoteQrCodes();
            (function showFileGalleryHttpHint() {{
                try {{
                    const u = new URL(window.location.href);
                    const need = u.protocol === 'file:' || !u.origin || u.origin === 'null';
                    const h = document.getElementById('fileGalleryHttpHint');
                    if (h && need && REMOTE_HUB_WS_BASE && !GALLERY_PUBLIC_HTTP_BASE) h.style.display = 'block';
                }} catch (e) {{}}
            }})();
            syncRemoteHubLedWrap();
            connectRemoteHub();
        }}
        slideshowBootPromise = runSlideshowBoot();
        
        // Generated: {now}
    </script>
</body>
</html>'''
