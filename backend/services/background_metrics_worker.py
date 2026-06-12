import asyncio
import logging

from backend.services.athena_client import AthenaClient
from backend.services.analytics_service import AnalyticsService
from backend.services.pipeline_metrics_service import PipelineMetricsService

logger = logging.getLogger("BackgroundWorker")

class BackgroundMetricsWorker:
    def __init__(self):
        self.athena_client = AthenaClient()
        self.analytics_service = AnalyticsService(self.athena_client)
        self.pipeline_service = PipelineMetricsService(self.athena_client)
        self.tasks = []
        self._running = False

    async def start(self):
        self._running = True
        logger.info("Starting Background Metrics Worker")
        
        self.tasks.append(asyncio.create_task(self._poll_pipeline_metrics(35)))
        self.tasks.append(asyncio.create_task(self._poll_fleet_analytics(60)))
        self.tasks.append(asyncio.create_task(self._poll_athena_analytics(300)))

    async def stop(self):
        self._running = False
        logger.info("Stopping Background Metrics Worker")
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def _poll_pipeline_metrics(self, interval: int):
        """Poll fast-moving pipeline metrics (Kinesis, Lambda, S3)."""
        while self._running:
            try:
                # Triggers cache refresh if TTL expired
                await self.pipeline_service.get_realtime_metrics()
            except Exception as e:
                logger.error(f"Error in pipeline metrics polling: {e}")
            await asyncio.sleep(interval)

    async def _poll_fleet_analytics(self, interval: int):
        """Poll medium-moving fleet analytics."""
        while self._running:
            try:
                await self.analytics_service.get_machines()
                await self.analytics_service.get_factory_summary()
                await self.analytics_service.get_telemetry_activity("24h")
            except Exception as e:
                logger.error(f"Error in fleet analytics polling: {e}")
            await asyncio.sleep(interval)

    async def _poll_athena_analytics(self, interval: int):
        """Poll slow-moving complex Athena aggregates."""
        while self._running:
            try:
                await self.analytics_service.get_alerts(50)
                await self.analytics_service.get_aggregated_analytics()
                await self.analytics_service.get_business_kpis()
                await self.analytics_service.get_energy_profile()
                await self.analytics_service.get_hourly_trends()
                await self.analytics_service.get_root_causes()
            except Exception as e:
                logger.error(f"Error in athena analytics polling: {e}")
            await asyncio.sleep(interval)

worker = BackgroundMetricsWorker()
