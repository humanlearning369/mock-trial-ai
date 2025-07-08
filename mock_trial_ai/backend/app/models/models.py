"""
Mock Trial AI Application (LawCourtIQ)
Copyright (c) 2025 Frank Garcia

This file is part of Mock Trial AI, dual-licensed under:
- GNU Affero General Public License v3.0 (AGPL-3.0)
- Commercial License (contact for terms)

See LICENSE and COMMERCIAL_LICENSE for details.
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DECIMAL, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base

class ApiCase(Base):
    __tablename__ = "api_cases"
    
    api_case_id = Column(Integer, primary_key=True)
    api_source = Column(String(50))      
    source_id = Column(String(100))     
    case_number = Column(String(50))
    court = Column(String(100))
    filing_date = Column(Date)
    case_title = Column(String(200))
    case_type = Column(String(100))
    case_status = Column(String(50))
    api_response = Column(JSON)

class ApiParty(Base):
    __tablename__ = "api_parties"
    
    api_party_id = Column(Integer, primary_key=True)
    api_case_id = Column(Integer, ForeignKey('api_cases.api_case_id'))
    party_name = Column(String(200))
    party_type = Column(String(50))
    representation = Column(String(200))

class ApiDocument(Base):
    __tablename__ = "api_documents"
    
    api_document_id = Column(Integer, primary_key=True)
    api_case_id = Column(Integer, ForeignKey('api_cases.api_case_id'))
    document_number = Column(String(50))
    document_type = Column(String(100))
    filing_date = Column(Date)
    description = Column(String)
    page_count = Column(Integer)
