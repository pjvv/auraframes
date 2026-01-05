"""Tests for I/O utilities."""
import json
import os
import tempfile
from pathlib import Path

import pytest
from pydantic import BaseModel

from auraframes.utils.io import build_path, write_model, read_model_json, IOError


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""
    id: str
    name: str
    value: int | None = None


class TestBuildPath:
    """Tests for build_path function."""

    def test_join_paths(self):
        """Should join path components."""
        result = build_path("/base", "sub", "file.txt", make_dir=False)
        assert result == "/base/sub/file.txt"

    def test_creates_directory(self):
        """Should create parent directories when make_dir=True."""
        with tempfile.TemporaryDirectory() as tmp:
            path = build_path(tmp, "new_dir", "file.txt", make_dir=True)
            assert os.path.exists(os.path.dirname(path))

    def test_no_create_directory(self):
        """Should not create directories when make_dir=False."""
        with tempfile.TemporaryDirectory() as tmp:
            path = build_path(tmp, "nonexistent", "file.txt", make_dir=False)
            assert not os.path.exists(os.path.dirname(path))

    def test_handles_existing_directory(self):
        """Should not fail when directory already exists."""
        with tempfile.TemporaryDirectory() as tmp:
            # First call creates directory
            path1 = build_path(tmp, "existing", "file1.txt", make_dir=True)
            # Second call should not fail
            path2 = build_path(tmp, "existing", "file2.txt", make_dir=True)
            assert os.path.exists(os.path.dirname(path1))
            assert os.path.exists(os.path.dirname(path2))


class TestWriteModel:
    """Tests for write_model function."""

    def test_write_single_model(self):
        """Should write single model to JSON file."""
        model = SampleModel(id="123", name="test", value=42)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            write_model(model, path)
            with open(path) as f:
                data = json.load(f)
            assert data == {"id": "123", "name": "test", "value": 42}
        finally:
            os.unlink(path)

    def test_write_model_list(self):
        """Should write list of models to JSON file."""
        models = [
            SampleModel(id="1", name="first"),
            SampleModel(id="2", name="second", value=100),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            write_model(models, path)
            with open(path) as f:
                data = json.load(f)
            assert len(data) == 2
            assert data[0] == {"id": "1", "name": "first", "value": None}
            assert data[1] == {"id": "2", "name": "second", "value": 100}
        finally:
            os.unlink(path)

    def test_write_permission_error(self):
        """Should raise IOError on permission denied."""
        model = SampleModel(id="123", name="test")

        # Try to write to a non-writable location
        with pytest.raises(IOError, match="Permission denied|Failed to write"):
            write_model(model, "/root/not_allowed.json")


class TestReadModelJson:
    """Tests for read_model_json function."""

    def test_read_dict(self):
        """Should read JSON object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            path = f.name

        try:
            data = read_model_json(path)
            assert data == {"key": "value"}
        finally:
            os.unlink(path)

    def test_read_list(self):
        """Should read JSON array."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([1, 2, 3], f)
            path = f.name

        try:
            data = read_model_json(path)
            assert data == [1, 2, 3]
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        """Should raise IOError for missing file."""
        with pytest.raises(IOError, match="File not found"):
            read_model_json("/nonexistent/path/file.json")

    def test_invalid_json(self):
        """Should raise ValueError for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json {")
            path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                read_model_json(path)
        finally:
            os.unlink(path)
