"""Stdlib-only fakes for SQLAlchemy / redis / FastAPI so service/worker logic can run
without third-party packages. Not part of the application; test support only."""
import sys,types,json,datetime

# ---------- SQLAlchemy fake ----------
class _Marker:
 def __init__(self,*args,**kw):self.args=args;self.kw=kw
 def __getattr__(self,name):return _Marker()
class _Column(_Marker):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.default=kw.get('default')
class _Meta(type):
 def __new__(mcs,name,bases,ns):
  columns={}
  annotations=ns.get('__annotations__',{})
  for key,val in list(ns.items()):
   if isinstance(val,_Column):columns[key]=val
  cls=super().__new__(mcs,name,bases,ns)
  cls.__columns__=dict(getattr(cls,'__columns__',{}),**columns)
  cls.__annotations__=annotations
  return cls
class _Base(metaclass=_Meta):
 def __init__(self,**kw):
  for key,col in type(self).__columns__.items():
   val=kw.pop(key,_undefined)
   if val is _undefined:
    d=col.default
    val=d() if callable(d) else (d if d is not None else None)
   setattr(self,key,val)
  if kw:raise TypeError('unknown fields %r'%list(kw))
class _Undefined:pass
_undefined=_Undefined()

def _make(name):
 def f(*a,**k):return _Column(*a,**k)
 return f
String=Double=Integer=Text=ForeignKey=UniqueConstraint=_make('x')
def JSON(*a,**k):return _Column(*a,**k)
class _Mapped:
 def __getitem__(self,item):return item
Mapped=_Mapped()
def mapped_column(*a,**k):return _Column(*a,**k)

class _Select:
 def __init__(self,entity):self.entity=entity;self.filters=[];self.locked=False;self.order=None
 def where(self,*f):self.filters.extend(f);return self
 def with_for_update(self):self.locked=True;return self
 def order_by(self,*a):self.order=a;return self
def select(entity):return _Select(entity)
class _Func:
 def max(self,col):return ('max',col)
 def count(self,*a):return ('count',)+a
func=_Func()
class IntegrityError(Exception):pass
class _Orm(types.ModuleType):
 Mapped=Mapped;mapped_column=mapped_column;DeclarativeBase=_Base;declarative_base=lambda:_Base;sessionmaker=lambda *a,**k:None
class _Exc(types.ModuleType):
 IntegrityError=IntegrityError
class _Types(types.ModuleType):
 class TypeDecorator:pass
 class LONGTEXT:pass
class _Dialects(types.ModuleType):pass
class _Mysql(types.ModuleType):LONGTEXT=_Types.LONGTEXT
class _DialectMysql(types.ModuleType):pass
sa=types.ModuleType('sqlalchemy');sa.String=String;sa.Double=Double;sa.Integer=Integer
sa.JSON=JSON;sa.ForeignKey=ForeignKey;sa.Text=Text;sa.UniqueConstraint=UniqueConstraint
sa.select=select;sa.func=func;sa.create_engine=lambda *a,**k:None;sa.text=lambda s:s
sa_orm=_Orm('sqlalchemy.orm');sa_exc=_Exc('sqlalchemy.exc');sa_types=_Types('sqlalchemy.types')
sa_dialects=_Dialects('sqlalchemy.dialects');sa_mysql=_Mysql('sqlalchemy.dialects.mysql')
sa_dialects.mysql=sa_mysql
class _Inspection:
 def inspect(self,row):
  class M:
   column_attrs=[type('C',(),{'key':k})() for k in type(row).__columns__]
  return type('R',(),{'mapper':M()})()
sa.inspect=_Inspection().inspect
sa_inspection=types.ModuleType('sqlalchemy.inspection');sa_inspection.inspect=sa.inspect
sys.modules.update({'sqlalchemy':sa,'sqlalchemy.orm':sa_orm,'sqlalchemy.exc':sa_exc,
 'sqlalchemy.types':sa_types,'sqlalchemy.dialects':sa_dialects,'sqlalchemy.dialects.mysql':sa_mysql,
 'sqlalchemy.inspection':sa_inspection})

