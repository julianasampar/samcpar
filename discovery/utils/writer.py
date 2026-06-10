
"""
writer.py

Creates the files generated at each step in the storage.
"""
from abc import ABC, abstractmethod
import boto3
import json
from datetime import datetime, timezone

import os 
from pathlib import Path
from dotenv import load_dotenv

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


############################################
#         LOCAL IMPLEMENTATION             #
############################################
class LocalDataStorage(DataStorage):
    def __init__(self, folder_path):
        self.folder_path = Path(folder_path)

    def write_json_to_storage(self, content: dict, domain_folder: str = None) -> str:
        """
        Saves profiling results locally.
        One JSON file per table plus a manifest.json.
        """

        output_path = self.folder_path

        if domain_folder:
            output_path = output_path / domain_folder

        output_path.mkdir(parents=True, exist_ok=True)

        profiled_at = datetime.now(timezone.utc).isoformat()

        # Write one JSON file per table
        for table_name, table_profile in content.items():
            file_path = output_path / f"{table_name}.json"

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(table_profile, f, indent=2, default=str)

            print(f"Saved: {file_path}")

        # Write manifest
        manifest = {
            "profiled_at": profiled_at,
            "table_count": len(content),
            "tables": [
                {
                    "name": name,
                    "row_count": profile["row_count"],
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
    

    def read_json_from_storage(self, directory: str) -> dict:
        """
        Reads a directory containing JSON profiling files.
        """

        directory = Path(directory)
        
        results = {}

        for file in directory.glob("*.json"):

            if file.name == "manifest.json":
                continue

            with open(file, "r", encoding="utf-8") as f:
                results[file.stem] = json.load(f)

        return results
        


############################################
#         AWS IMPLEMENTATION              #
############################################
class AWSDataStorage(DataStorage):
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )

    def write_json_to_storage(self, content: dict, domain_folder: str, bucket: str = os.getenv("S3_BUCKET_NAME")) -> str:
        """
        Saves profiling results to S3. One JSON file per table.

        Parameters:
            profiles : dict returned by profile_all_tables()
            bucket   : S3 bucket name
            prefix   : folder path inside the bucket (e.g. "profiles/dvd_rentals")
        """
        s3 = self.s3

        for table_name, table_profile in content.items():
            key     = f"{domain_folder}/{table_name}.json"
            json_content = json.dumps(table_profile, indent=2, default=str)

            s3.put_object(Bucket=bucket, Key=key, Body=json_content.encode("utf-8"))
            print(f"  Saved: s3://{bucket}/{key}")

        # Write the manifest
        manifest = {
            "profiled_at": datetime.now(timezone.utc).isoformat(),
            "table_count": len(content),
            "tables": [
                {"name": name, "row_count": p["row_count"], "file": f"{name}.json"}
                for name, p in content.items()
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
    
    def read_json_from_storage(self, directory=None) -> dict:
        raise ValueError("THERE IS NO AWS READ CONNECTION YET!! HOLD ON TIGHT!!")


def get_storage(storage_type: str, **kwargs) -> DataStorage:
    """
    Returns the correct DataStorage implementation based on storage_type.

    Usage:
        storage = get_storage("aws")

    Parameters:
        storage_type : one of "aws" (more to come)
        **kwargs    : arguments passed to the DataStorage constructor
    """
    storages = {
        "local": LocalDataStorage,
        "aws": AWSDataStorage
    }

    if storage_type not in storages:
        raise ValueError(f"Unknown source type '{storage_type}'. Available: {list(storages.keys())}")

    return storages[storage_type](**kwargs)