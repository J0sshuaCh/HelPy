# Changelog

## [0.3.0] - 2026-06-12

### Added
- Integration test suite for all LLM providers (`tests/test_providers.py`)
- `.env.template` with documented environment variables for development
- Automated release workflow via GitHub Actions (`.github/workflows/release.yml`)
- `flask` and `waitress` as explicit project dependencies for Local provider

### Changed
- Default Google model updated from `gemini-2.0-flash` to `gemini-3.1-flash-lite`
- Model download path centralized in `path_utils.writable_models_dir()`
- Model ID placeholder in UI reflects current Google model

### Fixed
- Inference server path in development mode (`llm_client.py:106`): `.parents[1]` → `.parent` — Local provider no longer crashes in dev
- `_local_error` not reset on successful Local server start — stale errors no longer persist across reloads

## [0.2.0] - 2026-05-?? (Initial release)