# ---------- in-memory session ----------
class FakeDB:
 def __init__(self):
  self.store={}       # model class -> {pk: instance}
  self.pending=[]     # rows awaiting commit
  self.snapshot=None
  self.fail_next_commit_integrity=False
  self.rollback_calls=0
  self.hide_next_scalar_model=None
 def _table(self,model):return self.store.setdefault(model,{})
 def add(self,row):
  if self.snapshot is None:self.snapshot={m:dict(t) for m,t in self.store.items()}
  self.pending.append(row)
 def flush(self):
  for row in self.pending:
   pk=[k for k,c in type(row).__columns__.items() if 'primary_key' in c.kw][0]
   self._table(type(row))[getattr(row,pk)]=row
  self.pending.clear()
 def get(self,model,pk):
  for row in self.pending:
   if isinstance(row,model):
    cpk=[k for k,c in model.__columns__.items() if 'primary_key' in c.kw][0]
    if getattr(row,cpk)==pk:return row
  return self._table(model).get(pk)
 def scalar(self,stmt):
  if self.hide_next_scalar_model is not None and self.hide_next_scalar_model==getattr(stmt.entity,'model',stmt.entity):
   self.hide_next_scalar_model=None;return None
  res=list(self._iter(stmt));return res[0] if res else None
 def scalars(self,stmt):
  rows=self._iter(stmt)
  if isinstance(stmt.entity,_Attr):return [getattr(r,stmt.entity.name) for r in rows]
  return rows
 def _iter(self,stmt):
  entity=stmt.entity.model if isinstance(stmt.entity,_Attr) else stmt.entity
  rows=list(self._table(entity).values())
  rows+=[r for r in self.pending if isinstance(r,entity)]
  for f in stmt.filters:
   rows=[r for r in rows if _match(r,f)]
  return rows
 def commit(self):
  if self.fail_next_commit_integrity:
   self.fail_next_commit_integrity=False
   self.rollback();raise IntegrityError('duplicate key')
  self.flush();self.snapshot=None
 def rollback(self):
  self.rollback_calls+=1
  if self.snapshot is not None:self.store=self.snapshot
  self.pending=[];self.snapshot=None
 def refresh(self,row):pass
 def close(self):pass
 def __enter__(self):return self
 def __exit__(self,*a):self.close()
class _Cmp:
 def __init__(self,key,op,value):self.key,self.op,self.value=key,op,value
class _In:
 def __init__(self,key,values):self.key,self.values=key,values
def _attr(model,name):
 # builds comparisons like EnvelopeStudy.id == 'x'
 return _Attr(model,name)
class _Attr:
 def __init__(self,model,name):self.model,self.name=model,name
 def __eq__(self,v):return _Cmp(self.name,'eq',v)
 def in_(self,values):return _In(self.name,list(values))
# attach attribute proxy to model classes lazily
_original_getattr=None
def _match(row,f):
 if isinstance(f,_Cmp):return getattr(row,f.key)==f.value
 if isinstance(f,_In):return getattr(row,f.key) in f.values
 raise NotImplementedError(type(f))
def install_model_attrs():
 from src.models import EnvelopeRun,EnvelopeStudy,FootprintReview,Report
 for model in (EnvelopeRun,EnvelopeStudy,FootprintReview,Report):
  for name in model.__columns__:
   setattr(model,name,_Attr(model,name))

# ---------- redis fake ----------
class FakeRedis:
 queues={}
 def __init__(self,*a,**k):pass
 @classmethod
 def from_url(cls,*a,**k):return cls()
 @classmethod
 def reset(cls):cls.queues.clear()
 def lpush(self,key,*vals):
  q=self.queues.setdefault(key,[]);q.extend(v.decode() if isinstance(v,bytes) else v for v in vals)
 def brpop(self,key,timeout=0):
  q=self.queues.get(key)
  if not q:return None
  return (key,q.pop(0).encode())
 def ping(self):return True
class RedisError(Exception):pass
class _DownRedis:
 def __init__(self,*a,**k):pass
 @classmethod
 def from_url(cls,*a,**k):return cls()
 def lpush(self,*a,**k):raise RedisError('down')
 def ping(self):raise RedisError('down')
redis_mod=types.ModuleType('redis');redis_mod.Redis=FakeRedis;redis_mod.RedisError=RedisError
sys.modules['redis']=redis_mod

# ---------- fastapi fake ----------
class HTTPException(Exception):
 def __init__(self,status_code,detail):self.status_code=status_code;self.detail=detail
fastapi=types.ModuleType('fastapi');fastapi.HTTPException=HTTPException
sys.modules['fastapi']=fastapi
