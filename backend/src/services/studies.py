import uuid
from fastapi import HTTPException
from sqlalchemy import select
from src.models import PointSurvey,BoundaryPolicy,EnvelopeStudy
from src.utils.serialization import serialize
from src.utils.time import now

def create(db,payload):
 survey=db.get(PointSurvey,payload.survey_id);policy=db.get(BoundaryPolicy,payload.policy_id)
 if not survey or not policy:raise HTTPException(404,'足迹测组或包络口径不存在')
 if len(set(payload.group_ids))!=len(payload.group_ids) or not set(payload.group_ids)<={g['group_id'] for g in survey.groups}:raise HTTPException(422,'选择点组ID须唯一且全部存在，源数据不会因选择而丢失')
 if db.scalar(select(EnvelopeStudy).where(EnvelopeStudy.name==payload.name)):raise HTTPException(409,'包络研究名称已存在')
 item=EnvelopeStudy(id=str(uuid.uuid4()),snapshot={'survey':serialize(survey),'policy':serialize(policy)},created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
