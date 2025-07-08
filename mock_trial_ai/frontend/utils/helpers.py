"""
Mock Trial AI Application (LawCourtIQ)
Copyright (c) 2025 Frank Garcia

This file is part of Mock Trial AI, dual-licensed under:
- GNU Affero General Public License v3.0 (AGPL-3.0)
- Commercial License (contact for terms)

See LICENSE and COMMERCIAL_LICENSE for details.
"""
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AnalysisHelper:
    @staticmethod
    def format_date(date_str: str) -> str:
        """Format date string to consistent format"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%B %d, %Y")
        except ValueError:
            return date_str

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency values"""
        return f"${amount:,.2f}"

    @staticmethod
    def calculate_success_probability(factors: Dict[str, float]) -> float:
        """Calculate case success probability based on various factors"""
        weights = {
            "technical_merit": 0.3,
            "prior_cases": 0.2,
            "evidence_strength": 0.3,
            "jurisdiction_favorability": 0.2
        }
        
        probability = sum(factors.get(k, 0) * v for k, v in weights.items())
        return min(max(probability, 0), 1)  

    @staticmethod
    def estimate_case_duration(case_type: str, complexity: float) -> str:
        """Estimate case duration based on type and complexity"""
        base_durations = {
            "patent": 24,
            "contract": 12,
            "employment": 18
        }
        
        base = base_durations.get(case_type, 18)
        adjusted = base * (1 + complexity)
        return f"{int(adjusted)-6}-{int(adjusted)} months"

    @staticmethod
    def validate_case_data(data: Dict[str, Any]) -> Optional[str]:
        """Validate case data completeness"""
        required_fields = {
            "patent": ["patent_number", "filing_date", "technical_field"],
            "contract": ["contract_date", "contract_value", "breach_type"],
            "employment": ["employment_type", "incident_date", "claim_type"]
        }
        
        case_type = data.get("type")
        if not case_type:
            return "Case type is required"
            
        missing = [field for field in required_fields[case_type] 
                  if not data.get(field)]
        
        if missing:
            return f"Missing required fields: {', '.join(missing)}"
        return None

class LogHelper:
    @staticmethod
    def log_analysis_event(event_type: str, details: Dict[str, Any]) -> None:
        """Log analysis events for tracking"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details
        }       
        print(json.dumps(log_entry))  
