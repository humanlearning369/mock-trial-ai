from pymongo import MongoClient
from dotenv import load_dotenv
from transformers import AutoModel, AutoModelForMaskedLM, AutoTokenizer
import torch
import os
import pinecone
from pinecone import Pinecone
import psycopg2
from datetime import datetime
from typing import Dict

load_dotenv(r'C:\[your_path_here]\mock_trial_app\config.env')

CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

DB_CONFIG = {
    "dbname": "mock_trial_db",
    "user": "[user]",
    "password": "[password]",
    "host": "localhost",
    "port": "5432"
}

class MockTrialAnalyzer:
    def __init__(self):        
        self.db = psycopg2.connect(**DB_CONFIG)    
        
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo_db = self.mongo_client['mock_trial_analytics']    
        
        pc = Pinecone(api_key=PINECONE_API_KEY)
        self.pinecone_index = pc.Index("[your_index_name_here")    
       
        self.model_path = r'C:\[your_path_here]\mock_trial_app\legalbertmt'
        self.masked_model = AutoModelForMaskedLM.from_pretrained(self.model_path)
        self.embedding_model = AutoModel.from_pretrained('nlpaueb/legal-bert-base-uncased')
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
    
    def test_model(self, text: str):
        """Test LegalBERT model with masked token prediction - make recursive agent - second file"""
        inputs = self.tokenizer(text, return_tensors="pt")
        token_ids = inputs["input_ids"][0]
        rand_idx = torch.randint(1, len(token_ids)-1, (1,))
        original_token = token_ids[rand_idx]
        token_ids[rand_idx] = self.tokenizer.mask_token_id
        attention_mask = torch.ones_like(token_ids)
    
        with torch.no_grad():
            outputs = self.masked_model(input_ids=token_ids.unsqueeze(0), 
                                     attention_mask=attention_mask.unsqueeze(0))
            predictions = outputs.logits
    
        predicted_token_id = torch.argmax(predictions[0, rand_idx]).item()
    
        return {
            "masked_text": self.tokenizer.decode(token_ids),
            "original_text": self.tokenizer.decode(original_token),
            "predicted_text": self.tokenizer.decode(predicted_token_id)
        }
    
    def get_embedding(self, text: str) -> list:
        """Generate embedding for text using LegalBERT"""
        try:
            inputs = self.tokenizer(text, return_tensors="pt", 
                                  max_length=512, truncation=True, padding=True)
            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                # this should work as AutoModel - last_hidden_state
                embedding = outputs.last_hidden_state.mean(dim=1)
            return embedding[0].tolist()
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

    def sync_to_mongodb(self):
        """Sync PostgreSQL data to MongoDB"""
        try:            
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT id, data 
                FROM mock_cases
            """)
            cases = cursor.fetchall()
            
            cursor.execute("""
                SELECT id, case_id, filename, extracted_text 
                FROM case_documents
            """)
            documents = cursor.fetchall()
            
            cases_collection = self.mongo_db.cases
            docs_collection = self.mongo_db.documents

            for case_id, data in cases:
                cases_collection.update_one(
                    {'postgresql_id': case_id},
                    {
                        '$set': {
                            'data': data,
                            'last_updated': datetime.now()
                        }
                    },
                    upsert=True
                )

            for doc_id, case_id, filename, text in documents:
                docs_collection.update_one(
                    {'postgresql_id': doc_id},
                    {
                        '$set': {
                            'case_id': case_id,
                            'filename': filename,
                            'text': text,
                            'last_updated': datetime.now()
                        }
                    },
                    upsert=True
                )

            return True
        except Exception as e:
            print(f"Sync error: {e}")
            return False
        
    def get_combined_similarity(self, case_id: int, test_text: str):
        """Get similarity using LegalBERT embeddings"""
        try:            
            test_embedding = self.get_embedding(test_text)        
            
            results = self.pinecone_index.query(
                vector=test_embedding,
                top_k=5,
                include_metadata=True
            )
        
            return results
        except Exception as e:
            print(f"Similarity search error: {e}")
            return None

    def analyze_case(self, case_id: int) -> Dict:
        """Enhanced case analysis with LegalBERT"""
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT data FROM mock_cases WHERE id = %s", (case_id,))
            case_data = cursor.fetchone()
    
            if not case_data:
                return {}
        
            cursor.execute("""
                SELECT extracted_text 
                FROM case_documents 
                WHERE case_id = %s
            """, (case_id,))
            documents = cursor.fetchall()
    
            analysis_results = []
            for doc in documents:
                text = doc[0]
                embedding = self.get_embedding(text)
                bert_analysis = self.test_model(text)            
                
                self.pinecone_index.upsert([{
                    'id': f"case_{case_id}_doc_{len(analysis_results)}",
                    'values': embedding,
                    'metadata': {'case_id': case_id}
                }])
            
                analysis_results.append(bert_analysis)    
            
            analytics_collection = self.mongo_db.analytics
            analytics_result = analytics_collection.insert_one({
                'case_id': case_id,
                'analysis_date': datetime.now(),
                'case_data': case_data[0],
                'bert_analysis': analysis_results
            })
    
            return {
                'case_id': case_id,
                'analysis_id': str(analytics_result.inserted_id),
                'bert_analysis': analysis_results
            }
    
        except Exception as e:
            print(f"Analysis error: {e}")
            self.db.rollback()
            return {}