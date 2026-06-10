import duckdb
import json

# Defining a function to run the tool (based on the LLM answer) and return the result
def run_tool(response, functions):
    tool_results = []

    tool_blocks = [block for block in response.content if block.type == "tool_use"]

    for tool in tool_blocks:
        tool_name = tool.name
        params = tool.input
        id = tool.id
        function = functions[tool_name]

        result = {
            "id": id,
            "response": function(**params)
        }

        tool_results.append(result)
    return tool_results

# Creating the ToolResultBlock
def get_tool_result_block(tool_results):
    ToolResultBlock = []

    for result in tool_results:
        try:
            # Convert response to string if it's a dict/object
            response_content = result['response']
            if isinstance(response_content, dict):
                response_content = json.dumps(response_content)
            elif not isinstance(response_content, str):
                response_content = str(response_content)

            result_block = {
                "tool_use_id": result['id'],
                "type": "tool_result",
                "content": response_content,
                "is_error": False
            }

        except Exception as e:
            result_block = {
                "tool_use_id": result['id'],
                "type": "tool_result",
                "content": f"Failed to execute function. Error: {e}",
                "is_error": True
            }

        ToolResultBlock.append(result_block)

    return ToolResultBlock