"""
handler.py

This function defines how the server connects to local and external applications 
to read and write data.

"""

import os
import json
import boto3
import duckdb
import snowflake.connector
from pathlib import Path
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from datetime import datetime, timezone

load_dotenv()

class DataStorage(ABC):

    @abstractmethod
    def write_json_to_storage(self, content: dict, domain_folder: str) -> str:
        """
        Writes JSON files into the storage. If a file already exist, this function overwrites it.
        """
        pass

    @abstractmethod
    def read_json_from_storage(self, directory: str) -> dict:
        pass


## LOCAL IMPLEMENTATION ## 

class LocalDataStorage(DataStorage):
    def __init__(self, folder_path):
        self.folder_path = Path(folder_path)

    def write_json_to_storage(self, content: dict, domain_folder: str = None, analysis_type: str = None) -> str:
        """
        Saves JSON results (from profiler or inspector steps) to a local directory.
        If analysis_type is provided, appends to a list. Otherwise, creates/overwrites (profiler mode).
        """

        output_path = self.folder_path

        if domain_folder:
            output_path = output_path / domain_folder

        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()

        # Write one JSON file per table
        for table_name, table_profile in content.items():
            file_path = output_path / f"{table_name}.json"

            if analysis_type:
                # Append mode: add to existing list or create new list
                existing_data = []
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Handle both list (new format) and dict (old format)
                        if isinstance(data, list):
                            existing_data = data
                        # If it's a dict (old profiler format), start fresh

                entry = {
                    "analysis_type": analysis_type,
                    "analysis": table_profile.get("analysis", table_profile),
                    "timestamp": timestamp
                }
                existing_data.append(entry)

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, indent=2, default=str)
            else:
                # Overwrite mode (profiler results)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(table_profile, f, indent=2, default=str)

            print(f"Saved: {file_path}")

        # Write manifest (only for profiler mode)
        if not analysis_type:
            manifest = {
                "profiled_at": timestamp,
                "table_count": len(content),
                "tables": [
                    {
                        "name": name,
                        "row_count": profile.get("row_count", 0),
                        "file": f"{name}.json",
                    }
                    for name, profile in content.items()
                ],
            }

            manifest_path = output_path / "manifest.json"

            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            print(f"Manifest written: {manifest_path}")

        path_written = str(output_path)
        return path_written
    

    def read_json_from_storage(self) -> dict:
        """
        Reads JSON files (from profiler or inspector steps) from a local directory.
        """

        input_path = self.folder_path
        
        results = {}

        for file in input_path.glob("*.json"):

            if file.name == "manifest.json":
                continue

            with open(file, "r", encoding="utf-8") as f:
                results[file.stem] = json.load(f)

        return results
    

## AWS IMPLEMENTATION ##

