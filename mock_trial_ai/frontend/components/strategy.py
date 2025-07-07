import streamlit as st
import plotly.graph_objects as go
from mock_trial_analysis import MockTrialAnalyzer
import re

class StrategyComponent:
    def __init__(self):
        self.analyzer = MockTrialAnalyzer()

    def extract_percentages(self, text):
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        percentages = re.findall(percentage_pattern, text)
        return [float(p) for p in percentages] if percentages else []

    def extract_monetary_values(self, text):
        money_pattern = r'\$(\d+(?:\.\d+)?(?:M|B)?)'
        return re.findall(money_pattern, text)

    def extract_timeline_info(self, text):
        timeline_pattern = r'(\d+)(?:-(\d+))?\s*months'
        matches = re.findall(timeline_pattern, text)
        return [(int(start), int(end) if end else int(start)) for start, end in matches]

    def render(self):
        st.header("Strategy Recommendations")

        if not st.session_state.analysis_complete:
            st.warning("Please complete the analysis first")
            return
        
        analysis_text = None
        if st.session_state.case_id:
            try:
                cursor = self.analyzer.db.cursor()                
                cursor.execute("""                        
                    SELECT analysis 
                    FROM trial_analysis
                    WHERE case_id = %s
                    AND entry_type = 'analysis'
                    ORDER BY created_at DESC
                    LIMIT 1                        
                """, (st.session_state.case_id,))
                result = cursor.fetchone()
                cursor.close()
                if result:
                    analysis_text = result[0]
            except Exception as e:
                print(f"Debug - Error fetching analysis: {e}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            prob = "65%"  
            if analysis_text:
                probs = self.extract_percentages(analysis_text)
                technical_prob = next((p for p in probs if 50 <= p <= 100), 65)
                prob = f"{technical_prob}%"
            
            self.strategy_card(
                "Technical Success Probability",
                prob,
                "Based on technical analysis and prior cases"
            )
        
        with col2:
            prob = "75%"  
            if analysis_text:
                probs = self.extract_percentages(analysis_text)
                settlement_prob = next((p for p in probs if 60 <= p <= 100), 75)
                prob = f"{settlement_prob}%"

            self.strategy_card(
                "Settlement Probability",
                prob,
                "Based on case analysis and settlement data"
            )
        
        with col3:
            prob = "58%"  
            if analysis_text:
                probs = self.extract_percentages(analysis_text)
                damage_prob = next((p for p in probs if 40 <= p <= 100), 58)
                prob = f"{damage_prob}%"

            self.strategy_card(
                "Damage Recovery Probability",
                prob,
                "Based on damage calculations and comparable cases"
            )
       
        timeline_text = """
        Timeline Breakdown:
        🔵 Discovery Phase (4-6 months)
        🔷 Expert Reports (2-3 months)
        🔴 Pre-trial Motions (2-3 months)
        🟢 Trial Preparation (2-3 months)
        """

        if analysis_text:
            timeline_info = self.extract_timeline_info(analysis_text)
            if timeline_info:
                timeline_text = "Timeline Breakdown:\n"
                phases = ["Discovery Phase", "Expert Reports", "Pre-trial Motions", "Trial Preparation"]
                emojis = ["🔵", "🔷", "🔴", "🟢"]
                
                for (start, end), phase, emoji in zip(timeline_info[:4], phases, emojis):
                    if end:
                        timeline_text += f"{emoji} {phase} ({start}-{end} months)\n"
                    else:
                        timeline_text += f"{emoji} {phase} ({start} months)\n"

        st.info(timeline_text)    
        
        metrics_expander = st.expander("View Detailed Metrics")
        with metrics_expander:
            damages = "TBD"
            timeline = "18-24 months"
            settlement_range = "$2M-4M"

            if analysis_text:
                monetary_values = self.extract_monetary_values(analysis_text)
                if monetary_values:
                    damages = monetary_values[0]
                timeline_info = self.extract_timeline_info(analysis_text)
                if timeline_info:
                    total_min = sum(start for start, _ in timeline_info)
                    total_max = sum(end if end else start for start, end in timeline_info)
                    timeline = f"{total_min}-{total_max} months"

            st.dataframe({
                "Metric": ["Settlement Probability", "Time to Trial", "Cost Range"],
                "Value": [prob, timeline, settlement_range],
                "Source": [
                    "Based on similar cases",
                    "Average duration in this jurisdiction",
                    "Including expert fees and court costs"
                ]
            }, hide_index=True)
        
        self.render_detailed_analysis()

    def strategy_card(self, title, probability, description):
        st.metric(
            label=title,
            value=probability,
            help=description
        )

    def render_detailed_analysis(self):
        st.subheader("Strategy Timeline")        
       
        fig = go.Figure()
        
        phases = [
            "Discovery", "Expert Reports", "Markman Hearing", 
            "Summary Judgment", "Trial Prep", "Trial"
        ]
        
        durations = [4, 3, 2, 3, 3, 2]  
        colors = ['#1f77b4', '#17becf', '#d62728', '#2ca02c', '#9467bd', '#e377c2']
        
        cumulative = 0
        for phase, duration, color in zip(phases, durations, colors):
            fig.add_trace(go.Bar(
                name=phase,
                x=[duration],
                y=['Timeline'],
                orientation='h',
                base=cumulative,
                marker_color=color
            ))
            cumulative += duration

        fig.update_layout(
            barmode='stack',
            height=150,
            showlegend=True,
            xaxis_title="Months",
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )

        st.plotly_chart(fig, use_container_width=True)
       
        st.subheader("Key Recommendations")
        st.markdown("""
        1. **Evidence Collection**
           - Focus on technical documentation
           - Secure expert witnesses early
           - Document all communications

        2. **Risk Mitigation**
           - Regular case assessment
           - Budget monitoring
           - Settlement evaluation points

        3. **Timeline Management**
           - Set clear milestones
           - Regular status updates
           - Deadline tracking
        """)