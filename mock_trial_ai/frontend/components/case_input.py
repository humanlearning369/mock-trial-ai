import streamlit as st
from datetime import datetime
import json
from utils.connection import get_analyzer
from io import BytesIO
import docx

class CaseInputComponent:
    def __init__(self):
        self.analyzer = get_analyzer()
        self.case_types = ["Patent Infringement", "Contract Dispute", "Employment Law"]
        self.technical_fields = [
            "Machine Learning/AI",
            "Software",
            "Hardware",
            "Biotechnology",
            "Other"
        ]

    # NEWLY ADDED FUNCTION TO HANDLE UPLOADING DOCUMENTS
    def handle_document_upload(self, case_id: int, uploaded_file) -> bool:
        """Optional new function for document handling"""
        if uploaded_file is not None:
            try:                
                file_content = uploaded_file.read()            
                
                if uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 
                    doc = docx.Document(BytesIO(file_content))
                    extracted_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                else:                    
                    extracted_text = file_content.decode('utf-8', errors='ignore')

                cursor = self.analyzer.db.cursor()
                cursor.execute("""
                    INSERT INTO case_documents 
                    (case_id, filename, file_content, file_type, extracted_text)
                    VALUES (%s, %s, %s, %s, %s)
                """, (case_id, uploaded_file.name, file_content, uploaded_file.type, extracted_text))
                self.analyzer.db.commit()
                return True
            except Exception as e:
                print(f"Error handling document: {e}")
                return False
        return False
    
    def verify_document_upload(self, case_id: int) -> dict:
        """Verify document was uploaded"""
        try:
            cursor = self.analyzer.db.cursor()
            cursor.execute("""
                SELECT id, filename, created_at 
                FROM case_documents 
                WHERE case_id = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """, (case_id,))
            result = cursor.fetchone()
            if result:
                return {
                    "success": True,
                    "doc_id": result[0],
                    "filename": result[1],
                    "uploaded_at": result[2]
                }
            return {"success": False}
        except Exception as e:
            print(f"DEBUG - Verification error: {e}")
            return {"success": False}
        # NEWLY ADDED ABOVE CODE BLOCK

    def render(self):
        st.header("Case Information Input")        
        
        case_action = st.radio(
            "Choose Action",
            ["Create New Case", "View/Edit Existing Case"],
            key="case_action"
        )
        
        if case_action == "View/Edit Existing Case":
            self.show_existing_cases()
        else:            
            case_type = st.selectbox("Select Case Type", self.case_types)

            if case_type == "Patent Infringement":
                self.show_new_case_form()                
            elif case_type == "Contract Dispute":
                self.render_contract_form()
            elif case_type == "Employment Law":
                self.render_employment_form()

    def show_existing_cases(self):
        """Show and select existing cases"""
        # ADDED TO HANDLE ST.SESSION STATE ISSUES WITH STREAMLIT       
        if 'file_selected' not in st.session_state:
            st.session_state.file_selected = False
        if 'file_object' not in st.session_state:
            st.session_state.file_object = None
        if 'upload_clicked' not in st.session_state:
            st.session_state.upload_clicked = False

        try:
            cursor = self.analyzer.db.cursor()
            cursor.execute("""
                SELECT 
                    data->'details'->>'patent_number' AS patent_number,
                    data->>'case_name' AS case_name,
                    data->'details'->>'filing_date' AS filing_date,
                    id,
                    analysis_in_progress
                FROM mock_cases
                ORDER BY (data->'details'->>'filing_date')::DATE DESC
            """)
            existing_cases = cursor.fetchall()
            cursor.close()

            if not existing_cases:
                st.warning("No existing cases found. Please create a new case.")
                return

            st.subheader("Select Existing Case")
            selected_case = st.selectbox(
                "Choose Case",
                options=existing_cases,
                format_func=lambda x: f"{x[1]} (Patent: {x[0]}, Filed: {x[2]})"
            )
            # FIXED - KEPT BEING REPLACED FROM THE CASE POINT **********************************************
            if selected_case:
                col1, col2 = st.columns([3,1])
                with col1:
                    st.info(f"Selected: {selected_case[1]} (Patent: {selected_case[0]})")
    
                with col2:
                    with st.expander("Add Document", expanded=True):                        
                        new_doc = st.file_uploader(
                            "Upload Document",
                            type=['pdf', 'docx'],
                            key="existing_case_doc"
                        )
                        
                        if new_doc and not st.session_state.file_selected:
                            st.session_state.file_object = new_doc
                            st.session_state.file_selected = True
                            st.rerun()
                            
                        if st.session_state.file_selected and not st.session_state.upload_clicked:
                            st.write(f"📄 Selected: {st.session_state.file_object.name}")
                            if st.button("Upload Document"):
                                st.session_state.upload_clicked = True
                                with st.spinner('Uploading document... Please wait...'):
                                # THIS NOW ACTUALLY LOADS THE FILE
                                    if self.handle_document_upload(selected_case[3], st.session_state.file_object):
                                        verify_result = self.verify_document_upload(selected_case[3])
                                        if verify_result["success"]:
                                            # st.session_state.upload_disabled = True
                                            st.session_state.analysis_params = {
                                                'patent_number': selected_case[0],
                                                'filing_date': selected_case[2],
                                                'case_name': selected_case[1]
                                            }
                                            st.session_state.case_data = True
                                            st.success(f"✅ Document uploaded successfully! Please click on the Analysis tab")                                            
                                            if st.button("Reset"):
                                                st.session_state.file_selected = False
                                                st.session_state.upload_clicked = False
                                                st.session_state.file_object = None
                                                st.rerun()
                                        else:
                                            st.error("Upload failed. Please try again.")
                                            st.session_state.upload_clicked = False
                # NEWLY ADDED ABOVE 

        except Exception as e:
            st.error(f"Error loading/selecting case: {str(e)}")            
            if hasattr(self.analyzer, 'db'):
                self.analyzer.db.rollback()

    def show_new_case_form(self):
        st.subheader("Enter New Case Details")        
        
        with st.form("new_case_form"):
            st.info("All fields marked with * are required")
           
            st.subheader("Basic Case Information")
            col1, col2 = st.columns(2)
            with col1:
                court = st.selectbox("Court *", ["CAFC", "District Court"], help="Select court jurisdiction")
                case_type = st.selectbox("Case Type *", ["civil"], help="Select case type")
                case_subject = st.selectbox("Case Subject *", ["patent"], help="Select case subject")
                docket_id = st.text_input("Docket ID *", help="Enter docket ID")
                
            with col2:
                case_name = st.text_input("Case Name *", help="Enter case name (e.g., TechInnovate LLC v DataCorp Systems)")
                filing_date = st.date_input("Filing Date *", help="Select filing date")
                representing = st.selectbox("Representing *", ["plaintiff", "defendant"], help="Select which party you represent")
            
            st.subheader("Patent Details")
            col3, col4 = st.columns(2)
            with col3:
                patent_number = st.text_input("Patent Number *", help="Enter patent number (e.g., US9123456)")
                technology = st.text_input("Technology *", help="Enter technology type (e.g., machine learning algorithm)")
                damages_sought = st.number_input("Damages Sought ($) *", min_value=0, help="Enter damages amount")

            with col4:
                claims = st.text_area("Claims at Issue * (one per line)", help="Enter patent claims\nExample:\nclaim 1\nclaim 2\nclaim 3")
            
            st.subheader("Plaintiff Information")
            col5, col6 = st.columns(2)
            with col5:
                plaintiff_type = st.text_input("Business Type *", help="Enter plaintiff's business type")
                plaintiff_revenue = st.number_input("Annual Revenue ($) *", min_value=0, help="Enter plaintiff's revenue")
            with col6:
                plaintiff_tech = st.text_area("Technology Usage *", help="Describe plaintiff's technology usage")
                plaintiff_licensing = st.text_area("Licensing History", help="Enter licensing history")
            
            st.subheader("Defendant Information")
            col7, col8 = st.columns(2)
            with col7:
                defendant_product = st.text_input("Product Name *", help="Enter defendant's product name")
                defendant_revenue = st.number_input("Product Revenue ($) *", min_value=0, help="Enter product revenue")
            with col8:
                defendant_tech = st.text_area("Technology Usage *", help="Describe defendant's technology usage")
                defendant_market = st.text_input("Market Share (%)", help="Enter market share percentage")
            
            st.subheader("Technical Evidence")
            col9, col10 = st.columns(2)
            with col9:
                source_code = st.text_input("Source Code Status *", help="Describe source code availability")
                documentation = st.text_input("Documentation *", help="Describe available documentation")
            with col10:
                expert_reports = st.text_input("Expert Reports *", help="Describe expert report status")

            # NEWLY ADDED 
            with st.expander("Case Document (Optional)"):
                uploaded_file = st.file_uploader(
                "Upload Case Document", 
                type=['pdf', 'docx'],
                help="Upload main case document for analysis"
            )
            if uploaded_file:
                st.info(f"Selected file: {uploaded_file.name}")

            submitted = st.form_submit_button("Submit Case")

        if submitted:           
            if not all([patent_number, case_name, court, docket_id, plaintiff_type, defendant_product]):
                st.error("Please fill in all required fields marked with *")
                return

            try:                
                cursor = self.analyzer.db.cursor()                
                cursor.execute("""
                    SELECT 
                        data->'details'->>'patent_number' as patent_number,
                        data->>'case_name' as case_name,
                        data->'details'->>'filing_date' as filing_date,
                        analysis_in_progress
                    FROM mock_cases 
                    WHERE data->'details'->>'patent_number' = %s 
                    AND data->>'case_name' = %s
                    AND data->'details'->>'filing_date' = %s
                """, (patent_number, case_name, filing_date.strftime("%Y-%m-%d")))
                existing_case = cursor.fetchone()

                if existing_case:                    
                    st.error(f"""
                        ⚠️ Similar case found in database:
                        
                        Existing Case Details:
                        • Patent Number: {existing_case[0]}
                        • Case Name: {existing_case[1]}
                        • Filing Date: {existing_case[2]}
                        
                        Please use the 'View/Edit Existing Case' option to work with this case.
                    """)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Use Existing Case"):
                            if existing_case[3]:  
                                st.warning("⚠️ Analysis is currently in progress for this case. Please try again later.")
                                return                                
                            
                            st.session_state.analysis_params = {
                                'patent_number': existing_case[0],
                                'filing_date': existing_case[2],
                                'case_name': existing_case[1]
                            }
                            st.session_state.case_data = True
                            st.success("✅ Existing case selected. You may proceed to the Analysis tab.")
                            return                    
                    
                else:                    
                    case_data = self._prepare_case_data(
                        patent_number, filing_date, case_name, court, case_type,
                        case_subject, docket_id, representing, technology, damages_sought,
                        claims, plaintiff_type, plaintiff_revenue, plaintiff_tech,
                        plaintiff_licensing, defendant_product, defendant_revenue,
                        defendant_tech, defendant_market, source_code, documentation,
                        expert_reports
                    )                    
                    cursor = self.analyzer.db.cursor()
                    cursor.execute("""
                        INSERT INTO mock_cases (data, analysis_in_progress)
                        VALUES (%s, 0)
                        RETURNING id
                    """, (json.dumps(case_data),))
                    case_id = cursor.fetchone()[0]
                    self.analyzer.db.commit()
                    
                    if uploaded_file:
                        if self.handle_document_upload(case_id, uploaded_file):
                            st.success("✅ New case and document saved successfully. You may proceed to the Analysis tab.")
                        else:
                            st.success("✅ New case saved successfully, but document upload failed.")
                    else:
                        st.success("✅ New case saved successfully. You may proceed to the Analysis tab.")
                    
                    st.session_state.analysis_params = {
                        'patent_number': case_data['details']['patent_number'],
                        'filing_date': case_data['details']['filing_date'],
                        'case_name': case_data['case_name']
                    }
                    st.session_state.case_data = True
                    # self._insert_new_case(case_data)

            except Exception as e:
                st.error(f"Error checking for existing case: {str(e)}")
                return

    def render_contract_form(self):
        with st.form("contract_case_form"):
            st.subheader("Contract Case Input")
            
            contract_date = st.date_input("Contract Date")
            contract_value = st.number_input("Contract Value ($)", min_value=0)
            breach_type = st.selectbox("Type of Breach", [
                "Non-performance",
                "Delayed Performance",
                "Defective Performance",
                "Other"
            ])
            performance_history = st.text_area("Performance History")

            st.subheader("Required Evidence")
            st.markdown("""
            * Contract Documents
            * Communication Records
            * Performance Reports
            * Financial Records
            """)

            if st.form_submit_button("Submit Case Details"):
                self.save_case_details({
                    "type": "contract",
                    "contract_date": contract_date.strftime("%Y-%m-%d"),
                    "contract_value": contract_value,
                    "breach_type": breach_type,
                    "performance_history": performance_history
                })

    def render_employment_form(self):
        with st.form("employment_case_form"):
            st.subheader("Employment Case Input")
            
            employment_type = st.selectbox("Employment Type", [
                "Full-time",
                "Part-time",
                "Contract",
                "Other"
            ])
            incident_date = st.date_input("Incident Date")
            claim_type = st.selectbox("Claim Type", [
                "Discrimination",
                "Harassment",
                "Wrongful Termination",
                "Wage Dispute"
            ])
            damages_sought = st.number_input("Damages Sought ($)", min_value=0)

            st.subheader("Required Evidence")
            st.markdown("""
            * Employment Records
            * HR Documents
            * Performance Reviews
            * Company Policies
            """)

            if st.form_submit_button("Submit Case Details"):
                self.save_case_details({
                    "type": "employment",
                    "employment_type": employment_type,
                    "incident_date": incident_date.strftime("%Y-%m-%d"),
                    "claim_type": claim_type,
                    "damages_sought": damages_sought
                })

    def _prepare_case_data(self, patent_number, filing_date, case_name, court, case_type,
                          case_subject, docket_id, representing, technology, damages_sought,
                          claims, plaintiff_type, plaintiff_revenue, plaintiff_tech,
                          plaintiff_licensing, defendant_product, defendant_revenue,
                          defendant_tech, defendant_market, source_code, documentation,
                          expert_reports):
        """Helper method to prepare case data dictionary"""
        return {
            "court": court.lower(),
            "case_name": case_name,
            "case_type": case_type,
            "case_subject": case_subject,
            "docket_id": docket_id,
            "details": {
                "filing_date": filing_date.strftime("%Y-%m-%d"),
                "representing": representing,
                "patent_number": patent_number,
                "technology": technology,
                "damages_sought": damages_sought,
                "claims_at_issue": [claim.strip() for claim in claims.split("\n") if claim.strip()],
                "plaintiff": {
                    "business_type": plaintiff_type,
                    "annual_revenue": plaintiff_revenue,
                    "tech_usage": plaintiff_tech,
                    "licensing_history": plaintiff_licensing
                },
                "defendant": {
                    "product_name": defendant_product,
                    "product_revenue": defendant_revenue,
                    "tech_usage": defendant_tech,
                    "market_share": defendant_market
                },
                "technical_evidence": {
                    "source_code": source_code,
                    "documentation": documentation,
                    "expert_reports": expert_reports
                }
            }
        }

    def _insert_new_case(self, case_data):
        """Helper method to insert new case"""
        try:
            cursor = self.analyzer.db.cursor()
            cursor.execute("""
                INSERT INTO mock_cases (data, analysis_in_progress)
                VALUES (%s, 0)
            """, (json.dumps(case_data),))
            self.analyzer.db.commit()
            
            st.session_state.analysis_params = {
                'patent_number': case_data['details']['patent_number'],
                'filing_date': case_data['details']['filing_date'],
                'case_name': case_data['case_name']
            }
            st.session_state.case_data = True
            st.success("✅ New case saved successfully. You may proceed to the Analysis tab.")

        except Exception as e:
            st.error(f"Error saving new case: {str(e)}")
            return

    def save_case_details(self, details):
        """Legacy method for non-patent cases"""
        st.session_state.case_data = details
        st.success("Case details saved successfully!")