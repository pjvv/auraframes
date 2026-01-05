"""File I/O utilities for the Aura Frames client."""
import json
import os
from collections.abc import Sequence

from loguru import logger
from pydantic import BaseModel

from auraframes.exceptions import AuraError


class IOError(AuraError):
    """Raised when file I/O operations fail."""
    pass


def build_path(*args: str, make_dir: bool = True) -> str:
    """
    Join path components and optionally create parent directories.

    :param args: Path components to join
    :param make_dir: If True, create parent directories (default True)
    :return: The joined path
    :raises IOError: If directory creation fails
    """
    path = os.path.join(*args)
    if make_dir:
        parent_dir = os.path.dirname(path)
        if parent_dir:
            try:
                os.makedirs(parent_dir, exist_ok=True)
            except PermissionError as e:
                raise IOError(f"Permission denied creating directory '{parent_dir}': {e}") from e
            except OSError as e:
                raise IOError(f"Failed to create directory '{parent_dir}': {e}") from e
    return path


def write_model(model: BaseModel | Sequence[BaseModel], path: str) -> None:
    """
    Write a Pydantic model or sequence of models to a JSON file.

    :param model: A single model or sequence of models to serialize
    :param path: File path to write to
    :raises IOError: If file write fails
    """
    try:
        with open(path, 'w') as out:
            if isinstance(model, Sequence) and not isinstance(model, BaseModel):
                json.dump([m.model_dump(mode='json') for m in model], out, indent=2)
            else:
                json.dump(model.model_dump(mode='json'), out, indent=2)
        logger.debug(f"Wrote model data to {path}")
    except PermissionError as e:
        raise IOError(f"Permission denied writing to '{path}': {e}") from e
    except OSError as e:
        raise IOError(f"Failed to write to '{path}': {e}") from e


def read_model_json(path: str) -> dict | list:
    """
    Read JSON data from a file.

    :param path: File path to read from
    :return: Parsed JSON data
    :raises IOError: If file read fails
    :raises ValueError: If JSON is invalid
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise IOError(f"File not found: '{path}'") from e
    except PermissionError as e:
        raise IOError(f"Permission denied reading '{path}': {e}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in '{path}': {e}") from e
    except OSError as e:
        raise IOError(f"Failed to read '{path}': {e}") from e
