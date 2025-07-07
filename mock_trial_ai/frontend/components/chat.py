import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from mock_trial_analysis import MockTrialAnalyzer
import streamlit as st

class ChatInterface:
    def __init__(self):
        self.analyzer = MockTrialAnalyzer()

    def render(self):
        st.header("Legal Analysis Chat")

        if not st.session_state.analysis_complete:
            st.warning("Please complete initial analysis first")
            return

        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        role = st.selectbox(
            "Select Perspective:",
            ["ATTORNEY", "JUDGE", "OPPOSING", "EXPERT", "SUGGESTIONS"],
            key="role_selector"
        )

        with st.expander("Suggested Questions"):
            st.markdown("""
            - What are our strongest arguments?
            - What evidence should we prioritize?
            - How does our timeline compare to similar cases?
            - What are potential counter-arguments to our position?
            - How do damages calculations typically work in similar cases?
            """)
       
        if prompt := st.chat_input("Ask your question"):            
            full_prompt = f"{role}: {prompt}" if role != "ATTORNEY" else prompt            
            
            st.session_state.messages.append({"role": "user", "content": full_prompt})
            with st.chat_message("user"):
                st.markdown(full_prompt)
            
            with st.spinner("Analyzing..."):
                try:
                    if not st.session_state.case_id:
                        raise ValueError("No case ID found. Please complete analysis first.")
                    # This is using existing mock_trial_analysis.py functionality
                    # ADDED EXPERT DOCUMENT SECTION ON  ********************************************
                    follow_up_prompt = f"""
                    Based on the previous mock trial analysis of {st.session_state.analysis_params['case_name']}:
                    
                    Expert Document:
                    {st.session_state.get('analysis_results', {}).get('expert_document', '')}

                    {role} PERSPECTIVE:
                    Question: {prompt.strip()}

                    Please respond as appropriate for the {role} role.
                    Previous Analysis: {st.session_state.get('analysis_results', {}).get('mock_trial_analysis', '')}
                    """
                    # enable this when ready for prod testing ************
                    response = self.analyzer.claude.messages.create(
                        model="claude-3-opus-20240229",
                        max_tokens=4000,
                        temperature=0.5,
                        system=f"You are an expert {role.lower()} analyzing this mock trial case.",
                        messages=[{"role": "user", "content": follow_up_prompt}]
                    )

                    # disable above code block when testing in terminal only ***********
                    # response = self.analyzer.get_chat_response(prompt.strip(), role)

                    ai_response = response.content[0].text  
                    
                    analysis_id = self.analyzer._save_analysis(                        
                        st.session_state.case_id,
                        prompt.strip(),
                        ai_response,
                        'chat'
                    )   
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    with st.chat_message("assistant"):
                        st.markdown(ai_response)

                except Exception as e:
                    st.error(f"Error getting response: {str(e)}")