"""合并运行/重试/恢复/不覆盖语义的单元测试（仅标准库 + fakes，无需 MySQL/Redis）。"""
import os,sys,types,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','..','..','backend'))
sys.path.insert(0,os.path.dirname(__file__))
import fakes
from fakes import FakeDB,HTTPException,IntegrityError,install_model_attrs

import src.config.database as database
from src.models import EnvelopeRun,EnvelopeStudy,FootprintReview,Report
from src.services import runs as runs_service
from src.utils import serialization

install_model_attrs()
database.Session=FakeDB  # worker 与审计之外的会话入口

def make_study(db,sid='study-1'):
 db.add(EnvelopeStudy(id=sid,name='研究'+sid,survey_id='sv',policy_id='po',
  group_ids=['G01'],snapshot={'k':'v'},created_at='t0'))
 return sid

class SerializeTests(unittest.TestCase):
 def test_serialize_includes_new_columns(self):
  db=FakeDB();sid=make_study(db)
  out=runs_service.create(db,sid)
  self.assertEqual(set(out),{'id','study_id','status','result','error','attempts','created_at','updated_at'})
  self.assertEqual(out['attempts'],1)
  self.assertEqual(out['status'],'queued')
  self.assertEqual(out['updated_at'],out['created_at'])

class CreateMergeTests(unittest.TestCase):
 def setUp(self):
  fakes.FakeRedis.reset();self.db=FakeDB();self.sid=make_study(self.db)
 def test_concurrent_calls_merge_to_single_run_and_single_queue_message(self):
  first=runs_service.create(self.db,self.sid)
  second=runs_service.create(self.db,self.sid)
  third=runs_service.create(self.db,self.sid)
  self.assertEqual(first['id'],second['id'])
  self.assertEqual(second['id'],third['id'])
  self.assertEqual(len(self.db.store[EnvelopeRun]),1)
  # Redis 仅入队一次：重复提交不产生重复队列消息
  self.assertEqual(fakes.FakeRedis.queues[runs_service.QUEUE_KEY],[first['id']])
 def test_completed_run_is_returned_not_recomputed(self):
  out=runs_service.create(self.db,self.sid)
  run=self.db.get(EnvelopeRun,out['id'])
  run.status='completed';run.result={'groups':[],'checksum':'keep-me'}
  again=runs_service.create(self.db,self.sid)
  self.assertEqual(again['id'],out['id'])
  self.assertEqual(again['status'],'completed')
  self.assertEqual(again['result']['checksum'],'keep-me')
  self.assertEqual(fakes.FakeRedis.queues[runs_service.QUEUE_KEY],[out['id']])
 def test_failed_run_requires_retry_endpoint(self):
  out=runs_service.create(self.db,self.sid)
  run=self.db.get(EnvelopeRun,out['id']);run.status='failed';run.error='计算异常X'
  with self.assertRaises(HTTPException) as ctx:runs_service.create(self.db,self.sid)
  self.assertEqual(ctx.exception.status_code,409)
  self.assertIn('重试',ctx.exception.detail)
 def test_unknown_study_404(self):
  with self.assertRaises(HTTPException) as ctx:runs_service.create(self.db,'nope')
  self.assertEqual(ctx.exception.status_code,404)
 def test_redis_down_marks_failed_and_keeps_reason(self):
  import redis as redis_mod
  old=redis_mod.Redis;redis_mod.Redis=fakes._DownRedis
  try:
   with self.assertRaises(HTTPException) as ctx:runs_service.create(self.db,self.sid)
   self.assertEqual(ctx.exception.status_code,503)
  finally:redis_mod.Redis=old
  run=next(iter(self.db.store[EnvelopeRun].values()))
  self.assertEqual(run.status,'failed');self.assertIn('队列不可用',run.error)
 def test_race_integrity_error_returns_existing_run(self):
  # 模拟并发事务：另一请求已提交同一研究的运行；本事务的存在性查询未命中，
  # 提交时唯一约束报错，回滚后重新读取到对方的运行
  winner=EnvelopeRun(id='winner',study_id=self.sid,status='queued',result={},error='',
   attempts=1,created_at='t1',updated_at='t1')
  self.db.add(winner);self.db.commit()
  self.db.hide_next_scalar_model=EnvelopeRun  # 存在性查询阶段看不到对方的行
  self.db.fail_next_commit_integrity=True
  out=runs_service.create(self.db,self.sid)
  self.assertGreaterEqual(self.db.rollback_calls,1)
  self.assertEqual(out['id'],'winner')
  self.assertEqual(len(self.db.store[EnvelopeRun]),1)

