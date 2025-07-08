"""
Mock Trial AI Application (LawCourtIQ)
Copyright (c) 2025 Frank Garcia

This file is part of Mock Trial AI, dual-licensed under:
- GNU Affero General Public License v3.0 (AGPL-3.0)
- Commercial License (contact for terms)

See LICENSE and COMMERCIAL_LICENSE for details.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_documents():
    """
    Endpoint to retrieve a list of documents.
    """
    return {"message": "Documents API works!"}

@router.post("/")
def create_document(document: dict):
    """
    Endpoint to create a new document.
    :param document: A dictionary containing document details.
    """
    return {"message": "Document created!", "document": document}
