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
def read_pacer():
    return {"message": "PACER endpoint is now running"}
