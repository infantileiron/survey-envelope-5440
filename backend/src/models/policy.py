from sqlalchemy import String,Double,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class BoundaryPolicy(Base):
 __tablename__='boundary_policies'
 id:Mapped[str]=mapped_column(String(80),primary_key=True)
 name:Mapped[str]=mapped_column(String(160),unique=True)
 deduplication:Mapped[str]=mapped_column(String(32))
 area_tie_relative:Mapped[float]=mapped_column(Double)
 algorithm_version:Mapped[str]=mapped_column(String(80))
 created_at:Mapped[str]=mapped_column(String(64))
