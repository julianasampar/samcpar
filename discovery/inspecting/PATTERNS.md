---
name: behaviorist
description: "Read JSON files to retrieve high-level information about data sources and query the database to grasp their underlying behavior."
argument-hint: "[--json-storage-path] [--source-domain]"
metadata:
  last-updated: 2026-05-16 20:59 UTC
  version: 1.0.0
  category: under development
---
/
## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--json-storage-path` | No | Path for logging and storing the interaction and discovery analysis results.  |
| `--source-domain` | No | Data domain related to the sources. The Agent should be able to find the pattern and read only the JSON files from the specified domain.  |


## Quick Guide

**The Agent Role:** You are a data developer responsible for describing a set of ingested source systems associated to a certain business domain, with the goal of inspecting and describing the underlying data architecture and relationships across the datasets.

**What It Does**: Connects to the file system storage and reads JSON files of the related data source specified domain. Performs discovery analysis, such as identifying PKs, FKs, Orchestration patterns and relationships.

**Hooks**:
> **`/behaviorist`** defines the task for READING JSON files and WRITING the interpreted results on the behavior of the data. 

**Example**:
> User: /behaviorist
> Agent: Detects no storage path neither domain was provided. By default, asks the user for the storage path and domain or data source pattern the user wants. 
> User: The storage path is /profiler/resources and the domain is dvd_rentals.
> Agent: The agent find the pattern related to dvd_rentals, read all respective JSON files and writes the results.

> You: /behaviorist zendesk
> Agent: Detects a domain was provided and searches for all JSON files containing zendesk text pattern. Reads and computes the discovery information for all tables for Zendesk domain.

# Behavioral Discovery

The provided JSON file has the following structure:
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

1. **Set of Records**: Identify the most important categorical features and filter each distinct value to understand the underlying behavior of the data in subsets. Iterate on the possible values of the most important features, analyze the behavior and register your conclusions. The features might be date, customer, status, type, or others. Some examples are:
   > The source table transactions contain information on customer, payment type, status, date. To understand the data, you filter out the customer = "10000001", payment_type = "credit", date = "2025-01-01". With the results, you observe that the customer made 1 transaction that went throught the status "created", "authorized", "captured" and "chargebacked" in the same day. You also may observe that the transaction amount for chargebacked transactions is negative.

   > The source table inventory_forecast contains information on warehouse_id, product_category, forecast_date, and forecasted_amount. To understand the data, you filter out the warehouse_id = "WH102" and product_category = "electronics". You observe that the table contains the aggregated forecast predictions by day, and to compute the expected revenue for the next month you need to get the forecasted amount of the last day of the month.

   > The source table customer_support_metrics contains information on support_team, status, ticket_priority, resolution_date, and handling_time. To understand the data, you filter out the support_team = "LATAM_ENTERPRISE" and ticket_priority = "high". You observe that each row corresponds to a change in status of the same ticket, and that only when the status is "completed" the resolution_date is assigned.

2. **Business Descriptions**: Using the knowledge observed in the data from the previous steps, connect them to business knowledge from the specified domain and write additional non-data related information.

3. **File Creation**: Write one file per table. If path not provided, write under the default path. The file name should be written as "<name_of_datasource>__<current_timestamp>".
   - Default Path: /Users/julianasampar/Desktop/learning_dev/personal_dev/pyprojects/.claude/agents/data_discovery_agent/behaviorist/resources/<domain>/<name_of_datasource>
   