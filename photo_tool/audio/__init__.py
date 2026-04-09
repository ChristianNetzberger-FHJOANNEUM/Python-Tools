"""Audio library access (workspace-scoped paths, browse, playlist helpers)."""

from .access import (
    AUDIO_EXTENSIONS,
    audio_roots_for_workspace,
    match_audio_root,
    resolve_path_under_audio_roots,
    resolve_dir_under_audio_roots,
    list_audio_directory,
    validate_playlist_paths,
    normalize_playlist_from_request,
    playlist_from_paths,
    guess_mimetype,
)

__all__ = [
    "AUDIO_EXTENSIONS",
    "audio_roots_for_workspace",
    "match_audio_root",
    "resolve_path_under_audio_roots",
    "resolve_dir_under_audio_roots",
    "list_audio_directory",
    "validate_playlist_paths",
    "normalize_playlist_from_request",
    "playlist_from_paths",
    "guess_mimetype",
]
