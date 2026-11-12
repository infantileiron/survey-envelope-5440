from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class PolicyInput(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 name:str=Field(min_length=2,max_length=160)
 deduplication:Literal['exact','reject']
 area_tie_relative:float=Field(default=1e-12,ge=0,le=1e-8)
 algorithm_version:Literal['andrews-edge-enumeration-v1']='andrews-edge-enumeration-v1'
