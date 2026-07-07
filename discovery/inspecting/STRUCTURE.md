---
name: inspect_structure_from_profile
description: "Read data sources profiling, stored in JSON files, to inspect underlying architectural structure, such as primary and foreign keys, relationships between tables and orchestration, and create a JSON file per table with inspected analysis. It should be used after profiler.py is executed or when there is already an existing profile JSON file in storage for the source domain in question."
argument-hint: "[--domain_name] [--storage_type] [--input_path] [--output_path] [--`input_bucket`] [--output_bucket]"
metadata:
  last-updated: 2026-07-07 18:30 UTC
  version: 1.0.0
  category: under development
---
/
## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--domain_name` | Yes | Data domain related to the sources. The Agent should be able to find the pattern and read only the JSON files from the specified domain.  |
| `--storage_type` | Yes | Path where the profiling JSON files are located.  |
| `--input_path` | No |   |
| `--output_path` | No |   |
| `--input_bucket` | No |   |
| `--output_bucket` | No |   |

# Inspect Structure From Profile
## Quick Guide

**The Agent Role:** You are a data developer responsible for discovering and documenting information about a set of ingested source systems associated to a business domain. Your main goal is to inspect and describe the underlying data architecture and relationships across the datasets.

**What It Does**: Connects to the file system storage and reads JSON files containing each table's profiling information. Performs discovery analysis, such as identifying PKs, FKs, Orchestration patterns and relationships.

**Hooks**:
> **`/inspector`** defines the task for READING the profiling JSON files and WRITING the interpreted results. 

**Example**:
<example-user-input>
``` 
User: /inspector
Agent: Detects no storage path nor domain. By default, uses the variables defined in .env. If any variable is provided, asks the user for the storage path and domain. 
```
```
User: The storage path is /profiler/resources and the domain is dvd_rentals.
Agent: The agent find the pattern related to dvd_rentals inside the provided storage, read all respective JSON files and writes the results.
```
```
You: /inspector zendesk
Agent: Detects a domain was provided and searches for all JSON files containing zendesk text pattern. Reads and inspects all tables for Zendesk domain.
```
</example-user-input>

# Architect Discovery

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

 1. **Primary Keys**: For each table, identify the Primary Key or main unique identifier column. If the table doesn't have a PK, create and document a hypothesis about which column combination makes the rows unique.

2. **Foreign Keys**: For each table, identify the Foreign Keys. If the table doesn't have FKs, skip this step.


3. **Orchestration**: For each table, identify the update timestamp column. Derive information about scheduling strategy and refresh latency using the JSON key `latest_dates`. The `latest_dates` key returns the last 10 dates in descending order for datetime columns. If it is not possible to collect the information, skip this step. Some examples are:
  <example-orchestration>
   > A source materialized as table, full-refresh every run.

   > An incremental source, which inserts and updates records from the previous day.
  </example-orchestration>

4. **Relationships**: Once the PKs are laid out, identify the possibilities of Primary Key-Foreign Key combinations between the set of sources. Some examples are:
  <example-relationships>
   > The source table transactions contains a FK column customer_id. The table customers contains a PK column customer_id. You identify that transactions and customers relates to each other through customer_id.

   > The source table purchase_orders contains a FK column supplier_id. The table suppliers contains a PK column supplier_id. You identify that purchase_orders and suppliers relate to each other through supplier_id.

   > The source table support_tickets contains a FK column agent_id. The table support_agents contains a PK column agent_id. You identify that support_tickets and support_agents relate to each other through agent_id.
  </example-relationships>
   For every data source, compute an Entity-Relationship-Diagram with all other data sourcer that it relates and the respective columns with their keys. Represent the ERD as a Mermaid diagram using erDiagram syntax.

5. **File Creation**: Write one JSON file per table. If path not provided, write under the default path.

</steps>


   