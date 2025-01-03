from typing import List, ClassVar, Tuple, Dict, Optional, Any
import json
import re
import asyncio

from pydantic import BaseModel
from openai import OpenAI
from call_api_hr import *
from prompts import Prompts
from create_vdb_data import MarkdownVectorDB

# VARS = json.load(open("VARs.json", encoding="utf-8"))
VARS = json.load(fp=open(file="VARs_HR.json", encoding="utf-8"))

from dotenv import load_dotenv
load_dotenv()

import os


client = OpenAI()


class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o-mini"
    instructions: str = "You are a helpful Agent"
    tools: List[str] = []


class APIAgent(Agent):
    input_vars: List[str] = []
    output_vars: List[str] = []
    api_use_case: str = ""
    api_url: str = ""
    missing_vars: List[str] = []


class RAGAgent(Agent):
    abc: Any = None


class ChatDB:
    def __init__(self):
        self.user_data: Dict[str, str] = {}
        self.chat_history: Dict[str, str] = {}
        # store in redis and create some supporting functions to store and retrieve the chat history
        self.api_data: Dict[str, str] = {}


class LLMResponsePostProcessor:
    def __init__(self):
        pass

    def process(self, response: Any, use: str = "generate_slave_queries"):
        if use == "generate_slave_queries":
            return self.process_slave_queries(response)
        if use == "get_missing_vars":
            return self.process_missing_vars(response)
        if use == "extract_vars":
            return self.process_extract_vars(response)
        if use == "api_evaluator":
            return self.process_api_evaluator(response)
        if use == "detect_chit_chat":
            return self.process_chit_chat(response)
        if use == "rag":
            return self.process_rag(response)

    def process_extract_vars(self, response):
        # response format: "{'var': 'value', 'var': 'value'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    def process_missing_vars(self, response):
        # response format: "{1: the query, 2: the query}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    def process_slave_queries(self, response):
        # some regular expression to extract slave queries and their dependent variables
        # response format: "{Slave Query 1: [var1, var2, var3], Slave Query 2: [var4, var5, var6]}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    def process_api_evaluator(self, response):
        # response format: "{response_type: 'direct' | 'llmatic' | 'rag', response: 'response text' | 'transformed response'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    def process_chit_chat(self, response):
        # response format: "{response_type: 'chit_chat', response: 'response text'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    def process_rag(self, response):
        # response format: "{response_type: 'rag', response: 'response text'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data


class LLMAgent(Prompts, LLMResponsePostProcessor):

    # def __init__(self):
    model = "gpt-4o-mini"

    def llm_call(self, query: str, use: str) -> str | Dict:
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": self.system_prompts[use]}]
            + [{"role": "user", "content": query}],
        )
        message = response.choices[0].message.content
        print(f"\n{'-'*20}LLM | {use} | {query}\n{message}\n{'-'*80}")
        return self.process(message, use)


