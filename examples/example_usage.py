"""
Example: Using Photo Tool as a Python library

This demonstrates how to use Photo Tool programmatically
instead of through the CLI.
"""

from pathlib import Path
from photo_tool.workspace import create_workspace, Workspace
from photo_tool.config import load_config, save_config
from photo_tool.io import scan_multiple_directories, get_capture_time
from photo_tool.analysis import group_by_time, cluster_similar_photos
from photo_tool.analysis.similarity import detect_blur, HashMethod
from photo_tool.actions import organize_clusters
from photo_tool.report import generate_text_report, generate_html_report


def example_create_workspace():
    """Example: Create a workspace"""
    workspace_path = Path("D:/MyPhotoWorkspace")
    photo_dirs = [
        Path("E:/Photos"),
        Path("F:/Camera/DCIM")
    ]
    
    # Create workspace
    workspace = create_workspace(
        workspace_path,
        scan_roots=photo_dirs
    )
    
    print(f"Workspace created: {workspace.root}")
    print(f"Config file: {workspace.config_file}")


def example_analyze_photos():
    """Example: Full analysis pipeline"""
    workspace_path = Path("D:/MyPhotoWorkspace")
    
    # Load workspace and config
    workspace = Workspace(workspace_path)
    config = load_config(workspace.config_file)
    
    # Step 1: Scan photos
    print("Scanning photos...")
    photos = scan_multiple_directories(
        config.scan.roots,
        config.scan.extensions,
        config.scan.recurse,
        show_progress=True
    )
    print(f"Found {len(photos)} photos")
    
    # Step 2: Get capture times
    print("Reading EXIF timestamps...")
    capture_times = []
    photo_paths = []
    
    for photo in photos:
        capture_time = get_capture_time(photo.path)
        if capture_time:
            capture_times.append(capture_time)
            photo_paths.append(photo.path)
    
    print(f"Photos with timestamps: {len(photo_paths)}")
    
    # Step 3: Time-based grouping
    print("Grouping by time...")
    time_groups = group_by_time(
        photo_paths,
        capture_times,
        config.grouping.time_window_seconds,
        config.grouping.max_group_gap_seconds
    )
    print(f"Found {len(time_groups)} time-based groups")
    
    # Step 4: Compute blur scores
    print("Computing quality scores...")
    blur_scores = {}
    for group in time_groups:
        for photo in group.photos:
            try:
                score = detect_blur(photo)
                blur_scores[photo] = score
            except Exception as e:
                print(f"Warning: Could not analyze {photo}: {e}")
    
    # Step 5: Cluster similar photos
    print("Clustering similar photos...")
    hash_method = HashMethod(config.similarity.method)
    clusters = cluster_similar_photos(
        time_groups,
        hash_method=hash_method,
        similarity_threshold=config.similarity.phash_threshold,
        blur_scores=blur_scores,
        show_progress=True
    )
    print(f"Found {len(clusters)} burst sequences")
    
    # Step 6: Organize (dry run)
    print("\nOrganizing photos (dry run)...")
    result = organize_clusters(
        clusters,
        naming_strategy=config.actions.burst_folder_naming,
        min_cluster_size=config.actions.min_group_size,
        dry_run=True  # Safe preview
    )
    
    print(f"\nResults:")
    print(f"  Clusters: {result.clusters_processed}")
    print(f"  Folders: {result.folders_created}")
    print(f"  Photos: {result.photos_moved}")
    
    # Step 7: Generate report
    print("\nGenerating reports...")
    
    # Text report
    text_report = generate_text_report(
        clusters,
        output_path=workspace.reports_dir / "analysis.txt",
        include_blur_scores=True
    )
    print(f"Text report: {workspace.reports_dir / 'analysis.txt'}")
    
    # HTML report
    generate_html_report(
        clusters,
        output_path=workspace.reports_dir / "analysis.html",
        thumbnails_dir=workspace.thumbnails_dir,
        include_thumbnails=True
    )
    print(f"HTML report: {workspace.reports_dir / 'analysis.html'}")


def example_find_blurry_photos():
    """Example: Find blurry photos"""
    workspace = Workspace("D:/MyPhotoWorkspace")
    config = load_config(workspace.config_file)
    
    # Scan photos
    photos = scan_multiple_directories(
        config.scan.roots,
        config.scan.extensions,
        config.scan.recurse
    )
    
    # Analyze blur
    results = []
    for photo in photos:
        try:
            score = detect_blur(photo.path)
            results.append((photo.path, score))
        except Exception as e:
            print(f"Error: {e}")
    
    # Sort by blur score (lower = blurrier)
    results.sort(key=lambda x: x[1])
    
    # Show top 10 blurriest
    print("Top 10 blurriest photos:")
    for i, (photo, score) in enumerate(results[:10], 1):
        print(f"{i}. {photo.name} - Score: {score:.2f}")


def example_custom_config():
    """Example: Create custom configuration"""
    workspace_path = Path("D:/MyPhotoWorkspace")
    workspace = Workspace(workspace_path)
    
    # Load existing config
    config = load_config(workspace.config_file)
    
    # Modify settings
    config.grouping.time_window_seconds = 5.0
    config.similarity.phash_threshold = 8
    config.actions.dry_run = False  # Be careful!
    
    # Save modified config
    save_config(config, workspace.config_file)
    print(f"Config updated: {workspace.config_file}")


if __name__ == "__main__":
    # Run examples
    print("="*60)
    print("Photo Tool - Python Library Examples")
    print("="*60)
    
    # Uncomment the example you want to run:
    
    # example_create_workspace()
    # example_analyze_photos()
    # example_find_blurry_photos()
    # example_custom_config()
    
    print("\nNote: Uncomment examples in the code to run them")
