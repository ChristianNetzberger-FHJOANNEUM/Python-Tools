"""
Project management for Photo Tool
Allows saving and loading photo selections with export settings
"""

from .manager import ProjectManager, Project
from .project_sidecar import ProjectSidecarManager

__all__ = ['ProjectManager', 'Project', 'ProjectSidecarManager']
