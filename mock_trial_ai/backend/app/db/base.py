"""
Mock Trial AI Application (LawCourtIQ)
Copyright (c) 2025 Frank Garcia

This file is part of Mock Trial AI, dual-licensed under:
- GNU Affero General Public License v3.0 (AGPL-3.0)
- Commercial License (contact for terms)

See LICENSE and COMMERCIAL_LICENSE for details.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://[user]:[password]@localhost/mock_trial_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
