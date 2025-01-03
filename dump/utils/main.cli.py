from openai import OpenAI
from pydantic import BaseModel
from typing import Optional
import json
from typing import List, ClassVar
from call_api_hr import *

# VARS = json.load(open("VARs.json"))
VARS = json.load(open("VARs_HR.json"))

from dotenv import load_dotenv
load_dotenv(override=True)

client = OpenAI()

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: List[str] = []

class APIAgent(Agent):
    input_vars: ClassVar[List[str]] = []  # Marked as ClassVar since it isn't part of the schema
    output_vars: ClassVar[List[str]] = []  # Marked as ClassVar
    api_use_case: ClassVar[str] = ""  # Marked as ClassVar
    api_url: ClassVar[str] = ""  # Marked as ClassVar

class RAGAgent(Agent):
    instructions: str = "You are a helpful RAG Agent"
    tools: List[str] = ["RAG"]

class ChatDB:
    def __init__(self):
        self.user_data = {}
        self.chat_history = {}  # store in redis and create some supporting functions to store and retrieve the chat history
        self.api_data = {} 
    
class Prompts:
    system_prompts = {
            "generate_slave_queries": """You are an intelligent system designed to decompose high-level user queries into actionable subqueries, with each subquery specifying:  

                                        1. **The precise information needed**  
                                        2. **The associated variables required to answer the subquery**  

                                        When given a user query, follow these steps:  

                                        1. Analyze the user query to determine the overall intent.  
                                        2. Break down the query into smaller subqueries needed to achieve the overall goal.  
                                        3. Identify the input variables required for each subquery and map them to relevant API calls.  
                                        4. Clearly format the output as a JSON structure, with each subquery as a key, and a list of output variables as the value.  

                                        #### Example Input Query:  
                                        "What will be the premium amount left and its due date for all of my policies?"

                                        #### Example Output JSON:  
                                        
                                        {
                                        "What are the policies the user has?": ["policy_id", "policy_name"],
                                        "What is the premium amount for each policy?": ["policy_id", "premium_amount", "premium_breakdown", "amount_paid"],
                                        "What is the due date of the premium for each policy?": ["policy_id", "premium_due_date", "penalty_charges"]
                                        }
                                        
                                        Note: 
                                        - The output should be in pure json format.
                                        - Use the exact variable names as provided and ensure subqueries depends on the provided varaibles only.
                                        - Ensure the subqueries are clear and independent.

                                        #### Guidelines for Generating Subqueries:  
                                        - Ensure subqueries are clear and independent.  
                                        - Include all variables required to generate a response for each subquery.  
                                        - Variables can be reused across multiple subqueries where applicable.  

                                        Now, proceed to generate subqueries for the given user query using the structure and format above.""",

            "get_missing_vars": """ You are an intelligent system designed to generate questions to collect missing details from the user. Given a query and the missing variables and create questions that the system can ask the user to retrieve those missing details.

                                    **Steps to follow:**
                                    1. Analyze the main user query .
                                    3. Generate clear and actionable questions to collect those missing variables from the user.
                                    4. Format the output as a numbered list of questions that need to be asked to the user.

                                    **Example Input:**
                                    User query: What will be the premium amount left and its due date for all of my policies?
                                    Missing variables: "policy_id", "policy_name", "premium_amount", "premium_breakdown", "amount_paid", "premium_due_date", "penalty_charges"
                                    

                                    **Example Output (List of Questions to ask):**
                                    
                                    {
                                        q1: What are the IDs of your policies?,
                                        q2: What are the names of your policies?,
                                        q3: What is the premium amount for each policy?,
                                        q4: What is the breakdown of the premium amount for each policy?,
                                        q5: What is the amount paid for each policy?,
                                        q6: What is the due date for the premium payment of each policy?,
                                        q7: Are there any penalty charges for late premium payments?
                                    }
                                    
                                    Note: The output should be in pure json format.

            """,

            "extract_vars": """You are an intelligent system designed to extract and store relevant variables from the user query and additional user data. 
                                Given a user query and additional user data, and variable names. extract the value in key-value pair.
                
                                    **Steps to follow:**
                                    1. Analyze the user query and additional user data.
                                    2. Identify the variables mentioned in the query and additional data.
                                    3. Extract the values associated with each variable in json format.
    
                                    **Example Input:**
                                    User query: What will be the premium amount left and its due date for all of my policies?
                                    Additional user data: {"what is your policy details": "12345", "Enter name of you policy": "Life Insurance Policy"}
                                    Variables: "policy_id", "policy_name"
    
                                    **Example Output (Stored Variables):**
                                    
                                    {
                                    "policy_id": "12345",
                                    "policy_name": "Life Insurance Policy",
                                    }
                                    

                                    Note: The output should be in pure json format.

                                    """,

            "api_evaluator": """You are an intelligent system designed to evaluate whether the current information is sufficient to answer the query satisfying its intent or do it need more analytic information over the present information.

                                Task:
                                Given the query and data, you need to decide the next course of action based on the following criteria:
                                1. If the information is sufficient to answer the query, and need no further processing, return the final response to the user.
                                2. If the information is sufficient but needs to provide a more humanized response, use LLMatic transformation to generate a more conversational response.
                                3. If the information is insufficient to answer the query, though it contains some factual data, use this information to generate more analytical responses from the documents using RAG agent.

                                Steps to follow:
                                1. Analyze the query and available data.
                                2. Extract the intent of the query, whether it is direct value-based or more analytical.
                                3. If response needs to be directly provided, return the final response.
                                4. If provided data are factual and need humanization, use LLMatic transformation.
                                5. If the data available need to be used along with some document and policies to generate more analytical response, use RAG agent to generate the response.

                                Expected output:
                                {
                                    "response_type" : "direct" | "llmatic" | "rag",
                                    "response" : "Response text" | "Transformed response" 
                                }

                                Note: The output should be in pure json format.
                                """,

        }


