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
  res = QLExecutor(db).execute(req.query)
  if res is None:
    return "Done"
  return res.dump()
