"""
handler.py

This function defines how the server connects to local and external applications 
to read and write data.

"""

import os
import json
import boto3
from pathlib import Path
from dotenv import load_dotenv
from abc import ABC, abstractmethod
from datetime import datetime, timezone

load_dotenv()

class DataStorage(ABC):

    @abstractmethod
    def write_json_to_storage(self, content: dict, domain_folder: str = None, analysis_type: str = None) -> str:
        """
        Writes JSON files into the storage. If a file already exist, this function overwrites it.
        """
        pass

    @abstractmethod
    def read_json_from_storage(self, domain_folder: str = None) -> dict:
        """
        Reads JSON files from the storage. 
        """
        pass


## LOCAL IMPLEMENTATION ## 

class LocalDataStorage(DataStorage):
    def __init__(self):
        
        self.file_path = os.getenv("DISCOVERY_STORAGE_PATH")

    def write_json_to_storage(self, content: dict, domain_folder: str = None, analysis_type: str = None) -> str:
        """
        Saves JSON results (from profiler or inspector steps) to a local directory.
        The argument 'analysis_type' informs the type of analysis, which can be 'profiling', 'structure' or 'patterns'.
        """

        file_path = self.file_path

        if domain_folder:
            file_path = file_path / domain_folder

        file_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).isoformat()

        # Write one JSON file per table
        for table_name, table_profile in content.items():
            file_path = file_path / f"{table_name}.json"

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

        path_written = str(file_path)
        return path_written
    

    def read_json_from_storage(self, domain_folder: str = None) -> dict:
        """
        Reads JSON files (from profiler or inspector steps) from a local directory.
        """

        file_path = self.file_path 
        
        if domain_folder:
            file_path = file_path / domain_folder
        
        results = {}

        for file in file_path.glob("*.json"):

            if file.name == "manifest.json":
                continue

            with open(file, "r", encoding="utf-8") as f:
                results[file.stem] = json.load(f)

        return results
    

## AWS IMPLEMENTATION ##

class AWSDataStorage(DataStorage):
    def __init__(self, **kwargs):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        self.bucket = os.getenv("S3_DISCOVERY_BUCKET")

    def write_json_to_storage(self, content: dict, domain_folder: str = None, analysis_type: str = None) -> str:
        """
        Saves profiling or analysis results to S3.
        The argument 'analysis_type' informs the type of analysis, which can be 'profiling', 'structure' or 'patterns'.
        """
        s3 = self.s3
        bucket = self.bucket
        timestamp = datetime.now(timezone.utc).isoformat()

        for table_name, table_profile in content.items():

            if domain_folder:
                key = f"{domain_folder}/{table_name}.json"
            else:
                key = {table_name}.json

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

        path_written = f"s3://{bucket}/{domain_folder}"

        return path_written
    
    def read_json_from_storage(self, domain_folder: str = None) -> dict:
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

    return storages[storage_type](**kwargs)