class AWSDataStorage(DataStorage):
    def __init__(self, bucket, **kwargs):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        self.bucket = bucket

    def write_json_to_storage(self, content: dict, domain_folder: str, analysis_type: str = None) -> str:
        """
        Saves profiling or analysis results to S3.
        If analysis_type is provided, appends to a list. Otherwise, creates/overwrites (profiler mode).
        """
        s3 = self.s3
        bucket = self.bucket
        timestamp = datetime.now(timezone.utc).isoformat()

        for table_name, table_profile in content.items():
            key = f"{domain_folder}/{table_name}.json"

            if analysis_type:
                # Append mode: read existing, add new entry
                existing_data = []
                try:
                    response = s3.get_object(Bucket=bucket, Key=key)
                    data = json.loads(response['Body'].read().decode('utf-8'))
                    # Handle both list (new format) and dict (old format)
                    if isinstance(data, list):
                        existing_data = data
                    # If it's a dict (old profiler format), start fresh
                except s3.exceptions.NoSuchKey:
                    existing_data = []

                entry = {
                    "analysis_type": analysis_type,
                    "analysis": table_profile.get("analysis", table_profile),
                    "timestamp": timestamp
                }
                existing_data.append(entry)
                json_content = json.dumps(existing_data, indent=2, default=str)
            else:
                # Overwrite mode (profiler results)
                json_content = json.dumps(table_profile, indent=2, default=str)

            s3.put_object(Bucket=bucket, Key=key, Body=json_content.encode("utf-8"))
            print(f"  Saved: s3://{bucket}/{key}")

        # Write the manifest (only for profiler mode)
        if not analysis_type:
            manifest = {
                "profiled_at": timestamp,
                "table_count": len(content),
                "tables": [
                    {"name": name, "row_count": profile.get("row_count", 0), "file": f"{name}.json"}
                    for name, profile in content.items()
                ],
            }
            s3.put_object(
                Bucket=bucket,
                Key=f"{domain_folder}/manifest.json",
                Body=json.dumps(manifest, indent=2).encode("utf-8"),
            )
            print(f"  Manifest written: s3://{bucket}/{domain_folder}/manifest.json")

        path_written = f"s3://{bucket}/{domain_folder}"

        return path_written
    
    def read_json_from_storage(self, domain_folder: str) -> dict:
        """
        Reads all JSON files inside an S3 prefix (folder) and returns
        a single dictionary where each file's content is merged.
        """

        response = self.s3.list_objects_v2(
            Bucket=self.bucket,
            Prefix=domain_folder
        )

        profiles = {}

        for obj in response.get("Contents", []):
            key = obj["Key"]

            if not key.endswith(".json"):
                continue

            file = self.s3.get_object(
                Bucket=self.bucket,
                Key=key
            )

            content = json.loads(
                file["Body"].read().decode("utf-8")
            )

            profiles.update(content)

        return profiles


## ASSISTANT FUNCTIONS ##

def manage_input_output_paths(
        storage_type,
        io_type:str,
        input_path=None,
        output_path=None,
        input_bucket=None,
        output_bucket=None,
    ):

        reading_kwargs = {}
        writting_kwargs = {}

        if storage_type == "local":

            if io_type == "profiler-inspector":

                reading_kwargs["folder_path"] = input_path or os.getenv("PROFILER_PATH")
                writting_kwargs["folder_path"] = output_path or os.getenv("INPESCTOR_PATH")

                if not reading_kwargs["folder_path"]:
                    raise ValueError(
                        "Please, provide input_path or add PROFILER_PATH in your environment variables."
                    )

                if not writting_kwargs["folder_path"]:
                    raise ValueError(
                        "Please, provide output_path or add INPESCTOR_PATH in your environment variables."
                    )

        elif storage_type == "aws":

            if io_type == "profiler-inspector":

                input_bucket = input_bucket or os.getenv("S3_PROFILER_BUCKET")
                output_bucket = output_bucket or os.getenv("S3_INSPECTOR_BUCKET")

                if not input_bucket:
                    raise ValueError(
                        "Please, provide input_bucket or add S3_PROFILER_BUCKET in your environment variables."
                    )

                if not output_bucket:
                    raise ValueError(
                        "Please, provide output_bucket or add S3_INSPECTOR_BUCKET in your environment variables."
                    )


            reading_kwargs["bucket"] = input_bucket
            writting_kwargs["bucket"] = output_bucket

        return reading_kwargs, writting_kwargs


def get_storage(storage_type: str, **kwargs) -> DataStorage:
    """
    Returns the correct DataStorage implementation based on storage_type.

    Usage:
        storage = get_storage("aws")

    Parameters:
        storage_type : "local" or "aws"
        **kwargs    : additional arguments that may be passed to the DataStorage constructor (for example, "folder_path" or "bucket")
    """
    storages = {
        "local": LocalDataStorage,
        "aws": AWSDataStorage
    }

    if storage_type not in storages:
        raise ValueError(f"Unknown source type '{storage_type}'. Available: {list(storages.keys())}")
    
    ## manage the folder reading/writting better
    ## maybe creating fixed folders/buckets for profiling and inspection rather then defining them in env variables
    
    manage_input_output_paths(
        storage_type,
        io_type=kwargs.get('io_type'),
        input_path=kwargs.get('input_path'),
        output_path=kwargs.get('output_path'),
        input_bucket=kwargs.get('input_bucket'),
        output_bucket=kwargs.get('output_bucket'),
    )

    return storages[storage_type](**kwargs)