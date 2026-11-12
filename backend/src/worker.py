from pathlib import Path
import redis,traceback
from sqlalchemy import select
from src.config.settings import REDIS_URL
from src.config.database import Session
from src.models import EnvelopeRun,EnvelopeStudy
from src.services.analysis import analyze
from src.utils.time import now
client=redis.Redis.from_url(REDIS_URL);heartbeat=Path('/artifacts/worker-heartbeat')
QUEUE_KEY='survey-envelope:jobs'
def execute(id):
 with Session() as db:
  run=db.get(EnvelopeRun,id)
  # 重复投递：已成功的结果与复核归档绝不覆盖；其它终态也不重复执行
  if not run or run.status not in ('queued','running'):return
  run.status='running';run.updated_at=now();db.commit()
  try:
   study=db.get(EnvelopeStudy,run.study_id)
   result=analyze(study.snapshot,study.group_ids)
   # 提交前再次确认未被其它路径终态化（单worker下为防御性检查）
   db.refresh(run)
   if run.status!='running':return
   run.result=result;run.status='completed';run.error='';run.updated_at=now()
  except Exception as e:
   db.rollback()
   run=db.get(EnvelopeRun,id)
   if run and run.status in ('queued','running'):
    run.error=str(e);run.status='failed';run.updated_at=now();traceback.print_exc()
  db.commit()
def recover():
 # 中断恢复：worker重启时把未完成的运行重新入队；completed/failed 保持不动，成功结果不重算
 with Session() as db:
  for id in db.scalars(select(EnvelopeRun.id).where(EnvelopeRun.status.in_(['queued','running']))):
   client.lpush(QUEUE_KEY,id)
def main():
 recover()
 while True:
  heartbeat.touch();job=client.brpop(QUEUE_KEY,timeout=1)
  if job:execute(job[1].decode())
if __name__=='__main__':main()
