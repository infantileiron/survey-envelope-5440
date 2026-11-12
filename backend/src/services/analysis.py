import json,hashlib
from src.services.hull import convex_hull
from src.services.rectangle import minimum_rectangle,axis_aligned

def analyze(snapshot,group_ids):
 survey=snapshot['survey'];policy=snapshot['policy'];output=[]
 for group in sorted(survey['groups'],key=lambda g:g['group_id']):
  if group['group_id'] not in group_ids:continue
  points=[[p['x'],p['y']] for p in group['points']];hull=convex_hull(points,policy['deduplication']=='exact');box=minimum_rectangle(points,policy['area_tie_relative']);axis=axis_aligned(points)
  output.append({'group_id':group['group_id'],'name':group['name'],'raw_points':group['points'],'hull':hull,'oriented_box':box,'axis_box':axis,'axis_reduction_fraction':None if axis['area']==0 else (axis['area']-box['area'])/axis['area'],'box_to_hull_ratio':None if hull['area']==0 else box['area']/hull['area']})
 data={'snapshot':snapshot,'group_ids':sorted(group_ids)}
 return {'groups':output,'policy':policy,'coordinate_system':survey['coordinate_system'],'source_group_count':len(survey['groups']),'selected_group_ids':sorted(group_ids),'checksum':hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'assumptions':['坐标必须声明local_m，单位米；不把经纬度度数当米，不执行投影变换。二维图使用统一x/y比例。','Andrew单调链，精确浮点坐标去重或reject重复；原始点不删改，公开输入/唯一/重复计数。','面积先平移局部原点再shoelace，避免大绝对坐标的乘积抵消；周长单位m，面积单位m²。','定向框枚举凸包每条边方向，O(h²)，不是线性旋转卡尺；polygon同面积容差内按最小[0,90)方向及角点字典序选择。','线方向为[0,180)，点无方向；点或共线凸包/定向框返回point/line、面积0，周长null，线另报line_length；不伪造polygon或分母0占比。','凸包填平凹口，轴框/凸包/定向框面积是三种包络，不代表真实采集覆盖、地籍或地理边界。']}
