# Development Guide

Guide for developers working on Photo Tool.

## Setup Development Environment

### Prerequisites
- Python 3.10+
- Git
- pip

### Installation

```bash
# Clone repository
git clone <repository-url>
cd Python-tools

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install in development mode with all dependencies
pip install -e ".[dev,gui,server]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=photo_tool --cov-report=html

# Run specific test file
pytest tests/test_time_grouping.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black photo_tool tests

# Lint with Ruff
ruff check photo_tool tests

# Type checking with mypy
mypy photo_tool
```

### Running CLI During Development

```bash
# Run without installing
python -m photo_tool.cli.main --help

# Or use installed command
photo-tool --help
```

## Project Structure

```
photo_tool/
├── cli/              # Command-line interface
├── config/           # Configuration system
├── workspace/        # Workspace management
├── io/               # File I/O and EXIF
├── analysis/         # Photo analysis algorithms
├── actions/          # Organization operations
├── report/           # Report generation
├── editing/          # Image editing (future)
├── ui/               # GUI components (future)
└── util/             # Utilities
```

## Adding New Features

### Adding a New Analysis Method

1. Create module in `photo_tool/analysis/similarity/`:

```python
# photo_tool/analysis/similarity/my_method.py

def compute_my_score(image_path: Path) -> float:
    """Your analysis method"""
    pass
```

2. Export in `__init__.py`:

```python
# photo_tool/analysis/similarity/__init__.py
from .my_method import compute_my_score
```

3. Add to clustering pipeline:

```python
# photo_tool/analysis/clustering.py
scores = {}
for photo in photos:
    scores[photo] = compute_my_score(photo)
```

4. Add tests:

```python
# tests/test_my_method.py
def test_compute_my_score():
    score = compute_my_score(test_image)
    assert score > 0
```

### Adding a New CLI Command

1. Create command in `photo_tool/cli/`:

```python
# photo_tool/cli/commands_myfeature.py

import typer
app = typer.Typer()

@app.command()
def my_command(
    param: str = typer.Option("default", "--param", help="Description")
):
    """Command description"""
    console.print(f"Running with {param}")
```

2. Register in main CLI:

```python
# photo_tool/cli/main.py
from . import commands_myfeature

app.add_typer(
    commands_myfeature.app, 
    name="myfeature", 
    help="My feature"
)
```

3. Test manually:

```bash
photo-tool myfeature my-command --param test
```

### Adding Configuration Options

1. Update schema:

```python
# photo_tool/config/schema.py

class MyFeatureConfig(BaseModel):
    enabled: bool = Field(default=True)
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)

class PhotoToolConfig(BaseModel):
    # ... existing ...
    my_feature: MyFeatureConfig = Field(default_factory=MyFeatureConfig)
```

2. Update defaults:

```yaml
# photo_tool/config/defaults.yaml
my_feature:
  enabled: true
  threshold: 0.5
```

## Code Style

### Python Style
- Follow PEP 8
- Use type hints
- Max line length: 100 characters
- Use `black` for formatting

### Docstrings
Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Short description of function
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Naming Conventions
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

## Testing Guidelines

### Writing Tests

```python
# tests/test_feature.py

import pytest
from photo_tool.analysis import my_function

def test_basic_functionality():
    """Test description"""
    result = my_function(input_data)
    assert result == expected_output

def test_edge_case():
    """Test edge case"""
    with pytest.raises(ValueError):
        my_function(invalid_input)

@pytest.fixture
def sample_photos():
    """Fixture for test photos"""
    return [Path("test1.jpg"), Path("test2.jpg")]
```

### Test Organization
- One test file per module
- Group related tests in classes
- Use fixtures for setup
- Mock file I/O when possible

## Debugging

### Enable Debug Logging

```bash
# CLI
photo-tool --debug scan

# In code
from photo_tool.util.logging import setup_logging
setup_logging(level="DEBUG")
```

### Using Rich Inspect

```python
from rich import inspect

# Inspect any object
inspect(my_object)
inspect(my_object, methods=True)
```

### Performance Profiling

```python
from photo_tool.util.timing import timer

with timer("Operation name"):
    # ... code to profile ...
```

## Common Tasks

### Update Dependencies

```bash
# Update all dependencies
pip install --upgrade pip setuptools wheel
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade pillow
```

### Generate Documentation

```bash
# Install sphinx (if needed)
pip install sphinx sphinx-rtd-theme

# Generate docs
cd docs
make html
```

### Release Checklist

- [ ] Update version in `photo_tool/__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run all tests
- [ ] Run linters
- [ ] Update documentation
- [ ] Create git tag
- [ ] Build package: `python -m build`
- [ ] Upload to PyPI: `twine upload dist/*`

## Git Workflow

### Branch Naming
- Feature: `feature/description`
- Bugfix: `fix/description`
- Hotfix: `hotfix/description`
- Release: `release/v1.0.0`

### Commit Messages
Follow conventional commits:

```
feat: add new similarity method
fix: correct EXIF reading for Lumix S5
docs: update installation guide
test: add tests for clustering
refactor: simplify time grouping logic
perf: optimize hash computation
```

### Pull Request Process
1. Create feature branch
2. Write tests
3. Update documentation
4. Run tests and linters
5. Create PR with description
6. Wait for review
7. Merge to main

## Performance Guidelines

### Optimization Tips
1. Cache expensive operations
2. Use generators for large datasets
3. Batch database operations
4. Profile before optimizing
5. Consider multiprocessing for CPU-bound tasks

### Example: Batch Processing

```python
from itertools import islice

def batch_process(photos, batch_size=1000):
    """Process photos in batches"""
    it = iter(photos)
    while batch := list(islice(it, batch_size)):
        # Process batch
        yield process_batch(batch)
```

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Reinstall in development mode
pip install -e .
```

**Test failures:**
```bash
# Clear pytest cache
pytest --cache-clear
```

**OpenCV issues:**
```bash
# Reinstall OpenCV
pip uninstall opencv-python
pip install opencv-python
```

## Resources

- [Python Style Guide](https://pep8.org/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

## Getting Help

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [GETTING_STARTED.md](GETTING_STARTED.md) for usage
- Open an issue on GitHub
- Join discussions

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.
