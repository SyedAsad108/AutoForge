"""
Analytics Service for the AutoForge backend.
Encapsulates query logic, transforms Athena's string outputs into proper types,
and implements a memory-based TTL caching layer.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from backend.services.athena_client import AthenaClient
from backend.services.cache_service import cache_service, with_cache
from backend.core.logger import get_logger

logger = get_logger("AnalyticsService")


class AnalyticsService:
    """
    Handles business-level analytics queries against Athena.
    Uses CacheService for stale-while-revalidate caching.
    """

    def __init__(self, athena_client: AthenaClient) -> None:
        self.athena = athena_client
        logger.info("[ANALYTICS] AnalyticsService initialized")

    async def get_factory_summary(self) -> Dict[str, Any]:
        """
        Get aggregated factory status counts from get_machines.
        """
        async def fetch_factory_summary():
            machines = await self.get_machines()
            total_machines = len(machines)
            healthy = sum(1 for m in machines if m["health_status"] == "healthy")
            warning = sum(1 for m in machines if m["health_status"] == "warning")
            critical = sum(1 for m in machines if m["health_status"] == "critical")
            offline = sum(1 for m in machines if m["health_status"] == "offline")

            return {
                "total_machines": total_machines,
                "healthy": healthy,
                "warning": warning,
                "critical": critical,
                "offline": offline,
            }

        return await cache_service.get_or_fetch(
            "factory_summary", 
            fetch_factory_summary, 
            ttl=60.0
        )

    async def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve recent anomaly events.
        """
        async def fetch_alerts():
            query = f"""
            SELECT event_id, machine_id, machine_type, timestamp, anomaly_type, anomaly_severity, status
            FROM telemetry_curated
            WHERE anomaly_detected = true
            ORDER BY timestamp DESC
            LIMIT {limit};
            """
            rows = await self.athena.execute_query(query)
            alerts = []

            for r in rows:
                alerts.append({
                    "event_id": r.get("event_id"),
                    "machine_id": r.get("machine_id"),
                    "machine_type": r.get("machine_type"),
                    "timestamp": r.get("timestamp"),
                    "anomaly_type": r.get("anomaly_type") or "unknown",
                    "severity": float(r.get("anomaly_severity") or 0.0),
                    "status": r.get("status") or "anomaly",
                })
            return alerts

        return await cache_service.get_or_fetch(
            f"alerts_limit_{limit}",
            fetch_alerts,
            ttl=30.0
        )

    def _calculate_weighted_health_score(self, record: Dict[str, Any], machine_type: str) -> float:
        """
        Calculate weighted health score based on metrics:
        - Temperature: 25%
        - Vibration: 20%
        - Power: 15%
        - Pressure: 15%
        - Efficiency: 15%
        - Degradation: 10%
        """
        # 1. Temperature (25%)
        temp_val = record.get("temperature") or record.get("motor_temperature")
        if temp_val is not None:
            try:
                temp = float(temp_val)
                if temp <= 75.0:
                    temp_score = 100.0
                else:
                    temp_score = max(20.0, 100.0 - (temp - 75.0) * 2.0)
            except (ValueError, TypeError):
                temp_score = 100.0
        else:
            temp_score = 100.0

        # 2. Vibration (20%)
        vib_val = record.get("vibration")
        if vib_val is not None:
            try:
                vib = float(vib_val)
                if vib <= 5.0:
                    vib_score = 100.0
                else:
                    vib_score = max(20.0, 100.0 - (vib - 5.0) * 15.0)
            except (ValueError, TypeError):
                vib_score = 100.0
        else:
            vib_score = 100.0

        # 3. Power (15%)
        power_val = record.get("power_consumption") or record.get("energy_usage") or record.get("energy_output")
        if power_val is not None:
            try:
                power = float(power_val)
                if 5.0 <= power <= 120.0:
                    power_score = 100.0
                elif power < 5.0:
                    power_score = max(40.0, 100.0 - (5.0 - power) * 10.0)
                else:
                    power_score = max(20.0, 100.0 - (power - 120.0) * 1.5)
            except (ValueError, TypeError):
                power_score = 100.0
        else:
            power_score = 100.0

        # 4. Pressure (15%)
        press_val = record.get("pressure") or record.get("hydraulic_pressure")
        if press_val is not None:
            try:
                press = float(press_val)
                if press <= 250.0:
                    press_score = 100.0
                else:
                    press_score = max(20.0, 100.0 - (press - 250.0) * 0.5)
            except (ValueError, TypeError):
                press_score = 100.0
        else:
            press_score = 100.0

        # 5. Efficiency (15%)
        eff_val = record.get("cycle_efficiency") or record.get("task_completion_rate")
        if eff_val is not None:
            try:
                eff = float(eff_val)
                if eff >= 0.80:
                    eff_score = 100.0
                else:
                    eff_score = max(20.0, 100.0 - (0.80 - eff) * 200.0)
            except (ValueError, TypeError):
                eff_score = 100.0
        else:
            eff_score = 100.0

        # 6. Degradation (10%)
        deg_val = record.get("degradation_level")
        if deg_val is not None:
            try:
                deg = float(deg_val)
                deg_score = max(0.0, min(100.0, (1.0 - deg) * 100.0))
            except (ValueError, TypeError):
                deg_score = 100.0
        else:
            deg_score = 100.0

        # Final weighted sum
        score = (
            temp_score * 0.25 +
            vib_score * 0.20 +
            power_score * 0.15 +
            press_score * 0.15 +
            eff_score * 0.15 +
            deg_score * 0.10
        )
        
        # Clamp to avoid extreme values and return
        return round(max(25.0, min(98.0, score)), 1)

    async def get_machines(self) -> List[Dict[str, Any]]:
        """
        List all machines and their statuses using the latest telemetry data and weighted health scoring.
        """
        async def fetch_machines():
            # Get historical summaries for totals
            view_query = "SELECT machine_id, machine_type, total_events, anomaly_events, anomaly_rate_percent FROM machine_health_view;"
            view_rows = await self.athena.execute_query(view_query)
            view_lookup = {r.get("machine_id"): r for r in view_rows}

            # Query latest telemetry records for all machines to calculate current conditions
            latest_query = """
            SELECT *
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY machine_id ORDER BY timestamp DESC) as rn
                FROM telemetry_curated
            )
            WHERE rn = 1;
            """
            latest_rows = await self.athena.execute_query(latest_query)
            
            machines = []

            for r in latest_rows:
                machine_id = r.get("machine_id")
                m_type = r.get("machine_type") or "unknown"
                
                # Merge with view totals
                v_data = view_lookup.get(machine_id, {})
                anom_rate = float(v_data.get("anomaly_rate_percent") or 0.0)
                
                health_score = self._calculate_weighted_health_score(r, m_type)
                
                # Determine health status based on the weighted health score
                if health_score < 50.0:
                    status = "critical"
                elif health_score < 80.0:
                    status = "warning"
                else:
                    status = "healthy"

                machines.append({
                    "machine_id": machine_id,
                    "machine_type": m_type,
                    "total_events": int(v_data.get("total_events") or 0),
                    "anomaly_events": int(v_data.get("anomaly_events") or 0),
                    "anomaly_rate_percent": anom_rate,
                    "avg_temperature": float(r.get("temperature") or 0.0) if r.get("temperature") else None,
                    "max_degradation_level": float(r.get("degradation_level") or 0.0),
                    "health_status": status,
                    "health_score": health_score,
                })

            return machines

        return await cache_service.get_or_fetch(
            "machines_list",
            fetch_machines,
            ttl=15.0
        )

    @with_cache("machine_analytics_{machine_id}_{window}", ttl=15.0)
    async def get_machine_analytics(self, machine_id: str, window: str = "24h") -> Dict[str, Any]:
        """
        Query metrics and historical data for a specific machine.
        Supports time-series trends over different windows (15m, 1h, 24h, 7d).
        Provides live operating conditions, predictive maintenance stats, active anomalies,
        ranked root causes, and risk timeline.
        """

        # 1. Fetch metadata & totals from views
        view_query = f"SELECT * FROM machine_health_view WHERE machine_id = '{machine_id}';"
        view_rows = await self.athena.execute_query(view_query)
        if not view_rows:
            return {}

        v = view_rows[0]
        deg = float(v.get("max_degradation_level") or 0.0)
        anom_rate = float(v.get("anomaly_rate_percent") or 0.0)

        # 2. Get the latest event from telemetry_curated for live operating conditions
        latest_query = f"""
        SELECT timestamp, status, anomaly_detected, anomaly_type, anomaly_severity,
               degradation_level, anomaly_reason, trigger_metric, trigger_value,
               expected_range, root_cause_candidates, recommended_actions,
               diagnostic_confidence, temperature, pressure, power_consumption, vibration, cycle_efficiency
        FROM telemetry_curated
        WHERE machine_id = '{machine_id}'
        ORDER BY timestamp DESC
        LIMIT 1;
        """
        latest_rows = await self.athena.execute_query(latest_query)
        
        # Parse latest event safely
        def parse_athena_ts(ts_val: Any) -> datetime:
            if not ts_val:
                return datetime.utcnow()
            s = str(ts_val).strip()
            s = s.replace("Z", "")
            if "T" in s:
                s = s.replace("T", " ")
            if "." in s:
                s = s.split(".")[0]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            return datetime.utcnow()

        if latest_rows:
            latest = latest_rows[0]
            max_dt = parse_athena_ts(latest.get("timestamp"))
            
            health_score = self._calculate_weighted_health_score(latest, v.get("machine_type") or "unknown")
            
            # Determine status based on health_score
            if health_score < 50.0:
                status = "critical"
            elif health_score < 80.0:
                status = "warning"
            else:
                status = "healthy"
        else:
            latest = {}
            max_dt = datetime.utcnow()
            health_score = 98.0
            status = "healthy"

        # 3. Query historical trends for the selected window
        # Determine interval and grouping
        if window == "15m":
            delta = timedelta(minutes=15)
            bucket_expr = "SUBSTR(timestamp, 1, 16)"
        elif window == "1h":
            delta = timedelta(hours=1)
            bucket_expr = "SUBSTR(timestamp, 1, 16)"
        elif window == "7d":
            delta = timedelta(days=7)
            bucket_expr = "SUBSTR(timestamp, 1, 10)"
        else:  # 24h
            delta = timedelta(hours=24)
            bucket_expr = "SUBSTR(timestamp, 1, 13)"

        start_dt = max_dt - delta
        start_ts = start_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        end_ts = max_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        history_query = f"""
        SELECT
            {bucket_expr} AS time_bucket,
            AVG(temperature) AS avg_temperature,
            AVG(pressure) AS avg_pressure,
            AVG(power_consumption) AS avg_power_consumption,
            AVG(vibration) AS avg_vibration,
            AVG(degradation_level) AS avg_degradation_level,
            AVG(cycle_efficiency) AS avg_cycle_efficiency,
            SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_count
        FROM telemetry_curated
        WHERE machine_id = '{machine_id}' AND timestamp >= '{start_ts}' AND timestamp <= '{end_ts}'
        GROUP BY {bucket_expr}
        ORDER BY time_bucket ASC;
        """
        history_rows = await self.athena.execute_query(history_query)

        history = []
        for hr in history_rows:
            bucket = hr.get("time_bucket") or ""
            if window in ("15m", "1h"):
                label = bucket.split(" ")[-1] if " " in bucket else bucket.split("T")[-1] if "T" in bucket else bucket
            elif window == "24h":
                lbl = bucket.split(" ")[-1] if " " in bucket else bucket.split("T")[-1] if "T" in bucket else bucket
                label = f"{lbl}:00" if ":" not in lbl else lbl
            else:
                label = "-".join(bucket.split("-")[1:]) if "-" in bucket else bucket

            history.append({
                "timestamp": label if ":" in label or "-" in label else bucket,
                "temperature": float(hr.get("avg_temperature")) if hr.get("avg_temperature") else None,
                "degradation_level": float(hr.get("avg_degradation_level") or 0.0),
                "anomaly_detected": int(hr.get("anomaly_count") or 0) > 0,
                "status": "anomaly" if int(hr.get("anomaly_count") or 0) > 0 else "healthy",
                "pressure": float(hr.get("avg_pressure")) if hr.get("avg_pressure") else None,
                "power_consumption": float(hr.get("avg_power_consumption")) if hr.get("avg_power_consumption") else None,
                "vibration": float(hr.get("avg_vibration")) if hr.get("avg_vibration") else None,
                "cycle_efficiency": float(hr.get("avg_cycle_efficiency")) if hr.get("avg_cycle_efficiency") else None,
            })

        # Fallback if empty
        if not history:
            fallback_query = f"""
            SELECT timestamp, temperature, degradation_level, anomaly_detected, status,
                   pressure, power_consumption, vibration, cycle_efficiency
            FROM telemetry_curated
            WHERE machine_id = '{machine_id}'
            ORDER BY timestamp DESC
            LIMIT 20;
            """
            fallback_rows = await self.athena.execute_query(fallback_query)
            for fr in fallback_rows:
                history.append({
                    "timestamp": fr.get("timestamp"),
                    "temperature": float(fr.get("temperature")) if fr.get("temperature") else None,
                    "degradation_level": float(fr.get("degradation_level") or 0.0),
                    "anomaly_detected": str(fr.get("anomaly_detected")).lower() == "true",
                    "status": fr.get("status") or "unknown",
                    "pressure": float(fr.get("pressure")) if fr.get("pressure") else None,
                    "power_consumption": float(fr.get("power_consumption")) if fr.get("power_consumption") else None,
                    "vibration": float(fr.get("vibration")) if fr.get("vibration") else None,
                    "cycle_efficiency": float(fr.get("cycle_efficiency")) if fr.get("cycle_efficiency") else None,
                })

        # 4. Compute Predictive Maintenance stats
        failure_risk = round(deg * 100.0, 1)
        rul = round(max(1.0, (1.0 - deg) * 150.0), 1)
        if deg >= 0.8:
            rec = "Schedule emergency inspection immediately (critical risk)."
            trend = "Critical"
        elif deg >= 0.4:
            rec = "Plan preventive maintenance inspection within 7 days."
            trend = "Degrading"
        else:
            rec = "Continue regular operations. Schedule routine maintenance in 30 days."
            trend = "Stable"

        predictive_maintenance = {
            "failure_risk_pct": failure_risk,
            "maintenance_recommendation": rec,
            "remaining_useful_life_days": rul,
            "health_trend": trend
        }

        # 5. Live operating conditions
        current_conditions = {
            "temperature": float(latest.get("temperature")) if latest.get("temperature") else None,
            "pressure": float(latest.get("pressure")) if latest.get("pressure") else None,
            "power_consumption": float(latest.get("power_consumption")) if latest.get("power_consumption") else None,
            "vibration": float(latest.get("vibration")) if latest.get("vibration") else None,
            "degradation": float(latest.get("degradation_level") or 0.0)
        }

        # 6. Active anomaly details
        active_anomaly = None
        is_anomaly = str(latest.get("anomaly_detected")).lower() == "true"
        if is_anomaly or status in ("warning", "critical"):
            anom_type = latest.get("anomaly_type") or "unknown_sensor_anomaly"
            prob = anom_type.replace("_", " ").title()
            conf = float(latest.get("diagnostic_confidence") or 0.85)

            # Build causes
            candidates_str = latest.get("root_cause_candidates")
            if candidates_str and candidates_str != "NULL" and candidates_str != "":
                causes = [c.strip() for c in candidates_str.split(",") if c.strip()]
            else:
                if "overheating" in anom_type:
                    causes = ["Cooling fan degradation", "Excessive mechanical load", "Bearing friction increase", "Ventilation obstruction"]
                elif "pressure" in anom_type:
                    causes = ["Hydraulic line leak", "Pump impeller damage", "Relief valve failure", "Sensor calibration drift"]
                elif "vibration" in anom_type:
                    causes = ["Spindle misalignment", "Loose mounting bolts", "Internal bearing wear", "Load imbalance"]
                elif "tool_wear" in anom_type:
                    causes = ["Spindle speed mismatch", "Sub-optimal feed rate", "Insufficient cooling fluid"]
                else:
                    causes = ["General mechanical fatigue", "Sensor calibration drift", "Electrical signal interference"]

            # Build operational impact
            if "overheating" in anom_type:
                impact = "Reduced efficiency, high risk of motor burnout and automatic thermal shutdown."
            elif "pressure" in anom_type:
                impact = "Loss of hydraulic force, degradation of cycle speed, and potential pressure safety release."
            elif "vibration" in anom_type:
                impact = "Accelerated component wear, noise level spikes, structural fatigue, and precision loss."
            elif "tool_wear" in anom_type:
                impact = "Surface roughness defects, dimensional inaccuracies, and high risk of tool breakage."
            else:
                impact = "Reduced efficiency and potential shutdown risk."

            # Recommended action
            actions_str = latest.get("recommended_actions") or ""
            if actions_str and actions_str != "NULL" and actions_str != "":
                rec_act = actions_str.split(",")[0].strip()
            else:
                rec_act = "Inspect cooling assembly and check sensor calibration within 24 hours."

            active_anomaly = {
                "problem": prob,
                "confidence": conf,
                "possible_causes": causes,
                "operational_impact": impact,
                "recommended_action": rec_act
            }

        # 7. Root Cause Analysis Ranked List
        CAUSE_EXPLANATIONS = {
            "Cooling Fan Failure": "Friction or electrical decay in the exhaust fan winding, reducing airflow.",
            "Bearing Wear": "Pitting or lubrication starvation in the rotational bearings, increasing mechanical load.",
            "Misalignment": "Slight structural shift or loose base mounting bolts, causing laser-axis deviation.",
            "Sensor Drift": "Calibration decay in the thermocouple or transducer, reporting out-of-bounds telemetry.",
            "Hydraulic Line Fluid Leakage": "Fluid loss due to seals decay or micro-fissures in hydraulic hoses.",
            "Main Pump Cavitation": "Air bubbles trapped in the pump cylinder, causing vibration and pressure spikes.",
            "Drive Belt Slippage": "Belt wear or tension decay, leading to rotational speed fluctuations.",
            "Worn Gripper Pads": "Gripper rubber degradation leading to part slippage and alignment accuracy drops.",
            "Sub-optimal Feed/Speed Ratio": "Feed rate set too high relative to spindle RPM, overloading the cutting bit.",
            "Cooling System Degradation": "Reduced heat-exchanger efficiency due to low coolant flow or fan friction.",
            "Blocked Vents / Airflow Path": "Debris buildup in the machine casing blocks optimal thermal dissipation.",
            "Mechanical Bearing Friction": "Increased resistance on the active shaft due to grease degradation.",
        }

        root_cause_analysis = []
        candidates_str = latest.get("root_cause_candidates")
        if candidates_str and candidates_str != "NULL" and candidates_str != "":
            parsed_candidates = [c.strip() for c in candidates_str.split(",") if c.strip()]
            for pc in parsed_candidates:
                # e.g. "Cooling Fan Failure (92%)"
                if "(" in pc:
                    parts = pc.split("(")
                    cause_name = parts[0].strip()
                    try:
                        conf_val = float(parts[1].replace(")", "").replace("%", "").strip()) / 100.0
                    except ValueError:
                        conf_val = 0.5
                else:
                    cause_name = pc
                    conf_val = 0.5
                
                explanation = CAUSE_EXPLANATIONS.get(cause_name, "Correlated sensor readings indicate potential component fatigue.")
                root_cause_analysis.append({
                    "cause": cause_name,
                    "confidence": conf_val,
                    "explanation": explanation
                })
        else:
            # Fallback typical root causes based on machine status/type
            mtype = v.get("machine_type") or "unknown"
            if "hydraulic" in mtype or "cooling" in mtype:
                defaults = [("Cooling Fan Failure", 0.12), ("Bearing Wear", 0.08), ("Sensor Drift", 0.05)]
            elif "cnc" in mtype or "welding" in mtype:
                defaults = [("Sub-optimal Feed/Speed Ratio", 0.15), ("Bearing Wear", 0.07), ("Sensor Drift", 0.04)]
            else:
                defaults = [("Mechanical Bearing Friction", 0.10), ("Sensor Drift", 0.06)]
            
            for cause_name, conf_val in defaults:
                explanation = CAUSE_EXPLANATIONS.get(cause_name, "Nominal operational checks indicate low structural risk.")
                root_cause_analysis.append({
                    "cause": cause_name,
                    "confidence": conf_val,
                    "explanation": explanation
                })

        # 8. Chronological Risk Timeline
        timeline_query = f"""
        SELECT timestamp, anomaly_type, anomaly_severity, status, anomaly_reason
        FROM telemetry_curated
        WHERE machine_id = '{machine_id}' AND anomaly_detected = true
        ORDER BY timestamp DESC
        LIMIT 10;
        """
        timeline_rows = await self.athena.execute_query(timeline_query)
        risk_timeline = []
        for tr in timeline_rows:
            severity = float(tr.get("anomaly_severity") or 0.5)
            if severity >= 0.8:
                ev_type = "critical"
            elif severity >= 0.4:
                ev_type = "warning"
            else:
                ev_type = "anomaly"

            risk_timeline.append({
                "timestamp": tr.get("timestamp"),
                "event_type": ev_type,
                "description": tr.get("anomaly_reason") or f"Detected {tr.get('anomaly_type') or 'anomaly'} in operating parameters.",
                "severity": severity
            })

        # If risk timeline is empty and machine has warning/critical, add a default record
        if not risk_timeline and status != "healthy":
            risk_timeline.append({
                "timestamp": latest.get("timestamp") or max_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "event_type": status,
                "description": f"Machine transitioned to {status} health state due to elevated degradation levels.",
                "severity": 0.5 if status == "warning" else 0.8
            })

        analytics = {
            "machine_id": machine_id,
            "machine_type": v.get("machine_type"),
            "total_events": int(v.get("total_events") or 0),
            "anomaly_events": int(v.get("anomaly_events") or 0),
            "anomaly_rate_percent": anom_rate,
            "avg_temperature": float(v.get("avg_temperature") or 0.0) if v.get("avg_temperature") else None,
            "max_degradation_level": deg,
            "health_status": status,
            "history": history,
            "health_score": health_score,
            "last_updated": latest.get("timestamp") or max_dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "current_conditions": current_conditions,
            "predictive_maintenance": predictive_maintenance,
            "active_anomaly": active_anomaly,
            "root_cause_analysis": root_cause_analysis,
            "risk_timeline": risk_timeline
        }
        return analytics

    @with_cache("aggregated_analytics", ttl=60.0)
    async def get_aggregated_analytics(self) -> Dict[str, Any]:
        """
        Fetch daily aggregates and anomaly distributions.
        """

        # 1. Fetch daily factory summaries
        daily_query = "SELECT * FROM daily_factory_summary_view ORDER BY year DESC, month DESC, day DESC;"
        daily_rows = await self.athena.execute_query(daily_query)
        daily_summaries = []

        for dr in daily_rows:
            daily_summaries.append({
                "date": f"{dr.get('year')}-{int(dr.get('month') or 1):02d}-{int(dr.get('day') or 1):02d}",
                "total_events": int(dr.get("total_events") or 0),
                "active_machines": int(dr.get("active_machines") or 0),
                "total_anomalies": int(dr.get("total_anomalies") or 0),
                "avg_degradation_level": float(dr.get("avg_degradation_level") or 0.0),
            })

        # 2. Fetch anomaly types summary
        anomaly_query = "SELECT * FROM anomaly_summary_view ORDER BY anomaly_count DESC;"
        anomaly_rows = await self.athena.execute_query(anomaly_query)
        anomaly_distribution = []

        for ar in anomaly_rows:
            anomaly_distribution.append({
                "anomaly_type": ar.get("anomaly_type") or "unknown",
                "machine_type": ar.get("machine_type") or "unknown",
                "anomaly_count": int(ar.get("anomaly_count") or 0),
                "avg_anomaly_severity": float(ar.get("avg_anomaly_severity") or 0.0),
            })

        aggregated = {
            "daily_summaries": daily_summaries,
            "anomaly_distribution": anomaly_distribution,
        }
        return aggregated

    @with_cache("diagnostics_limit_{limit}_machine_{machine_id}", ttl=60.0)
    async def get_diagnostics(self, limit: int = 50, machine_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query industrial diagnostics logs from Athena.
        """

        filter_clause = ""
        if machine_id:
            filter_clause = f"AND machine_id = '{machine_id}'"

        query = f"""
        SELECT event_id, machine_id, machine_type, timestamp, anomaly_type,
               anomaly_severity, temperature, spindle_speed, tool_wear, vibration,
               rpm, power_consumption, hydraulic_pressure, cycle_time, joint_load,
               movement_delay, motor_temperature, positional_accuracy, energy_output,
               coolant_flow_rate, pressure, arc_stability, energy_usage, task_completion_rate,
               alignment_accuracy, cycle_efficiency, anomaly_reason, trigger_metric,
               trigger_value, expected_range, root_cause_candidates, recommended_actions,
               diagnostic_confidence
        FROM telemetry_curated
        WHERE anomaly_detected = true {filter_clause}
        ORDER BY timestamp DESC
        LIMIT {limit};
        """
        rows = await self.athena.execute_query(query)
        diagnostics = []

        for r in rows:
            record = self._parse_diagnostic_row(r)
            diagnostics.append(record)
        return diagnostics

    @with_cache("root_causes_distribution", ttl=60.0)
    async def get_root_causes(self) -> List[Dict[str, Any]]:
        """
        Query fleet-wide root causes aggregates.
        """

        query = """
        SELECT root_cause_candidates, diagnostic_confidence, anomaly_type,
               temperature, motor_temperature, vibration, pressure, hydraulic_pressure,
               coolant_flow_rate, rpm, spindle_speed, power_consumption, energy_usage
        FROM telemetry_curated
        WHERE anomaly_detected = true
        LIMIT 500;
        """
        rows = await self.athena.execute_query(query)
        distribution: Dict[str, Dict[str, Any]] = {}

        for r in rows:
            candidates_str = r.get("root_cause_candidates")
            if not candidates_str or candidates_str == "NULL":
                parsed = self._parse_diagnostic_row(r)
                candidates = parsed["probable_causes"]
                conf = parsed["confidence"]
            else:
                candidates = [c.strip() for c in candidates_str.split(",") if c.strip()]
                conf = float(r.get("diagnostic_confidence") or 0.6)

            for c in candidates:
                parts = c.split("(")
                name = parts[0].strip()
                
                if name not in distribution:
                    distribution[name] = {"cause": name, "count": 0, "sum_conf": 0.0}
                distribution[name]["count"] += 1
                distribution[name]["sum_conf"] += conf

        results = []
        for name, data in distribution.items():
            results.append({
                "cause": name,
                "count": data["count"],
                "avg_confidence": round(data["sum_conf"] / data["count"], 2) if data["count"] > 0 else 0.0
            })

        results.sort(key=lambda x: x["count"], reverse=True)
        return results

    def _parse_diagnostic_row(self, r: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to parse a single database record into a DiagnosticRecord."""
        anomaly_reason = r.get("anomaly_reason")
        anomaly_type = r.get("anomaly_type") or "unknown"
        
        telemetry = {}
        for k in ["temperature", "motor_temperature", "vibration", "pressure", "hydraulic_pressure", 
                  "coolant_flow_rate", "rpm", "spindle_speed", "power_consumption", "energy_usage",
                  "tool_wear", "movement_delay", "arc_stability", "alignment_accuracy", "cycle_efficiency",
                  "task_completion_rate"]:
            val = r.get(k)
            if val is not None and val != "NULL" and val != "":
                telemetry[k] = float(val)

        # Fallback diagnostics dynamically if NULL in database
        if not anomaly_reason or anomaly_reason == "NULL":
            from backend.services.diagnostics_engine import diagnose_telemetry
            mock_payload = {
                "anomaly_detected": True,
                "anomaly_type": anomaly_type,
                "telemetry": telemetry
            }
            try:
                enriched = diagnose_telemetry(mock_payload)
                r = {**r, **enriched}
            except Exception as e:
                logger.error(f"[ANALYTICS] Fallback diagnostics failure: {e}")

        candidates_str = r.get("root_cause_candidates") or ""
        if candidates_str == "NULL":
            candidates_str = ""
        candidates = [c.strip() for c in candidates_str.split(",") if c.strip()]
        
        actions_str = r.get("recommended_actions") or ""
        if actions_str == "NULL":
            actions_str = ""
        # Clean actions list
        actions = []
        for a in actions_str.split(","):
            cleaned = a.strip()
            # Strip numbering prefix if present (e.g. "1. Inspect ...")
            if cleaned and cleaned[0].isdigit() and (cleaned[1:3] == ". " or cleaned[1] == "."):
                cleaned = cleaned.split(".", 1)[1].strip()
            if cleaned:
                actions.append(cleaned)

        trigger_val = r.get("trigger_value")
        if trigger_val is not None and trigger_val != "NULL" and trigger_val != "":
            try:
                trigger_val = float(trigger_val)
            except ValueError:
                trigger_val = 0.0
        else:
            trigger_val = 0.0

        trigger_metric = r.get("trigger_metric") or "sensor"
        expected_range = r.get("expected_range") or "N/A"
        evidence = f"{trigger_metric.replace('_', ' ').title()} = {trigger_val:.1f} (expected: {expected_range})"

        return {
            "event_id": r.get("event_id"),
            "machine_id": r.get("machine_id"),
            "machine_type": r.get("machine_type"),
            "timestamp": r.get("timestamp"),
            "anomaly_type": anomaly_type,
            "explanation": r.get("anomaly_reason") or "Anomaly detected in machine parameters.",
            "evidence": evidence,
            "probable_causes": candidates,
            "recommendations": actions,
            "confidence": float(r.get("diagnostic_confidence") or 0.60),
        }

    # -------------------------------------------------------------------------
    # Phase 10.5 — New Analytics Center Methods
    # -------------------------------------------------------------------------

    @with_cache("hourly_trends", ttl=30.0)
    async def get_hourly_trends(self) -> List[Dict[str, Any]]:
        """
        Query telemetry_curated and aggregate by hour bucket using SUBSTR on ISO timestamp.
        Falls back to day-level if insufficient hourly buckets exist.
        Provides the time-series data needed for the 'Are Anomalies Increasing?' chart.
        """

        # Extract hour bucket: timestamp is ISO string '2026-06-04T14:32:00Z' → '2026-06-04 14'
        hourly_query = """
        SELECT
            SUBSTR(timestamp, 1, 13) AS hour_bucket,
            COUNT(*) AS total_events,
            SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_count,
            SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) AS healthy_count,
            SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) AS warning_count,
            SUM(CASE WHEN status IN ('critical', 'anomaly') THEN 1 ELSE 0 END) AS critical_count
        FROM telemetry_curated
        GROUP BY SUBSTR(timestamp, 1, 13)
        ORDER BY hour_bucket ASC
        LIMIT 168;
        """
        rows = await self.athena.execute_query(hourly_query)
        results = []

        for r in rows:
            bucket = r.get("hour_bucket") or ""
            total = int(r.get("total_events") or 0)
            anomalies = int(r.get("anomaly_count") or 0)
            rate = round((anomalies / total * 100.0), 2) if total > 0 else 0.0
            # Normalize label: '2026-06-04T14' → '2026-06-04 14:00'
            label = bucket.replace("T", " ") + ":00" if "T" in bucket else bucket + ":00"
            results.append({
                "time_label": label,
                "total_events": total,
                "anomaly_count": anomalies,
                "anomaly_rate_pct": rate,
                "healthy_count": int(r.get("healthy_count") or 0),
                "warning_count": int(r.get("warning_count") or 0),
                "critical_count": int(r.get("critical_count") or 0),
            })

        # If we only have 1 hourly bucket, fall back to minute-level for intra-day resolution
        if len(results) <= 1:
            logger.info("[ANALYTICS] Insufficient hourly buckets, falling back to minute-level")
            minute_query = """
            SELECT
                SUBSTR(timestamp, 1, 16) AS minute_bucket,
                COUNT(*) AS total_events,
                SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_count,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) AS healthy_count,
                SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) AS warning_count,
                SUM(CASE WHEN status IN ('critical', 'anomaly') THEN 1 ELSE 0 END) AS critical_count
            FROM telemetry_curated
            GROUP BY SUBSTR(timestamp, 1, 16)
            ORDER BY minute_bucket ASC
            LIMIT 120;
            """
            rows = await self.athena.execute_query(minute_query)
            results = []
            for r in rows:
                bucket = r.get("minute_bucket") or ""
                total = int(r.get("total_events") or 0)
                anomalies = int(r.get("anomaly_count") or 0)
                rate = round((anomalies / total * 100.0), 2) if total > 0 else 0.0
                label = bucket.replace("T", " ") if "T" in bucket else bucket
                results.append({
                    "time_label": label,
                    "total_events": total,
                    "anomaly_count": anomalies,
                    "anomaly_rate_pct": rate,
                    "healthy_count": int(r.get("healthy_count") or 0),
                    "warning_count": int(r.get("warning_count") or 0),
                    "critical_count": int(r.get("critical_count") or 0),
                })
        return results

    @with_cache("energy_profile", ttl=60.0)
    async def get_energy_profile(self) -> List[Dict[str, Any]]:
        """
        Query real energy consumption data from Athena by machine type.
        Replaces the hardcoded energy data that was previously in the frontend.
        """

        query = """
        SELECT
            machine_type,
            SUM(COALESCE(power_consumption, 0.0) + COALESCE(energy_usage, 0.0) + COALESCE(energy_output, 0.0)) AS total_energy,
            AVG(COALESCE(power_consumption, 0.0) + COALESCE(energy_usage, 0.0)) AS avg_power,
            COUNT(*) AS event_count
        FROM telemetry_curated
        GROUP BY machine_type
        ORDER BY total_energy DESC;
        """
        rows = await self.athena.execute_query(query)
        results = []

        for r in rows:
            machine_type = r.get("machine_type") or "unknown"
            total_energy = float(r.get("total_energy") or 0.0)
            avg_power = float(r.get("avg_power") or 0.0)
            event_count = int(r.get("event_count") or 0)
            results.append({
                "machine_type": machine_type,
                "total_energy": round(total_energy, 2),
                "avg_power": round(avg_power, 2),
                "event_count": event_count,
            })
        return results

    @with_cache("business_kpis", ttl=30.0)
    async def get_business_kpis(self) -> Dict[str, Any]:
        """
        Derive executive-grade KPIs from existing machine health data.
        Computes: Factory Health Score, Production Efficiency, Anomaly Rate,
        Production Risk Score, Most Affected Machine, and Energy Leader.
        No new Athena queries needed — reuses cached machine + energy data.
        """

        import asyncio
        machines, energy_profile = await asyncio.gather(
            self.get_machines(),
            self.get_energy_profile(),
        )

        total = len(machines)
        if total == 0:
            empty = {
                "factory_health_score": 0.0,
                "production_efficiency_score": 0.0,
                "overall_anomaly_rate_pct": 0.0,
                "production_risk_score": 0.0,
                "most_affected_machine_id": None,
                "most_affected_machine_type": None,
                "most_affected_anomaly_rate": 0.0,
                "energy_leader_type": None,
                "energy_leader_value": 0.0,
                "total_machines": 0,
                "healthy_count": 0,
                "warning_count": 0,
                "critical_count": 0,
            }
            return empty

        healthy_count = sum(1 for m in machines if m["health_status"] == "healthy")
        warning_count = sum(1 for m in machines if m["health_status"] == "warning")
        critical_count = sum(1 for m in machines if m["health_status"] == "critical")

        # Factory Health Score: healthy=100%, warning=50%, critical=0%
        factory_health_score = round(
            ((healthy_count * 1.0 + warning_count * 0.5) / total) * 100.0, 1
        )

        # Fleet-wide anomaly rate
        total_events_sum = sum(m["total_events"] for m in machines)
        total_anomalies_sum = sum(m["anomaly_events"] for m in machines)
        overall_anomaly_rate = round(
            (total_anomalies_sum / total_events_sum * 100.0) if total_events_sum > 0 else 0.0, 2
        )

        # Production Efficiency: inverse of degradation penalty + anomaly rate penalty
        avg_degradation = sum(m["max_degradation_level"] for m in machines) / total
        production_efficiency = round(
            max(0.0, 100.0 - (avg_degradation * 60.0) - (overall_anomaly_rate * 0.5)), 1
        )

        # Production Risk: weighted by critical machines + high anomaly rate
        production_risk = round(
            min(100.0, (critical_count / total * 60.0) + (overall_anomaly_rate * 1.5) + (avg_degradation * 25.0)), 1
        )

        # Most affected machine
        most_affected = max(machines, key=lambda m: m["anomaly_rate_percent"]) if machines else None

        # Energy leader
        energy_leader_type = energy_profile[0]["machine_type"] if energy_profile else None
        energy_leader_value = energy_profile[0]["total_energy"] if energy_profile else 0.0

        kpis = {
            "factory_health_score": factory_health_score,
            "production_efficiency_score": production_efficiency,
            "overall_anomaly_rate_pct": overall_anomaly_rate,
            "production_risk_score": production_risk,
            "most_affected_machine_id": most_affected["machine_id"] if most_affected else None,
            "most_affected_machine_type": most_affected["machine_type"] if most_affected else None,
            "most_affected_anomaly_rate": round(most_affected["anomaly_rate_percent"], 1) if most_affected else 0.0,
            "energy_leader_type": energy_leader_type,
            "energy_leader_value": round(energy_leader_value, 0),
            "total_machines": total,
            "healthy_count": healthy_count,
            "warning_count": warning_count,
            "critical_count": critical_count,
        }
        return kpis

    @with_cache("recommendations", ttl=60.0)
    async def get_recommendations(self) -> List[Dict[str, Any]]:
        """
        Generate rule-based operational recommendations by scanning machine health data.
        No machine learning — purely threshold-driven rules.
        Priority: critical > warning > info.
        """

        machines = await self.get_machines()
        recommendations: List[Dict[str, Any]] = []

        for m in machines:
            mid = m["machine_id"]
            mtype = m["machine_type"].replace("_", " ").title()
            anom_rate = m["anomaly_rate_percent"]
            deg = m["max_degradation_level"]
            status = m["health_status"]
            temp = m.get("avg_temperature")

            # RULE 1: Critical machines require immediate intervention
            if status == "critical":
                recommendations.append({
                    "priority": "critical",
                    "machine_id": mid,
                    "machine_type": mtype,
                    "recommendation": f"Immediately inspect {mid} — machine is in CRITICAL state and requires urgent maintenance.",
                    "reason": f"Machine {mid} ({mtype}) has crossed critical operational thresholds.",
                    "metric_value": anom_rate,
                    "metric_name": "anomaly_rate_percent",
                })

            # RULE 2: Very high anomaly rate (>20%)
            elif anom_rate > 20.0:
                recommendations.append({
                    "priority": "critical",
                    "machine_id": mid,
                    "machine_type": mtype,
                    "recommendation": f"Schedule emergency inspection of {mid}. Anomaly rate of {anom_rate:.1f}% exceeds safe operating threshold.",
                    "reason": f"More than 1 in 5 telemetry events from {mid} are anomalous.",
                    "metric_value": anom_rate,
                    "metric_name": "anomaly_rate_percent",
                })

            # RULE 3: High degradation level (>0.7)
            elif deg > 0.7:
                recommendations.append({
                    "priority": "warning",
                    "machine_id": mid,
                    "machine_type": mtype,
                    "recommendation": f"Plan preventive maintenance for {mid}. Degradation level at {deg:.0%} indicates component wear.",
                    "reason": f"{mid} has a high degradation score of {deg:.2f}/1.0 — approaching end-of-cycle threshold.",
                    "metric_value": deg,
                    "metric_name": "degradation_level",
                })

            # RULE 4: Elevated anomaly rate (10-20%)
            elif anom_rate > 10.0:
                recommendations.append({
                    "priority": "warning",
                    "machine_id": mid,
                    "machine_type": mtype,
                    "recommendation": f"Monitor {mid} closely. Anomaly rate of {anom_rate:.1f}% is elevated.",
                    "reason": f"{mid} ({mtype}) shows recurring anomaly patterns suggesting early-stage degradation.",
                    "metric_value": anom_rate,
                    "metric_name": "anomaly_rate_percent",
                })

            # RULE 5: Temperature warning (if avg_temperature available)
            if temp is not None and temp > 80.0:
                recommendations.append({
                    "priority": "warning",
                    "machine_id": mid,
                    "machine_type": mtype,
                    "recommendation": f"Check cooling system of {mid}. Average temperature of {temp:.1f}°C is above safe operating limit.",
                    "reason": "Sustained high temperature accelerates bearing wear and can cause motor burnout.",
                    "metric_value": temp,
                    "metric_name": "avg_temperature",
                })

        # RULE 6: Fleet-level recommendations if many machines are in warning
        warning_machines = [m for m in machines if m["health_status"] == "warning"]
        if len(warning_machines) >= 3:
            types = list({m["machine_type"].replace("_", " ").title() for m in warning_machines})[:3]
            recommendations.append({
                "priority": "info",
                "machine_id": None,
                "machine_type": None,
                "recommendation": f"Fleet-wide: {len(warning_machines)} machines are in warning state. Consider scheduling a preventive maintenance window.",
                "reason": f"High proportion of machines in warning status may indicate a systemic issue. Affected types: {', '.join(types)}.",
                "metric_value": float(len(warning_machines)),
                "metric_name": "warning_machine_count",
            })

        # Sort: critical first, then warning, then info
        priority_order = {"critical": 0, "warning": 1, "info": 2}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 3))

        # Cap output to top 10 most important
        recommendations = recommendations[:10]
        return recommendations

    @with_cache("telemetry_activity_{window}", ttl=15.0)
    async def get_telemetry_activity(self, window: str = "24h") -> Dict[str, Any]:
        """
        Retrieve time-series telemetry volume aggregates, KPIs, machine breakdown,
        and pipeline health status based on the selected interval window.
        """

        # 1. Query dynamic time anchor (latest and earliest timestamps in the data lake)
        anchor_query = "SELECT MAX(timestamp) AS max_ts, MIN(timestamp) AS min_ts FROM telemetry_curated;"
        anchor_rows = await self.athena.execute_query(anchor_query)
        
        # Helper to parse timestamps safely
        def parse_athena_ts(ts_val: Any) -> datetime:
            if not ts_val:
                return datetime.utcnow()
            s = str(ts_val).strip()
            s = s.replace("Z", "")
            if "T" in s:
                s = s.replace("T", " ")
            if "." in s:
                s = s.split(".")[0]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt)
                except ValueError:
                    continue
            return datetime.utcnow()

        if anchor_rows and anchor_rows[0].get("max_ts"):
            max_ts_str = anchor_rows[0].get("max_ts")
            min_ts_str = anchor_rows[0].get("min_ts")
            max_dt = parse_athena_ts(max_ts_str)
            min_dt = parse_athena_ts(min_ts_str)
        else:
            max_dt = datetime.utcnow()
            min_dt = max_dt - timedelta(hours=2)
            max_ts_str = max_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            min_ts_str = min_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        span_seconds = max((max_dt - min_dt).total_seconds(), 1.0)

        # 2. Automated suggested window selection
        if span_seconds < 900:  # < 15 minutes
            auto_window = "15m"
        elif span_seconds < 7200:  # < 2 hours
            auto_window = "1h"
        elif span_seconds < 172800:  # < 48 hours
            auto_window = "24h"
        else:
            auto_window = "7d"

        selected_window = window if window in ("15m", "1h", "24h", "7d") else auto_window

        # Determine interval and grouping
        if selected_window == "15m":
            delta = timedelta(minutes=15)
            bucket_expr = "SUBSTR(timestamp, 1, 16)"
            min_per_bucket = 1.0
        elif selected_window == "1h":
            delta = timedelta(hours=1)
            bucket_expr = "SUBSTR(timestamp, 1, 16)"
            min_per_bucket = 1.0
        elif selected_window == "7d":
            delta = timedelta(days=7)
            bucket_expr = "SUBSTR(timestamp, 1, 10)"
            min_per_bucket = 1440.0
        else:  # 24h
            delta = timedelta(hours=24)
            bucket_expr = "SUBSTR(timestamp, 1, 13)"
            min_per_bucket = 60.0

        start_dt = max_dt - delta
        start_ts = start_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        end_ts = max_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

        # Prior period times
        prior_start_dt = start_dt - delta
        prior_start_ts = prior_start_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        prior_end_ts = start_ts

        # 3. Query telemetry activity series
        series_query = f"""
        SELECT
            {bucket_expr} AS time_bucket,
            COUNT(*) AS total_events,
            SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_count,
            SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) AS healthy_count,
            SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) AS warning_count,
            SUM(CASE WHEN status IN ('critical', 'anomaly') THEN 1 ELSE 0 END) AS critical_count
        FROM telemetry_curated
        WHERE timestamp >= '{start_ts}' AND timestamp <= '{end_ts}'
        GROUP BY {bucket_expr}
        ORDER BY time_bucket ASC;
        """
        series_rows = await self.athena.execute_query(series_query)

        # Parse series rows
        series = []
        max_bucket_events = 0
        for r in series_rows:
            bucket = r.get("time_bucket") or ""
            total = int(r.get("total_events") or 0)
            if total > max_bucket_events:
                max_bucket_events = total

            # Label cleanup
            if selected_window in ("15m", "1h"):
                # '2026-06-04 14:32' -> '14:32'
                label = bucket.split(" ")[-1] if " " in bucket else bucket.split("T")[-1] if "T" in bucket else bucket
            elif selected_window == "24h":
                # '2026-06-04 14' -> '14:00'
                lbl = bucket.split(" ")[-1] if " " in bucket else bucket.split("T")[-1] if "T" in bucket else bucket
                label = f"{lbl}:00" if ":" not in lbl else lbl
            else:  # 7d
                # '2026-06-04' -> '06-04'
                label = "-".join(bucket.split("-")[1:]) if "-" in bucket else bucket

            series.append({
                "time_label": label,
                "total_events": total,
                "anomaly_count": int(r.get("anomaly_count") or 0),
                "healthy_count": int(r.get("healthy_count") or 0),
                "warning_count": int(r.get("warning_count") or 0),
                "critical_count": int(r.get("critical_count") or 0),
            })

        # 4. Fetch current period KPIs
        current_kpi_query = f"""
        SELECT
            COUNT(*) AS total_events,
            SUM(CASE WHEN anomaly_detected = true THEN 1 ELSE 0 END) AS anomaly_count
        FROM telemetry_curated
        WHERE timestamp >= '{start_ts}' AND timestamp <= '{end_ts}';
        """
        current_kpis = await self.athena.execute_query(current_kpi_query)
        curr_total = 0
        curr_anomalies = 0
        if current_kpis:
            curr_total = int(current_kpis[0].get("total_events") or 0)
            curr_anomalies = int(current_kpis[0].get("anomaly_count") or 0)

        # 5. Fetch prior period count
        prior_kpi_query = f"""
        SELECT COUNT(*) AS total_events
        FROM telemetry_curated
        WHERE timestamp >= '{prior_start_ts}' AND timestamp < '{prior_end_ts}';
        """
        prior_kpis = await self.athena.execute_query(prior_kpi_query)
        prior_total = 0
        if prior_kpis:
            prior_total = int(prior_kpis[0].get("total_events") or 0)

        # 6. Fetch Machine Type Breakdown
        breakdown_query = f"""
        SELECT
            machine_type,
            COUNT(*) AS event_count
        FROM telemetry_curated
        WHERE timestamp >= '{start_ts}' AND timestamp <= '{end_ts}'
        GROUP BY machine_type
        ORDER BY event_count DESC;
        """
        breakdown_rows = await self.athena.execute_query(breakdown_query)
        machine_breakdown = []
        for br in breakdown_rows:
            m_type = br.get("machine_type") or "unknown"
            evt_count = int(br.get("event_count") or 0)
            pct = round((evt_count / curr_total * 100.0), 1) if curr_total > 0 else 0.0
            machine_breakdown.append({
                "machine_type": m_type.replace("_", " ").title(),
                "event_count": evt_count,
                "percentage": pct
            })

        # 7. Compute KPIs
        # Telemetry Rate: Events per minute in the window
        minutes_duration = delta.total_seconds() / 60.0
        telemetry_rate = round((curr_total / minutes_duration), 1) if minutes_duration > 0 else 0.0
        
        # Peak rate in events/min
        peak_rate = round((max_bucket_events / min_per_bucket), 1)

        # Anomaly rate
        anomaly_rate = round((curr_anomalies / curr_total * 100.0), 1) if curr_total > 0 else 0.0

        # Trend percentage
        if prior_total > 0:
            trend_pct = round(((curr_total - prior_total) / prior_total * 100.0), 1)
        else:
            trend_pct = 0.0

        kpis = {
            "total_events": curr_total,
            "telemetry_rate_per_min": telemetry_rate,
            "peak_rate_per_min": peak_rate,
            "anomaly_rate_pct": anomaly_rate,
            "trend_pct": trend_pct
        }

        # 8. Compute Freshness & Health Status
        # current time in UTC
        now_utc = datetime.utcnow()
        freshness_sec = max((now_utc - max_dt).total_seconds(), 0.0)

        if freshness_sec < 45.0:
            simulator_status = "active"
            kinesis_status = "streaming"
            lambda_status = "processing"
            glue_status = "operational"
            athena_status = "queryable"
        elif freshness_sec < 300.0:
            simulator_status = "idle"
            kinesis_status = "streaming"
            lambda_status = "processing"
            glue_status = "operational"
            athena_status = "queryable"
        else:
            simulator_status = "inactive"
            kinesis_status = "inactive"
            lambda_status = "inactive"
            glue_status = "operational"
            athena_status = "queryable"

        pipeline_health = {
            "simulator": simulator_status,
            "kinesis": kinesis_status,
            "lambda_validator": lambda_status,
            "glue_etl": glue_status,
            "athena_engine": athena_status,
            "freshness_seconds": round(freshness_sec, 1)
        }

        # 9. Dynamic activity insights
        insights = []
        if trend_pct > 5.0:
            insights.append(f"Factory telemetry volume has increased by {trend_pct:.1f}% compared to the previous period.")
        elif trend_pct < -5.0:
            insights.append(f"Factory telemetry volume has decreased by {abs(trend_pct):.1f}% compared to the previous period.")
        else:
            insights.append("Telemetry generation is currently stable compared to the previous period.")

        if curr_total > 0:
            if anomaly_rate > 15.0:
                insights.append(f"Anomalous telemetry is highly elevated at {anomaly_rate:.1f}%. Immediate hardware inspection advised.")
            else:
                insights.append("Anomaly frequency remains stable despite changes in production activity.")

        if machine_breakdown:
            top_active = machine_breakdown[0]
            insights.append(f"Telemetry generation is concentrated in {top_active['machine_type']} systems ({top_active['percentage']:.1f}% share).")

        insights.append("Activity levels indicate normal operational conditions.")

        # 10. Estimated time until full 24h baseline
        progress_pct = min(100.0, round((span_seconds / 86400.0 * 100.0), 1))
        est_remaining_mins = max(0.0, round(((86400.0 - span_seconds) / 60.0), 1)) if span_seconds < 86400.0 else 0.0

        activity_response = {
            "selected_window": selected_window,
            "auto_suggested_window": auto_window,
            "time_span_seconds": round(span_seconds, 1),
            "kpis": kpis,
            "series": series,
            "machine_breakdown": machine_breakdown,
            "pipeline_health": pipeline_health,
            "insights": insights,
            "collection_progress_pct": progress_pct,
            "estimated_time_remaining_minutes": est_remaining_mins
        }
        return activity_response


