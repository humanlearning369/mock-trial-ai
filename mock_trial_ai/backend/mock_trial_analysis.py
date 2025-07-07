import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
import psycopg2
import json
import re
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List
import time

# Add this at the top after imports --------------ADDED 1/17/24
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.env')

load_dotenv('config.env')

DB_CONFIG = {
    "dbname": "mock_trial_db",
    "user": "[user]",
    "password": "[password]",
    "host": "localhost",
    "port": "5432"
}

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

client = OpenAI(api_key=OPENAI_API_KEY)  
claude = anthropic.Client(api_key=CLAUDE_API_KEY)

class MockTrialAnalyzer:
    def __init__(self):
        self.db = psycopg2.connect(**DB_CONFIG)
        self.claude = anthropic.Client(api_key=CLAUDE_API_KEY) # ADDED ON 1/17/24

    # NEWLY ADDED ON 012325 TO GET LATEST DOC
    def get_latest_document(self, case_id: int) -> str:
        """Optional method to get latest document"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                WITH doc AS (
                    SELECT extracted_text
                    FROM case_documents 
                    WHERE case_id = %s 
                    ORDER BY created_at DESC 
                    LIMIT 1
                )
                SELECT 
                    SUBSTRING(extracted_text FROM 'Prepared By:.*?Date:.*?\n') ||
                    SUBSTRING(extracted_text FROM '4\. Source Code Analysis[\s\S]*?(?=5\.)') ||
                    SUBSTRING(extracted_text FROM '5\. Financial Impact Assessment[\s\S]*?(?=6\.)') ||
                    SUBSTRING(extracted_text FROM '6\. Expert Conclusions[\s\S]*?(?=7\.)')
                FROM doc
            """, (case_id,))
            result = cursor.fetchone()
            return result[0] if result else ""
        except Exception as e:
            print(f"Error getting document: {e}")
            return ""
        
    def _get_case_details(self, patent_number: str, filing_date: str, case_name: str) -> Dict:
        """Retrieve case details from database"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT data FROM mock_cases 
            WHERE data->'details'->>'patent_number' = %s 
            AND data->'details'->>'filing_date' = %s 
            AND data->>'case_name' = %s
            AND analysis_in_progress = 1
        """, (patent_number, filing_date, case_name))
        result = cursor.fetchone()
        cursor.close()
        if not result:
            raise ValueError(f"No case found for Patent: {patent_number}, Case: {case_name}")
        return result[0]
    
    def _get_case_id(self, patent_number: str, filing_date: str, case_name: str) -> int:
        """Get case ID for Current Case (ex TechInnovate)"""
        cursor = self.db.cursor()
        cursor.execute("""            
            SELECT id FROM mock_cases 
            WHERE data->'details'->>'patent_number' = %s 
            AND data->'details'->>'filing_date' = %s 
            AND data->>'case_name' = %s 
            AND analysis_in_progress = 1
        """, (patent_number, filing_date, case_name)) 
        result = cursor.fetchone()
        cursor.close()
        if not result:
            raise ValueError("Case ID not found")
        return result[0]

    def _get_reference_cases(self) -> List[Dict]:
        """Retrieve related patent cases"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT     
            mc.data ->> 'caseName' AS case_name,
            mc.data ->> 'caseNameFull' AS case_name_full,
            mc.data ->> 'docketNumber' AS docket_number,
            mc.data ->> 'court' AS court_name,
            mc.data ->> 'suitNature' AS nature_suit,
            mc.data ->> 'dateFiled' AS filing_date,
            mc.data ->> 'judge' AS judge,
            mc.data ->> 'status' AS case_status,
            mc.data ->> 'procedural_history' AS procedural_history,
            mc.data ->> 'attorney' AS attorney,
            mc.data -> 'citation' AS citation,  -- JSON array of citations
            mc.data -> 'opinions' AS opinions,  -- JSON array of opinions
            mc.data ->> 'posture' AS posture,
    
            -- Docket Cases (dc) Table
            dc.data ->> 'case_name' AS docket_case_name,
            dc.data ->> 'court' AS docket_court,
            dc.data ->> 'docket_number' AS docket_case_number,
    
            -- Case Opinions (co) Table - Replacing docket_entries with detailed opinion data
            COALESCE(cc.data ->> 'summary', co.snippet) AS case_summary,  
            co.citation_ids AS opinion_citations,
            co.type AS opinion_type,
            co.author_id AS opinion_author_id,
            co.per_curiam AS opinion_per_curiam,
    
            -- Cluster Cases (cc) Table
            cc.data -> 'citations' AS citations,  -- JSON array of citation details
            cc.data ->> 'case_name_full' AS cluster_case_name_full,
            cc.data ->> 'judges' AS judges,
            cc.data ->> 'syllabus' AS syllabus,
            COALESCE(cc.data ->> 'disposition', co.type) AS case_disposition,  
            cc.data ->> 'precedential_status' AS precedential_status,
            cc.data -> 'sub_opinions' AS sub_opinions,  -- JSON array of sub-opinions
            cc.data ->> 'arguments' AS arguments
            FROM main_cases mc
            JOIN docket_cases dc ON mc.data ->> 'docket_id' = dc.data ->> 'id'
            JOIN cluster_cases cc ON cc.data ->> 'docket_id' = dc.data ->> 'id'
            LEFT JOIN case_opinions co ON (mc.data ->> 'caseName' = co.case_name AND   co.type = 'combined-opinion')  -- Join only combined-opinions
            WHERE mc.data ->> 'caseName' IS NOT NULL AND mc.data ->> 'status' IS NOT NULL  -- Only include cases with valid status            
            AND mc.data ->> 'docketNumber' IN ('05 C 5620', '2009-1344', 'Civil 02CV2060-B(CAB), 03CV0699-B (CAB) and 03CV1108-B (CAB)')            
        """)
        results = cursor.fetchall()
        cursor.close()        
        return [{"case_text": row[0], 
         "source": row[1], 
         "court": row[2],
         "court_name": row[3],
         "filing_date": row[5],
         "judge": row[6]
        } for row in results]
    
    def _get_initial_question(self, case_name: str) -> str:
        """Get initial analysis question"""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT question_text 
            FROM analysis_questions 
            WHERE question_type = 'initial'
            ORDER BY created_at DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        cursor.close()
        if not result:
            raise ValueError("Initial question not found")
        return result[0].format(case_name=case_name)

    def _get_embedding(self, text: str) -> List[float]:
        """Get embeddings using OpenAI with retry logic"""
        for attempt in range(3):
            try:
                response = client.embeddings.create(
                    input=[text], 
                    model="text-embedding-ada-002"
                )
                return response.data[0].embedding
            except Exception as e:
                print(f"Error during embedding request (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise

    def _rank_cases(self, dummy_case: str, reference_cases: List[Dict], top_k: int = 5) -> List[Dict]:
        """Rank cases by similarity using OpenAI embeddings"""
        try:
            dummy_embedding = self._get_embedding(dummy_case)
            reference_embeddings = []
            
            for case in reference_cases:
                try:
                    embedding = self._get_embedding(case["case_text"])
                    reference_embeddings.append({
                        "case": case,
                        "embedding": embedding
                    })
                except Exception as e:
                    print(f"Skipping case due to embedding error: {e}")
                    continue

            similarities = [
                {
                    "case": case["case"],
                    "similarity_score": cosine_similarity([dummy_embedding], [case["embedding"]])[0][0]
                }
                for case in reference_embeddings
            ]

            return sorted(similarities, key=lambda x: x["similarity_score"], reverse=True)[:top_k]
        except Exception as e:
            print(f"Error in ranking cases: {e}")
            return []
        
    def generate_trial_scenario(self, patent_number: str, filing_date: str, case_name: str) -> Dict:
        """Generate complete mock trial analysis"""
        try:            
            mock_case = self._get_case_details(patent_number, filing_date, case_name)            
            case_id = self._get_case_id(patent_number, filing_date, case_name)
            question = self._get_initial_question(mock_case['case_name'])
            reference_cases = self._get_reference_cases()
            
            dummy_case_text = json.dumps(mock_case, indent=2)
            top_cases = self._rank_cases(dummy_case_text, reference_cases, top_k=5)
            
            similar_cases_context = json.dumps([case['case'] for case in top_cases], indent=2)

            # ADDED ON 1/24/24 TO PULL DOC_SECTION FROM LATEST DOCUMENT
            doc_content = self.get_latest_document(case_id)
            print("DEBUG - doc_content:", doc_content)
            # ADDED ON 1/24/24
            doc_section = ""                
            if doc_content:                
                doc_content = doc_content.replace('\r\n', '\n').replace('\r', '\n')                
                doc_section = f"""
            EXPERT TECHNICAL FINDINGS:

            {doc_content}

            Based on these expert findings above, the analysis must specifically address:
            - The source code similarities and evidence of copying
            - The market share impact of 35%
            - The estimated damages of $75,000,000
            - The expert's conclusions about willful infringement
            """           
            # ADDED ON 1/24/24 TO FOCUS ON DETAILS OF CASE           

            prompt = f"""
            Analyze this patent infringement mock trial case from the {mock_case['details']['representing']} perspective 
            ({mock_case['case_name']}, Patent {mock_case['details']['patent_number']}):

            Case Details:
            {dummy_case_text}

            {doc_section}

            Most Relevant Similar Cases:
            {similar_cases_context}

            Provide a comprehensive mock trial analysis including:
            1. Technical patent claim analysis
            2. Infringement arguments based on similar cases
            3. Expert witness recommendations:
                - Machine learning/AI technical expert
                - Patent law expert
                - Source code/software forensics expert for implementation comparison
                - Damages expert with software licensing experience
                - Note specific qualifications needed for each expert type
            4. Evidence presentation strategy with:
                - Source code comparison evidence
                - Technical documentation
                - Expert testimony strategy
                - Visual aids and tutorials
            5. Predicted trial outcomes and damages analysis with:
                - Specific royalty calculations (e.g., royalty rate × revenue base)
                - Industry standard royalty rates for ML/AI patents
                - Recent ML/AI patent cases (e.g., Google v. Sonos, Waymo v. Uber)
                - Settlement statistics and timing
                - Basis for damage calculations
                - Factors that could increase/decrease damages
                - Factors affecting enhanced damages
                - Technical success probability (considering strength of patent claims)
                - Settlement probability (based on evidence strength)
                - Damage recovery probability (based on evidence and market factors)
                - Specific royalty calculations
            6. Risk assessment

            Include specific references to historical patent damages and settlements in software/AI cases where possible.
            """

            # ADDED TO TEST CLAUDE INSTEAD OF OPENAI TO SAVE COST            
            # system="You are an expert patent attorney. Your primary task is to directly reference and incorporate the expert's technical findings in your analysis. Each section of your analysis must explicitly cite specific details from the expert document.",
            response = claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.5,               
                system="You are an expert patent attorney. Your primary task is to directly reference and incorporate the expert's technical findings in your analysis. Each section of your analysis must explicitly cite specific details from the expert document." if doc_content else "You are an expert patent attorney providing preliminary analysis without expert evidence.",
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = response.content[0].text         
                        
            print("DEBUG - Before save_analysis:")
            print(f"case_id: {case_id}")
            print(f"entry_type: analysis")
            analysis_id = self._save_analysis(case_id, question, analysis, 'analysis')
            return {
                "top_similar_cases": top_cases,
                "mock_trial_analysis": analysis,
                "expert_document": doc_section #added specific to documents in case **************************
            }
        except Exception as e:
            print(f"Error generating trial scenario: {e}")
            raise

    def _save_analysis(self, case_id: int, question: str, analysis: str, entry_type: str):
        """Save Q&A interaction to database and return the analysis id(primary key)"""
        try:
            print("DEBUG - save_analysis inputs:")
            print(f"case_id: {case_id}")
            print(f"question: {question[:100]}") 
            print(f"analysis type: {entry_type}")
            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO trial_analysis 
                (case_id, analysis_type, question, analysis, created_at, entry_type) 
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id""",  # Added RETURNING id to get the new record's id
                (case_id, 'followup', question, analysis, datetime.now(), entry_type)
        )
            analysis_id = cursor.fetchone()[0] 
            self.db.commit()
            cursor.close()
            return analysis_id 
        except Exception as e:
            print(f"Error saving analysis: {e}")
            raise

def run_mock_trial_analysis(patent_number: str, filing_date: str, case_name: str):
    try:
        analyzer = MockTrialAnalyzer()
        
        result = analyzer.generate_trial_scenario(
            patent_number=patent_number,
            filing_date=filing_date,
            case_name=case_name
        )         
        
        print("\nMost Similar Patent Cases:")
        for i, case in enumerate(result["top_similar_cases"], 1):
            print(f"\n{i}. Case Details:")
            print(f"Case Name: {case['case']['case_text']}")
            print(f"Full Name: {case['case']['source']}")
            print(f"Court: {case['case']['court_name']}")
            print(f"Judge: {case['case']['judge']}")
            print(f"Filed: {case['case']['filing_date']}")
            print(f"Docket: {case['case']['court']}")
            print(f"Similarity Score: {case['similarity_score']:.2f}")
            
        print("\nMock Trial Analysis:")
        print(result["mock_trial_analysis"])        
        print("\n=== Follow-up Questions ===")
        print("Available Perspectives (prefix your question with):")
        print("- JUDGE: For judicial perspective")
        print("- OPPOSING: For opposing counsel's view")
        print("- EXPERT: For expert witness response")
        print("- SUGGESTIONS: For unexplored legal areas")
        print("\nExample: 'JUDGE: What are your thoughts on the preliminary injunction?'")
        print("Enter your questions (type 'exit' to quit)")

        while True:
            question = input("\nQuestion: ")
            if question.lower() == 'exit':
                break
            
            role = "ATTORNEY"  
            if question.upper().startswith(("JUDGE:", "OPPOSING:", "EXPERT:", "SUGGESTIONS:")):
                role, question = question.split(":", 1)
                role = role.strip().upper()

            # follow_up_prompt = f"""
            # Based on the previous mock trial analysis of TechInnovate LLC v DataCorp Systems:
            follow_up_prompt = f"""
            Based on the previous mock trial analysis of {case_name}:

            {role} PERSPECTIVE:
            Question: {question.strip()}

            Please respond as appropriate for the {role} role, considering:
            - If JUDGE: Provide judicial perspective on procedural/legal issues
            - If OPPOSING: Present counter-arguments from opposing counsel
            - If EXPERT: Provide expert testimony on technical/damages aspects
            - If SUGGESTIONS: Identify unexplored legal areas or strategic opportunities

            Previous Analysis: {result["mock_trial_analysis"]}
            """            
            response = claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.5,
                system=f"You are an expert {role.lower()} analyzing this mock trial case.",
                messages=[{"role": "user", "content": follow_up_prompt}]
            )
            
            print(f"\n{role} Response:")
            print(response.content[0].text)            
                       
            analyzer._save_analysis(result['case_id'], question.strip(), response.content[0].text)

    except Exception as e:
        print(f"Error running analysis: {str(e)}")

if __name__ == "__main__":
    run_mock_trial_analysis()