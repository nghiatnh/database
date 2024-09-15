import os
from typing import Optional
from _pyio import FileIO


class FileHandler:
  """
  FileHandler
  ===========
  FileHandler class provides methods to read, write, and extend a file. It
  requires the path to the file.
  """

  def __init__(self, path: str):
    self._path = path
    self._file: Optional[FileIO] = None

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def path(self) -> str:
    """
    Returns the path of the file.
    """
    return self._path

  @property
  def is_open(self) -> bool:
    """
    Returns True if the file is open, False otherwise.
    """
    return self._file is not None and not self._file.closed

  @property
  def size(self) -> int:
    """
    Returns the size of the file in bytes.
    """
    assert self._file is not None
    return os.fstat(self._file.fileno()).st_size

  def open(self, mode: str):
    """
    Opens the file in the given mode.
    """
    if not self.is_open:
      self._file = FileIO(self._path, mode)

  def close(self):
    """
    Closes the file.
    """
    if self._file is not None:
      self._file.close()

  def read(self, offset: int, size: int) -> bytes:
    """
    Reads the data from the file at the given offset and size in bytes.
    """
    assert self._file is not None
    assert size > 0
    self._file.seek(offset)
    res = self._file.read(size)
    assert res is not None
    return res

  def write(self, offset: int, data: bytes):
    """
    Writes the data to the file at the given offset.
    """
    assert self._file is not None
    self._file.seek(offset)
    self._file.write(data)

  def extend(self, size: int):
    """
    Extends the file to the given size in bytes.
    """
    assert self._file is not None
    self._file.seek(0)
    self._file.truncate(size)

  def flush(self):
    """
    Flushes the file.
    """
    assert self._file is not None
    self._file.flush()
