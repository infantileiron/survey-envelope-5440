"""Enumerate every hull-edge orientation, O(h^2), not linear rotating calipers."""
import math
from src.services.hull import convex_hull,prepare

def axis_aligned(points):
 _,unique=prepare(points);xs=[p[0] for p in unique];ys=[p[1] for p in unique];x0,x1=min(xs),max(xs);y0,y1=min(ys),max(ys);w,h=x1-x0,y1-y0
 if w==0 and h==0:kind='point';corners=[[x0,y0]]
 elif w==0 or h==0:kind='line';corners=[[x0,y0],[x1,y1]]
 else:kind='polygon';corners=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]
 value=w*h
 if not math.isfinite(value):raise ValueError('axis box overflow')
 return {'geometry_type':kind,'corners':corners,'area':value,'width':w,'height':h,'perimeter':2*(w+h) if kind=='polygon' else None}

def minimum_rectangle(points,tie_relative=1e-12):
 if not math.isfinite(tie_relative) or not 0<=tie_relative<=1e-8:raise ValueError('invalid area tie tolerance')
 hull=convex_hull(points);vertices=hull['vertices'];kind=hull['geometry_type'];ox,oy=vertices[0];local=[(x-ox,y-oy) for x,y in vertices]
 if kind!='polygon':
  length=hull['line_length'] or 0.;angle=math.degrees(math.atan2(local[-1][1],local[-1][0]))%180 if kind=='line' else 0.
  return {'geometry_type':kind,'corners':vertices,'area':0.,'perimeter':None,'width':length,'height':0.,'angle_degrees':angle,'candidate_count':len(vertices),'method':'hull-edge enumeration O(h^2)','containment_max_violation_m':0.,'containment_tolerance_m':1e-8*max(1.,length),'tie_relative':tie_relative,'tie_rule':'degenerate line uses [0,180); point has no direction, angle0 is a display placeholder'}
 candidates=[]
 for i,p in enumerate(local):
  q=local[(i+1)%len(local)];angle=math.atan2(q[1]-p[1],q[0]-p[0])%(math.pi/2)
  if abs(angle-math.pi/2)<1e-14:angle=0.
  co,si=math.cos(angle),math.sin(angle);us=[x*co+y*si for x,y in local];vs=[-x*si+y*co for x,y in local];u0,u1=min(us),max(us);v0,v1=min(vs),max(vs);w,h=u1-u0,v1-v0;value=w*h
  if not math.isfinite(value):raise ValueError('oriented box overflow')
  corners=[[ox+u*co-v*si,oy+u*si+v*co] for u,v in ((u0,v0),(u1,v0),(u1,v1),(u0,v1))];first=min(range(4),key=lambda k:tuple(corners[k]));corners=corners[first:]+corners[:first]
  candidates.append({'angle':angle,'area':value,'width':w,'height':h,'corners':corners,'bounds':(u0,u1,v0,v1),'cos':co,'sin':si})
 minimum=min(c['area'] for c in candidates);tied=[c for c in candidates if c['area']-minimum<=tie_relative*max(1.,abs(minimum))];best=min(tied,key=lambda c:(c['angle'],c['corners']));co,si=best['cos'],best['sin'];u0,u1,v0,v1=best['bounds'];tol=1e-8*max(1.,best['width'],best['height']);violation=0.
 for x,y in points:
  x-=ox;y-=oy;u=x*co+y*si;v=-x*si+y*co;violation=max(violation,u0-u,u-u1,v0-v,v-v1)
 if violation>tol:raise ValueError('point containment certificate failed')
 return {'geometry_type':'polygon','corners':best['corners'],'area':best['area'],'perimeter':2*(best['width']+best['height']),'width':best['width'],'height':best['height'],'angle_degrees':math.degrees(best['angle']),'candidate_count':len(candidates),'method':'hull-edge enumeration O(h^2)','containment_max_violation_m':violation,'containment_tolerance_m':tol,'tie_relative':tie_relative,'tie_rule':'within tie_relative*max(1,min_area), then smallest canonical angle [0,90), then corners lexicographic'}
