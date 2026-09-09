"""Strict portable file names and containment checks for local storage."""
from pathlib import Path

def filename(value: str) -> str:
    if (not value or value != value.strip() or Path(value).name != value
        or any(c in value for c in '/\\:\x00') or value in {'.', '..'}
        or value.endswith(('.', ' ')) or len(value) > 200
        or value.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(10)], *[f'LPT{i}' for i in range(10)]}):
        raise ValueError('Invalid filename')
    return value

def inside(root: Path, *parts: str) -> Path:
    root = root.resolve()
    result = root.joinpath(*(filename(p) for p in parts)).resolve()
    if not result.is_relative_to(root) or result == root:
        raise ValueError('Path is outside storage root')
    return result

def atomic_text(path: Path, content: str):
    """Readers see either the old complete file or the new complete file."""
    import os
    import tempfile
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         suffix='.tmp', delete=False, newline='') as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
