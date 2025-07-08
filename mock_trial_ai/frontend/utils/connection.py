"""
Mock Trial AI Application (LawCourtIQ)
Copyright (c) 2025 Frank Garcia

This file is part of Mock Trial AI, dual-licensed under:
- GNU Affero General Public License v3.0 (AGPL-3.0)
- Commercial License (contact for terms)

See LICENSE and COMMERCIAL_LICENSE for details.
"""
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from mock_trial_analysis import MockTrialAnalyzer
import streamlit as st

@st.cache_resource
def get_analyzer():
    """Create or get cached analyzer instance"""
    return MockTrialAnalyzer()
