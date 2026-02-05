"""
Example: Export gallery with slideshow and music support

This demonstrates the new slideshow and music features added to the export functionality.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from photo_tool.actions.export import export_gallery
from photo_tool.workspace import Workspace
from photo_tool.config import load_config
from photo_tool.io import scan_multiple_directories, filter_by_type
from photo_tool.actions.metadata import get_metadata


def example_basic_slideshow():
    """Example 1: Basic slideshow without music"""
    print("=" * 60)
    print("Example 1: Basic Slideshow Export")
    print("=" * 60)
    
    # Get some photos from workspace
    workspace_path = Path("C:/PhotoTool_Test")
    ws = Workspace(workspace_path)
    config = load_config(ws.config_file)
    
    all_media = scan_multiple_directories(
        config.scan.roots,
        config.scan.extensions,
        config.scan.recurse,
        show_progress=False
    )
    
    photos = filter_by_type(all_media, "photo")
    
    # Get first 20 photos
    photo_paths = [p.path for p in photos[:20]]
    
    print(f"\nExporting {len(photo_paths)} photos...")
    
    gallery_dir = export_gallery(
        photo_paths=photo_paths,
        output_dir=workspace_path / "exports" / "slideshow-basic",
        title="Basic Slideshow Demo",
        slideshow_enabled=True,
        slideshow_duration=5  # 5 seconds per photo
    )
    
    print(f"\n✅ Gallery created: {gallery_dir}")
    print(f"📂 Open: {gallery_dir / 'index.html'}")
    print(f"\n🎬 Click 'Start Slideshow' button to begin!")


def example_with_music():
    """Example 2: Slideshow with background music"""
    print("\n" + "=" * 60)
    print("Example 2: Slideshow with Music")
    print("=" * 60)
    
    workspace_path = Path("C:/PhotoTool_Test")
    ws = Workspace(workspace_path)
    config = load_config(ws.config_file)
    
    all_media = scan_multiple_directories(
        config.scan.roots,
        config.scan.extensions,
        config.scan.recurse,
        show_progress=False
    )
    
    photos = filter_by_type(all_media, "photo")
    photo_paths = [p.path for p in photos[:30]]
    
    # Example music files (update these paths to your actual music files!)
    music_files = [
        Path("C:/Music/track1.mp3"),
        Path("C:/Music/track2.mp3"),
    ]
    
    # Filter to existing files
    existing_music = [m for m in music_files if m.exists()]
    
    if not existing_music:
        print("\n⚠️  No music files found at specified paths!")
        print("   Update the music_files list with your actual music file paths.")
        print("   Exporting without music...\n")
        existing_music = None
    else:
        print(f"\n🎵 Found {len(existing_music)} music tracks:")
        for m in existing_music:
            print(f"   - {m.name}")
    
    print(f"\nExporting {len(photo_paths)} photos...")
    
    gallery_dir = export_gallery(
        photo_paths=photo_paths,
        output_dir=workspace_path / "exports" / "slideshow-music",
        title="Slideshow with Music Demo",
        music_files=existing_music,
        slideshow_enabled=True,
        slideshow_duration=7  # 7 seconds per photo
    )
    
    print(f"\n✅ Gallery created: {gallery_dir}")
    print(f"📂 Open: {gallery_dir / 'index.html'}")
    print(f"\n🎬 Click 'Start Slideshow' - music will play automatically!")


def example_smart_tv():
    """Example 3: Smart TV optimized export"""
    print("\n" + "=" * 60)
    print("Example 3: Smart TV Optimized Gallery")
    print("=" * 60)
    
    workspace_path = Path("C:/PhotoTool_Test")
    ws = Workspace(workspace_path)
    config = load_config(ws.config_file)
    
    all_media = scan_multiple_directories(
        config.scan.roots,
        config.scan.extensions,
        config.scan.recurse,
        show_progress=False
    )
    
    photos = filter_by_type(all_media, "photo")
    
    # Filter to 5-star photos only for TV display
    high_rated = []
    for p in photos:
        metadata = get_metadata(p.path)
        if metadata.get('rating', 0) >= 4:
            high_rated.append(p.path)
    
    if not high_rated:
        print("\n⚠️  No highly rated photos found (4-5 stars)")
        print("   Using first 25 photos instead...")
        high_rated = [p.path for p in photos[:25]]
    else:
        print(f"\n⭐ Found {len(high_rated)} photos with 4-5 star rating")
    
    print(f"\nExporting {len(high_rated)} photos...")
    
    gallery_dir = export_gallery(
        photo_paths=high_rated,
        output_dir=workspace_path / "exports" / "smart-tv-demo",
        title="Best Photos - TV Slideshow",
        slideshow_enabled=True,
        slideshow_duration=8,  # Longer duration for TV viewing
        smart_tv_mode=True,    # 🆕 Larger buttons for TV remote
        max_image_size=1920,   # HD resolution (saves bandwidth)
        thumbnail_size=300     # Smaller thumbnails
    )
    
    print(f"\n✅ Gallery created: {gallery_dir}")
    print(f"📂 Gallery folder: {gallery_dir}")
    print(f"\n📺 To view on Smart TV:")
    print(f"   1. Copy '{gallery_dir.name}' folder to USB drive")
    print(f"   2. Or serve via network: python -m http.server 8080")
    print(f"   3. Open TV browser and navigate to gallery/index.html")


def example_filtered_export():
    """Example 4: Export filtered photos (5-star + specific keyword)"""
    print("\n" + "=" * 60)
    print("Example 4: Filtered Gallery Export")
    print("=" * 60)
    
    workspace_path = Path("C:/PhotoTool_Test")
    ws = Workspace(workspace_path)
    config = load_config(ws.config_file)
    
    all_media = scan_multiple_directories(
        config.scan.roots,
        config.scan.extensions,
        config.scan.recurse,
        show_progress=False
    )
    
    photos = filter_by_type(all_media, "photo")
    
    # Filter: 5-star photos with keyword "landscape"
    filtered = []
    for p in photos:
        metadata = get_metadata(p.path)
        rating = metadata.get('rating', 0)
        keywords = metadata.get('keywords', [])
        
        # 5 stars OR has "landscape" keyword
        if rating == 5 or 'landscape' in keywords:
            filtered.append(p.path)
    
    if not filtered:
        print("\n⚠️  No photos match filter (5-star or 'landscape' keyword)")
        print("   Using first 15 photos instead...")
        filtered = [p.path for p in photos[:15]]
    else:
        print(f"\n✨ Found {len(filtered)} photos matching filter")
    
    print(f"\nExporting {len(filtered)} photos...")
    
    gallery_dir = export_gallery(
        photo_paths=filtered,
        output_dir=workspace_path / "exports" / "best-landscapes",
        title="Best Landscapes 2026",
        slideshow_enabled=True,
        slideshow_duration=6,
        include_metadata=True  # Show ratings, keywords in gallery
    )
    
    print(f"\n✅ Gallery created: {gallery_dir}")
    print(f"📂 Open: {gallery_dir / 'index.html'}")


def main():
    """Run all examples"""
    print("\n" + "🎬🎵 " + "=" * 56)
    print("🎬🎵  Slideshow + Music Export Examples")
    print("🎬🎵 " + "=" * 56 + "\n")
    
    try:
        # Run examples
        example_basic_slideshow()
        
        print("\n" + "-" * 60)
        input("\nPress Enter to continue to next example...")
        
        example_with_music()
        
        print("\n" + "-" * 60)
        input("\nPress Enter to continue to next example...")
        
        example_smart_tv()
        
        print("\n" + "-" * 60)
        input("\nPress Enter to continue to next example...")
        
        example_filtered_export()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        print("\n📁 Check C:/PhotoTool_Test/exports/ for generated galleries")
        print("🌐 Open any index.html file in your browser to view")
        print("📺 Copy to USB or serve via network for Smart TV viewing")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure:")
        print("   1. Workspace exists at C:/PhotoTool_Test")
        print("   2. Run 'photo-tool scan' first to add photos")
        print("   3. Update music file paths if using music example")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
