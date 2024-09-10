from database.btree import InsertReq
from database.btree import DeleteReq
from database.btree import BIter
from database.kvstore.kv import KVStore
from database.constants import CompareOP


class KVTX:
  def __init__(self) -> None:
    self.db: KVStore
    self.root: int
    self.head: int

  def get(self, key: bytes) -> bytes:
    return self.db.tree.get(key)

  def update(self, req: InsertReq) -> bool:
    self.db.tree.insert(req)
    return req.added

  def delete(self, req: DeleteReq) -> bool:
    return self.db.tree.delete(req)

  def seek(self, key: bytes, op: CompareOP) -> BIter:
    return BIter.seek(self.db.tree, key, op)
