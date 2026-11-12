import uuid
from fastapi import HTTPException
from sqlalchemy import select
from src.models import BoundaryPolicy
from src.utils.serialization import serialize
from src.utils.time import now

def create(db,payload):
 if db.scalar(select(BoundaryPolicy).where(BoundaryPolicy.name==payload.name)):raise HTTPException(409,'包络口径名称已存在')
 item=BoundaryPolicy(id=str(uuid.uuid4()),created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
