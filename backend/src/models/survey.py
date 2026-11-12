from sqlalchemy import String,Double,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
from src.config.json_type import PreciseJSON as JSON
class PointSurvey(Base):
 __tablename__='point_surveys'
 id:Mapped[str]=mapped_column(String(80),primary_key=True)
 name:Mapped[str]=mapped_column(String(160),unique=True)
 source:Mapped[str]=mapped_column(String(180))
 coordinate_system:Mapped[str]=mapped_column(String(32))
 groups:Mapped[list]=mapped_column(JSON)
 created_at:Mapped[str]=mapped_column(String(64))
