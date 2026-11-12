from pydantic import BaseModel,Field,ConfigDict
from typing import Literal
class StudyInput(BaseModel):
 model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
 name:str=Field(min_length=2,max_length=160)
 survey_id:str
 policy_id:str
 group_ids:list[str]=Field(min_length=1,max_length=8)
