"""
Stage 1: Time-based grouping for burst detection
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from ..util.logging import get_logger


logger = get_logger("time_grouping")


@dataclass
class TimeGroup:
    """Group of photos taken within a time window"""
    photos: List[Path]
    capture_times: List[datetime]
    start_time: datetime
    end_time: datetime
    
    @property
    def duration(self) -> timedelta:
        """Duration of the group"""
        return self.end_time - self.start_time
    
    @property
    def count(self) -> int:
        """Number of photos in group"""
        return len(self.photos)
    
    def __repr__(self) -> str:
        return f"TimeGroup({self.count} photos, {self.duration.total_seconds():.1f}s)"


def group_by_time(
    photos: List[Path],
    capture_times: List[datetime],
    time_window: float = 3.0,
    max_gap: float = 2.0
) -> List[TimeGroup]:
    """
    Group photos by capture time (Stage 1 of pipeline)
    
    This creates candidate groups for further visual analysis.
    Photos are grouped if they're within time_window seconds of each other,
    with no gap larger than max_gap.
    
    Args:
        photos: List of photo paths
        capture_times: List of capture times (must match photos)
        time_window: Maximum total duration of a group (seconds)
        max_gap: Maximum gap between consecutive photos (seconds)
        
    Returns:
        List of TimeGroup objects
    """
    if len(photos) != len(capture_times):
        raise ValueError("photos and capture_times must have same length")
    
    if not photos:
        return []
    
    # Sort by time
    sorted_pairs = sorted(zip(capture_times, photos), key=lambda x: x[0])
    
    groups = []
    current_group_times = [sorted_pairs[0][0]]
    current_group_photos = [sorted_pairs[0][1]]
    
    for i in range(1, len(sorted_pairs)):
        current_time, current_photo = sorted_pairs[i]
        last_time = current_group_times[-1]
        first_time = current_group_times[0]
        
        # Check if this photo fits in current group
        gap = (current_time - last_time).total_seconds()
        total_duration = (current_time - first_time).total_seconds()
        
        if gap <= max_gap and total_duration <= time_window:
            # Add to current group
            current_group_times.append(current_time)
            current_group_photos.append(current_photo)
        else:
            # Start new group (but only save previous if it has multiple photos)
            if len(current_group_photos) >= 2:
                groups.append(TimeGroup(
                    photos=current_group_photos,
                    capture_times=current_group_times,
                    start_time=current_group_times[0],
                    end_time=current_group_times[-1]
                ))
            
            # Start new group
            current_group_times = [current_time]
            current_group_photos = [current_photo]
    
    # Don't forget last group
    if len(current_group_photos) >= 2:
        groups.append(TimeGroup(
            photos=current_group_photos,
            capture_times=current_group_times,
            start_time=current_group_times[0],
            end_time=current_group_times[-1]
        ))
    
    logger.info(f"Created {len(groups)} time-based groups from {len(photos)} photos")
    
    return groups
