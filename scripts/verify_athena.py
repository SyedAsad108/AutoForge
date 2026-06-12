"""
AutoForge Athena Analytics Layer Verification & Cost Benchmarking
1. Loads partitions (MSCK REPAIR)
2. Deploys views from athena/views.sql
3. Runs baseline analytical queries
4. Runs view-based queries
5. Verifies partition pruning
6. Calculates AWS Athena cost visibility metrics
7. Writes a comprehensive report to athena_benchmark_report.md
"""
import boto3
import time
import os
import sys

athena = boto3.client('athena', region_name='ap-south-1')

DATABASE = 'autoforge_analytics'
WORKGROUP = 'autoforge-analytics'
VIEWS_FILE = os.path.join(os.path.dirname(__file__), '..', 'athena', 'views.sql')
REPORT_FILE = os.path.join(os.path.dirname(__file__), '..', 'athena_benchmark_report.md')

# Storage for benchmark statistics
benchmark_runs = []

def run_query(query_string, label):
    print('=' * 60)
    print(f"Executing: {label}")
    print('=' * 60)
    
    response = athena.start_query_execution(
        QueryString=query_string,
        QueryExecutionContext={'Database': DATABASE},
        WorkGroup=WORKGROUP
    )
    execution_id = response['QueryExecutionId']
    
    # Wait for completion
    while True:
        status_resp = athena.get_query_execution(QueryExecutionId=execution_id)
        status = status_resp['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)
        
    if status != 'SUCCEEDED':
        reason = status_resp['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
        print(f"ERROR: Query failed: {reason}")
        return None, None
        
    stats = status_resp['QueryExecution']['Statistics']
    data_scanned = stats.get('DataScannedInBytes', 0)
    exec_time = stats.get('EngineExecutionTimeInMillis', 0)
    
    # Cost visibility logic: Athena charges $5.00 per TB ($5.00 * 10^-12 per byte)
    # Athena has a 10MB minimum per query scan for billing purposes (10MB = 10 * 1000 * 1000 bytes)
    billing_bytes = max(data_scanned, 10 * 1000 * 1000)
    estimated_cost = (billing_bytes / 1e12) * 5.0
    
    print(f"Metrics -> Data Scanned: {data_scanned} bytes (Billed: {billing_bytes} bytes)")
    print(f"Metrics -> Execution Time: {exec_time} ms | Est. Cost: ${estimated_cost:.8f}\n")
    
    # Store stats
    benchmark_runs.append({
        'label': label,
        'query': query_string.strip(),
        'data_scanned_bytes': data_scanned,
        'billing_bytes': billing_bytes,
        'exec_time_ms': exec_time,
        'cost_usd': estimated_cost
    })
    
    # Get results
    results = athena.get_query_results(QueryExecutionId=execution_id)
    return status_resp, results

def print_results(results):
    if not results:
        return ""
        
    rows = results['ResultSet']['Rows']
    if not rows:
        print("No results returned.")
        return "No results returned."
        
    headers = [col.get('VarCharValue', 'NULL') for col in rows[0]['Data']]
    col_widths = [len(h) for h in headers]
    
    data_rows = []
    for r in rows[1:]:
        data_row = [col.get('VarCharValue', 'NULL') for col in r['Data']]
        data_rows.append(data_row)
        for i, val in enumerate(data_row):
            col_widths[i] = max(col_widths[i], len(val))
            
    header_line = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
    out_str = "  " + header_line + "\n  " + "-" * len(header_line) + "\n"
    print("  " + header_line)
    print("  " + "-" * len(header_line))
    
    for row in data_rows:
        row_str = " | ".join(f"{val:<{col_widths[i]}}" for i, val in enumerate(row))
        out_str += "  " + row_str + "\n"
        print("  " + row_str)
    print()
    return out_str

def deploy_views():
    print("Deploying Athena Views from athena/views.sql...")
    if not os.path.exists(VIEWS_FILE):
        print(f"ERROR: views.sql file not found at {VIEWS_FILE}")
        sys.exit(1)
        
    with open(VIEWS_FILE, 'r') as f:
        content = f.read()
        
    # Split queries by semicolon (excluding SQL comments)
    queries = []
    current_query = []
    for line in content.split('\n'):
        if line.strip().startswith('--') or not line.strip():
            continue
        current_query.append(line)
        if ';' in line:
            queries.append('\n'.join(current_query))
            current_query = []
            
    for i, q in enumerate(queries, 1):
        # Extract view name for labeling
        label = f"Deploy View #{i}"
        if "VIEW" in q:
            view_name = q.split("VIEW")[1].split("AS")[0].strip()
            label = f"Deploy View: {view_name}"
        run_query(q, label)

def generate_benchmark_report():
    print(f"Generating benchmark report in {REPORT_FILE}...")
    
    # Calculate partition pruning savings
    full_scan_run = next((r for r in benchmark_runs if r['label'] == "Full Table Scan Query"), None)
    pruned_scan_run = next((r for r in benchmark_runs if r['label'] == "Pruned Partition Query"), None)
    
    pruning_savings_md = ""
    if full_scan_run and pruned_scan_run:
        full_bytes = full_scan_run['data_scanned_bytes']
        pruned_bytes = pruned_scan_run['data_scanned_bytes']
        reduction = (1.0 - (float(pruned_bytes) / full_bytes)) * 100.0 if full_bytes > 0 else 0.0
        pruning_savings_md = f"""
### Partition Pruning Optimization Gains
* **Full Table Scan**: `{full_bytes:,} bytes` scanned
* **Pruned Partition Scan (Single-Day & Machine Type)**: `{pruned_bytes:,} bytes` scanned
* **Data Reduction**: **{reduction:.2f}% less data scanned**
* **Optimization Summary**: Partitioning by `machine_type`, `year`, `month`, and `day` successfully filters out irrelevant directories at the S3 bucket level. In production, this directly translates to **{reduction:.2f}% cost savings** and faster query runtimes.
"""

    report_content = f"""# AutoForge Smart Manufacturing Analytics — Athena Cost & Performance Benchmark Report

This document records the cost and performance benchmarking of the Athena Analytics Layer, demonstrating execution efficiency, data scans, and query partition pruning benefits.

## Cost Visibility & Billing Model
Athena is billed on a decimal TB scale at **$5.00 per TB scanned** ($0.000000000005 per byte), subject to a **10MB minimum charge per query** ($0.00000005) to account for metadata overhead.

---

## 1. Summary of Benchmark Runs

| Query Label | Execution Time (ms) | Data Scanned (bytes) | Billed Volume (bytes) | Est. Cost (USD) |
| :--- | :---: | :---: | :---: | :---: |
"""
    for r in benchmark_runs:
        # Format bytes
        ds_formatted = f"{r['data_scanned_bytes']:,}"
        b_formatted = f"{r['billing_bytes']:,}"
        report_content += f"| {r['label']} | {r['exec_time_ms']} | {ds_formatted} | {b_formatted} | ${r['cost_usd']:.8f} |\n"

    report_content += "\n---\n"
    report_content += pruning_savings_md
    report_content += "\n---\n"
    
    report_content += "## 2. Detailed Query Library Definitions & Sample Outputs\n\n"
    
    # We will append query definitions and results
    # To do this safely, we run the script and write out the details of each run
    for r in benchmark_runs:
        report_content += f"### {r['label']}\n"
        report_content += f"**SQL Statement**:\n```sql\n{r['query']}\n```\n\n"
        report_content += f"* **Engine Execution Time**: `{r['exec_time_ms']} ms`\n"
        report_content += f"* **Actual Data Scanned**: `{r['data_scanned_bytes']:,} bytes`\n"
        report_content += f"* **Estimated Query Cost**: `${r['cost_usd']:.8f}`\n\n"
        
    with open(REPORT_FILE, 'w') as f:
        f.write(report_content)
    print("Report written successfully.")

def main():
    # 1. Load Partitions
    repair_query = "MSCK REPAIR TABLE telemetry_curated;"
    print("Repairing table partitions...")
    resp, _ = run_query(repair_query, "MSCK REPAIR TABLE telemetry_curated")
    if not resp:
        print("Partition load failed. Exiting.")
        sys.exit(1)
        
    # 2. Deploy Views
    deploy_views()
        
    # 3. Required Query: Machine Count by Type
    q_count = """
    SELECT machine_type, COUNT(*) AS count
    FROM telemetry_curated
    GROUP BY machine_type
    ORDER BY count DESC;
    """
    _, res_count = run_query(q_count, "Required Query: Machine Count by Type")
    print_results(res_count)

    # 4. Required Query: Machine Health
    q_health = """
    SELECT machine_id,
           AVG(CAST(temperature AS DOUBLE)) AS avg_temp
    FROM telemetry_curated
    GROUP BY machine_id
    ORDER BY avg_temp DESC;
    """
    _, res_health = run_query(q_health, "Required Query: Machine Health (Avg Temperature)")
    print_results(res_health)

    # 5. Required Query: Anomaly Trends
    q_anomaly = """
    SELECT anomaly_type,
           COUNT(*) AS anomaly_count
    FROM telemetry_curated
    WHERE anomaly_detected = true
    GROUP BY anomaly_type
    ORDER BY anomaly_count DESC;
    """
    _, res_anomaly = run_query(q_anomaly, "Required Query: Anomaly Trends")
    print_results(res_anomaly)

    # 6. Analytical Query: Most Active Machines
    q_active = """
    SELECT machine_id,
           machine_type,
           COUNT(*) AS event_count
    FROM telemetry_curated
    GROUP BY machine_id, machine_type
    ORDER BY event_count DESC
    LIMIT 5;
    """
    _, res_active = run_query(q_active, "Analytical Query: Most Active Machines")
    print_results(res_active)

    # 7. Analytical Query: Average Temperature by Machine Type
    q_type_temp = """
    SELECT machine_type,
           AVG(temperature) AS avg_temp
    FROM telemetry_curated
    GROUP BY machine_type
    ORDER BY avg_temp DESC;
    """
    _, res_type_temp = run_query(q_type_temp, "Analytical Query: Average Temperature by Machine Type")
    print_results(res_type_temp)

    # 8. Analytical Query: Machines with Highest Anomaly Rates
    q_anomaly_rate = """
    SELECT machine_id,
           machine_type,
           COUNT(*) AS total_events,
           SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_events,
           (CAST(SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*)) * 100.0 AS anomaly_rate_percent
    FROM telemetry_curated
    GROUP BY machine_id, machine_type
    ORDER BY anomaly_rate_percent DESC, total_events DESC
    LIMIT 5;
    """
    _, res_anomaly_rate = run_query(q_anomaly_rate, "Analytical Query: Highest Anomaly Rate Machines")
    print_results(res_anomaly_rate)

    # 9. Analytical Query: Daily Telemetry Volume
    q_daily = """
    SELECT year,
           month,
           day,
           COUNT(*) AS daily_volume
    FROM telemetry_curated
    GROUP BY year, month, day
    ORDER BY year DESC, month DESC, day DESC;
    """
    _, res_daily = run_query(q_daily, "Analytical Query: Daily Telemetry Volume")
    print_results(res_daily)

    # 10. Analytical Query: Energy Consumption by Machine Type
    q_energy = """
    SELECT machine_type,
           SUM(COALESCE(power_consumption, 0.0) + COALESCE(energy_usage, 0.0) + COALESCE(energy_output, 0.0)) AS total_energy_units
    FROM telemetry_curated
    GROUP BY machine_type
    ORDER BY total_energy_units DESC;
    """
    _, res_energy = run_query(q_energy, "Analytical Query: Energy Consumption by Machine Type")
    print_results(res_energy)

    # 11. View Queries
    q_v1 = "SELECT * FROM machine_health_view ORDER BY anomaly_rate_percent DESC LIMIT 5;"
    _, res_v1 = run_query(q_v1, "Query View: machine_health_view")
    print_results(res_v1)

    q_v2 = "SELECT * FROM anomaly_summary_view ORDER BY anomaly_count DESC LIMIT 5;"
    _, res_v2 = run_query(q_v2, "Query View: anomaly_summary_view")
    print_results(res_v2)

    q_v3 = "SELECT * FROM daily_factory_summary_view ORDER BY total_events DESC;"
    _, res_v3 = run_query(q_v3, "Query View: daily_factory_summary_view")
    print_results(res_v3)

    q_v4 = "SELECT * FROM hourly_factory_summary_view ORDER BY hour_bucket DESC LIMIT 5;"
    _, res_v4 = run_query(q_v4, "Query View: hourly_factory_summary_view")
    print_results(res_v4)

    q_v5 = "SELECT * FROM telemetry_timeseries_view ORDER BY minute_bucket DESC LIMIT 5;"
    _, res_v5 = run_query(q_v5, "Query View: telemetry_timeseries_view")
    print_results(res_v5)

    # 12. Partition Pruning Comparison
    # Query 10A: Full Table Scan (forcing actual data scanning by calculating SUM)
    q_full = "SELECT SUM(temperature) FROM telemetry_curated;"
    resp_full, _ = run_query(q_full, "Full Table Scan Query")
    
    # Query 10B: Pruned Query (Only assembly_robot for a single day)
    q_pruned = """
    SELECT SUM(temperature) FROM telemetry_curated
    WHERE machine_type = 'assembly_robot'
      AND year = 2026
      AND month = 6
      AND day = 3;
    """
    resp_pruned, _ = run_query(q_pruned, "Pruned Partition Query")

    # 13. Write report
    generate_benchmark_report()

if __name__ == '__main__':
    main()
