from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv
import json

from discovery.utils import logger
from discovery.utils import executor

# Loading Anthropic API Key and Client
load_dotenv()
client = Anthropic()

database="agentic_database.db"
database_table='agent_log_events'

# Functions add_user_message and add_assistant_message to maintain context for conversations
def add_user_message(messages, text):
    user_message = {"role": "user", "content": text if isinstance(text, Message) else text}
    messages.append(user_message)
    
    value_to_insert = json.dumps(user_message, default=str)
    logger.ingest_metadata(value_to_insert, database=database, database_table=database_table)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text if isinstance(text, Message) else text}
    messages.append(assistant_message)
    
    value_to_insert = json.dumps(assistant_message, default=str)
    logger.ingest_metadata(value_to_insert, database=database, database_table=database_table)

def get_streamed_request(stream_text, **params):
    stream = client.messages.stream(**params)

    
    with stream as stream:
        for text in stream.text_stream:
            if stream_text:
                print(text, end="")

    response = stream.get_final_message()

    return response

def interaction(user_input, stream_text, **params):
    if user_input:
        add_user_message(params["messages"], user_input)
    
    response = get_streamed_request(stream_text, **params)
    add_assistant_message(params["messages"], response.content)
    return response

def chat(
        messages,
        model,
        max_tokens,
        stream_text=True,
        user_input=None, 
        tools=None, 
        tools_functions=None, 
        system=None,
        stop_sequences=None
        ):
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "messages":messages,
        }
    
    # Adding optional arguments, if they are declated
    if system: # system = system message. An initial prompt to give the LLM context about how it should approach the interaction
        params["system"] = [{
            "type":"text",
            "text": system,
            "cache_control": {"type": "ephemeral"}
        }]

    if tools: # tools = Python fuctions that the LLM might ask to execute to get external context
        params["tools"] = tools

    if stop_sequences:
        params["stop_sequences"] = stop_sequences

    response = interaction(user_input, stream_text, **params)

    while response.stop_reason == 'tool_use': # If the LLM requires a tool call
        if not tools_functions:
            raise ValueError("Function not defined.")
        else:
            tool_outputs = executor.run_tool(response, functions=tools_functions)
            tool_result = executor.get_tool_result_block(tool_outputs)
            response = interaction(tool_result, stream_text, **params)

    return response