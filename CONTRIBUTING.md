# Contributing to Photo Tool

Thank you for considering contributing to Photo Tool! This document provides guidelines and instructions for contributing.

## Ways to Contribute

### 1. Report Bugs
- Search existing issues first
- Use the bug report template
- Include:
  - OS and Python version
  - Steps to reproduce
  - Expected vs actual behavior
  - Error messages and logs
  - Sample photos (if safe to share)

### 2. Suggest Features
- Search existing issues/discussions
- Use the feature request template
- Explain:
  - Use case and motivation
  - Proposed solution
  - Alternatives considered
  - Example usage

### 3. Improve Documentation
- Fix typos and unclear wording
- Add examples and tutorials
- Translate documentation
- Create video tutorials

### 4. Submit Code
- Bug fixes
- New features
- Performance improvements
- Tests
- Refactoring

## Getting Started

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/Python-tools.git
cd Python-tools

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/Python-tools.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e ".[dev]"

# Verify installation
photo-tool --version
```

### 3. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/my-feature

# Or bug fix branch
git checkout -b fix/bug-description
```

## Development Workflow

### 1. Write Code

Follow the [DEVELOPMENT.md](DEVELOPMENT.md) guide:
- Use type hints
- Follow PEP 8 style
- Add docstrings
- Keep functions small and focused

### 2. Write Tests

```bash
# Create test file
tests/test_my_feature.py

# Run tests
pytest tests/test_my_feature.py

# Check coverage
pytest --cov=photo_tool.my_module
```

### 3. Format and Lint

```bash
# Format code
black photo_tool tests

# Lint
ruff check photo_tool tests

# Fix auto-fixable issues
ruff check --fix photo_tool tests
```

### 4. Update Documentation

- Update docstrings
- Update relevant .md files
- Add examples if needed

### 5. Commit Changes

Use conventional commits:

```bash
git add .
git commit -m "feat: add new feature"
# or
git commit -m "fix: correct bug in module"
# or
git commit -m "docs: update README"
```

**Commit Message Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `style`: Code style (formatting)
- `chore`: Maintenance tasks

### 6. Push and Create PR

```bash
# Push to your fork
git push origin feature/my-feature

# Go to GitHub and create Pull Request
```

## Pull Request Guidelines

### PR Checklist

- [ ] Tests pass locally (`pytest`)
- [ ] Code is formatted (`black`)
- [ ] Code is linted (`ruff`)
- [ ] Docstrings added/updated
- [ ] Type hints added
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] PR description explains changes
- [ ] Linked to relevant issues

### PR Description Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Screenshots (if applicable)

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted and linted
```

### Review Process

1. Automated checks run (tests, linting)
2. Maintainer reviews code
3. Feedback and discussion
4. Revisions if needed
5. Approval and merge

## Code Style

### Python Style Guide

```python
# Good
def process_photos(
    photos: List[Path],
    threshold: float = 0.5
) -> List[PhotoCluster]:
    """
    Process photos and create clusters
    
    Args:
        photos: List of photo paths
        threshold: Similarity threshold
        
    Returns:
        List of photo clusters
    """
    clusters = []
    for photo in photos:
        # Process each photo
        cluster = analyze_photo(photo, threshold)
        clusters.append(cluster)
    return clusters
```

### Naming Conventions

```python
# Classes
class PhotoCluster:
    pass

# Functions and variables
def compute_similarity(photo1, photo2):
    similarity_score = 0.0
    return similarity_score

# Constants
MAX_CLUSTER_SIZE = 100
DEFAULT_THRESHOLD = 0.5

# Private methods
class MyClass:
    def _internal_method(self):
        pass
```

### Import Organization

```python
# Standard library
import os
from pathlib import Path
from typing import List, Optional

# Third-party
import numpy as np
from PIL import Image

# Local
from ..util.logging import get_logger
from .clustering import PhotoCluster
```

## Testing Guidelines

### Test Structure

```python
def test_feature_basic_case():
    """Test basic functionality"""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected_output

def test_feature_edge_case():
    """Test edge case"""
    with pytest.raises(ValueError):
        my_function(invalid_input)
```

### Test Coverage

- Aim for >80% coverage
- Test happy path and edge cases
- Test error handling
- Use fixtures for common setup

### Running Tests Locally

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_my_feature.py::test_function_name

# Run with coverage
pytest --cov=photo_tool --cov-report=html

# View coverage report
open htmlcov/index.html  # or start htmlcov/index.html on Windows
```

## Documentation Guidelines

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int = 10) -> bool:
    """
    One-line summary
    
    More detailed description if needed. Can span
    multiple lines.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When param2 is negative
        
    Example:
        >>> my_function("test", 5)
        True
    """
    pass
```

### README Updates

When adding features:
1. Update feature list
2. Add usage examples
3. Update screenshots if applicable

## Performance Guidelines

### Optimization Rules

1. **Measure first**: Profile before optimizing
2. **Cache expensive operations**: Hashes, thumbnails
3. **Use generators**: For large datasets
4. **Batch operations**: Database and file I/O
5. **Consider complexity**: O(n) > O(n log n) > O(n²)

### Example: Efficient Processing

```python
# Good - Generator
def process_photos_lazy(photos):
    for photo in photos:
        yield process_single_photo(photo)

# Better for large datasets
from itertools import islice

def batch_process(photos, batch_size=1000):
    it = iter(photos)
    while batch := list(islice(it, batch_size)):
        yield process_batch(batch)
```

## Release Process

### For Maintainers

1. **Update versions**:
   - `photo_tool/__init__.py`
   - `pyproject.toml`

2. **Update CHANGELOG.md**:
   - Move "Unreleased" to new version
   - Add release date

3. **Create release commit**:
   ```bash
   git commit -am "Release v0.2.0"
   ```

4. **Tag release**:
   ```bash
   git tag -a v0.2.0 -m "Version 0.2.0"
   git push origin main --tags
   ```

5. **Build and publish**:
   ```bash
   python -m build
   twine upload dist/*
   ```

6. **Create GitHub release**:
   - Go to GitHub Releases
   - Create new release from tag
   - Copy CHANGELOG entry
   - Attach built artifacts

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the issue, not the person
- Respect different viewpoints

### Communication

- **Issues**: Bug reports, feature requests
- **Discussions**: Questions, ideas, help
- **Pull Requests**: Code contributions
- **Email**: Security issues only

### Getting Help

- Read documentation first
- Search existing issues
- Ask in discussions
- Be specific and provide context
- Include error messages and logs

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md (alphabetically)
- GitHub contributors page
- Release notes
- Project README

Thank you for contributing! 🎉
