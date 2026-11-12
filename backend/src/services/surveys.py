import uuid
from fastapi import HTTPException
from sqlalchemy import select
from src.models import PointSurvey
from src.services.validation import validate_survey
from src.utils.serialization import serialize
from src.utils.time import now

def create(db,payload):
 data=payload.model_dump()
 try:validate_survey(data['groups'])
 except ValueError as e:raise HTTPException(422,str(e))
 if db.scalar(select(PointSurvey).where(PointSurvey.name==payload.name)):raise HTTPException(409,'足迹测组名称已存在')
 item=PointSurvey(id=str(uuid.uuid4()),created_at=now(),**data);db.add(item);db.commit();return serialize(item)
