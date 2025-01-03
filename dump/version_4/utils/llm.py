from typing import Any, List, Dict, Optional, Tuple, Union

from dotenv import load_dotenv
load_dotenv(override=True)

import json
import re

from prompts import Prompts

from openai import OpenAI, AsyncOpenAI
client = OpenAI()
client_async = AsyncOpenAI()


class LLMResponsePostProcessor:
    def __init__(self):
        pass

    async def process(self, response: Any, use: str = "detect_relevant_vars")-> Any:
        if use == "detect_relevant_vars":
            return await self.process_slave_queries(response=response)
        if use == "get_missing_vars":
            return await self.process_missing_vars(response=response)
        if use == "extract_vars":
            return await self.process_extract_vars(response=response)
        if use == "api_evaluator":
            return await self.process_api_evaluator(response=response)
        if use == "detect_chit_chat":
            return await self.process_chit_chat(response=response)
        if use == "rag":
            return await self.process_rag(response=response)
        if use == "generate_SAQ_and_intent":
            return await self.process_SAQ_and_intent(response=response)
        else:
            return await self.process_slave_queries(response=response)

    async def process_extract_vars(self, response: Any) -> Any:
        # response format: "{'var': 'value', 'var': 'value'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    async def process_missing_vars(self, response: Any) -> Any:
        # response format: "{1: the query, 2: the query}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)
        # remove the keys having None values
        json_data = {key: value for key, value in json_data.items() if value}
        return json_data

    async def process_slave_queries(self, response: Any) -> Any:
        # some regular expression to extract slave queries and their dependent variables
        # response format: "{Slave Query 1: [var1, var2, var3], Slave Query 2: [var4, var5, var6]}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    async def process_api_evaluator(self, response: Any) -> Any:
        # response format: "{response_type: 'direct' | 'llmatic' | 'rag', response: 'response text' | 'transformed response'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    async def process_chit_chat(self, response: Any) -> Any:
        # response format: "{response_type: 'chit_chat', response: 'response text'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data

    async def process_rag(self, response: Any) -> Any:
        # response format: "{response_type: 'rag', response: 'response text'}"
        if "```json" in response:
            # remove the code block
            response = re.sub(r"```json\n?", "", response)
        if "```" in response:
            response = re.sub(r"```", "", response)
        json_data = json.loads(response)

        return json_data
    
    async def process_SAQ_and_intent(self, response: Any) -> Any:
        # response format: "{SAQ: 'SAQ text', intent: 'intent text'}"
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

    async def llm_call(self, query: str, use: str) -> Any:
        response = await client_async.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompts[use]},
                {"role": "user", "content": query},
            ],
            temperature=0.0,
        )
        message = response.choices[0].message.content

        processed_output = await self.process(response=message, use=use)
        print(f"####### LLM ####### | {use} | \n*** INPUT ****: \n{query} \n*** OUTPUT ****: \n{processed_output} \n{'-'*50}")
        return processed_output