class RetryTests(unittest.TestCase):
 def setUp(self):
  fakes.FakeRedis.reset();self.db=FakeDB();self.sid=make_study(self.db)
 def _failed_run(self,reason='计算异常Y'):
  out=runs_service.create(self.db,self.sid)
  fakes.FakeRedis.queues[runs_service.QUEUE_KEY].clear()  # 首条消息已被worker消费后才失败
  run=self.db.get(EnvelopeRun,out['id']);run.status='failed';run.error=reason
  return run
 def test_retry_keeps_failure_reason_until_success_and_increments_attempts(self):
  run=self._failed_run()
  retried=runs_service.retry(self.db,run.id)
  self.assertEqual(retried['status'],'queued')
  self.assertEqual(retried['attempts'],2)
  # 重试期间失败原因仍然保留可查
  self.assertEqual(self.db.get(EnvelopeRun,run.id).error,'计算异常Y')
  self.assertEqual(fakes.FakeRedis.queues[runs_service.QUEUE_KEY].count(run.id),1)
 def test_retry_unknown_404(self):
  with self.assertRaises(HTTPException) as ctx:runs_service.retry(self.db,'ghost')
  self.assertEqual(ctx.exception.status_code,404)
 def test_retry_on_inflight_merges(self):
  out=runs_service.create(self.db,self.sid)  # queued
  again=runs_service.retry(self.db,out['id'])
  self.assertEqual(again['id'],out['id']);self.assertEqual(again['attempts'],1)
 def test_retry_on_completed_is_refused(self):
  out=runs_service.create(self.db,self.sid)
  run=self.db.get(EnvelopeRun,out['id']);run.status='completed';run.result={'checksum':'z'}
  with self.assertRaises(HTTPException) as ctx:runs_service.retry(self.db,run.id)
  self.assertEqual(ctx.exception.status_code,409)
  self.assertEqual(run.result,{'checksum':'z'})
 def test_second_retry_attempts_three(self):
  run=self._failed_run()
  runs_service.retry(self.db,run.id)
  run.status='failed';run.error='再次失败'
  out=runs_service.retry(self.db,run.id)
  self.assertEqual(out['attempts'],3)
  self.assertEqual(self.db.get(EnvelopeRun,run.id).error,'再次失败')

class WorkerTests(unittest.TestCase):
 def setUp(self):
  fakes.FakeRedis.reset();self.db=FakeDB();self.sid=make_study(self.db)
  database.Session=lambda: self.db
  import src.worker as worker
  self.worker=worker
  worker.Session=lambda: self.db
  worker.client=fakes.FakeRedis()
  self._analyze=worker.analyze
 def tearDown(self):self.worker.analyze=self._analyze
 def _enqueue(self):
  out=runs_service.create(self.db,self.sid)
  fakes.FakeRedis.queues[runs_service.QUEUE_KEY].clear()  # 服务端已入队，worker测试自行控制
  return self.db.get(EnvelopeRun,out['id'])
 def test_execute_completes_and_clears_error(self):
  run=self._enqueue()  # queued，带着上一轮失败原因重试的场景
  run.error='旧原因'
  fakes.FakeRedis.queues[runs_service.QUEUE_KEY].append(run.id)
  self.worker.analyze=lambda snap,gids:{'groups':[],'checksum':'new'}
  self.worker.execute(run.id)
  self.assertEqual(run.status,'completed');self.assertEqual(run.result['checksum'],'new')
  self.assertEqual(run.error,'');self.assertEqual(run.attempts,1)
 def test_duplicate_delivery_never_overwrites_completed_result(self):
  run=self._enqueue();run.status='completed';run.result={'checksum':'frozen'};run.error=''
  self.worker.analyze=lambda *a:self.fail('成功结果不应被重新计算')
  self.worker.execute(run.id)  # 队列重复投递
  self.worker.execute(run.id)
  self.assertEqual(run.result,{'checksum':'frozen'});self.assertEqual(run.status,'completed')
 def test_failure_records_reason_and_can_retry(self):
  run=self._enqueue()
  def boom(snap,gids):raise RuntimeError('几何计算失败')
  self.worker.analyze=boom
  self.worker.execute(run.id)
  self.assertEqual(run.status,'failed');self.assertIn('几何计算失败',run.error)
  # 通过服务重试后再次成功
  runs_service.retry(self.db,run.id)
  self.worker.analyze=lambda snap,gids:{'checksum':'ok'}
  self.worker.execute(run.id)
  self.assertEqual(run.status,'completed');self.assertEqual(run.error,'');self.assertEqual(run.attempts,2)
 def test_recovery_requeues_unfinished_only(self):
  running=self._enqueue();running.status='running'
  sid2=make_study(self.db,'study-2')
  out2=runs_service.create(self.db,sid2)
  done=self.db.get(EnvelopeRun,out2['id']);done.status='completed';done.result={'checksum':'d'}
  fakes.FakeRedis.reset()
  self.worker.recover()
  q=fakes.FakeRedis.queues[runs_service.QUEUE_KEY]
  self.assertIn(running.id,q);self.assertNotIn(done.id,q)
  self.assertEqual(len(q),1)
 def test_completed_run_with_review_archive_stays_intact(self):
  run=self._enqueue();run.status='completed';run.result={'checksum':'archived'}
  self.db.add(FootprintReview(id='rv',run_id=run.id,version=1,note='n',decision='accepted',
   author='a@x',created_at='t'))
  self.db.add(Report(id='rp',run_id=run.id,review_id='rv',title='t',published_by='admin',created_at='t'))
  self.worker.analyze=lambda *a:self.fail('归档运行不可重算')
  self.worker.execute(run.id)
  self.assertEqual(run.result,{'checksum':'archived'})
  self.assertTrue(self.db.get(Report,'rp'))
  self.assertEqual(self.db.get(FootprintReview,'rv').run_id,run.id)

class DistinctStudyTests(unittest.TestCase):
 def test_different_group_selection_or_policy_studies_each_get_own_run(self):
  fakes.FakeRedis.reset();db=FakeDB()
  make_study(db,'s-a');make_study(db,'s-b')
  a=runs_service.create(db,'s-a');b=runs_service.create(db,'s-b')
  self.assertNotEqual(a['id'],b['id'])
  self.assertEqual(len(db.store[EnvelopeRun]),2)
  self.assertEqual(sorted(fakes.FakeRedis.queues[runs_service.QUEUE_KEY]),sorted([a['id'],b['id']]))

if __name__=='__main__':
 unittest.main(verbosity=2)
