"""Andrew monotone chain, exact-coordinate deduplication, translated shoelace."""
import math

def prepare(points,deduplicate=True):
 if not points:raise ValueError('point set must not be empty')
 output=[]
 for p in points:
  if len(p)!=2 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in p):raise ValueError('finite x/y pairs required')
  output.append((float(p[0]),float(p[1])))
 unique=sorted(set(output))
 if not deduplicate and len(unique)!=len(output):raise ValueError('重复坐标被当前reject口径拒绝；可新建exact去重口径，不修改原始点')
 return output,unique

def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])

def area(vertices):
 if len(vertices)<3:return 0.0
 x0,y0=vertices[0];local=[(x-x0,y-y0) for x,y in vertices];value=abs(math.fsum(local[i][0]*local[(i+1)%len(local)][1]-local[(i+1)%len(local)][0]*local[i][1] for i in range(len(local))))/2
 if not math.isfinite(value):raise ValueError('area overflow')
 return value

def convex_hull(points,deduplicate=True):
 original,unique=prepare(points,deduplicate)
 if len(unique)<=1:vertices=unique
 else:
  lower=[]
  for p in unique:
   while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
   lower.append(p)
  upper=[]
  for p in reversed(unique):
   while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
   upper.append(p)
  vertices=lower[:-1]+upper[:-1]
 kind='point' if len(vertices)==1 else 'line' if len(vertices)==2 else 'polygon';length=0. if kind=='point' else math.dist(vertices[0],vertices[1]) if kind=='line' else None
 perimeter=math.fsum(math.dist(vertices[i],vertices[(i+1)%len(vertices)]) for i in range(len(vertices))) if kind=='polygon' else None
 if perimeter is not None and not math.isfinite(perimeter):raise ValueError('perimeter overflow')
 return {'geometry_type':kind,'vertices':[list(p) for p in vertices],'area':area(vertices),'perimeter':perimeter,'line_length':length,'input_count':len(original),'unique_count':len(unique),'duplicate_count':len(original)-len(unique),'orientation':'CCW polygon; lexicographic first vertex; no repeated closure'}
