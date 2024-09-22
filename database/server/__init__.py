import os
import random
from fastapi import FastAPI


from database.btree import SetRequest
from database.kvstore import KVTX
from database.kvstore import KVStore

app = FastAPI()

kv = KVStore("test")
kv.open()


@app.get("/read")
def _read():
  tx = KVTX()
  kv.begin_read(tx)
  try:
    i = random.randint(0, 9)
    res = tx.get(str(i).encode() * 1000)
  finally:
    kv.end_read(tx)
  return res.decode() if res is not None else "None"


@app.get("/write")
def _write():
  tx = KVTX()
  kv.begin(tx)
  try:
    i = random.randint(0, 9)
    tx.set(SetRequest(str(i).encode() * 1000, str(i).encode() * 3000))
    kv.commit(tx)
  except Exception as e:
    kv.rollback(tx)
    raise e
  return "Done"
