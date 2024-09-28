from fastapi import FastAPI
from pydantic import BaseModel

from database.db import Database
from database.ql import QLExecutor

app = FastAPI()


class QueryRequest(BaseModel):
  query: str


db = Database("database.db")
db.open()


@app.post("/query")
def _query(req: QueryRequest):
  try:
    res = QLExecutor(db).execute(req.query)
  except Exception as e:
    return {"error": str(e)}
  if res is None:
    return []
  return res.dump()
