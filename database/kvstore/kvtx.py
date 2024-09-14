from database.btree import InsertReq
from database.btree import DeleteReq
from database.btree import BIter
from database.kvstore.kv import KVStore
from database.constants import CompareOP


class KVTX:
  """
  KVTX
  ====
  KVTX class represents the KVStore transaction. It provides methods to get,
  update, and delete key-value pairs from the database.
  """

  def __init__(self):
    self.db: KVStore
    self.root: int
    self.head: int

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  def get(self, key: bytes) -> bytes:
    """
    Returns the value for the given key.
    """
    return self.db.tree.get(key)

  def update(self, req: InsertReq) -> bool:
    """
    Inserts or updates the key-value pair in the database.
    """
    self.db.tree.insert(req)
    return req.added

  def delete(self, req: DeleteReq) -> bool:
    """
    Deletes the key-value pair from the database for the given key.
    """
    return self.db.tree.delete(req)

  def seek(self, key: bytes, op: CompareOP) -> BIter:
    """
    Seeks the key in the database and returns an iterator.
    """
    return BIter.seek(self.db.tree, key, op)
