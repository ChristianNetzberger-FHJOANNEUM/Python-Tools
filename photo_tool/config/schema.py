"""
Configuration schema using Pydantic for validation
"""

from pathlib import Path
from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class WorkspaceConfig(BaseModel):
    """Workspace location and settings"""
    path: Path = Field(description="Workspace root directory")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        return Path(v).resolve()


class ScanConfig(BaseModel):
    """File scanning configuration"""
    roots: List[Path] = Field(
        default_factory=list,
        description="Source directories to scan for photos"
    )
    extensions: List[str] = Field(
        default=[".jpg", ".jpeg", ".png"],
        description="File extensions to include"
    )
    recurse: bool = Field(
        default=True,
        description="Scan subdirectories recursively"
    )
    
    @field_validator('roots')
    @classmethod
    def validate_roots(cls, v):
        return [Path(p).resolve() for p in v]
    
    @field_validator('extensions')
    @classmethod
    def normalize_extensions(cls, v):
        return [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in v]


class GroupingConfig(BaseModel):
    """Time-based grouping settings"""
    time_window_seconds: float = Field(
        default=3.0,
        ge=0.1,
        le=60.0,
        description="Maximum time gap to consider photos as burst"
    )
    max_group_gap_seconds: float = Field(
        default=2.0,
        ge=0.1,
        le=30.0,
        description="Maximum gap within a burst group"
    )


class SimilarityConfig(BaseModel):
    """Visual similarity detection settings"""
    method: Literal["phash", "dhash", "ahash"] = Field(
        default="phash",
        description="Hashing method for similarity"
    )
    phash_threshold: int = Field(
        default=6,
        ge=0,
        le=64,
        description="Maximum hash distance for similar photos (lower = stricter)"
    )
    use_ssim_refine: bool = Field(
        default=False,
        description="Use SSIM for refinement (slower but more accurate)"
    )
    ssim_threshold: float = Field(
        default=0.92,
        ge=0.0,
        le=1.0,
        description="SSIM threshold for similarity"
    )


class QualityConfig(BaseModel):
    """Photo quality analysis settings"""
    blur_method: Literal["laplacian", "variance"] = Field(
        default="laplacian",
        description="Method for blur detection"
    )
    blur_threshold: float = Field(
        default=120.0,
        ge=0.0,
        description="Blur threshold (higher = sharper)"
    )
    compute_histogram: bool = Field(
        default=True,
        description="Compute exposure histogram"
    )


class ActionsConfig(BaseModel):
    """Actions and organization settings"""
    dry_run: bool = Field(
        default=True,
        description="Preview changes without applying them"
    )
    burst_folder_naming: Literal["first_filename", "timestamp", "sequential"] = Field(
        default="first_filename",
        description="How to name burst folders"
    )
    min_group_size: int = Field(
        default=2,
        ge=2,
        description="Minimum photos in a group to create folder"
    )


class PhotoToolConfig(BaseModel):
    """Main configuration for Photo Tool"""
    workspace: WorkspaceConfig
    scan: ScanConfig = Field(default_factory=ScanConfig)
    grouping: GroupingConfig = Field(default_factory=GroupingConfig)
    similarity: SimilarityConfig = Field(default_factory=SimilarityConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    actions: ActionsConfig = Field(default_factory=ActionsConfig)
    
    # New: Project-based folder management
    folders: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Workspace folders with metadata (path, enabled, counts)"
    )
    
    class Config:
        validate_assignment = True
