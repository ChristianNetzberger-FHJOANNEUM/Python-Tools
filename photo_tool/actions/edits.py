"""
Photo Edits Actions
===================

Manage non-destructive edit metadata in JSON sidecars.
Completely isolated from existing metadata (rating, color, keywords).

Edit Structure:
{
    "edits": {
        "version": 1,
        "exposure": 0.5,
        "contrast": 15,
        "highlights": -20,
        "shadows": 30,
        "whites": 0,
        "blacks": 0,
        "applied": false,
        "edited_at": "2026-02-09T15:00:00Z",
        "edited_by": "Photo Tool v3.0"
    }
}
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


def get_sidecar_path(photo_path: str | Path) -> Path:
    """
    Get JSON sidecar path for photo.
    Matches existing sidecar logic in photo_tool.
    
    Args:
        photo_path: Path to photo file
        
    Returns:
        Path to JSON sidecar file
        
    Example:
        >>> get_sidecar_path('E:/Photos/P1012345.JPG')
        Path('E:/Photos/.P1012345.metadata.json')
    """
    photo_path = Path(photo_path)
    sidecar_name = f".{photo_path.stem}.metadata.json"
    return photo_path.parent / sidecar_name


def get_edits(photo_path: str | Path) -> Dict:
    """
    Load edit metadata from JSON sidecar.
    
    Args:
        photo_path: Path to photo file
        
    Returns:
        Dict with edit values, or empty dict if no edits exist
        
    Example:
        >>> edits = get_edits('photo.jpg')
        >>> print(edits.get('exposure', 0))
        0.5
    """
    sidecar_path = get_sidecar_path(photo_path)
    
    if not sidecar_path.exists():
        return {}
    
    try:
        with open(sidecar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Return edits dict, or empty if not present
        return data.get('edits', {})
    
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️  Error reading edits from {sidecar_path}: {e}")
        return {}


def set_edits(photo_path: str | Path, edits: Dict, merge: bool = True) -> bool:
    """
    Save edit metadata to JSON sidecar.
    Preserves existing metadata (rating, color, keywords, etc.).
    
    Args:
        photo_path: Path to photo file
        edits: Dict with edit values (exposure, contrast, etc.)
        merge: If True, merge with existing edits. If False, replace completely.
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> new_edits = {'exposure': 0.5, 'contrast': 15}
        >>> set_edits('photo.jpg', new_edits)
        True
    """
    sidecar_path = get_sidecar_path(photo_path)
    
    try:
        # Load existing sidecar data
        if sidecar_path.exists():
            with open(sidecar_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        
        # Merge or replace edits
        if merge and 'edits' in data:
            # Update existing edits
            existing_edits = data['edits']
            existing_edits.update(edits)
            existing_edits['edited_at'] = datetime.now().isoformat()
            data['edits'] = existing_edits
        else:
            # Create new edits entry
            data['edits'] = {
                'version': 1,
                **edits,
                'applied': False,
                'edited_at': datetime.now().isoformat(),
                'edited_by': 'Photo Tool v3.0'
            }
        
        # Write back to file
        with open(sidecar_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    
    except (OSError, json.JSONDecodeError) as e:
        print(f"❌ Error saving edits to {sidecar_path}: {e}")
        return False


def has_edits(photo_path: str | Path) -> bool:
    """
    Check if photo has any edits.
    
    Args:
        photo_path: Path to photo file
        
    Returns:
        True if photo has edits, False otherwise
    """
    edits = get_edits(photo_path)
    
    # Check if any non-metadata edit values exist
    edit_keys = ['exposure', 'contrast', 'highlights', 'shadows', 'whites', 'blacks']
    return any(edits.get(key, 0) != 0 for key in edit_keys)


def clear_edits(photo_path: str | Path) -> bool:
    """
    Remove all edits from photo (reset to defaults).
    Preserves other metadata.
    
    Args:
        photo_path: Path to photo file
        
    Returns:
        True if successful, False otherwise
    """
    sidecar_path = get_sidecar_path(photo_path)
    
    if not sidecar_path.exists():
        return True  # No edits to clear
    
    try:
        with open(sidecar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Remove edits key if exists
        if 'edits' in data:
            del data['edits']
            
            # Write back
            with open(sidecar_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    
    except (OSError, json.JSONDecodeError) as e:
        print(f"❌ Error clearing edits from {sidecar_path}: {e}")
        return False


def get_default_edits() -> Dict:
    """
    Get default edit values (all zeros).
    
    Returns:
        Dict with default edit values
    """
    return {
        'exposure': 0.0,
        'contrast': 0.0,
        'highlights': 0.0,
        'shadows': 0.0,
        'whites': 0.0,
        'blacks': 0.0
    }


# Standalone test
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python edits.py <photo_path>")
        print("\nCommands:")
        print("  python edits.py photo.jpg              # Show edits")
        print("  python edits.py photo.jpg set          # Set test edits")
        print("  python edits.py photo.jpg clear        # Clear edits")
        sys.exit(1)
    
    photo_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'show'
    
    print(f"\n📸 Photo: {photo_path}")
    print("=" * 60)
    
    if command == 'show':
        edits = get_edits(photo_path)
        
        if edits:
            print(f"\n✅ Photo has edits:")
            for key, value in edits.items():
                if key not in ['version', 'applied', 'edited_at', 'edited_by']:
                    print(f"  {key:12s}: {value:+.1f}" if isinstance(value, (int, float)) else f"  {key:12s}: {value}")
            
            if 'edited_at' in edits:
                print(f"\n📅 Last edited: {edits['edited_at']}")
        else:
            print(f"\n⚪ No edits (using defaults)")
    
    elif command == 'set':
        test_edits = {
            'exposure': 0.5,
            'contrast': 20,
            'shadows': 30,
            'highlights': -20
        }
        
        print(f"\n📝 Setting test edits:")
        for key, value in test_edits.items():
            print(f"  {key:12s}: {value:+.1f}")
        
        success = set_edits(photo_path, test_edits)
        
        if success:
            print(f"\n✅ Edits saved successfully!")
            sidecar = get_sidecar_path(photo_path)
            print(f"📁 Sidecar: {sidecar}")
        else:
            print(f"\n❌ Failed to save edits")
    
    elif command == 'clear':
        success = clear_edits(photo_path)
        
        if success:
            print(f"\n✅ Edits cleared!")
        else:
            print(f"\n❌ Failed to clear edits")
    
    else:
        print(f"\n❌ Unknown command: {command}")
        print("Available commands: show, set, clear")
