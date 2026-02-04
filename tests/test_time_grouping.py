"""
Tests for time-based grouping
"""

from datetime import datetime, timedelta
from pathlib import Path

from photo_tool.analysis.time_grouping import group_by_time


def test_group_by_time_basic():
    """Test basic time grouping"""
    # Create test data: 3 photos within 2 seconds, then 2 photos after 10 seconds
    base_time = datetime.now()
    
    photos = [
        Path("photo1.jpg"),
        Path("photo2.jpg"),
        Path("photo3.jpg"),
        Path("photo4.jpg"),
        Path("photo5.jpg"),
    ]
    
    times = [
        base_time,
        base_time + timedelta(seconds=1),
        base_time + timedelta(seconds=2),
        base_time + timedelta(seconds=15),
        base_time + timedelta(seconds=16),
    ]
    
    groups = group_by_time(photos, times, time_window=3.0, max_gap=2.0)
    
    # Should have 2 groups
    assert len(groups) == 2
    assert groups[0].count == 3
    assert groups[1].count == 2


def test_group_by_time_no_groups():
    """Test when no groups are formed (all photos far apart)"""
    base_time = datetime.now()
    
    photos = [Path(f"photo{i}.jpg") for i in range(5)]
    times = [base_time + timedelta(seconds=i*10) for i in range(5)]
    
    groups = group_by_time(photos, times, time_window=3.0, max_gap=2.0)
    
    # Should have 0 groups (no pairs within window)
    assert len(groups) == 0


def test_group_by_time_single_large_group():
    """Test single large burst"""
    base_time = datetime.now()
    
    photos = [Path(f"photo{i}.jpg") for i in range(10)]
    times = [base_time + timedelta(milliseconds=i*200) for i in range(10)]  # 0.2s apart
    
    groups = group_by_time(photos, times, time_window=5.0, max_gap=1.0)
    
    # Should have 1 group with all photos
    assert len(groups) == 1
    assert groups[0].count == 10


def test_group_by_time_empty_input():
    """Test empty input"""
    groups = group_by_time([], [], time_window=3.0, max_gap=2.0)
    assert len(groups) == 0
