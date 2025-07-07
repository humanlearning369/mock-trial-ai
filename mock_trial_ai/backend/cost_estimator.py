import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor

@dataclass
class CostConfig:
    """Configuration for API and processing costs"""
    CLAUDE_INPUT_COST_PER_MILLION = 15.0  
    CLAUDE_OUTPUT_COST_PER_MILLION = 75.0  
    OPENAI_EMBEDDING_COST_PER_MILLION = 0.10  
    DB_QUERY_COST_PER_HOUR = 0.50  
    STORAGE_COST_PER_GB = 0.10  

@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str = "localhost"
    port: int = 5432
    dbname: str = "mock_trial_db"
    user: str = "[user]"
    password: str = "[password]"

class SQLQueryAnalyzer:
    """Analyzes SQL queries and their results"""
    def __init__(self):        
        self.special_sequences = [
            "http://", "https://", ".com", ".org", ".gov",
            "@", "#", "$", "%", "&", 
            "SELECT", "FROM", "WHERE", "JOIN", "ORDER BY",
            "JSON", "VARCHAR", "INTEGER", "TIMESTAMP"
        ]
        
    def estimate_token_count(self, text: Union[str, dict, list]) -> int:
        """Estimate tokens using Claude-like tokenization logic"""
        if isinstance(text, (dict, list)):
            text = json.dumps(text, ensure_ascii=False)
        elif not isinstance(text, str):
            text = str(text)            
        
        for seq in self.special_sequences:
            text = text.replace(seq, "TOKEN")            
        
        import re
        words = re.findall(r'\b\w+\b|[^\w\s]', text)        
        
        token_count = 0
        for word in words:            
            if word.isdigit():
                token_count += len(word) // 2 + 1            
            elif len(word) > 8:
                token_count += len(word) // 4 + 1            
            else:
                token_count += 1                
        
        token_count += text.count('\n')
        token_count += text.count('  ') 
        
        return token_count

    def analyze_query_result(self, result: List[Dict]) -> Dict:
        """Analyze query results for size and token counts"""
        total_chars = 0
        total_tokens = 0
        rows_analyzed = 0
        
        for row in result:
            row_str = json.dumps(row, ensure_ascii=False)
            total_chars += len(row_str)
            total_tokens += self.estimate_token_count(row_str)
            rows_analyzed += 1
            
        return {
            "rows": rows_analyzed,
            "total_chars": total_chars,
            "total_tokens": total_tokens,
            "avg_tokens_per_row": total_tokens / rows_analyzed if rows_analyzed > 0 else 0
        }

