import asyncio
from backend.services.athena_client import AthenaClient
from backend.services.analytics_service import AnalyticsService

async def main():
    client = AthenaClient()
    service = AnalyticsService(client)
    
    machines = await service.get_machines()
    
    healthy = 0
    warning = 0
    critical = 0
    offline = 0
    
    print("Machine Health Report:")
    for m in machines[:10]:
        print(f"[{m['machine_id']}] {m['machine_type']} -> Score: {m.get('health_score')}% | Status: {m['health_status']}")
        
    for m in machines:
        s = m['health_status']
        if s == 'healthy': healthy += 1
        elif s == 'warning': warning += 1
        elif s == 'critical': critical += 1
        else: offline += 1
        
    total = len(machines)
    print("\nOverall Distribution:")
    print(f"Total Machines: {total}")
    if total > 0:
        print(f"Healthy:  {healthy} ({healthy/total*100:.1f}%)")
        print(f"Warning:  {warning} ({warning/total*100:.1f}%)")
        print(f"Critical: {critical} ({critical/total*100:.1f}%)")
        print(f"Offline:  {offline} ({offline/total*100:.1f}%)")

if __name__ == '__main__':
    asyncio.run(main())
