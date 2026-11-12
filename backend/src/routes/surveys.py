from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy import select
from src.config.database import db_session
from src.controllers.auth import current_user,writer,admin
from src.models import PointSurvey
from src.schemas.survey import SurveyInput
from src.services import surveys as service
from src.utils.serialization import rows,serialize
router=APIRouter(prefix='/surveys')
@router.get('')
def listing(db=Depends(db_session),user=Depends(current_user)):return rows(db.scalars(select(PointSurvey).order_by(PointSurvey.created_at.desc())))
@router.post('')
def create(payload:SurveyInput,db=Depends(db_session),user=Depends(writer)):return service.create(db,payload)
