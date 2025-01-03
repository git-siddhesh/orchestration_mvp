prompt_file = "./version_3/prompts.yaml"
import yaml


with open(prompt_file, encoding='utf-8') as file:
    prompts = yaml.load(file, Loader=yaml.FullLoader)
    
class Prompts:
    system_prompts = {
        "detect_chit_chat": prompts.get("chitchat"),
        "generate_SAQ_and_intent": prompts.get("saq_and_intent"),
        "detect_relevant_vars": prompts.get("relevant_vars"),
        "get_missing_vars": prompts.get("counter_queries"),
        "extract_vars": prompts.get("extract_vars"),
        "api_evaluator": prompts.get("evaluate_api_reponse"),
        "rag": prompts.get("rag_response"),
    }