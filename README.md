Files in current Branch

## Front-End

### `ui.py`

to run the streamlit demo

### `cli.py`

to run the app on cli (for debugging)

## Backend

### Gateway : `main_cli.py`

to send and recieve the packets to and fro from client  
to start the local conversation session

### Backend main : `backend.py`

1. Query preprocessing
2. Pipeline handler
3. Execute pipelines

4. Orchestrator (WIP)

## Agents

```markdown
base.py
|-- chat.py
|-- api.py  
 |-- rag.py
```

## Pipeline

`api_extract_pipeline.py`  
`rag_pipeline.py`

## Utils

`call_api_hr.py` : DUMB-APIS  
`create_vdb_data.py` : RAG-UTILS  
`db_utils.py` - DB-UTILS  
`llm.py` - LLM-UTILS

## Files

`api_info.yaml` : Dummy apis  
`hr_bot.db` : SQLITE3 db  
`prompts.yaml` : Prompt file  
`ui_tree_data.json` : UI tree file
