"""PostgreSQL Database Classes."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy import Column, String, Integer

db_url = "postgresql://postgres:postgres@acidc-postgres:5432/nso"
engine = create_engine(db_url, pool_size=5, pool_recycle=3600)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

Base = declarative_base()
metadata = Base.metadata


class AcidcVrf(Base):
    """Acidc vrf main database model."""

    __tablename__ = "acidcvrfs"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    enforcement = Column(String, nullable=False)
    vrf_type = Column(String, nullable=False)


def clear_db() -> None:
    """Clear all records in database tables."""
    with Session() as session:
        session.query(AcidcVrf).delete()
        session.commit()
