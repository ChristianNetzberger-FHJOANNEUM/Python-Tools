#!/usr/bin/env python3
"""
Quick Performance Test for Phase 1 & 2 Optimizations
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_performance():
    """Test the optimized /api/photos endpoint"""
    
    print("="*70)
    print("🚀 Performance Test: Phase 1 & 2 Optimizations")
    print("="*70)
    
    url = f"{BASE_URL}/api/photos?limit=100"
    
    # Test 1: Cache Miss (First Request)
    print("\n📊 Test 1: First Request (Cache Miss)")
    print("-" * 70)
    
    start = time.time()
    try:
        r1 = requests.get(url, timeout=30)
        time1 = time.time() - start
        
        if r1.status_code == 200:
            data1 = r1.json()
            total_photos = data1.get('total', 0)
            returned = len(data1.get('photos', []))
            perf1 = data1.get('performance', {})
            
            print(f"✅ Status: {r1.status_code}")
            print(f"📸 Total Photos: {total_photos}")
            print(f"📄 Returned: {returned}")
            print(f"⏱️  Total Time: {time1:.3f}s")
            print(f"\n🔍 Performance Breakdown:")
            for key, value in perf1.items():
                print(f"   {key:30s}: {value:.3f}s")
        else:
            print(f"❌ Error: {r1.status_code}")
            print(r1.text)
            return
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    # Test 2: Cache Hit (Second Request within 60s)
    print("\n" + "="*70)
    print("📊 Test 2: Second Request (Cache Hit)")
    print("-" * 70)
    
    start = time.time()
    try:
        r2 = requests.get(url, timeout=30)
        time2 = time.time() - start
        
        if r2.status_code == 200:
            data2 = r2.json()
            perf2 = data2.get('performance', {})
            
            print(f"✅ Status: {r2.status_code}")
            print(f"⏱️  Total Time: {time2:.3f}s")
            print(f"\n🔍 Performance Breakdown:")
            for key, value in perf2.items():
                print(f"   {key:30s}: {value:.3f}s")
            
            # Compare
            print(f"\n📈 Improvement:")
            speedup = ((time1 - time2) / time1) * 100
            print(f"   Time Saved: {time1 - time2:.3f}s ({speedup:.1f}% faster)")
            
            # Check if cache was used
            if 'directory_scan' in perf1 and 'directory_scan' not in perf2:
                print(f"   ✅ Cache was used (no directory scan)")
            elif perf2.get('directory_scan', 999) < perf1.get('directory_scan', 0) / 2:
                print(f"   ✅ Cache was used (much faster scan)")
            
        else:
            print(f"❌ Error: {r2.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return
    
    # Test 3: Multiple parallel requests
    print("\n" + "="*70)
    print("📊 Test 3: Parallel Requests (Stress Test)")
    print("-" * 70)
    
    from concurrent.futures import ThreadPoolExecutor
    
    def make_request(i):
        start = time.time()
        r = requests.get(url, timeout=30)
        duration = time.time() - start
        return i, duration, r.status_code
    
    print("🔥 Sending 5 parallel requests...")
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(make_request, range(5)))
    
    print("\nResults:")
    for i, duration, status in results:
        print(f"   Request {i+1}: {duration:.3f}s (Status: {status})")
    
    avg_time = sum(r[1] for r in results) / len(results)
    print(f"\n📊 Average Time: {avg_time:.3f}s")
    
    # Summary
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    print(f"\n💡 Summary:")
    print(f"   First Request:  {time1:.3f}s (with cache warming)")
    print(f"   Second Request: {time2:.3f}s (cache hit)")
    print(f"   Improvement:    {speedup:.1f}% faster")
    print(f"   Parallel Avg:   {avg_time:.3f}s")
    
    # Targets
    print(f"\n🎯 Performance Targets:")
    if time1 < 5:
        print(f"   ✅ First request < 5s: PASS")
    else:
        print(f"   ⚠️  First request < 5s: {time1:.3f}s (target: <5s)")
    
    if time2 < 1.5:
        print(f"   ✅ Cached request < 1.5s: PASS")
    else:
        print(f"   ⚠️  Cached request < 1.5s: {time2:.3f}s (target: <1.5s)")
    
    print("\n")

if __name__ == '__main__':
    print("\n⚠️  Make sure server is running:")
    print("   cd gui_poc")
    print("   python server.py\n")
    
    input("Press Enter to start test...")
    
    test_performance()
