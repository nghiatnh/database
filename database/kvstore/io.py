import os
from typing import Literal, Optional
from pathlib import Path
from _pyio import FileIO


class FileHandler:
  """
  FileHandler
  ===========
  FileHandler class is a wrapper around the FileIO class that provides a
  simple interface for reading and writing files.
  """

  def __init__(self, path: Path) -> None:
    self._path = path
    self._file: Optional[FileIO] = None

  @property
  def path(self) -> Path:
    """
    The path of the file.
    """
    return self._path

  @property
  def size(self) -> int:
    """
    The size of the file in bytes.
    """
    return os.stat(self.path).st_size

  @property
  def is_open(self) -> bool:
    """
    Check if the file is open.
    """
    return self._file is not None and not self._file.closed

  def open(self, mode: Literal["r+b", "wb"]) -> FileIO:
    """
    Open the file in the given mode.
    """
    if not self.is_open:
      self._file = FileIO(str(self.path), mode)
    return self._file

  def close(self) -> None:
    """
    Close the file.
    """
    if self._file is not None:
      self._file.close()
      self._file = None

  def read(self, offset: int, size: int) -> bytes:
    """
    Read the data from the file at the given offset and size in bytes.
    """
    assert self._file is not None
    assert offset <= self.size
    self._file.seek(offset)
    return self._file.read(size)

  def write(self, offset: int, data: bytes) -> None:
    """
    Write the data to the file at the given offset.
    """
    assert self._file is not None
    assert offset <= self.size
    self._file.seek(offset)
    self._file.write(data)

  def flush(self) -> None:
    """
    Flush the data to the file.
    """
    assert self._file is not None
    self._file.flush()

  def extend(self, size: int) -> None:
    """
    Extend the file to the given size in bytes.
    """
    assert self._file is not None
    self._file.truncate(size)
    self._file.flush()