class LLMResponsePostProcessor:
    def __init__(self):
        pass

    def process(self, response, use="generate_slave_queries"):
        if use == "generate_slave_queries":
            return self.process_slave_queries(response)
        if use == "get_missing_vars":
            return self.process_missing_vars(response)
        if use == "extract_vars":
            return self.process_extract_vars(response)
    
    def process_extract_vars(self, response):
        # response format: "{'var': 'value', 'var': 'value'}"
        return json.loads(response)

    def process_missing_vars(self, response):
        # response format: "{1: the query, 2: the query}"
        return json.loads(response)

    def process_slave_queries(self, response):
        # some regular expression to extract slave queries and their dependent variables
        # response format: "{Slave Query 1: [var1, var2, var3], Slave Query 2: [var4, var5, var6]}"
        return json.loads(response)


class LLMAgent(Prompts, LLMResponsePostProcessor):

    # def __init__(self):
    model = "gpt-4o-mini"

    def llm_call(self, query, use):
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompts[use]}] + [{"role": "user", "content": query}],
            
        )
        message = response.choices[0].message.content
        print(f"{'-'*20}\n{message}\n{'-'*20}")
        return self.process(message, use)


class ChatBotBackend(LLMAgent):

    def __init__(self, memory, rag_agent):
        self.master_query = ""
        self.slave_queries = {}
        self.slave_responses = []
        self.api_agents = []
        self.apis = {} # {api_name: {"input_vars": [], "output_vars": []}}
        self.memory = memory
        self.missing_vars = []
        self.api_based_responses = None
        self.rag_agent = rag_agent

    def reset_state(self):
        self.master_query = ""
        self.slave_queries = {}
        self.slave_responses = []
        self.api_agents = []
        self.apis = {}
        self.memory = None
        self.missing_vars = []
        self.api_based_responses = None
        self.rag_agent = None
   
    def generate_slave_queries(self):
        llm_query = f"User query: {self.master_query}\n Variables: {', '.join(VARS.keys())}"
        response = self.llm_call(llm_query, use="generate_slave_queries")
        self.slave_queries = response

    def resolve_slave_queries_api_dependencies(self):
        for slave_query in self.slave_queries:
            for output_var in self.slave_queries[slave_query]:
                api_name = VARS[output_var]["api_to_be_called"]
                input_vars = VARS[output_var]["input_vars"]
                api = self.apis.get(api_name, {"input_vars": [], "output_vars": []})
                for input_var in input_vars:
                    if input_var not in self.memory.api_data or not self.memory.api_data[input_var]:
                        self.missing_vars.append(input_var)
                api["input_vars"] += input_vars
                api["output_vars"].append(output_var)
                self.apis[api_name] = api

        print("APIs:", self.apis)

    def update_memory(self, additional_user_data):
        llm_query = f"User query: {self.master_query}\nAdditional user data: {additional_user_data}\nVariables: {', '.join(self.missing_vars)}"
        response = self.llm_call(llm_query, use="extract_vars")
        self.memory.api_data.update(response)
    
    def execute_apis(self):
        for api_name in self.apis:
            # pass both memory.api_data and self.memory.user_data to the api
            api_response = tools[api_name](**self.memory.api_data, **self.memory.user_data)
            self.memory.api_data.update(api_response)

    def call_rag_agent(self, query):
        return f"This is RAG based response for the query: {query} : {self.api_based_responses}"

    def api_evaluator(self):
        """
        A decision maker that evaluates the API responses and decides the next course of action.
        1. Return the final response to the user as it is.
        2. Humanize the response using LLMatic transformation.
        3. Use these information and pass to RAG agent to generate more analytical response from the DOCUMETNS.
        """        
        print(self.memory.api_data)
        print(self.memory.user_data)
        string_formatted_api_data = ', '.join([f"{key}: {value}" for key, value in self.memory.api_data.items()])
        string_formatted_user_data = ', '.join([f"{key}: {value}" for key, value in self.memory.user_data.items()])
        llm_query = f"Mater query: {self.master_query}\n Available data: {self.memory.api_data + self.memory.user_data}"
        response = self.llm_call(llm_query, use="api_evaluator")
        self.api_based_responses = response["response"]

        if response["response_type"] == "direct":
            return response["response"]
        if response["response_type"] == "llmatic":
            return response["response"]
        if response["response_type"] == "rag":
            return self.call_rag_agent(response["response"])

    def get_api_response(self, query, additional_user_data):
        if query:
            # self.reset_state()
            print("User input:", query)
            self.master_query = query
            self.generate_slave_queries()

            print("Slave queries:", self.slave_queries)
            self.resolve_slave_queries_api_dependencies()
            if self.missing_vars:
                llm_query = f"User query: {query}\nMissing variables: {', '.join(self.missing_vars)}"
                response = self.llm_call(llm_query, use="get_missing_vars")
                return response, 1
            
            
        if additional_user_data:
            self.update_memory(additional_user_data)

        self.execute_apis()
        return self.api_evaluator()

        # return "This is a placeholder response for now. Please implement this method."
    

