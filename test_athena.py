import asyncio
from backend.services.athena_client import AthenaClient

async def main():
    client = AthenaClient()
    query = """
    SELECT *
    FROM (
        SELECT machine_id, temperature, vibration, pressure, degradation_level, cycle_efficiency, power_consumption,
               ROW_NUMBER() OVER (PARTITION BY machine_id ORDER BY timestamp DESC) as rn
        FROM telemetry_curated
    )
    WHERE rn = 1
    LIMIT 5;
    """
    rows = await client.execute_query(query)
    for r in rows:
        print(r)

if __name__ == '__main__':
    asyncio.run(main())
