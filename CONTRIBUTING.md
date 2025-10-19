# Contributing to Halloween LEDs

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"  # Install with development extras
   ```

## Project Structure

```
halloween_leds/
├── halloween_leds/       # Main package
│   ├── __init__.py
│   ├── music_sync.py     # Music synchronization
│   └── wled_preset_uploader.py
├── docs/                 # Documentation
├── presets/             # WLED preset files
├── scripts/             # Build and utility scripts
├── tests/              # Test files
└── pyproject.toml      # Project configuration
```

## Pull Request Process

1. Create a new branch for your feature
2. Update documentation as needed
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for functions and classes
- Keep functions focused and small

## Testing

Run tests with:
```bash
pytest
```

## Building

Build process:
```bash
python scripts/build.py clean   # Clean old builds
python scripts/build.py all     # Build everything
```

## Release Process

1. Update version in:
   - pyproject.toml
   - halloween_leds/__init__.py
2. Update CHANGELOG.md
3. Create release branch
4. Build and test release
5. Create GitHub release
6. Upload artifacts
