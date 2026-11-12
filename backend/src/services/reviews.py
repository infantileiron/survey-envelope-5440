import uuid
from sqlalchemy import select,func
from src.models import FootprintReview,EnvelopeRun
from src.services.runs import require_completed
from src.utils.serialization import serialize
from src.utils.time import now

def create(db,payload,user):
 require_completed(db,payload.run_id);db.scalar(select(EnvelopeRun).where(EnvelopeRun.id==payload.run_id).with_for_update())
 version=(db.scalar(select(func.max(FootprintReview.version)).where(FootprintReview.run_id==payload.run_id)) or 0)+1
 item=FootprintReview(id=str(uuid.uuid4()),version=version,author=user['email'],created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
