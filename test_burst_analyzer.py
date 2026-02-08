"""
Test: Check if BurstAnalyzer can be imported and works
"""

print("Testing BurstAnalyzer import and execution...")

try:
    from photo_tool.prescan.analyzers.burst import BurstAnalyzer
    print("OK: BurstAnalyzer imported successfully")
    
    from pathlib import Path
    
    # Test with some photos
    test_folder = Path("E:/Lumix-2026-01/101_PANA")
    photos = list(test_folder.glob("*.JPG"))[:5]  # Test with first 5 photos
    
    print(f"OK: Found {len(photos)} test photos")
    
    # Create analyzer
    analyzer = BurstAnalyzer(
        time_threshold=3,
        similarity_threshold=0.85,
        max_neighbors=20
    )
    print("OK: BurstAnalyzer created")
    
    # Run analysis
    print("Running burst analysis...")
    results = analyzer.analyze_batch(photos)
    
    print(f"OK: Analysis complete! {len(results)} results")
    
    # Show sample result
    if results:
        first_key = list(results.keys())[0]
        first_result = results[first_key]
        print(f"\nSample result for {Path(first_key).name}:")
        print(f"  is_burst_candidate: {first_result.get('is_burst_candidate')}")
        print(f"  burst_id: {first_result.get('burst_id')}")
        print(f"  neighbors: {len(first_result.get('neighbors', []))} photos")
        print(f"  score: {first_result.get('score')}")
        print(f"  detection_date: {first_result.get('detection_date')}")
    
    print("\nOK: BurstAnalyzer works correctly!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
