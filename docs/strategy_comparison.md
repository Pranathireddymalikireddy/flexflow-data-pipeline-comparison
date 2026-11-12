# Data Pipeline Strategy Comparison



## 1. Business Problem



Data engineering pipelines need reliable methods to load and update data in target databases. Different loading strategies have different performance characteristics, data movement requirements, and failure-recovery behavior.



This project compares three data publishing strategies:



1. Full Refresh

2. Incremental Merge

3. Partition Replacement



The objective is to compare their execution time, scalability, data correctness, complexity, and failure-recovery trade-offs using a consistent dataset.



## 2. Project Objective and Scope



The project implements and evaluates all three strategies using Python, Pandas, and SQLite.



The solution covers:



- Generating a reproducible dataset of customer and order records.

- Validating and cleaning incoming data.

- Publishing data using three different strategies.

- Comparing final target data to confirm equivalent results.

- Measuring execution time at multiple dataset sizes.

- Simulating a realistic incremental workload.

- Testing rollback, retry, and idempotency behavior.

- Documenting performance and operational trade-offs.



## 3. Technology Stack



| Technology | Purpose |

|---|---|

| Python | Pipeline implementation |

| Pandas | Data processing and comparison |

| SQLite | Target database |

| SQL | Insert, update, delete, and merge operations |

| CSV | Raw data and benchmark reports |

| unittest | Automated testing |

| Matplotlib | Benchmark visualizations, where applicable |



## 4. Dataset Description



The project uses generated customer and order data.



The order dataset includes:



- `order_id`: Unique order identifier.

- `customer_id`: Customer associated with the order.

- `order_date`: Date used for partitioning.

- `amount`: Order amount.

- `status`: Order status.

- `updated_at`: Timestamp used to identify newer records.



The data generator uses a fixed random seed to make benchmark runs reproducible.



Four dataset sizes are evaluated:



- 1,000 orders

- 10,000 orders

- 50,000 orders

- 100,000 orders



Order dates are distributed across a 30-day period.



## 5. Data Publishing Strategies



### 5.1 Full Refresh



Full Refresh deletes the existing target records and loads the complete incoming dataset.



**Process:**



1. Start a database transaction.

2. Delete existing orders and customers.

3. Insert all incoming customers.

4. Insert all incoming orders.

5. Commit the transaction.

6. Roll back if an error occurs.



**Advantages:**

- Simple implementation.

- Target data is rebuilt from the complete source.

- Useful for small datasets and full rebuilds.



**Disadvantages:**

- Reprocesses the entire dataset.

- Can require significant data movement.

- May take longer as the dataset grows.



### 5.2 Incremental Merge



Incremental Merge processes only new and changed records.



**Process:**



1. Start a database transaction.

2. Insert new customers when they do not already exist.

3. Insert new orders.

4. Update existing orders only when the incoming `updated_at` timestamp is newer.

5. Commit the transaction.

6. Roll back if an error occurs.



**Advantages:**

- Processes only changed and new records.

- Avoids rewriting unchanged records.

- Suitable for frequent updates and sparse changes.



**Disadvantages:**

- Requires a reliable unique key.

- Requires change detection, such as an update timestamp.

- More complex than a full refresh.



### 5.3 Partition Replacement



Partition Replacement replaces complete affected date partitions rather than rewriting the entire dataset.



**Process:**



1. Start a database transaction.

2. Identify the affected `order_date` partitions.

3. Delete existing records in those partitions.

4. Insert the complete incoming snapshots for those partitions.

5. Commit the transaction.

6. Roll back if an error occurs.



**Advantages:**

- Avoids rewriting unaffected partitions.

- Useful when complete snapshots are available for selected partitions.

- Can reduce data movement compared with a full refresh.



**Disadvantages:**

- Requires complete and accurate snapshots for affected partitions.

- Replaces all records in each affected partition.

- An incomplete snapshot can cause valid records to be deleted.



**Important assumption:** Partition Replacement receives the complete final snapshot for every affected date, not just the changed rows.



## 6. Benchmark Methodology



Two separate benchmark experiments were performed.



### 6.1 Initial-Load Scalability Benchmark



Each strategy was tested against an empty target database using the complete dataset.



Dataset sizes:



| Dataset size | Orders |

|---|---:|

| Small | 1,000 |

| Medium | 10,000 |

| Large | 50,000 |

| Very Large | 100,000 |



All three strategies were checked to ensure that they produced equivalent final customer and order data.



Results were saved in:



`reports/strategy_scalability.csv`



### 6.2 Realistic Incremental Workload Benchmark



A second experiment simulated an existing database receiving new and updated records.



Workload design:



- 80% of the final orders were initially loaded.

- 20% of the initial orders were updated.

- 20% additional new orders were introduced.

