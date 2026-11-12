from sqlalchemy import String,Integer,ForeignKey,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
from src.config.json_type import PreciseJSON as JSON
class EnvelopeRun(Base):
 __tablename__='envelope_runs'
 __table_args__=(UniqueConstraint('study_id',name='uq_envelope_runs_study'),)
 id:Mapped[str]=mapped_column(String(80),primary_key=True)
 study_id:Mapped[str]=mapped_column(ForeignKey('envelope_studies.id'))
 status:Mapped[str]=mapped_column(String(32))
 result:Mapped[dict]=mapped_column(JSON,default=dict)
 error:Mapped[str]=mapped_column(Text,default='')
 attempts:Mapped[int]=mapped_column(Integer,default=0)
 created_at:Mapped[str]=mapped_column(String(64))
 updated_at:Mapped[str]=mapped_column(String(64),default='')
