import uuid,csv,io,json
from sqlalchemy import select
from fastapi import HTTPException
from src.models import Report,FootprintReview,EnvelopeRun
from src.services.runs import require_completed
from src.utils.serialization import serialize
from src.utils.time import now

def create(db,payload,user):
 require_completed(db,payload.run_id);db.scalar(select(EnvelopeRun).where(EnvelopeRun.id==payload.run_id).with_for_update())
 review=db.scalar(select(FootprintReview).where(FootprintReview.run_id==payload.run_id).order_by(FootprintReview.version.desc()))
 if not review or review.decision!='accepted':raise HTTPException(409,'最新足迹复核须接受后才能归档')
 if db.scalar(select(Report).where(Report.review_id==review.id)):raise HTTPException(409,'此复核版本已归档')
 item=Report(id=str(uuid.uuid4()),review_id=review.id,published_by=user['email'],created_at=now(),**payload.model_dump());db.add(item);db.commit();return serialize(item)
def export(db,id):
 report=db.get(Report,id)
 if not report:raise HTTPException(404,'归档不存在')
 result=require_completed(db,report.run_id).result;review=db.get(FootprintReview,report.review_id);buf=io.StringIO();writer=csv.DictWriter(buf,['run_id','checksum','review_version','group_id','coordinate_system','method','geometry_type','area_m2','perimeter_m','line_length_m','input_count','unique_count','duplicate_count','vertices_json']);writer.writeheader()
 for group in result['groups']:
  for method in ('hull','axis_box','oriented_box'):
   obj=group[method];writer.writerow({'run_id':report.run_id,'checksum':result['checksum'],'review_version':review.version,'group_id':group['group_id'],'coordinate_system':'local_m','method':method,'geometry_type':obj['geometry_type'],'area_m2':obj['area'],'perimeter_m':obj.get('perimeter'),'line_length_m':obj.get('line_length'),'input_count':group['hull']['input_count'],'unique_count':group['hull']['unique_count'],'duplicate_count':group['hull']['duplicate_count'],'vertices_json':json.dumps(obj.get('vertices',obj.get('corners')),ensure_ascii=False)})
 return chr(0xfeff)+buf.getvalue()
