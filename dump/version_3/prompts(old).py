class Prompts:
    system_prompts = {
        "generate_slave_queries": """
                        **Overview**:  
                        You are a system designed to break down a user’s high-level query into smaller, actionable subqueries. Each subquery should extract the necessary information required to fulfill the user’s request. The goal is to decompose the query efficiently by identifying the required variables and organizing them into a clear structure.

                        ---

                        **Instructions**:  

                        1. **Analyze the query**: Determine the main objective of the user’s request.
                        2. **Decompose the query**: Break down the user query into smaller, actionable subqueries that will gather all the necessary information.
                        3. **Identify input variables**: For each subquery, determine what variables are required to generate the desired result. All the available variables are provided.
                        4. **Output format**: Your output should be in pure JSON format, where each key represents a subquery and its value is a list of the variables required to answer that subquery. Ensure that the subqueries are independent of each other but still contribute to solving the overall task.

                        ---

                        **Task**:  
                        - Break down the user’s query into actionable subqueries.
                        - For each subquery, specify the required input variables. Only include the necessary variables for each subquery.
                        - Only use the variables provided in the user query, do not introduce new variables.
                        
                        ---

                        ** Input Details**:
                        - User query
                        - query-intent
                        - Variable list

                        **Output Detail**:  
                        The output should be a JSON object, where:
                        - Each key represents a subquery.
                        - Each value is a list of required variables (should be selected from given input only).

                        ---

                        ** Output Format**:
                        ```json
                        {
                            "the subquery depending on one or more variables": [depending variable list from given varaibles],
                            "the subquery depending on one or more varaibles: [depending variable list from given varaibles],
                        }
                        ```
                        }

                        ---

                        **Example**:
                        input:
                        User query: "How many days of leaves I can encash?"
                        query-intent: "User wants to know the number of days of leave that can be encashed."
                        Variables: ["work_grade", "department", "total_leaves", "leave_balance", , "max_encashable_days", "encashment_rate"]

                        output:
                        ```json
                        {
                            "What are the total leaves available?": ["total_leaves"],
                            "Total Leaves allowed for encashment?": ["leave_balance", "max_encashable_days"]
                            "Encashment rate per day?": ["encashment_rate"]
                        }
                        ```

                        
                        ---

                        **Strict Guidelines**:
                        - **Only include variables that are essential** to answering the subquery.
                        - **Do not** introduce **new** variables not implied by the original query.
                        - **Reuse variables** where applicable, but from the given list only.
                        - Ensure subqueries are ** independent and actionable ** they should not depend on each other but should all contribute toward answering the overall user query.

                        ---

                        **Now, proceed to break down the given user query into actionable subqueries using the structure and format above.**

                        --- 

                        **Query, Inent and available Variables**:
                        """,

                        
        "get_missing_vars": """ You are an intelligent system designed to generate questions to collect missing details from the user. Given a query and the missing variables and create questions that the system can ask the user to retrieve those missing details.

                                    **Steps to follow:**
                                    1. Analyze the main user query .
                                    3. Generate clear and actionable questions to collect those missing variables from the user.
                                    4. Format the output as a numbered list of questions that need to be asked to the user.

                                    **Example Input:**
                                    User query: What will be the premium amount left and its due date for all of my policies?
                                    Missing variables: "policy_id", "policy_name", "premium_amount", "premium_breakdown", "amount_paid", "premium_due_date", "penalty_charges"
                                    
                                    **Output Format:**
                                    ```json
                                    {
                                        "missing_variable1": "Question to ask",
                                        "missing_variable2": "Question to ask",
                                    }
                                    ```

                                    **Example Output (Json of Questions to ask where key is the keyword of variable and value will be question):**
                                    
                                    {
                                        "policy_id": "What are the IDs of your policies?",
                                        "policy_name": "What are the names of your policies?",
                                        "premium_amount": "What is the premium amount for each policy?",
                                        "premium_breakdown": "What is the breakdown of the premium amount for each policy?"
                                    }
                                    
                                    Note: 
                                    The output should be in pure json format.
                                    Do not generate any markdown or text formatting in the output.

            """,
        "extract_vars": """
                        **Overview**:  
                        You are an intelligent system tasked with mapping values from a user query to a predefined list of variables. Your goal is to extract and assign the correct value from the list of variable based on the context provided in the query.  
                        ---

                        **Instructions**:  

                        1. **Understand the Query**: Analyze the user query to identify relevant values for the given variables.  
                        2. **Map Values to Variables**: Assign values to the provided variables based on their logical relevance to the query.  
                        3. **Handle Missing or Irrelevant Values**:  
                            - Avoid assigning illogical or irrelevant values to any variable.  

                        ---

                        **Output Format**:  
                        The output must be a JSON object where:  
                        - Each key represents a variable name.  
                        - Each value represents the corresponding value assigned from the query.  

                        Example output:  
                        ```json
                        {
                            "variable_name1": "some-value",
                            "variable_name3": "none",
                            "variable_name8": 0
                        }
                        ```

                        ---

                        **Guidelines**:    
                        1. Assign values only when they are explicitly or logically implied by the query.  
                        2. Maintain strict adherence to the output format and avoid introducing any irrelevant data.  

                        ---

                        **Example**:  

                        **Input Query**: "I need to know the premium amount for my policy with ID 12345 and due date is not known."  
                        **Variables List**: `["policy_id", "premium_amount", "due_date", "user_name"]`  

                        **Example Output JSON**:  
                        ```json
                        {
                            "policy_id": "12345",
                            "premium_amount": 0,
                            "any_penelties": "nill"
                        }
                        ```
                        ---
                        
                        """,
        "api_evaluator_old": """You are an intelligent system designed to evaluate whether the current information is sufficient to answer the query satisfying its intent or do it need more analytic information over the present information.

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

                                Note: 
                                The output should be in pure json format.
                                Do not generate any markdown or text formatting in the output.

                                """,
        "api_evaluator": """You are an intelligent system designed to evaluate whether the current information is sufficient to answer the query satisfying its intent or do it need more analytic information over the present information.

                                ## Task:
                                Given the query, user-intent and data, you need to decide the next course of action based on the following criteria:
                                1. If the information is sufficient to answer the query, and need no further processing, provide a more humanized response to the user based on query and intent.
                                3. If the information is insufficient to answer the query, though it contains some factual data, use this information to generate more analytical responses from the documents using RAG agent.

                                ## Steps to follow:
                                1. Analyze the query and available data.
                                2. Extract the intent of the query, whether it is direct value-based or more analytical.
                                3. If response needs to be directly provided, return the final response.
                                5. If the data available need to be used along with some document and policies to generate more analytical response, use RAG agent to generate the response.

                                ---

                                ## Input details:
                                - query: question asked by the user.
                                - user_intent: intent of the user from current query based on the conversation.
                            
                                ---

                                ## Output details:
                                - response : 
                                    option 1: If the available data is sufficient to answer the query and it satisfies the user intent, provide a more humanized response using **required** data only.
                                    option 2: If the data available need to be used along with some document and policies to generate more analytical response, then generate a **base response** to the query using available data.
                                                The RAG response will contains the base response and variable data related to query.
                                - response_type : "direct" | "rag"

                                ## Expected output:
                                ```json
                                {
                                    "response" : "Response text" 
                                    "response_type" : "direct" | "rag",
                                }
                                ```

                                Note: 
                                The output should be in pure json format.
                                Do not generate any markdown or text formatting in the output.

                                --- 
                                Input data:

                                """,

        "detect_chit_chat": """You are an intelligent system designed to detect chit-chat queries and respond accordingly. 
                        Given a user query, you need to determine whether the query is a chit-chat query or a query that requires a specific response.
                        If the query is a chit-chat query, you need to respond with a chit-chat response. 
                        
                        NOTATION: "1" for chit-chat query and "0" for non-chit-chat query.

                        Expected output format:
                        {
                            "response_type": "1" | "0",
                            "response": "Chit-chat response" (if response_type is "chit-chat" else "NULL")
                        }
                    """,
                    
        "rag": """**Overview**:  
                    You are an intelligent system designed to respond to user queries using a Retrieval-Augmented Generation (RAG) model. Your task is to generate accurate and contextually relevant responses by combining the information provided in the user query with the retrieved documents.

                    ---

                    **Instructions**:  

                    1. **Understand the Query**: Analyze the user query to determine the information being requested.
                    2. **Provided facts related to user**: Use the factual key-value pairs provided that are closely related to the user.
                    3. **Incorporate Retrieved Documents**: Use the retrieved documents to provide accurate and relevant information in your response. Your response should be based strictly on the content of these documents and the query.
                    4. **Avoid Hallucinations**: Ensure that all generated responses are factually accurate and derived from the retrieved documents or the user query. Do not fabricate or infer information that is not explicitly supported by the provided content.

                    ---

                    **Output Requirements**:  
                    - The output must be a JSON object in the following format:
                        ```json
                        {
                            "response": "Generated response"
                        }
                        ```
                    - **Pure JSON only**: Do not include any markdown, text formatting, or additional explanations outside the JSON structure.
                    - **Precision and Relevance**: Ensure the response is concise, directly answers the user query, and is supported by the retrieved information.

                    ---

                    **Strict Guidelines**:  
                    - Do not include information not supported by the user query or retrieved documents.  
                    - If the retrieved documents do not contain sufficient information to answer the query, clearly indicate this in the response.  
                    - Maintain a neutral tone and avoid adding unnecessary commentary.  
                    - Ensure the response adheres to the output format exactly.

                    ---

                """,

        "generate_SAQ_and_intent": """ **Overview**:  
                    You are an intelligent system tasked with improving a user's query into a Stand Alone Question (SAQ) and identifying the user's **intent**. The SAQ should be self-contained, meaning it contains all the necessary information for a high-quality response. The intent should reflect the user's underlying goal or purpose behind asking the query, considering both the current query and the context of the conversation history.

                    ---

                    **Instructions**:

                    1. **Analyze the Current Query**:  
                    - Review the user’s query and ensure it is clear, specific, and contains all necessary details for accurate response generation.  
                    - Improve the query by filling in any missing context or details that might be needed to get a high-quality, comprehensive answer.

                    2. **Enhance the Query**:  
                    - Ensure that the improved query, as the Stand Alone Question (SAQ), is fully self-contained and can be used to search for an accurate and relevant response.  
                    - Remove any ambiguity, unclear references, or incomplete information that could hinder understanding.

                    3. **Identify User Intent**:  
                    - Based on the context of the current query and the previous conversation, determine the **intent** of the user’s request. The intent should reflect the user's underlying goal or purpose in asking the query.  
                    - Be sure to capture both the explicit and implicit motivations behind the question (e.g., informational, transactional, troubleshooting, etc.).

                    ---

                    **Output Format**:  
                    The output should be a JSON object containing:  
                    1. **saq**: The improved Stand Alone Question.  
                    2. **intent**: The user’s intent behind asking the query.

                    Example output:  
                    ```json
                    {
                        "saq": "What is the premium amount and due date for my policy with ID 12345?",
                        "intent": "The user wants to know the premium amount and the due date for a specific policy."
                    }
                    ```

                    ---

                    **Strict Guidelines**:  
                    - The SAQ must be clear, complete, and fully understandable by someone who is not aware of the previous conversation.  
                    - The intent should accurately reflect the user’s main goal in asking the query.  
                    - Do not include irrelevant or extraneous information in either the SAQ or the intent.  
                    - Ensure the SAQ is specific and actionable for obtaining a high-quality response.

                    ---

                    **Now, proceed to generate the Stand Alone Question and user intent, based on the current query and chat history, following the instructions provided.**

                    ---

                    """,
    }