class ChatBotUI:
    def __init__(self):
        self.tree = {
            "Main Menu": {
                "Insurance": {
                    "Life Insurance": ["Policy Options", "Coverage Details", "Claim Process", "Premium Payment Options"],
                    "Health Insurance": ["Policy Comparison", "Family vs. Individual Plans", "Network Hospitals", "Claim Assistance"],
                    "Motor Insurance": ["Policy Types", "Add-ons", "Renewal Process", "Claim Process"]
                },
                "Loans": {
                    "Home Loan": {
                        "Product FAQs": ["Eligibility Criteria", "Interest Rates", "Loan Tenure", "Prepayment and Foreclosure"],
                        "Sales Pitch": ["Why Choose Us?", "Benefits of Our Home Loan", "Customer Testimonials"],
                        "Finance": ["Loan Against Property", "Top-up Loans", "Balance Transfer"]
                    }
                },
                "Investments": {
                    "Pension": ["Pension Plan Options", "Tax Benefits", "Withdrawal Rules"],
                    "Mutual Funds": ["Types of Mutual Funds", "Risk Assessment", "SIP vs. Lump Sum Investment"],
                    "Stock & Securities": ["Stock Market Basics", "Trading vs. Investing", "Stock Tips and Strategies"],
                    "FD & Digital Gold": ["Fixed Deposit Options", "Digital Gold Investment", "Returns and Benefits"],
                    "Tax Solutions": ["Tax-Saving Investments", "Filing Income Tax Returns", "Deductions Under 80C"]
                },
                "Payments": {
                    "Payment for Individuals": ["Bill Payments", "Loan EMI Payment", "Insurance Premium Payment"]
                },
                "Cards": {
                    "Credit Cards": ["Card Features", "Eligibility and Application", "Rewards and Cashback", "Payment and Billing"],
                    "Debit Cards": ["Usage and Benefits", "Lost Card Assistance", "Replacement Process"]
                }
            }
        }

        self.hr_tree = {
                "Main Menu": {
                    "Recruitment and Staffing": {
                        "Job Openings": ["Current Openings", "How to Apply", "Referral Programs"],
                        "Interview Process": ["Interview Stages", "Expected Timelines", "Feedback Mechanism"],
                        "Onboarding": ["Joining Formalities", "Orientation Programs", "Documentation Requirements"],
                    },
                    "Compensation and Benefits": {
                        "Salary & Benefits": {
                            "Salary Details": ["Salary Structure", "Payslip Download", "Salary FAQs"],
                            "Reimbursements & Claims": [
                                "Track Claims Status", 
                                "View Claim History", 
                                "Claim Policies", 
                                "Ask Anything?"
                            ],
                            "Taxation": ["Tax Deduction Details", "Investment Declarations", "Tax Saving Plans"],
                        },
                        "Leave Management": ["Leave Policies", "Leave Balances", "Apply for Leave"],
                    },
                    "Performance Management": {
                        "Performance Reviews": ["Review Schedule", "Feedback Process", "Goal Setting"],
                        "Incentive Policy": ["Incentive Criteria", "Performance Rewards", "Incentive FAQs"],
                    },
                    "Compliance and Legal": {
                        "Policies": ["Code of Conduct", "Workplace Harassment Policy", "Compliance Training"],
                        "Regulations": ["PF Regulations", "Taxation Compliance", "Grievance Redressal"],
                    },
                    "Bonus and Increments": {
                        "Bonus Details": ["Eligibility Criteria", "Bonus Amount", "Payout Timelines"],
                        "Increments": ["Increment Policies", "Effective Dates", "Percentage Increases"],
                    },
                    "IT Damage Recovery Policy": {
                        "Recovery Process": ["Damaged Equipment Report", "Recovery Amount Details", "Appeal Process"],
                    },
                    "Staff Welfare": {
                        "Welfare Programs": ["Gym Memberships", "Meal Coupons", "Health Camps"],
                        "Eligibility": ["Full-time Employees", "Contract Employees", "Eligibility FAQs"],
                    },
                    "Travel Policy": {
                        "Travel Booking": ["Booking Assistance", "Allowed Expenses", "Travel Reimbursement"],
                        "Travel Limits": ["Domestic Travel", "International Travel", "Emergency Travel"],
                    },
                    "Provident Fund (PF)": {
                        "PF Contributions": ["Employee vs. Employer Contributions", "Total Accrued Amount", "Withdrawal Rules"],
                        "PF Regulations": ["Eligibility", "Tax Benefits", "Compliance Rules"],
                    },
                    "Salary Structure": {
                        "Breakdown": ["Basic Salary", "HRA", "Allowances"],
                        "Comparison": ["Department Salary Equity", "Industry Benchmarks"],
                    },
                    "Payroll Management": {
                        "Payroll Status": ["Processed Payroll", "Pending Payroll", "Payroll FAQs"],
                        "Payment Security": ["Fraud Prevention", "Data Security"],
                    },
                    "Taxation Compliance": {
                        "Tax Returns": ["Filing Assistance", "Tax Deduction Rules", "Common Errors"],
                        "Taxation Queries": ["80C Benefits", "Deductions", "Tax Liability Details"],
                    },
                    "Salary Transparency and Equity": {
                        "Comparison Reports": ["Internal Equity", "Industry Standards"],
                        "Transparency Initiatives": ["Open Salary Policies", "Employee Feedback"],
                    },
                    "Payroll Technology and Security": {
                        "Technology Features": ["Automated Payroll", "Integration with Tax Filing"],
                        "Security Policies": ["Data Encryption", "Access Control"],
                    },
                    "International Payroll Considerations": {
                        "Global Policies": ["Currency Conversion", "Local Regulations"],
                        "Expat Salaries": ["Salary Breakdown", "Tax Compliance"],
                    },
                    "Documents & Requests": {
                        "Document Requests": ["Experience Letter", "Salary Certificate", "Relieving Letter"],
                        "Policy Downloads": ["HR Manual", "Specific Policy Documents"],
                    },
                    "HR Support": {
                        "Helpdesk": ["Report an Issue", "Contact HR"],
                        "FAQs": ["General Questions", "Policy Specific Questions"],
                    },
                    "Ask Anything?": ["Open Query Input"],
                }
            }

        self.selected_path = []

    def display_menu(self):
        current_menu = self.hr_tree["Main Menu"]

        while True:
            print("\n" + ("-" * 30))
            print("Options:")
            if isinstance(current_menu, list):
                for i, item in enumerate(current_menu, start=1):
                    print(f"{i}. {item}")
                print(f"{len(current_menu) + 1}. Back")
                choice = input("Enter your choice: ")

                if not choice.isdigit() or int(choice) < 1 or int(choice) > len(current_menu) + 1:
                    print("Invalid choice. Please try again.")
                    continue

                choice = int(choice)

                if choice == len(current_menu) + 1:
                    print("Going back...")
                    self.selected_path.pop()
                    current_menu = self.hr_tree["Main Menu"]
                    for path in self.selected_path:
                        current_menu = current_menu[path]
                    continue

                self.selected_path.append(current_menu[choice - 1])
                return self.selected_path

            else:
                keys = list(current_menu.keys())
                for i, key in enumerate(keys, start=1):
                    print(f"{i}. {key}")
                print(f"{len(keys) + 1}. Exit")

                choice = input("Enter your choice: ")

                if not choice.isdigit() or int(choice) < 1 or int(choice) > len(keys) + 1:
                    print("Invalid choice. Please try again.")
                    continue

                choice = int(choice)

                if choice == len(keys) + 1:
                    if not self.selected_path:
                        print("Exiting...")
                        exit()
                    else:
                        print("Going back...")
                        self.selected_path.pop()
                        current_menu = self.hr_tree["Main Menu"]
                        for path in self.selected_path:
                            current_menu = current_menu[path]
                        continue

                selected_key = keys[choice - 1]
                self.selected_path.append(selected_key)
                current_menu = current_menu[selected_key]

class ChatBot:

    def __init__(self):
        self.ui = ChatBotUI()
        self.memory = ChatDB()
        self.rag_agent = RAGAgent()
        self.engine = ChatBotBackend(self.memory, self.rag_agent)

    def start_chat(self):
        print("\nStarting chat with the following context:")
        print(" > ".join(self.memory.user_data["selected_path"]))
        while True:
            user_query = input("\nEnter your query: ")
            response, status = self.engine.get_api_response(user_query,None)
            while status == 1: # ask additional details from user in a form 
                additional_user_data = {}
                for key, value in response.items():
                    additional_user_data[value] = input(f"{key}. {value}: ")
                response, status = self.engine.get_api_response(None, additional_user_data)
            else:
                print(response)


    
    def start(self):
        print("Welcome to the Finance and Investment Chatbot CLI!")
        selected_path = self.ui.display_menu()
        # selected_path = ['Insurance', 'Life Insurance', 'Policy Options']
        self.memory.user_data["selected_path"] = ",".join(selected_path)
        print("Selected Path:", selected_path)
        self.start_chat()


if __name__ == "__main__":
    bot = ChatBot()
    bot.start()
