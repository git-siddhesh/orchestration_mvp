from utils.db_utils import execute_query
from typing import Dict, List, Tuple, Any, Union

def get_user_paysheet(**kwargs:Dict[str, Any]) -> Dict | None:
    code = kwargs.get("user_id")
    result:Any = execute_query("SELECT * FROM paysheet WHERE Code = ?", args=(code,))
    print(result)
    return result[0] if result else {}


def get_leave_balance(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    month = kwargs.get("month")
    department = kwargs.get("department")
    return {
        "Sick_Leave": 10,
        "Casual_Leave": 5,
        "Earned_Leave": 15,
    }


def calculate_bonus_amount(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    fiscal_year = kwargs.get("fiscal_year")
    bonus_amount = 50000
    bonus_type = "Performance Bonus"
    return {
        "bonus_amount": bonus_amount,
        "bonus_type": bonus_type,
    }

def process_leave_encashment(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    leave_type = kwargs.get("leave_type")
    encashment_request = kwargs.get("encashment_request")

    return {
        "encashment_amount": 5000,
    }

def calc_total_reimbursement_for_dept(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    department = kwargs.get("department")
    month = kwargs.get("month")
    total_reimbursement = 500000
    return {
        "total_reimbursement": total_reimbursement,
    }

def update_paysheet(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    department = kwargs.get("Department")
    designation = kwargs.get("Designation")

    return {
        "status": "Updated",
        "message": "Paysheet updated successfully",
    }

def add_deduction(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    name = kwargs.get("Name")
    deductions = kwargs.get("Deductions")
    reason = kwargs.get("Reason")

    return {
        "status": "Success",
        "message": "Deduction added successfully",
    }

def fetch_deductions(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    return {
        "user_id": user_id,
        "Deductions": 5000,
        "Reason": "Loan repayment",
    }

def submit_reimbursement_request(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    reimbursements = kwargs.get("Reimbursements")
    reason = kwargs.get("Reason")
    remarks = kwargs.get("Remarks")

    return {
        "status": "Success",
        "message": "Reimbursement request submitted successfully",
    }

def get_monthly_reimbursements(**kwargs:Dict[str, Any]) -> Dict[str, Any]:
    user_id = kwargs.get("user_id")
    return {
        "amount": 10000,
        "Bill_No": "BILL123",
        "Reason": "Travel expenses",
        "Approval_Status": "Approved",
        "Remark": "Approved by manager",
    }

def get_user_bonus_details(**kwargs):
    user_id = kwargs.get("user_id")
    fiscal_year = kwargs.get("fiscal_year")
    return {
        "bonus_amount": 50000,
        "bonus_type": "Performance Bonus",
    }

def get_user_increment_details(**kwargs):
    user_id = kwargs.get("user_id")
    fiscal_year = kwargs.get("fiscal_year")
    return {
        "increment_percentage": 10,
        "effective_date": "2024-04-01",
    }

def get_travel_claim_status(**kwargs):
    user_id = kwargs.get("user_id")
    claim_id = kwargs.get("claim_id")
    return {
        "status": "Approved",
        "settlement_amount": 12000,
        "settlement_date": "2024-05-15",
    }

def get_local_conveyance_limit(**kwargs):
    user_id = kwargs.get("user_id")
    location = kwargs.get("location")
    return {
        "daily_limit": 500,
        "monthly_limit": 15000,
    }

def get_staff_welfare_eligibility(**kwargs):
    user_id = kwargs.get("user_id")
    employment_type = kwargs.get("employment_type")
    return {
        "eligibility": True,
        "benefits": "Gym membership, meal coupons",
    }

def get_rnr_rewards_details(**kwargs):
    user_id = kwargs.get("user_id")
    achievement_id = kwargs.get("achievement_id")
    return {
        "reward_points": 1000,
        "reward_description": "Outstanding Performer Award",
    }

def get_user_incentive_details(**kwargs):
    user_id = kwargs.get("user_id")
    fiscal_year = kwargs.get("fiscal_year")
    performance_rating = kwargs.get("performance_rating")
    return {
        "incentive_amount": 25000,
        "criteria": "Exceeds Expectations",
    }

def get_it_damages_recovery_amount(**kwargs):
    user_id = kwargs.get("user_id")
    item_damaged = kwargs.get("item_damaged")
    return {
        "recovery_amount": 15000,
        "item_description": "Laptop screen damage",
    }

def get_user_tax_deductions(**kwargs):
    user_id = kwargs.get("user_id")
    fiscal_year = kwargs.get("fiscal_year")
    return {
        "tax_deducted": 75000,
        "taxable_income": 500000,
    }

def get_pf_contribution_details(**kwargs):
    user_id = kwargs.get("user_id")
    fiscal_year = kwargs.get("fiscal_year")
    return {
        "employee_contribution": 30000,
        "employer_contribution": 30000,
        "total_pf": 60000,
    }

def get_salary_breakdown(**kwargs):
    user_id = kwargs.get("user_id")
    month = kwargs.get("month")
    return {
        "basic": 50000,
        "hra": 25000,
        "other_allowances": 10000,
        "total_salary": 85000,
    }

def get_user_payroll_status(**kwargs):
    user_id = kwargs.get("user_id")
    month = kwargs.get("month")
    return {
        "status": "Processed",
        "payment_date": "2024-03-31",
    }

def get_international_payroll_details(**kwargs):
    user_id = kwargs.get("user_id")
    country = kwargs.get("country")
    return {
        "local_currency_salary": 3000,
        "conversion_rate": 75,
        "home_currency_salary": 225000,
    }

def get_travel_policy_limits(**kwargs):
    user_id = kwargs.get("user_id")
    travel_type = kwargs.get("travel_type")
    return {
        "domestic_limit": 50000,
        "international_limit": 200000,
    }

def get_salary_equity_comparison(**kwargs):
    user_id = kwargs.get("user_id")
    department = kwargs.get("department")
    position = kwargs.get("position")
    return {
        "average_salary": 70000,
        "position_salary_range": "60000-80000",
        "equity_status": "Fair",
    }

def get_leave_balance(**kwargs):
    user_id = kwargs.get("user_id")
    leave_type = kwargs.get("leave_type")
    return {
        "leave_balance": 10,
        "leave_type": "sick",
    }

def get_max_encashable_leave(**kwargs):
    user_id = kwargs.get("user_id")
    leave_type = kwargs.get("leave_type")
    return {
        "max_encashable_leave": 5,
        "leave_type": "earned",
    }


tools = {
    "get_user_paysheet": get_user_paysheet,
    "calculate_bonus_amount": calculate_bonus_amount,
    "process_leave_encashment": process_leave_encashment,
    "calc_total_reimbursement_for_dept": calc_total_reimbursement_for_dept,
    "update_paysheet": update_paysheet,
    "add_deduction": add_deduction,
    "fetch_deductions": fetch_deductions,
    "submit_reimbursement_request": submit_reimbursement_request,
    "get_monthly_reimbursements": get_monthly_reimbursements,
    "get_user_bonus_details": get_user_bonus_details,
    "get_user_increment_details": get_user_increment_details,
    "get_travel_claim_status": get_travel_claim_status,
    "get_local_conveyance_limit": get_local_conveyance_limit,
    "get_staff_welfare_eligibility": get_staff_welfare_eligibility,
    "get_rnr_rewards_details": get_rnr_rewards_details,
    "get_user_incentive_details": get_user_incentive_details,
    "get_it_damages_recovery_amount": get_it_damages_recovery_amount,
    "get_user_tax_deductions": get_user_tax_deductions,
    "get_pf_contribution_details": get_pf_contribution_details,
    "get_salary_breakdown": get_salary_breakdown,
    "get_user_payroll_status": get_user_payroll_status,
    "get_international_payroll_details": get_international_payroll_details,
    "get_travel_policy_limits": get_travel_policy_limits,
    "get_salary_equity_comparison": get_salary_equity_comparison,
    "get_leave_balance": get_leave_balance,
    "get_max_encashable_leave": get_max_encashable_leave

}