class ChatBotBackend(LLMAgent):

    def __init__(
        self, memory: ChatDB, rag_agent: RAGAgent, vector_db: MarkdownVectorDB
    ):
        self.master_query: str = ""
        self.slave_queries: Dict[str, str] = {}
        self.slave_responses: list[Any] = []
        self.api_agents: list[Any] = []
        self.apis: Dict[str, Dict[str, List[str]]] = (
            {}
        )  # {api_name: {"input_vars": [], "output_vars": []}}
        self.memory: ChatDB = memory
        self.missing_vars: list[Any] = []
        self.api_based_responses = None
        self.rag_agent: RAGAgent = rag_agent
        self.vector_db: MarkdownVectorDB = vector_db
        self.subqueries: list[Any] = []

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
        llm_query = (
            f"User query: {self.master_query}\n Variables: {', '.join(VARS.keys())}"
        )
        response = self.llm_call(llm_query, use="generate_slave_queries")
        self.slave_queries = response

    def generate_missing_vars_questions(self):
        llm_query = f"User query: {self.master_query}\nMissing variables: {', '.join(self.missing_vars)}"
        response = self.llm_call(llm_query, use="get_missing_vars")
        self.subqueries = [(key, value) for key, value in response.items()]

    def initialize_api_agents(self):
        for api_name, api_data in self.apis.items():
            api_agent = APIAgent(
                name=api_name,
                model="gpt-4o-mini",
                instructions="You are a helpful API Agent",
                tools=[api_name],
                input_vars=api_data["input_vars"],
                output_vars=api_data["output_vars"],
            )
            self.api_agents.append(api_agent)

    async def find_missing_vars(self, agent: APIAgent):
        missing_inputs = [
            var
            for var in agent.input_vars
            if var not in self.memory.api_data and var not in self.memory.user_data
        ]
        if missing_inputs:
            self.missing_vars.extend(missing_inputs)

    async def resolve_slave_queries_agentic_api_dependencies(self):
        for slave_query in self.slave_queries:
            for output_var in self.slave_queries[slave_query]:
                api_name: str = VARS[output_var]["api_to_be_called"]
                if api_name not in self.apis:
                    self.apis[api_name] = {
                        "input_vars": VARS[output_var]["input_vars"],
                        "output_vars": [output_var],
                        # "output_vars": VARS[output_var]["output_vars"],
                    }
                elif output_var not in self.apis[api_name]["output_vars"]:
                    self.apis[api_name]["output_vars"].append(output_var)

        self.initialize_api_agents()
        tasks = [self.find_missing_vars(agent) for agent in self.api_agents]
        await asyncio.gather(*tasks)

        # deduplicate the missing variables list
        if self.missing_vars:
            self.missing_vars = list(set(self.missing_vars))
            self.generate_missing_vars_questions()
            print("Missing variables:", self.missing_vars)
            print("Subqueries:", self.subqueries)

    def update_memory(self, subquery):
        llm_query = f"User query: {self.master_query}\nAdditional user data: {subquery}\nVariables: {', '.join(self.missing_vars)}"
        response = self.llm_call(llm_query, use="extract_vars")
        self.memory.api_data.update(response)

    def execute_apis(self):
        for api_name in self.apis:
            # pass both memory.api_data and self.memory.user_data to the api
            api_response = tools[api_name](
                **self.memory.api_data, **self.memory.user_data
            )
            self.memory.api_data.update(api_response)

    def call_rag_agent(self, query, var_data, recreate_vector_db=False):
        self.vector_db.recreate_or_load_vector_db(recreate=recreate_vector_db)
        rag_search_query = f"{query}\n{var_data}"
        docs = self.vector_db.retrieve_documents(rag_search_query)
        # for i, doc in enumerate(docs):
        #     print(f"Document {i+1}:")
        #     print(f"Content: {doc.page_content}")
        #     print(f"Metadata: {doc.metadata}")

        formatted_docs = "\n\n".join(
            [
                f"Document {i+1}:\nContent: {doc.page_content}"
                for i, doc in enumerate(docs)
            ]
        )
        rag_query = f"User query: {query}\nAvailable data: {var_data}\n\nRetrieved documents: {formatted_docs}"
        response = self.llm_call(rag_query, use="rag")
        return response["response"], docs

    def api_evaluator(self):
        """
        A decision maker that evaluates the API responses and decides the next course of action.
        1. Return the final response to the user as it is.
        2. Humanize the response using LLMatic transformation.
        3. Use these information and pass to RAG agent to generate more analytical response from the DOCUMETNS.
        """
        print(self.memory.api_data)
        print(self.memory.user_data)
        string_formatted_api_data = ", ".join(
            [f"{key}: {value}" for key, value in self.memory.api_data.items()]
        )
        string_formatted_user_data = ", ".join(
            [f"{key}: {value}" for key, value in self.memory.user_data.items()]
        )
        var_data = string_formatted_api_data + string_formatted_user_data
        llm_query = f"Mater query: {self.master_query}\n Available data: {var_data}"
        response = self.llm_call(llm_query, use="api_evaluator")

        print(response)
        self.api_based_responses = response["response"]

        if response["response_type"] == "direct":
            return ("PLAIN", response["response"], None)
        if response["response_type"] == "llmatic":
            return ("LLMATIC", response["response"], None)
        if response["response_type"] == "rag":
            rag_response = self.call_rag_agent(
                response["response"], var_data, recreate_vector_db=False
            )
            return ("RAG", rag_response[0], rag_response[1])

    def chit_chat_detector(self, query: str) -> Tuple[bool, Any]:
        llm_query = f"User query: {query}"
        response = self.llm_call(llm_query, use="detect_chit_chat")
        if response["response_type"] == "1" or response["response_type"] == 1:
            return True, response["response"]
        return False, None

    async def get_api_response(
        self, query: Any = None, subquery_response: Any = None
    ) -> Tuple[Tuple[str, str, Any], int]:
        if query:

            status, response = self.chit_chat_detector(query)
            if status:
                return ("greeting", response, None), 0

            self.master_query = query

            self.generate_slave_queries()
            print("Slave queries:", self.slave_queries)
            await self.resolve_slave_queries_agentic_api_dependencies()
            # asyncio.run(self.resolve_slave_queries_agentic_api_dependencies())

        if subquery_response:
            self.update_memory(subquery_response)

        if len(self.subqueries) > 0:
            current_subquery = self.subqueries.pop(0)
            return (current_subquery[0], current_subquery[1], None), 1

        self.execute_apis()
        return self.api_evaluator(), 0

        # return "This is a placeholder response for now. Please implement this method."
