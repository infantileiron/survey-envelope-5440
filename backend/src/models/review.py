from sqlalchemy import String,Double,Integer,JSON,ForeignKey,Text
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class FootprintReview(Base):
 __tablename__='footprint_reviews'
 id:Mapped[str]=mapped_column(String(80),primary_key=True)
 run_id:Mapped[str]=mapped_column(ForeignKey('envelope_runs.id'))
 version:Mapped[int]=mapped_column(Integer)
 note:Mapped[str]=mapped_column(Text)
 decision:Mapped[str]=mapped_column(String(32))
 author:Mapped[str]=mapped_column(String(160))
 created_at:Mapped[str]=mapped_column(String(64))
