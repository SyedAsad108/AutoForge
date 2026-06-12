"""
AutoForge End-to-End Pipeline Verification
Checks: raw/ JSON files, curated/ Parquet partitions, quarantine records
"""
import boto3
import json

s3 = boto3.client('s3', region_name='ap-south-1')
DATALAKE = 'autoforge-data-lake'
QUARANTINE = 'autoforge-quarantine'

# ---------------------------------------------------------------------------
# Raw layer
# ---------------------------------------------------------------------------
print('=' * 60)
print('RAW LAYER')
print('=' * 60)
resp = s3.list_objects_v2(Bucket=DATALAKE, Prefix='raw/', MaxKeys=5)
raw_objects = resp.get('Contents', [])
print('Objects in raw/ (sample):', len(raw_objects), '(up to 5 shown)')
for o in raw_objects:
    print(' ', o['Key'], '-', o['Size'], 'bytes')

if raw_objects:
    sample = s3.get_object(Bucket=DATALAKE, Key=raw_objects[0]['Key'])
    record = json.loads(sample['Body'].read())
    print()
    print('Sample raw record:')
    for k in ['machine_id', 'machine_type', 'status', 'anomaly_detected']:
        print(f'  {k} = {record.get(k)}')
    print('  _enqueue_epoch stripped =', '_enqueue_epoch' not in record)

# Total raw count
total_raw = 0
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=DATALAKE, Prefix='raw/'):
    total_raw += len(page.get('Contents', []))
print()
print('Total raw/ objects:', total_raw)

# ---------------------------------------------------------------------------
# Curated layer
# ---------------------------------------------------------------------------
print()
print('=' * 60)
print('CURATED LAYER (Parquet)')
print('=' * 60)
resp2 = s3.list_objects_v2(Bucket=DATALAKE, Prefix='curated/', MaxKeys=20)
curated = resp2.get('Contents', [])
print('Curated objects (sample):', len(curated))
for o in curated[:10]:
    print(' ', o['Key'], '-', o['Size'], 'bytes')

# Count Parquet files per partition
partitions = {}
for o in curated:
    parts = o['Key'].split('/')
    # curated/machine_type=X/year=Y/month=M/day=D/file.parquet
    if len(parts) >= 5:
        machine = parts[1]
        partitions[machine] = partitions.get(machine, 0) + 1

if partitions:
    print()
    print('Parquet files by machine_type partition:')
    for k, v in sorted(partitions.items()):
        print(f'  {k}: {v} file(s)')
else:
    print('(No curated Parquet files found yet — Glue job may still be running)')

# ---------------------------------------------------------------------------
# Quarantine
# ---------------------------------------------------------------------------
print()
print('=' * 60)
print('QUARANTINE')
print('=' * 60)
resp3 = s3.list_objects_v2(Bucket=QUARANTINE, MaxKeys=5)
q_objects = resp3.get('Contents', [])
print('Quarantine objects:', len(q_objects))
for o in q_objects:
    print(' ', o['Key'])

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print('=' * 60)
pipeline_ok = total_raw > 0
curated_ok = len(curated) > 0
print('PIPELINE STATUS')
print(f'  Simulator -> Kinesis -> Lambda -> Raw S3 : {"[ OK ] VERIFIED" if pipeline_ok else "[ FAIL ] NO DATA"}')
print(f'  EventBridge -> Glue -> Curated Parquet  : {"[ OK ] VERIFIED" if curated_ok else "[ PENDING ] (Glue may be running)"}')
print('=' * 60)
