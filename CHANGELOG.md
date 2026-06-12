# Changelog

## [0.4.0] - 2026-06-12

### Added
- Animated collapse functionality and new light themes for improved UI experience
- `reload_icons` method for dynamic icon updates across UI components

### Fixed
- Groq client initialization with optional HTTP client for better connection handling

## [0.3.0] - 2026-06-12

### Added
- Integration test suite for all LLM providers (`tests/test_providers.py`)
- `.env.template` with documented environment variables for development
- Automated release workflow via GitHub Actions (`.github/workflows/release.yml`)
- `flask` and `waitress` as explicit project dependencies for Local provider
- New path utilities module (`path_utils.py`) for centralized model download path
- PyInstaller spec file (`ayudin.spec`) for reproducible builds

### Changed
- Default Google model updated from `gemini-2.0-flash` to `gemini-3.1-flash-lite`
- Model download path centralized in `path_utils.writable_models_dir()`
- Model ID placeholder in UI reflects current Google model
- UI components refactored: `overlay_window` and `script_window` extracted into modular packages
- Dependencies consolidated into `pyproject.toml` as single source of truth
- Build-backend updated from legacy to `setuptools.build_meta`
- `download_model.py` moved to `scripts/` directory
- `test_run.py` moved to `tests/` directory
- `README.md` updated with application overview, features, and installation instructions

### Fixed
- Inference server path in development mode (`llm_client.py:106`): `.parents[1]` → `.parent` — Local provider no longer crashes in dev
- `_local_error` not reset on successful Local server start — stale errors no longer persist across reloads
- CI workflow issues resolved with proper build configuration

### Removed
- Stale `.bak` files from git tracking; `*.bak` added to `.gitignore`
- `.vscode/settings.json` from version control
- Empty `app/recordings/` directory
- Redundant `package.json` (Python project, not Node.js)

## [0.2.0] - 2026-06-06

### Added
- Theme support with customizable palettes and dynamic styling in OverlayWindow and ScriptWindow
- Script loading for multiple file formats: Markdown (`.md`), PDF (`.pdf`), and plain text (`.txt`)
- PDF and Markdown viewing capabilities in ScriptWindow with opacity control and drag support
- Draggable headers with opacity control in OverlayWindow and ScriptWindow
- Installation and run scripts for Windows (`.bat`) and Unix/macOS (`.sh`) environments
- `package.json` with cross-platform installation and start scripts
- `.env.example` with environment variable documentation
- Model download script (excludes heavy model from repository)
- Environment management configuration (`.gitignore` for `.env`)

### Changed
- OverlayWindow and ScriptWindow layout and styling: position adjustments, enhanced opacity controls
- Improved script window layout with better positioning and styling

## [0.1.0] - 2026-05-25

### Added
- Initial project setup and module initialization
- Main application interface with overlay and script windows
- Audio capture from microphone and system audio in parallel
- `DualChannelTranscriber` for simultaneous audio transcription
- Window visibility toggle functionality
- UI settings and audio capture configuration

### Changed
- Transcription system updated from initial implementation
- Audio processing and transcription pipeline refactored
- Window layout and transcription field adjustments in the UI
- Requirements reorganized and settings updated for environment management
