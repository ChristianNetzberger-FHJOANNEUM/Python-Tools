"""Actions: organize, rate, deduplicate photos"""

from .organizer import organize_clusters, OrganizeResult
from .rating import set_rating, get_rating
from .dedupe import deduplicate_photos
from .metadata import (
    get_metadata,
    set_metadata,
    set_color_label,
    get_color_label,
    set_keywords,
    add_keyword,
    remove_keyword,
    get_all_keywords
)
from .export import export_gallery

__all__ = [
    "organize_clusters", 
    "OrganizeResult", 
    "set_rating", 
    "get_rating", 
    "deduplicate_photos",
    "get_metadata",
    "set_metadata",
    "set_color_label",
    "get_color_label",
    "set_keywords",
    "add_keyword",
    "remove_keyword",
    "get_all_keywords",
    "export_gallery",
]
