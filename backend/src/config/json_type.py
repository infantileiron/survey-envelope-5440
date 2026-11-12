import json
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.mysql import LONGTEXT

class PreciseJSON(TypeDecorator):
 """LONGTEXT JSON serialized by Python to preserve binary64 round-trip digits."""
 impl=LONGTEXT
 cache_ok=True
 def process_bind_param(self,value,dialect):
  return None if value is None else json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':'))
 def process_result_value(self,value,dialect):
  return None if value is None else json.loads(value)
