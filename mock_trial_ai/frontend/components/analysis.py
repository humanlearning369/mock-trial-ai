import sys
import os
import json
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(os.path.dirname(current_dir), 'backend')
sys.path.append(backend_dir)
from mock_trial_analysis import MockTrialAnalyzer
import streamlit as st
import time

class AnalysisComponent:
    def __init__(self):
        self.analyzer = MockTrialAnalyzer()
        #ADDED (B) FOR ANALYSIS PERSISTENCE
        if 'case_id' not in st.session_state:
            st.session_state.case_id = None

    def render(self):
        st.header("Case Analysis")
        print("DEBUG - case_data:", st.session_state.case_data)
        print("DEBUG - analysis_params:", st.session_state.get('analysis_params'))
        if not st.session_state.case_data:
            st.warning("Please input case details first")
            return
        
        #ADDED FOR ANALYSIS PERSISTENCE
        if st.session_state.case_id:
            try:
                cursor = self.analyzer.db.cursor()                
                cursor.execute("""                        
                        SELECT analysis, entry_type
                        FROM trial_analysis
                        WHERE case_id = %s
                        AND entry_type = 'analysis'
                        ORDER BY created_at DESC
                        LIMIT 1                        
                """, (st.session_state.case_id,))
                existing_analysis = cursor.fetchone()
                cursor.close()

                if existing_analysis:                    
                    print("Debugging analysis content:", existing_analysis[0][:100])
                    analysis_data = existing_analysis[0]  
                    entry_type = existing_analysis[1]    
                    
                    if entry_type == 'analysis':
                        st.subheader("Analysis Results:")
                        st.markdown(analysis_data)
                    else:                        
                        st.markdown(existing_analysis[0])               
           
            except Exception as e:
                st.error(f"Error loading previous analysis: {str(e)}")
                print(f"Error details: {e}") 
        
        if st.button("Start Analysis", type="primary"):
            progress = st.progress(0)
            status = st.empty()
        
            for i, phase in enumerate([
                "Processing Documents",
                "Finding Similar Cases",
                "Analyzing Patterns",
                "Generating Recommendations"
            ]):
                status.text(f"Phase {i+1}/4: {phase}")
                progress.progress((i + 1) * 25)
                time.sleep(1)
                
            with st.spinner("Analyzing case..."):
                try:                    
                    patent_number = st.session_state.analysis_params.get('patent_number')
                    filing_date = st.session_state.analysis_params.get('filing_date')
                    case_name = st.session_state.analysis_params.get('case_name')                    
                    
                    if not all([patent_number, filing_date, case_name]):
                        raise ValueError("Missing required parameters")
                    
                    # NEW CODE ADDED TO TEST INSERTING NEW CASES                     
                    cursor = self.analyzer.db.cursor()
                    cursor.execute("""
                        UPDATE mock_cases 
                        SET analysis_in_progress = 1 
                        WHERE data->'details'->>'patent_number' = %s 
                        AND data->'details'->>'filing_date' = %s 
                        AND data->>'case_name' = %s
                    """, (patent_number, filing_date, case_name))
                    self.analyzer.db.commit()
                    cursor.close()
                    # NEW CODE ADDED TO TEST INSERTING NEW CASES
                   
                    case_id = self.analyzer._get_case_id(
                        patent_number=patent_number,
                        filing_date=filing_date,
                        case_name=case_name
                    )
                    st.session_state.case_id = case_id                    
                    
                    results = self.analyzer.generate_trial_scenario(
                        patent_number=patent_number,
                        filing_date=filing_date,
                        case_name=case_name
                    )                    
                   
                    st.session_state.analysis_results = results
                    st.session_state.analysis_complete = True
                    
                    st.subheader("Similar Cases Found:")
                    for i, case in enumerate(results["top_similar_cases"], 1):
                        with st.expander(f"Case {i}: {case['case']['case_text']}"):
                            st.write(f"Court: {case['case']['court_name']}")
                            st.write(f"Judge: {case['case']['judge']}")
                            st.write(f"Filed: {case['case']['filing_date']}")
                            st.write(f"Similarity: {case['similarity_score']:.2f}")
                    
                    st.subheader("Analysis Results:")
                    st.markdown(results["mock_trial_analysis"])

                except Exception as e:
                    st.error(f"Error during analysis: {str(e)}")