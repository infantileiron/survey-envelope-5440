from sqlalchemy import String,Double,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
from src.config.json_type import PreciseJSON as JSON
class EnvelopeRun(Base):
 __tablename__='envelope_runs'
 id:Mapped[str]=mapped_column(String(80),primary_key=True)
 study_id:Mapped[str]=mapped_column(ForeignKey('envelope_studies.id'))
 status:Mapped[str]=mapped_column(String(32))
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default='')
 created_at:Mapped[str]=mapped_column(String(64))
