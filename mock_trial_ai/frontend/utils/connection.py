import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from mock_trial_analysis import MockTrialAnalyzer
import streamlit as st

@st.cache_resource
def get_analyzer():
    """Create or get cached analyzer instance"""
    return MockTrialAnalyzer()