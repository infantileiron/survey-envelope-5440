import math,re

def validate_survey(groups):
 if not 1<=len(groups)<=8:raise ValueError('须1至8个点组')
 seen=set()
 for group in groups:
  key=group['group_id']
  if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,24}',key) or key in seen:raise ValueError('点组ID须唯一英数短ID')
  seen.add(key);ids=set()
  if not 1<=len(group['points'])<=300:raise ValueError('每组须1至300个原始点')
  for p in group['points']:
   if not p['point_id'] or p['point_id'] in ids:raise ValueError('点ID须在组内唯一，重复坐标按口径处理')
   ids.add(p['point_id'])
   if not all(math.isfinite(p[k]) and abs(p[k])<=1e9 for k in ('x','y')):raise ValueError('须有限局部米制坐标且绝对值不超过1e9')
 return True
