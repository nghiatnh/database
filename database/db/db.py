from typing import Optional

from database.kvstore import KVStore
from database.protocol import KVTX
from database.protocol import DatabaseTX


class TransactionError(Exception):
  """
  TransactionError
  ================
  TransactionError class represents an exception raised when there is an error
  in the transaction.
  """


class Database:
  """
  Database
  ========
  Database class represents the database. It provides methods to open and close
  the database, begin and commit transactions.
  """

  def __init__(self, path: str):
    self.path = path
    self.kv = KVStore(path)
    self.tx: Optional[KVTX] = None

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def open(self):
    """
    Opens the database.
    """
    self.kv.open()

  def close(self):
    """
    Closes the database.
    """
    self.kv.close()

  def begin(self, tx: DatabaseTX):
    """
    Begins the transaction.
    """
    tx.db = self
    self.tx = self.kv.begin(tx.kv)

  def commit(self, tx: DatabaseTX):
    """
    Commits the transaction. It writes the changes made during the transaction
    to the file.
    """
    if self.tx is None:
      raise TransactionError("no transaction")
    self.kv.commit(tx.kv)

  def abort(self, tx: DatabaseTX):
    """
    Aborts the transaction. It discards the changes made during the transaction.
    """
    if self.tx is None:
      raise TransactionError("no transaction")
    self.kv.abort(tx.kv)
