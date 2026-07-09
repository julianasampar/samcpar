---
name: inspect_pattern_from_profile
description: "Read data sources profiling, stored in JSON files, to analyze underlying data patterns by querying pre-defined samples of the data and understanding overall business processes embedded in data patterns, and create a JSON file per table with inspected analysis. It should be executed after profile_data tool or when there is already an existing profile JSON file in storage for the source domain in question."
argument-hint: "[--domain_name] [--storage_type] [--source_type] [--input_path] [--output_path] [--input_bucket] [--output_bucket]"
metadata:
  last-updated: 2026-07-09 18:30 UTC
  version: 1.0.0
  category: under development
---

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--domain_name` | Yes | Data domain related to the sources. The Agent should be able to find the pattern and read only the JSON files from the specified domain.  |
| `--storage_type` | Yes | Type of storage where the profiling JSON files is located (it can be 'local' or 'AWS').  |
| `--source_type` | Yes | Type of source where the data is located (it can be 'csv' or 'Snowflake').  |
| `--input_path` | No | If 'local' as storage type, local path to read the profiling data. |
| `--output_path` | No | If 'local' as storage type, local path to write the inspected data. |
| `--input_bucket` | No | If 'AWS' as storage type, bucket to read the profiling data. |
| `--output_bucket` | No | If 'AWS' as storage type, bucket to write the inspected data. |


# Inspect Pattern From Profile
## Quick Guide

**The Agent Role:** You are a data developer responsible for describing a set of ingested source systems associated to a certain business domain, with the goal of inspecting and indentifying the business processes embedded in the data across the datasets.

**What It Does**: Connects to the file system storage and reads JSON files containing each table's profiling information. Queries each table filtering distinct categorical values to retrieve a sample of the data. Then, analyzes and identifies business-related patterns to generate insights on how data should be treated and used.

**Hooks**:
> **`/inspect_pattern_from_profile`** defines the task for READING JSON files and WRITING the interpreted results on the behavior of the data. 

**Example**:
<example-user-input>
``` 
User: /inspect_pattern_from_profile
Agent: Detects no domain_name, storage_type and source_type were provided. Asks the user the required arguments.
``` 
``` 
User: /inspect_pattern_from_profile The domain is dvd_rentals, the storage path is /profiler/resources and the source_type is Snowflake.
Agent: Retrieves the Snowflake environment variables to connect to the warehouse and execute the queries. Then, identifies the storage path was provided where the type is 'local', so it reads and writes the local JSONs related to 'dvd_rentals' from the provided directory.
``` 
</example-user-input>

# Behavioral Discovery

The profiling provided through JSON files has the following structure:
<profile-structure>
```
{
  "table": "table_name",
  "row_count": 1,
  "columns": {
    "table_id": {
      "type": "numeric",
      "dtype": "BIGINT",
      "nullable": true,
      "metrics": {
        "count": 1,
        "mean": 1,
        "std": 0,
        "min": 1,
        "25%": 1,
        "50%": 1,
        "75%": 1,
        "max": 1
      },
      "distinct": {
        "distinct_count": 1,
        "values": [
          1,
        ],
        "skipped": false
      },
      "latest_dates": null
      }
    }
  }
```
</profile-structure>

## Steps
<steps>

1. **Set of Records**: Identify and filter ONLY the most important categorical features and filter each distinct value to understand the underlying behavior of the data in subsets. You can skip columns and/or values to filter, if their meaning don't look relevant to the domain. Rank the importance of that column/filter in overall data behavior. Columns that have distinct values that differs a lot in behaviour between them are more important than columns that do not vary between values. Iterate on the possible values of the most important features, analyze the behavior and register your conclusions. The features might be date, customer, status, type, or others. If no filters are provided, return a sample of the table and analyze it. Some examples are:
  <example-steps>
   > The source table transactions contain information on customer, payment type, status, date. To understand the data, you filter out the customer = "10000001", payment_type = "credit", date = "2025-01-01". With the results, you observe that the customer made 1 transaction that went throught the status "created", "authorized", "captured" and "chargebacked" in the same day. You also may observe that the transaction amount for chargebacked transactions is negative.

   > The source table inventory_forecast contains information on warehouse_id, product_category, forecast_date, and forecasted_amount. To understand the data, you filter out the warehouse_id = "WH102" and product_category = "electronics". You observe that the table contains the aggregated forecast predictions by day, and to compute the expected revenue for the next month you need to get the forecasted amount of the last day of the month.

   > The source table customer_support_metrics contains information on support_team, status, ticket_priority, resolution_date, and handling_time. To understand the data, you filter out the support_team = "LATAM_ENTERPRISE" and ticket_priority = "high". You observe that each row corresponds to a change in status of the same ticket, and that only when the status is "completed" the resolution_date is assigned.
   </example-steps>

2. **Business Descriptions**: Using the knowledge observed in the data from the previous steps, connect them to business knowledge from the specified domain and write additional non-data related information.

3. **File Creation**: Write one JSON file per table. If path not provided, write under the default path.
</steps>