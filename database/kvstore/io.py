import os
from typing import Optional
from _pyio import FileIO


class FileHandler:
  def __init__(self, path: str) -> None:
    self._path = path
    self._file: Optional[FileIO] = None

  @property
  def path(self) -> str:
    return self._path

  def open(self, mode: str) -> None:
    self._file = FileIO(self._path, mode)

  def close(self) -> None:
    if self._file is not None:
      self._file.close()

  def read(self, offset: int, size: int) -> bytes:
    assert self._file is not None
    self._file.seek(offset)
    res = self._file.read(size)
    assert res is not None
    return res

  def write(self, offset: int, data: bytes) -> None:
    assert self._file is not None
    self._file.seek(offset)
    self._file.write(data)

  def size(self) -> int:
    assert self._file is not None
    return os.fstat(self._file.fileno()).st_size

  def extend(self, size: int) -> None:
    assert self._file is not None
    self._file.seek(0)
    self._file.truncate(size)

  def flush(self) -> None:
    assert self._file is not None
    self._file.flush()
