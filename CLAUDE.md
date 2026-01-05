# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Unofficial Python client for the Aura Frames (PUSHD) API. This library reverse-engineers and implements the mobile app's API interactions for programmatic photo frame management.

## Running the Project

```bash
# Install dependencies
uv sync

# Run main entry point
uv run python main.py

# Run TUI
uv run python -m auraframes.tui

# Run tests
uv run pytest

# Type checking
uv run mypy auraframes/
```

## Environment Variables

Required for authentication:
- `AURA_EMAIL` - Account email
- `AURA_PASSWORD` - Account password

Optional configuration:
- `AURA_DEBUG` - Enable debug logging (default: `false`)
- `AURA_LOCALE` - Device locale (default: `en-US`)
- `AURA_DEVICE_IDENTIFIER` - Device ID to mimic (default: `0000000000000000`)
- `AURA_APP_IDENTIFIER` - App identifier (default: `com.pushd.client`)
- `AURA_IMAGE_PROXY_URL` - Image proxy URL (default: `https://imgproxy.pushd.com`)

AWS (required for upload functionality):
- `AWS_UPLOAD_IDENTITY_POOL_ID` - Cognito pool for S3 uploads
- `AWS_SQS_IDENTITY_POOL_ID` - Cognito pool for SQS

Supports `.env` file via Pydantic Settings. See [`.env.example`](.env.example) for all options.

## Architecture

### Core Components

**`Aura` class** (`auraframes/aura.py`) - Main orchestrator that:
- Initializes all API clients with a shared HTTP client
- Handles authentication flow via `login()`
- Provides high-level operations: `dump_frame()`, `get_all_assets()`, `caption_album()`, `download_images_from_assets()`

**`Client`** (`auraframes/client.py`) - HTTP/2 client wrapper using httpx:
- Base URL: `https://api.pushd.com/v5`
- Maintains request history and handles cookies
- Supports per-request timeout override
- All API classes receive this shared client instance

### API Layer (`auraframes/api/`)

All API classes inherit from `BaseApi` and use the shared `Client`:
- `AccountApi` - Authentication
- `FrameApi` - Frame management, asset selection, activities
- `AssetApi` - Asset batch operations
- `ActivityApi` - Activity feed
- `PlaylistApi` - Album/playlist management
- `AttachmentApi` - Captions and attachments

### Services Layer (`auraframes/services/`)

Business logic extracted from API layer:
- `ImageService` - Bulk image downloads with EXIF writing
- `CaptionService` - Album captioning with progress tracking

### AWS Integration (`auraframes/aws/`)

Uses AWS Cognito Identity Pools for unauthenticated access:
- **AWSClient** - Base class with credential expiration tracking and auto-refresh
- **S3Client** - Image uploads to `images.senseapp.co` bucket
- **SQSClient** - Queue polling for frame updates

### Models (`auraframes/models/`)

Pydantic models for API responses: `Asset`, `Frame`, `User`, `Activity`, `Meta`, `Attachment`

### Utilities (`auraframes/utils/`)

- `settings.py` - Pydantic Settings configuration with `.env` support
- `pagination.py` - Async pagination with retry support
- `retry.py` - Exponential backoff retry decorator
- `validation.py` - Shared validation utilities
- `io.py` - File I/O helpers
- `dt.py` - Date/time utilities

### Key Flows

**Image Upload** (see README.md for full sequence):
1. Create asset with `local_identifier`
2. Call `select_asset` twice with SQS poll between
3. Upload to S3, get filename and MD5
4. Call `batch_update` with asset metadata

**Image Download/Export** (`auraframes/export.py`):
- Fetches from image proxy: `https://imgproxy.pushd.com/{user_id}/{filename}`
- Writes EXIF data (location, timestamps) via `ExifWriter`
- Thread-safe geocoding cache with LRU eviction

**Album Captioning** (`auraframes/services/caption_service.py`):
- Fetches all assets in playlist
- Deletes existing captions
- Creates new attachments with optional date suffix

## Testing

- 125 tests in `tests/` directory
- Uses pytest-asyncio for async tests
- Uses respx for HTTP mocking
- All tests passing, mypy clean

## Code Quality

- Full type annotations throughout
- Pydantic v2 models with validation
- Custom exceptions in `auraframes/exceptions.py`
- Loguru for structured logging
