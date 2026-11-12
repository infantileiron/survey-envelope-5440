from sqlalchemy import String,Double,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
from src.config.json_type import PreciseJSON as JSON
class EnvelopeStudy(Base):
 __tablename__='envelope_studies'
 id:Mapped[str]=mapped_column(String(80),primary_key=True)
 name:Mapped[str]=mapped_column(String(160),unique=True)
 survey_id:Mapped[str]=mapped_column(ForeignKey('point_surveys.id'))
 policy_id:Mapped[str]=mapped_column(ForeignKey('boundary_policies.id'))
 group_ids:Mapped[list]=mapped_column(JSON)
 snapshot:Mapped[dict]=mapped_column(JSON)
 created_at:Mapped[str]=mapped_column(String(64))
