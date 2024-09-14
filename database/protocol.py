from typing import Protocol


class KVStore(Protocol):
  ...


class Database(Protocol):
  ...


class KVTX(Protocol):
  @property
  def db(self) -> KVStore:
    ...

  @db.setter
  def db(self, db: KVStore):
    ...

  @property
  def root(self) -> int:
    ...

  @root.setter
  def root(self, root: int):
    ...

  @property
  def head(self) -> int:
    ...

  @head.setter
  def head(self, head: int):
    ...


class DatabaseTX(Protocol):
  @property
  def kv(self) -> KVTX:
    ...

  @property
  def db(self) -> Database:
    ...

  @db.setter
  def db(self, db: Database):
    ...
