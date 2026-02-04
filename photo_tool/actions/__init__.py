"""Actions: organize, rate, deduplicate photos"""

from .organizer import organize_clusters, OrganizeResult
from .rating import set_rating, get_rating
from .dedupe import deduplicate_photos

__all__ = ["organize_clusters", "OrganizeResult", "set_rating", "get_rating", "deduplicate_photos"]
