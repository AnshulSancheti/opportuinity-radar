"""Run inside the local backend container; redirect SQL to a private ignored file."""
import json,sys,uuid
from datetime import datetime,timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Account,Article,Hackathon,UserAction,ScrapeRun


def literal(value):
    if value is None:return 'NULL'
    if isinstance(value,datetime):value=value.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
    elif isinstance(value,(list,dict)):value=json.dumps(value,ensure_ascii=False,separators=(',',':'))
    elif isinstance(value,uuid.UUID):value=str(value)
    elif isinstance(value,(int,float)):return str(value)
    return "'"+str(value).replace("'","''")+"'"

counts={}
with SessionLocal() as db:
    for model in [Account,Article,Hackathon,UserAction,ScrapeRun]:
        query=select(model.__table__)
        if model==UserAction:query=query.where(model.item_type.in_(['article','hackathon']),model.action.in_(['saved','applied']))
        if model==ScrapeRun:query=query.where(model.module.in_(['news','hackathons']))
        rows=db.execute(query).mappings().all();counts[model.__tablename__]=len(rows)
        for row in rows:
            cols=list(row)
            print(f"INSERT INTO {model.__tablename__} ({','.join(cols)}) VALUES ({','.join(literal(row[c]) for c in cols)});")
print(json.dumps(counts),file=sys.stderr)