class QueryExecutor:
    """Executes SQL queries and measures performance"""
    def __init__(self, db_config: DatabaseConfig):
        self.db_config = db_config
        
    def execute_query(self, query: str) -> tuple[List[Dict], float]:
        """Execute query and return results with execution time"""
        start_time = time.time()
        
        with psycopg2.connect(
            host=self.db_config.host,
            port=self.db_config.port,
            dbname=self.db_config.dbname,
            user=self.db_config.user,
            password=self.db_config.password,
            cursor_factory=RealDictCursor
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("EXPLAIN ANALYZE " + query)
                execution_plan = cur.fetchall()
                
                cur.execute(query)
                results = cur.fetchall()
                
        execution_time = time.time() - start_time
        return results, execution_time

class ImprovedMockTrialCostEstimator:
    """Enhanced cost estimator for mock trial application queries"""
    
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        self.config = CostConfig()
        self.db_config = db_config or DatabaseConfig()
        self.query_analyzer = SQLQueryAnalyzer()
        self.query_executor = QueryExecutor(self.db_config)
        
    def estimate_query_costs(self, query: str) -> Dict:
        """Estimate costs for executing and processing a query"""        
        
        results, execution_time = self.query_executor.execute_query(query)        
        
        result_analysis = self.query_analyzer.analyze_query_result(results)        
        
        db_cost = (execution_time / 3600) * self.config.DB_QUERY_COST_PER_HOUR
        
        input_tokens = result_analysis["total_tokens"]
        estimated_output_tokens = int(input_tokens * 1.5)  
        
        claude_input_cost = (input_tokens / 1_000_000) * self.config.CLAUDE_INPUT_COST_PER_MILLION
        claude_output_cost = (estimated_output_tokens / 1_000_000) * self.config.CLAUDE_OUTPUT_COST_PER_MILLION        
       
        storage_size_gb = result_analysis["total_chars"] / (1024 * 1024 * 1024)
        storage_cost = storage_size_gb * self.config.STORAGE_COST_PER_GB
        
        total_cost = db_cost + claude_input_cost + claude_output_cost + storage_cost
        
        return {
            "timestamp": datetime.now().isoformat(),
            "query_stats": {
                "execution_time_seconds": execution_time,
                "rows_processed": result_analysis["rows"],
                "total_chars": result_analysis["total_chars"],
                "total_input_tokens": input_tokens,
                "estimated_output_tokens": estimated_output_tokens,
                "avg_tokens_per_row": result_analysis["avg_tokens_per_row"]
            },
            "costs": {
                "database_cost": db_cost,
                "claude_input_cost": claude_input_cost,
                "claude_output_cost": claude_output_cost,
                "storage_cost": storage_cost,
                "total_cost": total_cost
            }
        }

    def print_cost_report(self, query_name: str, cost_estimate: Dict):
        """Print formatted cost report"""
        print(f"\nCost Analysis Report for: {query_name}")
        print("=" * 80)
        print(f"Generated on: {datetime.now()}\n")
        
        print("QUERY STATISTICS")
        print("-" * 40)
        stats = cost_estimate["query_stats"]
        print(f"Execution Time: {stats['execution_time_seconds']:.3f} seconds")
        print(f"Rows Processed: {stats['rows_processed']:,}")
        print(f"Total Characters: {stats['total_chars']:,}")
        print(f"Input Tokens: {stats['total_input_tokens']:,}")
        print(f"Est. Output Tokens: {stats['estimated_output_tokens']:,}")
        print(f"Avg Tokens/Row: {stats['avg_tokens_per_row']:.1f}\n")
        
        print("COST BREAKDOWN")
        print("-" * 40)
        costs = cost_estimate["costs"]
        print(f"Database Cost: ${costs['database_cost']:.4f}")
        print(f"Claude Input Cost: ${costs['claude_input_cost']:.4f}")
        print(f"Claude Output Cost: ${costs['claude_output_cost']:.4f}")
        print(f"Storage Cost: ${costs['storage_cost']:.4f}")
        print(f"Total Cost: ${costs['total_cost']:.4f}\n")

def main():    
    simple_query = """
    SELECT data FROM mock_cases 
    WHERE data->>'case_name' ILIKE '%TechInnovate%DataCorp%'
    """
    
    complex_query = """
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
            mc.data -> 'citation' AS citation,  
            mc.data -> 'opinions' AS opinions,  
            mc.data ->> 'posture' AS posture,
   
            -- Docket Cases (dc) Table
            dc.data ->> 'case_name' AS docket_case_name,
            dc.data ->> 'court' AS docket_court,
            dc.data ->> 'docket_number' AS docket_case_number,
   
            -- Case Opinions (co) Table
            COALESCE(cc.data ->> 'summary', co.snippet) AS case_summary,  
            co.citation_ids AS opinion_citations,
            co.type AS opinion_type,
            co.author_id AS opinion_author_id,
            co.per_curiam AS opinion_per_curiam,
   
            -- Cluster Cases (cc) Table
            cc.data -> 'citations' AS citations,  
            cc.data ->> 'case_name_full' AS cluster_case_name_full,
            cc.data ->> 'judges' AS judges,
            cc.data ->> 'syllabus' AS syllabus,
            COALESCE(cc.data ->> 'disposition', co.type) AS case_disposition,  
            cc.data ->> 'precedential_status' AS precedential_status,
            cc.data -> 'sub_opinions' AS sub_opinions,  
            cc.data ->> 'arguments' AS arguments
            FROM main_cases mc
            JOIN docket_cases dc ON mc.data ->> 'docket_id' = dc.data ->> 'id'
            JOIN cluster_cases cc ON cc.data ->> 'docket_id' = dc.data ->> 'id'
            LEFT JOIN case_opinions co ON (mc.data ->> 'caseName' = co.case_name AND co.type = 'combined-opinion')
            WHERE mc.data ->> 'caseName' IS NOT NULL
            AND mc.data ->> 'status' IS NOT NULL  
            ORDER BY (mc.data->>'dateFiled')::DATE DESC
            LIMIT 5
    """    
    
    estimator = ImprovedMockTrialCostEstimator()    
    
    simple_costs = estimator.estimate_query_costs(simple_query)
    estimator.print_cost_report("Simple Query", simple_costs)
    
    complex_costs = estimator.estimate_query_costs(complex_query)
    estimator.print_cost_report("Complex Query", complex_costs)

if __name__ == "__main__":
    main()