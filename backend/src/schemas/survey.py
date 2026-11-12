from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class PointInput(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 point_id:str=Field(min_length=1,max_length=64)
 x:float
 y:float
class GroupInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 group_id:str
 name:str=Field(min_length=1,max_length=80)
 points:list[PointInput]=Field(min_length=1,max_length=300)
class SurveyInput(BaseModel):
 model_config=ConfigDict(extra='forbid')
 name:str=Field(min_length=2,max_length=160)
 source:str=Field(min_length=2,max_length=180)
 coordinate_system:Literal['local_m']
 groups:list[GroupInput]=Field(min_length=1,max_length=8)
