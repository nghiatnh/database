from typing import Optional

from database.kvstore import KVStore
from database.protocol import KVTX
from database.protocol import DatabaseTX


class TransactionError(Exception):
  pass


class Database:
  def __init__(self, path: str) -> None:
    self.path = path
    self.kv = KVStore(path)
    self.tx: Optional[KVTX] = None

  def open(self):
    self.kv.open()

  def close(self):
    self.kv.close()

  def begin(self, tx: DatabaseTX):
    tx.db = self
    self.tx = self.kv.begin(tx.kv)

  def commit(self, tx: DatabaseTX):
    if self.tx is None:
      raise TransactionError("no transaction")
    self.kv.commit(tx.kv)

  def abort(self, tx: DatabaseTX):
    if self.tx is None:
      raise TransactionError("no transaction")
    self.kv.abort(tx.kv)
