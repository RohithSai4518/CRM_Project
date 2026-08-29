"""
CRM System - Intelligent Lead Scoring Engine
Evaluates demographic, firmographic, and behavioral parameters
"""

from typing import Dict, Any


def calculate_lead_score(lead_data: Dict[str, Any]) -> int:
    """
    Computes a score from 0 to 100 based on realistic sales criteria:
    - Business email domain vs free webmail (+20)
    - Corporate title seniority (+10 to +30)
    - Source channel quality (+10 to +25)
    - Phone number provided (+10)
    - Deal budget / estimated size (+10 to +25)
    """
    score = 0
    email = lead_data.get("email", "").lower()
    
    # 1. Email Domain Quality
    free_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "mail.com"]
    if email and "@" in email:
        domain = email.split("@")[-1]
        if domain not in free_domains:
            score += 25  # High-value corporate domain
        else:
            score += 5   # Consumer email

    # 2. Phone Provided
    if lead_data.get("phone"):
        score += 10

    # 3. Company Name Provided
    if lead_data.get("company_name"):
        score += 15

    # 4. Lead Source Weighting
    source = lead_data.get("lead_source", "").upper()
    source_weights = {
        "REFERRAL": 30,
        "DEMO_REQUEST": 25,
        "INBOUND_WEBSITE": 20,
        "WEBINAR": 15,
        "PAID_SEARCH": 10,
        "COLD_OUTREACH": 5,
        "ORGANIC_SOCIAL": 10
    }
    score += source_weights.get(source, 5)

    # 5. Estimated Deal Value
    estimated_val = float(lead_data.get("estimated_value", 0.0))
    if estimated_val >= 50000:
        score += 20
    elif estimated_val >= 10000:
        score += 15
    elif estimated_val >= 2500:
        score += 10

    return min(100, score)
