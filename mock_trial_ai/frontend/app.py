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
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'backend')
sys.path.append(backend_dir)
import streamlit as st
from components.analysis import AnalysisComponent
from components.case_input import CaseInputComponent
from components.chat import ChatInterface
from components.strategy import StrategyComponent
from utils.connection import get_analyzer

class MockTrialApp:    
    def __init__(self):
        st.set_page_config(page_title="Mock Trial Analysis System", layout="wide", initial_sidebar_state="expanded")
        self.load_css()  
        self.analyzer = get_analyzer()
        self.initialize_session_state()

    def load_css(self): 
        with open(os.path.join(current_dir, 'static/style.css')) as f:
            st.markdown(f"""
                <style>
                {f.read()}
                </style>
                """, unsafe_allow_html=True)

    def initialize_session_state(self):
        if 'case_data' not in st.session_state:
            st.session_state.case_data = None
        if 'analysis_complete' not in st.session_state:
            st.session_state.analysis_complete = False
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
    
    def run(self):    
        header_container = st.container()
        with header_container:            
            image_path = os.path.join(current_dir, 'static', 'lawcourtiq_logo.png')        
            
            import base64
            with open(image_path, "rb") as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode()

            st.markdown(f"""
                <div class="main-header-container">
                    <div class="header-content">
                        <div class="logo-section">
                            <img src="data:image/png;base64,{encoded_image}" alt="LawCourtIQ Logo" width="110">
                        </div>
                        <div class="title-section">
                            <h1 class='app-header'>Mock Trial Analysis System</h1>
                            <div class='app-subheader'>POWERED BY AI</div>
                        </div>
                    </div>
                </div>
                <div class="header-accent-bar"></div>
            """, unsafe_allow_html=True)
        
        st.markdown("<hr class='header-divider'>", unsafe_allow_html=True)        
        
        tabs = st.tabs(["Case Input", "Analysis", "Strategy", "Chat"])
        
        with tabs[0]:
            case_input = CaseInputComponent()
            case_input.render()

        with tabs[1]:
            analysis = AnalysisComponent()
            analysis.render()

        with tabs[2]:
            strategy = StrategyComponent()
            strategy.render()

        with tabs[3]:
            chat = ChatInterface()
            chat.render()

if __name__ == "__main__":
    app = MockTrialApp()
    app.run()
