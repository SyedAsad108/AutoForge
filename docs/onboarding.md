# AutoForge Onboarding Documentation

This guide provides everything a new software engineer, cloud architect, or security reviewer needs to get AutoForge running from scratch.

---

## 1. Prerequisites

Before starting, install the following tools on your local machine:
- **Python (3.12.x)**: Check with `python --version`. Pre-packaged binaries are available on the [Python Official Downloads page](https://www.python.org/downloads/).
- **Node.js (18.x or 20.x) & npm**: Check with `node --version`.
- **Terraform CLI (1.5.0+)**: Check with `terraform --version`. Pre-packaged binaries are available on the [HashiCorp Install Page](https://developer.hashicorp.com/terraform/downloads).
- **AWS CLI**: Required to configure remote AWS resources. Download from the [AWS CLI Install Page](https://aws.amazon.com/cli/).
- **Docker Desktop**: Recommended for container verification.

---

## 2. Installation & Setup

### Step 1: Install Python Core Dependencies
From the workspace root directory:
```bash
# Install root testing and SDK libraries
pip install -r requirements.txt

# Install backend API frameworks
pip install -r backend/requirements.txt
```

### Step 2: Install Frontend Web Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 3: Configure Environment Variables
Create your local `.env` environment file:
```bash
cp .env.example .env
```
Ensure the default API Key and Kinesis region parameters are set:
```ini
API_KEY=autoforge-dev-key-2026
KINESIS_REGION=ap-south-1
KINESIS_STREAM_NAME=autoforge-telemetry-stream
```

---

## 3. Infrastructure Deployment (AWS Cloud)

To deploy the required cloud resources to your AWS account, configure your regional AWS credentials and use Terraform:

```bash
# 1. Login to your AWS account CLI
aws configure
# Enter your Access Key ID, Secret Access Key, Default Region (ap-south-1), and Output Format (json)

# 2. Navigate to infrastructure folder
cd infra

# 3. Initialize Terraform plugins
terraform init

# 4. Perform a dry-run preview of the infrastructure changes
terraform plan

# 5. Apply the configuration to AWS
terraform apply -auto-approve
```
*Note: This command will output resources details (e.g. Lambda ARN, Kinesis name, S3 buckets).*

---

## 4. Local Execution & Verification

### Step 1: Run Unit Tests
Verify that all unit test components are functional:
```bash
python -m pytest tests/ -v
```
You should see 48 test cases pass successfully.

### Step 2: Launch Backend Ingestion API
```bash
python -m uvicorn backend.main:app --port 8000 --reload
```
Open your browser to: `http://localhost:8000/docs` to test endpoints.

### Step 3: Launch Frontend React App
In a new terminal window:
```bash
cd frontend
npm run dev
```
Open: `http://localhost:5173/`

### Step 4: Run Telemetry Simulator
In a new terminal window:
```bash
python simulator/main.py
```
Check that the console displays machine telemetry counts.

---

## 5. Verification Checklists

### Check 1: S3 Raw Data Verification
Verify that Lambda successfully processes events and writes JSON files to raw partitions:
```bash
python scripts/verify_s3.py
```
Expected output:
`[VERIFY] Successfully found X raw telemetry records in bucket autoforge-data-lake.`

### Check 2: Athena Database Query Verification
Verify that Athena successfully scans the Snappy Parquet partition databases:
```bash
python scripts/verify_athena.py
```

---

## 6. Operational Runbooks

### Runbook 1: Triaging Ingestion Failures
If records fail schema rules, the Lambda validator routes them to the Quarantine S3 bucket.
1. Find quarantined files under:
   `s3://autoforge-quarantine/year=YYYY/month=MM/day=DD/reason=<code>/`
2. Download and inspect the validation error payload:
   ```bash
   aws s3 cp s3://autoforge-quarantine/year=2026/month=06/day=12/ ./quarantine_temp/ --recursive
   ```
3. Inspect `_validation_error` and `_validation_detail` keys inside the quarantined JSON.
4. Correct the simulator configuration/schema, and execute a custom script to republish payloads if required.

### Runbook 2: Manual Data Catalog Repair
When the Glue ETL job writes new partitions to `s3://autoforge-data-lake/curated/` and they do not show up in Athena:
1. Log in to the AWS Console, open the Athena Workgroup.
2. Run partition repair query:
   ```sql
   MSCK REPAIR TABLE telemetry_curated;
   ```
3. Verify partitions are registered:
   ```sql
   SHOW PARTITIONS telemetry_curated;
   ```

### Runbook 3: Tearing Down the Infrastructure
To completely destroy the AWS resources and prevent any residual charges:
```bash
cd infra
terraform destroy -auto-approve
```
Ensure that the output logs confirm: `Destroy complete! Resources: 24 destroyed.`
