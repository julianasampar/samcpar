---
name: inspecting
description: "Read JSON files to explore data sources and grasp their underlying architectural structure."
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
> **`/inspector`** defines the task for READING JSON files and WRITING the interpreted results on the structure of the data . 

**Example**:
> User: /inspector
> Agent: Detects no storage path neither domain was provided. By default, asks the user for the storage path and domain or data source pattern the user wants. 
> User: The storage path is /profiler/resources and the domain is dvd_rentals.
> Agent: The agent find the pattern related to dvd_rentals, read all respective JSON files and writes the results.

> You: /inspector zendesk
> Agent: Detects a domain was provided and searches for all JSON files containing zendesk text pattern. Reads and computes the discovery information for all tables for Zendesk domain.


# Architect Discovery

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


## Steps

 1. **Primary Keys**: For each table, identify the Primary Key or main unique identifier column. If the table doesn't have a PK, create and document a hypothesis about which column combination makes the rows unique.

2. **Foreign Keys**: For each table, identify the Foreign Keys. If the table doesn't have FKs, skip this step.


3. **Orchestration**: For each table, identify the update timestamp column. Derive information about scheduling strategy and refresh latency using the JSON key `latest_dates`. The `latest_dates` key returns the last 10 dates in descending order for datetime columns. If it is not possible to collect the information, skip this step. Some examples are: 

   > A source materialized as table, full-refresh every run.

   > An incremental source, which inserts and updates records from the previous day.

4. **Relationships**: Once the PKs are laid out, identify the possibilities of Primary Key-Foreign Key combinations between the set of sources. Some examples are: 
   > The source table transactions contains a FK column customer_id. The table customers contains a PK column customer_id. You identify that transactions and customers relates to each other through customer_id.

   > The source table purchase_orders contains a FK column supplier_id. The table suppliers contains a PK column supplier_id. You identify that purchase_orders and suppliers relate to each other through supplier_id.

   > The source table support_tickets contains a FK column agent_id. The table support_agents contains a PK column agent_id. You identify that support_tickets and support_agents relate to each other through agent_id.

   For every data source, compute an Entity-Relationship-Diagram with all other data sourcer that it relates and the respective columns with their keys. Represent the ERD as a Mermaid diagram using erDiagram syntax.

5. **File Creation**: Write one file per table. If path not provided, write under the default path. The file name should be written as "<name_of_datasource>__<current_timestamp>".
   - Default Path: /Users/julianasampar/Desktop/learning_dev/personal_dev/pyprojects/.claude/agents/data_discovery_agent/inspector/resources/<domain>/<name_of_datasource>

   