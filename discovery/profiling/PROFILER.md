# Data Profiling Tool

This Python set performs automated data profiling using DuckDB. The goal is to generate a structured JSON output containing metadata, descriptive statistics, and categorical insights for each table loaded from the source files.

## Workflow

### 1. Columns and Data Types

For each table created from the CSV files, retrieve:

* column names
* inferred data types

---

### 2. Descriptive Metrics

For every column in each table, compute profiling metrics according to the column type.

#### Numeric Columns

Collect:

* `count`: number of non-null values
* `mean`: average value
* `std`: standard deviation
* `min`: minimum value
* `25%`: first quartile
* `50%`: median
* `75%`: third quartile
* `max`: maximum value

#### Object / Categorical Columns

Collect:

* `count`: number of non-null values
* `unique`: number of distinct values
* `top`: most frequent value
* `freq`: frequency of the most frequent value

---

### 3. Distinct Categorical Values

For each non-key categorical column, retrieve the distinct possible values present in the data. Distinct values are only retrieved for columns which contains up to 25 distinct values. The reason for that is to guarantee that primary keys and identifier-like columns are excluded from this step to avoid generating excessively large outputs.

### 4. Latest Date Values

For each date column, retrieve the most recent 10 distinct date stamps. 

In contrast to topic #3, this information is retrieved regardless of how many distinct values the date column contains. This information is used downstream to infer the orchestration and update frequency of the table.


---

## Output

The functions generate a JSON structure containing:

* table metadata
* column data types
* descriptive statistics
* categorical distributions
* distinct categorical values
* distinct date values

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

This output can be used for:

* exploratory data analysis (EDA)
* data quality validation
* schema understanding
* downstream transformation planning
* automated documentation