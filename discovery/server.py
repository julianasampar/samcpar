import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from discovery.utils.reader import get_datasource
from discovery.utils.handler import get_storage
from discovery.profiling.profiler import profile_all_tables
from discovery.inspecting.inspector import inspect_structure_from_profile, inspect_pattern_from_profile

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
        import os
        kwargs = {}

        if datasource_type == "csv":
            kwargs["folder_path"] = input_path or os.getenv("INPUT_DATA_PATH")

            if not kwargs["folder_path"]:
                return "Error: input_path for datasource_type type 'csv'."

        if datasource_type == "snowflake":
            db = database or os.getenv('SNOWFLAKE_DATABASE')
            sch = schema or os.getenv('SNOWFLAKE_SCHEMA')
            if not db or not sch:
                return "Error: Snowflake database and schema are required. Either pass them as parameters or set SNOWFLAKE_DATABASE and SNOWFLAKE_SCHEMA environment variables."
            kwargs["database"] = db
            kwargs["schema"] = sch

        source  = get_datasource(datasource_type, **kwargs)
        results = profile_all_tables(source)

        storage_kwargs = {}
        if storage_type == "local":
            storage_kwargs["folder_path"] = output_path or os.getenv("PROFILER_PATH")

            if not storage_kwargs["folder_path"]:
                return "Error: output_path is required when storage_type is 'local'"

        if storage_type == "aws":
            aws_bucket = bucket or os.getenv('S3_BUCKET_NAME')
            if not aws_bucket:
                return "Error: S3 bucket is required. Either pass bucket parameter or set S3_BUCKET_NAME environment variable."
            storage_kwargs["bucket"] = aws_bucket

        storage = get_storage(storage_type, **storage_kwargs)
        storage.write_json_to_storage(content=results, domain_folder=domain)

        return "Profiling successfully executed"
    
    # Runs the blocking code in a thread so it doesn't block the event loop
    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_profiling)
    return result

mcp.add_tool(
    inspect_pattern_from_profile,
    name="inspect_pattern",
    description="""
            Analyzes behavioral patterns and business relationships within previously profiled datasets.

            The tool reads profiling metadata, generates representative filters from distinct values,
            retrieves data samples, and uses AI-powered analysis to identify behavioral patterns,
            business rules, trends, correlations, and notable characteristics of each datasource.

            Results are automatically written back to the configured storage location for future
            documentation and semantic discovery workflows.

            Supported storage types:
            - local
            - aws

            Use this tool after profiling has been completed and filter metadata is available.
        """
    )

mcp.add_tool(
    inspect_structure_from_profile,
    name="inspect_structure",
    description="""
            Analyzes the structural organization of previously profiled datasets.

            The tool examines profiling metadata and infers primary keys, foreign keys,
            table relationships, entity dependencies, and overall data model structure.

            It helps discover how datasources are connected, identify candidate join paths,
            and generate structural documentation useful for analytics engineering,
            semantic modeling, data governance, and business understanding.

            Results are automatically persisted to the configured storage location.

            Supported storage types:
            - local
            - aws

            Use this tool after profiling has been completed and structural metadata
            discovery is required.
        """
)


if __name__ == "__main__":
    mcp.run()