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
  def db(self, db: KVStore) -> None:
    ...

  @property
  def root(self) -> int:
    ...

  @root.setter
  def root(self, root: int) -> None:
    ...

  @property
  def head(self) -> int:
    ...

  @head.setter
  def head(self, head: int) -> None:
    ...


class DatabaseTX(Protocol):
  @property
  def kv(self) -> KVTX:
    ...

  @property
  def db(self) -> Database:
    ...

  @db.setter
  def db(self, db: Database) -> None:
    ...
