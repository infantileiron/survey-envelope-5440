import uuid
import redis
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from src.models import EnvelopeRun,EnvelopeStudy
from src.config.settings import REDIS_URL
from src.utils.time import now
from src.utils.serialization import serialize

QUEUE_KEY='survey-envelope:jobs'

def _enqueue(run):
 try:
  redis.Redis.from_url(REDIS_URL).lpush(QUEUE_KEY,run.id)
 except redis.RedisError:
  run.status='failed';run.error='队列不可用，请稍后重试';run.updated_at=now()
  return False
 return True

def _get_study_lock(db,study_id):
 study=db.scalar(select(EnvelopeStudy).where(EnvelopeStudy.id==study_id).with_for_update())
 if not study:raise HTTPException(404,"包络研究不存在")
 return study

def create(db,study_id):
 # 锁定研究行：同一研究的并发提交在此串行，合并为同一次计算
 _get_study_lock(db,study_id)
 existing=db.scalar(select(EnvelopeRun).where(EnvelopeRun.study_id==study_id))
 if existing:
  if existing.status in ('queued','running'):return serialize(existing) # 已有在途计算，合并请求
  if existing.status=='completed':return serialize(existing) # 成功结果不重算、不覆盖
  raise HTTPException(409,'该研究上次计算失败，失败原因已保留，请调用重试接口发起重算')
 stamp=now()
 item=EnvelopeRun(id=str(uuid.uuid4()),study_id=study_id,status='queued',result={},error='',attempts=1,created_at=stamp,updated_at=stamp)
 db.add(item)
 try:db.commit()
 except IntegrityError:
  db.rollback()
  raced=db.scalar(select(EnvelopeRun).where(EnvelopeRun.study_id==study_id))
  if raced:return serialize(raced)
  raise
 if not _enqueue(item):
  db.commit();raise HTTPException(503,item.error)
 return serialize(item)

def retry(db,run_id):
 run=db.get(EnvelopeRun,run_id)
 if not run:raise HTTPException(404,'运行不存在')
 # 与 create 相同的加锁顺序（先研究后运行），避免交叉加锁死锁
 _get_study_lock(db,run.study_id)
 run=db.get(EnvelopeRun,run_id)
 if run.status in ('queued','running'):return serialize(run) # 已在计算中，重试请求合并
 if run.status=='completed':raise HTTPException(409,'运行已成功完成，结果与复核归档不可覆盖')
 # 仅 failed 可重试：保留 error 中的失败原因直至重算成功，attempts 记录尝试次数
 run.status='queued';run.attempts=(run.attempts or 0)+1;run.updated_at=now()
 db.commit()
 if not _enqueue(run):
  db.commit();raise HTTPException(503,run.error)
 return serialize(run)

def require_completed(db,id):
 item=db.get(EnvelopeRun,id)
 if not item:raise HTTPException(404,'运行不存在')
 if item.status!='completed':raise HTTPException(409,'运行尚未成功完成')
 return item
