import math,random,json
from sqlalchemy import select,func
from src.config.database import Base,engine,Session
from src.models import User,PointSurvey,BoundaryPolicy,EnvelopeStudy,EnvelopeRun,FootprintReview,Report
from src.services.analysis import analyze
from src.utils.security import hash_password
from src.utils.time import now
from src.utils.serialization import serialize

def seed():
 Base.metadata.create_all(engine)
 with Session() as db:
  for role in ('admin','analyst','viewer'):
   if not db.get(User,role):db.add(User(id=role,email=role+'@lantu.demo',password=hash_password('Envelope2026!'),role=role))
  rng=random.Random(2408);groups=[]
  def make(id,name,xy):return {'group_id':id,'name':name,'points':[{'point_id':id+f'-P{i+1:03}','x':round(x,9),'y':round(y,9)} for i,(x,y) in enumerate(xy)]}
  def rotate(x,y,angle,ox,oy):c,s=math.cos(angle),math.sin(angle);return (ox+x*c-y*s,oy+x*s+y*c)
  local=[(-60,-8),(60,-8),(60,8),(-60,8)]+[(rng.uniform(-60,60),rng.uniform(-8,8)) for _ in range(116)];groups.append(make('G01','斜长带·30度投影足迹',[rotate(x,y,math.pi/6,5000,7000) for x,y in local]))
  local=[(0,0),(80,0),(80,15),(15,15),(15,70),(0,70)]
  for _ in range(114):local.append((rng.uniform(0,80),rng.uniform(0,15)) if rng.random()<.5 else (rng.uniform(0,15),rng.uniform(0,70)))
  groups.append(make('G02','L形·凹口被凸包填平',[rotate(x,y,-math.pi/18,5300,7100) for x,y in local]))
  local=[]
  for _ in range(100):angle=rng.uniform(0,2*math.pi);radius=math.sqrt(rng.random());local.append((5500+34*radius*math.cos(angle),7050+23*radius*math.sin(angle)))
  local+=local[:20];groups.append(make('G03','重复点·精确坐标去重',local));groups.append(make('G04','共线·不可伪造面',[(5700+i,7200+2*i) for i in range(120)]));groups.append(make('G05','单位置·120条同一点',[(5900.,7150.)]*120))
  if not db.get(PointSurvey,'demo-survey'):db.add(PointSurvey(id='demo-survey',name='岚图·五组局部米制采集足迹',source='lantu_local_footprints_20261112.json',coordinate_system='local_m',groups=groups,created_at=now()));db.flush()
  for id,name,mode in [('demo-policy','精确去重·最小方向同面积规则','exact'),('demo-reject','拒绝重复坐标·完整核验','reject')]:
   if not db.get(BoundaryPolicy,id):db.add(BoundaryPolicy(id=id,name=name,deduplication=mode,area_tie_relative=1e-12,algorithm_version='andrews-edge-enumeration-v1',created_at=now()))
  db.flush()
  if not db.get(EnvelopeStudy,'demo-study'):db.add(EnvelopeStudy(id='demo-study',name='五组足迹·三种包络比较',survey_id='demo-survey',policy_id='demo-policy',group_ids=[g['group_id'] for g in groups],snapshot={'survey':serialize(db.get(PointSurvey,'demo-survey')),'policy':serialize(db.get(BoundaryPolicy,'demo-policy'))},created_at=now()));db.flush()
  if not db.get(EnvelopeRun,'demo-run'):
   study=db.get(EnvelopeStudy,'demo-study');db.add(EnvelopeRun(id='demo-run',study_id='demo-study',status='completed',result=analyze(study.snapshot,study.group_ids),error='',created_at=now()));db.flush()
  if not db.get(FootprintReview,'demo-review'):db.add(FootprintReview(id='demo-review',run_id='demo-run',version=1,note='已核对local_m米制声明、原始点/精确去重计数与三种面积。凸包填凹口不代表真实覆盖，共线/单位置保留退化类型，不能伪造采集面。',decision='accepted',author='analyst@lantu.demo',created_at=now()));db.flush()
  if not db.get(Report,'demo-report'):db.add(Report(id='demo-report',run_id='demo-run',review_id='demo-review',title='岚图足迹·包络人工复核稿',published_by='admin@lantu.demo',created_at=now()))
  db.commit();return {m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in (User,PointSurvey,BoundaryPolicy,EnvelopeStudy,EnvelopeRun,FootprintReview,Report)}
if __name__=='__main__':print(json.dumps(seed(),ensure_ascii=False))
