def get_life_policy_options(**kwargs):
    user_id = kwargs.get("user_id")
    age = kwargs.get("age")
    sum_assured = kwargs.get("sum_assured")
    policy_type = kwargs.get("policy_type")
    return {
        "policy_id": "LIFE123",
        "policy_name": "Comprehensive Life Plan",
        "premium": 15000,
        "benefits": "Life cover, accidental death benefits",
    }

def get_life_coverage_details(**kwargs):
    user_id = kwargs.get("user_id")
    policy_id = kwargs.get("policy_id")
    return {
        "coverage": "1 Crore",
        "exclusions": "Pre-existing conditions for 2 years",
        "riders": "Critical illness, disability cover",
        "claim_limit": "10 claims per year",
    }

def submit_life_claim_request(**kwargs):
    user_id = kwargs.get("user_id")
    policy_id = kwargs.get("policy_id")
    claim_reason = kwargs.get("claim_reason")
    documents = kwargs.get("documents")
    return {
        "claim_id": "CLM456",
        "status": "Under Review",
        "expected_settlement": "2 Lakhs",
    }

def calculate_life_premium(**kwargs):
    user_id = kwargs.get("user_id")
    age = kwargs.get("age")
    policy_id = kwargs.get("policy_id")
    payment_frequency = kwargs.get("payment_frequency")
    return {
        "premium_amount": 12000,
        "payment_due_date": "2024-01-15",
    }

def compare_health_policies(**kwargs):
    user_id = kwargs.get("user_id")
    age = kwargs.get("age")
    family_members = kwargs.get("family_members")
    coverage_amount = kwargs.get("coverage_amount")
    return {
        "policy_comparison_table": ["Policy A: $500 premium", "Policy B: $450 premium"],
        "best_option": "Policy B",
    }

def get_network_hospitals(**kwargs):
    user_id = kwargs.get("user_id")
    pincode = kwargs.get("pincode")
    policy_id = kwargs.get("policy_id")
    return {
        "hospital_list": ["Hospital A", "Hospital B"],
        "cashless_eligibility": True,
    }

def submit_health_claim(**kwargs):
    user_id = kwargs.get("user_id")
    policy_id = kwargs.get("policy_id")
    hospital_id = kwargs.get("hospital_id")
    treatment_details = kwargs.get("treatment_details")
    return {
        "claim_status": "Approved",
    }

def get_motor_policy_types(**kwargs):
    user_id = kwargs.get("user_id")
    vehicle_type = kwargs.get("vehicle_type")
    vehicle_age = kwargs.get("vehicle_age")
    coverage_amount = kwargs.get("coverage_amount")
    return {
        "policy_options": ["Basic Plan", "Premium Plan"],
        "premium_breakdown": "Base premium: $300, Add-ons: $50",
    }

def renew_motor_policy(**kwargs):
    user_id = kwargs.get("user_id")
    policy_id = kwargs.get("policy_id")
    vehicle_condition_report = kwargs.get("vehicle_condition_report")
    return {
        "new_policy_id": "MOTOR789",
    }

def check_home_loan_eligibility(**kwargs):
    user_id = kwargs.get("user_id")
    income = kwargs.get("income")
    credit_score = kwargs.get("credit_score")
    loan_amount = kwargs.get("loan_amount")
    return {
        "eligibility_status": "Eligible",
        "max_loan_amount": "50 Lakhs",
        "interest_rate": "7.5%",
    }

def calculate_tax_benefits(**kwargs):
    user_id = kwargs.get("user_id")
    investment_id = kwargs.get("investment_id")
    income_details = kwargs.get("income_details")
    return {
        "tax_saved": "15,000",
        "eligibility_sections": "Section 80C, 80D",
    }

def get_pension_plan_options(**kwargs):
    user_id = kwargs.get("user_id")
    investment_amount = kwargs.get("investment_amount")
    age = kwargs.get("age")
    return {
        "plan_id": "PENS101",
        "returns_projection": "7% annual return",
    }

def get_card_rewards(**kwargs):
    user_id = kwargs.get("user_id")
    card_id = kwargs.get("card_id")
    transaction_category = kwargs.get("transaction_category")
    return {
        "reward_points": 1200,
        "cashback_offered": "$50",
    }

tools = {
    "get_life_policy_options": get_life_policy_options,
    "get_life_coverage_details": get_life_coverage_details,
    "submit_life_claim_request": submit_life_claim_request,
    "calculate_life_premium": calculate_life_premium,
    "compare_health_policies": compare_health_policies,
    "get_network_hospitals": get_network_hospitals,
    "submit_health_claim": submit_health_claim,
    "get_motor_policy_types": get_motor_policy_types,
    "renew_motor_policy": renew_motor_policy,
    "check_home_loan_eligibility": check_home_loan_eligibility,
    "calculate_tax_benefits": calculate_tax_benefits,
    "get_pension_plan_options": get_pension_plan_options,
    "get_card_rewards": get_card_rewards
}