- Changes were restricted to 10 affected date partitions.

- Incremental Merge received only updated and new records.

- Partition Replacement received complete snapshots of the affected partitions.

- Full Refresh received the complete final dataset.



All strategies were compared against the same expected final dataset.



Results were saved in:



`reports/incremental_workload_comparison.csv`



## 7. Initial-Load Benchmark Results



Execution time in seconds:



| Orders | Full Refresh | Incremental Merge | Partition Replacement |

|---:|---:|---:|---:|

| 1,000 | 0.032462 | 0.026636 | 0.041843 |

| 10,000 | 0.121812 | 0.111649 | 0.113611 |

| 50,000 | 0.472910 | 0.543621 | 0.522749 |

| 100,000 | 2.131293 | 4.038866 | 1.366499 |



These results represent initial loading into empty databases. Incremental Merge receives the full dataset in this experiment, and Partition Replacement replaces all date partitions. Therefore, these measurements should not be interpreted as realistic incremental-update performance.



## 8. Realistic Incremental Workload Results



Execution time in seconds:



| Orders | Full Refresh | Incremental Merge | Partition Replacement |

|---:|---:|---:|---:|

| 1,000 | 0.025731 | 0.019986 | 0.023601 |

| 10,000 | 0.123289 | 0.078197 | 0.104745 |

| 50,000 | 0.778921 | 0.425094 | 0.471403 |

| 100,000 | 2.149464 | 1.037311 | 1.261006 |



### Key Observations



- Incremental Merge was the fastest strategy at all four dataset sizes in this workload.

- At 100,000 orders, Incremental Merge completed in approximately 1.04 seconds.

- Full Refresh took approximately 2.15 seconds at 100,000 orders.

- Partition Replacement took approximately 1.26 seconds at 100,000 orders.

- At the largest size, Incremental Merge was approximately 51.7% faster than Full Refresh.

- Partition Replacement was approximately 41.3% faster than Full Refresh.

- Partition Replacement processed 46,685 records in its affected partition snapshots instead of replacing all 100,000 orders.



These are measurements from a single local benchmark run. Actual performance can vary with hardware, database configuration, data distribution, and workload.



## 9. Complexity and Data Movement



| Strategy | Main work | Approximate cost |
|---|---|---|
| Full Refresh | Delete and insert all N records | O(N), plus index maintenance |
| Incremental Merge | Process D new or changed records and perform key lookups | Approximately O(D log N) for indexed key operations |
| Partition Replacement | Replace R records across affected partitions | Approximately O(P + R log N), depending on partition lookup and indexing |

Where:

- N = total records in the dataset.
- D = number of new and changed records.
- P = number of affected partitions.
- R = total records in the affected partition snapshots.




### Data Movement Trade-off



- Full Refresh moves the complete dataset.

- Incremental Merge moves only changed and new records.

- Partition Replacement moves complete snapshots of affected partitions.



## 10. Failure Recovery and Reliability



All three publishing strategies use database transactions.



### Full Refresh



If an error occurs during deletion or insertion, the transaction is rolled back. This protects the previously committed target data.



### Incremental Merge



If an error occurs during the merge, the transaction is rolled back. Retrying the same input is safe for the implemented insert and timestamp-based update behavior. Existing orders are updated only when the incoming timestamp is newer.



### Partition Replacement



Deletion and insertion of affected partitions happen within one transaction. If insertion fails, the deletion is rolled back.



However, the source must provide complete snapshots for affected partitions. An incomplete snapshot can remove records that are absent from the supplied snapshot.



## 11. Automated Testing

Automated tests were implemented using Python's `unittest` framework.

The test suite contains **24 tests across four test modules**.

### Data Cleaning Tests (9)

- Duplicate customer detection.
- Invalid order validation.
- Invalid order status validation.
- Missing customer ID validation.
- Valid customer records.
- Empty customer dataset handling.
- Empty order dataset handling.
- Malformed order values.
- Invalid customer references.

### Ingestion Tests (3)

- Valid CSV schema validation.
- Detection of missing columns.
- Detection of unexpected columns.

### Publishing Strategy Tests (11)

- Full Refresh publishing.
- Incremental insertion of new records.
- Updating records with newer timestamps.
- Ignoring records with older timestamps.
- Preserving unaffected partitions.
- Transaction rollback during failures.
- Handling duplicate order IDs in the same batch.
- Incremental Merge rollback.
- Partition Replacement rollback.
- Retry after failure and idempotent reruns.
- Preserving the latest record during out-of-order arrival.

### Pipeline Tracking Tests (1)

- Logging rejected records with the correct pipeline run ID.
- Preserving source filename and source record number.
- Recording record type and rejection reason.

**Test result:** All 24 automated tests passed successfully.

