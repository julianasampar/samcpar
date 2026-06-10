import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discovery.utils.reader import get_datasource
from discovery.utils.writer import get_storage
from discovery.profiling.profiler import profile_all_tables

from anthropic import Anthropic
from mcp.server.fastmcp import FastMCP
from fastmcp.prompts import Message
from mcp.types import ToolAnnotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor()

mcp = FastMCP("system_notifier", log_level="ERROR")

@mcp.tool(
    name="profile_data",
    description=""" 
        This tool reads, profiles and writes a set of datasources. 
            Available connectors: 
            - Reads from csv, Snowflake.
                If csv: folder_path is required.
                If snowflake: database and schema are optional (defaults to .env values).
            - Writes in local folders, S3 bucket.
                For AWS, by default, uses bucket defined in .env file.

            Parameters:
                domain          : A concise tag to group the datasource (Required)
                datasource_type : "csv" or "snowflake" (Required)
                storage_type    : "aws" (Required)
                input_path      : Path for READING CSV folder. Required if datasource_type is "csv"
                database        : Snowflake database. Optional, defaults to .env value
                schema          : Snowflake schema. Optional, defaults to .env value
                output_path     : Path for WRITING on local folder. Required if storage_type is "local"
                bucket          : S3 bucket name. Optional, defaults to .env value
        """,
    annotations=ToolAnnotations(
        title="Profiles datasources",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True
    )
)
async def profile_data(
    domain:          str,
    datasource_type: str,
    storage_type:    str,
    input_path=None,   # required for csv
    database=None,   # optional for snowflake
    schema=None,   # optional for snowflake
    output_path=None,   # required for local
    bucket=None,   # optional for s3
) -> str:
    
    def run_profiling():
        kwargs = {}

        if datasource_type == "csv":
            if not input_path:
                return "Error: folder_path is required when datasource_type is 'csv'"
            kwargs["folder_path"] = input_path

        if datasource_type == "snowflake":
            if database: kwargs["database"] = database
            if schema:   kwargs["schema"]   = schema

        source  = get_datasource(datasource_type, **kwargs)
        results = profile_all_tables(source)

        storage_kwargs = {}
        if storage_type == "local":
            if not output_path:
                    return "Error: folder_path is required when storage_type is 'local'"
            storage_kwargs["folder_path"] = output_path
        
        if bucket: storage_kwargs["bucket"] = bucket

        storage = get_storage(storage_type, **storage_kwargs)
        storage.write_json_to_storage(content=results, folder=domain)

        return "Profiling successfully executed"
    
    # Runs the blocking code in a thread so it doesn't block the event loop
    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_profiling)
    return result