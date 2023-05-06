"""PostgreSQL Database Classes."""
from typing import List, Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy import Column, String, Integer

db_url = "postgresql://postgres:postgres@10.1.182.3:5432/nso"
engine = create_engine(db_url, pool_size=5, pool_recycle=3600)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

Base = declarative_base()
metadata = Base.metadata


class AcidcVrf(Base):
    """Acidc vrf main database model."""

    __tablename__ = "acidcvrfs"

    id = Column(Integer, primary_key=True)
    fabric = Column(String, nullable=False)
    tenant = Column(String, nullable=False)
    vrf_name = Column(String, nullable=False)
    vrf_description = Column(String)
    enforcement = Column(String, nullable=False)

    @staticmethod
    def clear_db() -> None:
        """Clear all records in database vrf table."""
        with Session() as session:
            session.query(AcidcVrf).delete()
            session.commit()

    @staticmethod
    def write_db(acidc_vrf: List[Dict]) -> None:
        """Get service list data from subscriber and write it to database.

        Returns:
            None
        """
        with Session() as session:
            session.bulk_insert_mappings(AcidcVrf, acidc_vrf)
            session.commit()