The test suite covers data validation, schema handling, publishing correctness, transaction safety, and pipeline tracking.

---

## 12. Pipeline Run Tracking and Observability

The project implements pipeline execution tracking using SQLite to maintain an execution history for all three publishing strategies.

Two additional database tables support pipeline observability.

### 12.1 Pipeline Runs Table

The `pipeline_runs` table stores execution metadata.

| Column | Description |
|---|---|
| `run_id` | Unique pipeline execution identifier |
| `pipeline_name` | Name of the publishing strategy |
| `started_at` | Pipeline start timestamp in UTC |
| `completed_at` | Pipeline completion timestamp in UTC |
| `status` | Execution status |
| `input_count` | Total number of input records |
| `inserted_count` | Number of records loaded into the target |
| `updated_count` | Number of updates recorded |
| `rejected_count` | Number of rejected input records |
| `error_message` | Error details when applicable |

Supported execution statuses:

- `RUNNING`: Pipeline execution has started.
- `SUCCESS`: Pipeline completed successfully.
- `MISMATCH`: Final results differ from the reference results.
- `FAILED`: Pipeline execution encountered an exception.

### 12.2 Rejected Records Table

The `rejected_records` table maintains details about records that fail data validation.

It stores:

- Rejected record identifier.
- Associated pipeline run ID.
- Source filename.
- Source record number.
- Record type (CUSTOMER or ORDER).
- Rejection reason.
- Original record information in JSON format.

This provides traceability and helps identify data-quality issues.

### 12.3 Execution Tracking Process

For each publishing strategy:

1. Create a unique pipeline run record.
2. Record the start timestamp in UTC.
3. Store rejected records associated with the run.
4. Execute the selected publishing strategy.
5. Validate the resulting target data.
6. Record the execution status and completion timestamp.
7. Store execution counts and error information.

If an exception occurs, the run is marked as `FAILED` with the corresponding error message.

### 12.4 Verification Results

The comparison runner was executed successfully for all three strategies.

| Strategy | Run ID | Input Records | Loaded Records | Rejected |
|---|---:|---:|---:|---:|
| Full Refresh | 1 | 1,100 | 1,100 | 0 |
| Incremental Merge | 2 | 1,100 | 1,100 | 0 |
| Partition Replacement | 3 | 1,100 | 1,100 | 0 |

All three runs completed with `SUCCESS` status.

The database verification confirmed that execution timestamps, record counts, statuses, and error fields were stored correctly.

A separate automated test verified rejected-record logging using a synthetic invalid order.

This implementation improves pipeline observability, execution traceability, and debugging capabilities.


## 13. Result Equivalence Validation

After each benchmark, the final customer and order data from each strategy were compared with the expected final dataset.

Validation included:

- Customer record equivalence.
- Order record equivalence.
- Matching record counts.
- Matching final values.
- Successful completion of all strategy runs.

All 12 runs in the realistic incremental workload benchmark completed successfully, and all strategies produced equivalent final data.

All 12 runs in the initial-load scalability benchmark also completed successfully with equivalent results.



## 14. Limitations



- Benchmarks use a local SQLite database rather than a distributed or cloud data platform.

- Data is generated synthetically.

- Each reported execution time is from a single run, not a median across repeated runs.

- The dataset uses 30 calendar dates, with 10 affected dates in the realistic workload.

- Results may differ under concurrent workloads or production-scale infrastructure.

- Benchmark timings should be interpreted as local publishing-operation measurements, not universal performance guarantees.



## 15. Recommendations



| Scenario | Recommended strategy | Reason |

|---|---|---|

| Small dataset or complete rebuild | Full Refresh | Simple and reliable |

| Frequent sparse row-level changes | Incremental Merge | Processes only changed and new records |

| Complete snapshots for selected dates or partitions | Partition Replacement | Replaces only affected partitions |



For the simulated incremental workload, Incremental Merge performed best because it processed only the changed and newly added records.



Partition Replacement is a strong alternative when complete snapshots are available for a limited set of partitions.



Full Refresh remains useful when a complete rebuild is required or when simplicity is more important than minimizing data movement.



## 16. Conclusion



This project successfully implemented and compared Full Refresh, Incremental Merge, and Partition Replacement.



Both benchmark experiments confirmed that the strategies can produce equivalent final data when their input requirements are satisfied.



The initial-load benchmark demonstrated how the strategies behave when loading complete datasets. The realistic incremental workload demonstrated the benefit of processing only changed records or affected partitions.



The results show that Incremental Merge is the most efficient option for the tested sparse-change workload, while Partition Replacement is useful when complete partition snapshots are available. Full Refresh remains a straightforward option for complete rebuilds.



The project also demonstrates transactional failure recovery, automated testing, data correctness validation, and performance measurement across increasing dataset sizes.

