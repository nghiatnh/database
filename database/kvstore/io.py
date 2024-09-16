import os
from typing import Literal, Optional
from pathlib import Path
from _pyio import FileIO


class FileHandler:
  def __init__(self, path: Path) -> None:
    self._path = path
    self._file: Optional[FileIO] = None

  @property
  def path(self) -> Path:
    return self._path

  @property
  def size(self) -> int:
    return os.stat(self.path).st_size

  @property
  def is_open(self) -> bool:
    return self._file is not None and not self._file.closed

  def open(self, mode: Literal["r+b", "wb"]) -> FileIO:
    if not self.is_open:
      self._file = FileIO(str(self.path), mode)
    return self._file

  def close(self) -> None:
    if self._file is not None:
      self._file.close()
      self._file = None

  def read(self, offset: int, size: int) -> bytes:
    assert self._file is not None
    assert offset <= self.size
    self._file.seek(offset)
    return self._file.read(size)

  def write(self, offset: int, data: bytes) -> None:
    assert self._file is not None
    assert offset <= self.size
    self._file.seek(offset)
    self._file.write(data)

  def flush(self) -> None:
    assert self._file is not None
    self._file.flush()

  def extend(self, size: int) -> None:
    assert self._file is not None
    self._file.truncate(size)
    self._file.flush()
