# AutoForge Manufacturing Intelligence Center — Executive Explainability Report

This document serves as a self-contained operational manual for the AutoForge Manufacturing Intelligence Center. It describes every metric, unit, formula, threshold, and diagnostic rule, allowing any user—whether a plant manager, executive, student, or external reviewer—to understand the platform within 5 minutes.

---

## 1. Core KPIs (Key Performance Indicators)

### Factory Health Score
* **What is it?**: A weighted representation of the proportion of machines currently operating within expected normal limits.
* **Unit**: `%` (Percentage of fleet)
* **Formula**:
  $$\text{Factory Health Score} = \frac{\text{Healthy Machines} + (0.5 \times \text{Warning Machines})}{\text{Total Machines}} \times 100$$
* **Health Ranges / Thresholds**:
  * **90.0% – 100.0% (Normal / Stable)**: Excellent operation. No immediate action required.
  * **75.0% – 90.0% (Warning)**: Minor machine distress. Monitor warning assets closely.
  * **Below 75.0% (Critical)**: Immediate intervention required; high chance of escalating fault.
* **Time Context**: Evaluated over the active 24-hour sliding window.

### Production Efficiency
* **What is it?**: A performance rating estimating current factory output capacity by accounting for friction caused by component degradation and problem frequency.
* **Unit**: `%` (Percentage of nominal capacity)
* **Formula**:
  $$\text{Production Efficiency} = 100 - (0.6 \times \text{Average Fleet Degradation \%} + 0.4 \times \text{Overall Problem Rate \%})$$
* **Health Ranges / Thresholds**:
  * **85.0% – 100.0% (Normal)**: High efficiency; nominal throughput achieved.
  * **70.0% – 85.0% (Warning)**: Production friction present; check machines in warning status.
  * **Below 70.0% (Critical)**: Severe throughput loss; potential equipment binding or shutdown.
* **Time Context**: Evaluated over the active 24-hour sliding window.

### Overall Machine Problem Rate
* **What is it?**: The proportion of telemetry events containing out-of-bounds sensor readings.
* **Unit**: `%` (Percentage of total telemetry events)
* **Formula**:
  $$\text{Problem Rate} = \frac{\text{Anomalous Telemetry Events}}{\text{Total Telemetry Events}} \times 100$$
* **Health Ranges / Thresholds**:
  * **Below 5.0% (Normal)**: Optimal; normal telemetry baseline noise.
  * **5.0% – 15.0% (Warning)**: Elevated problems; potential sensor drift or minor fault.
  * **Above 15.0% (Critical)**: Severe machine distress; high risk of line stoppage.
* **Time Context**: Evaluated over the active 24-hour sliding window.

### Production Risk Score
* **What is it?**: A composite risk rating representing the likelihood of an unscheduled line stoppage or safety shutdown in the next 24–48 hours.
* **Unit**: `points` (Scale of 0 to 100)
* **Formula**:
  $$\text{Production Risk Score} = \text{Weighted Index of } (\text{Critical Machine Count}, \text{Average Fleet Degradation}, \text{Most Affected Machine Severity})$$
* **Health Ranges / Thresholds**:
  * **0 – 30 (Normal)**: Low risk; normal operations.
  * **30 – 60 (Warning)**: Moderate risk; schedule preventive inspections.
  * **Above 60 (Critical)**: High risk; prioritize immediate maintenance to avoid failure.
* **Time Context**: Real-time evaluation based on active alerts and recent 24-hour trend.

---

## 2. Sensor Threshold Legends & Units

All sensor telemetry collected from the factory floor is validated against the following physical calibration ranges:

| Sensor Attribute | Unit | Normal Range | Warning Range | Critical Range | Why It Matters |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Temperature** | °C (Celsius) | 20.0 – 70.0 °C | 70.0 – 85.0 °C | Above 85.0 °C | Runaway heating indicates motor winding shorts, cooling system failures, or excessive bearing friction. |
| **Pressure** | bar | 10.0 – 30.0 bar | 30.0 – 40.0 bar | Above 40.0 bar | High pressure risks hose bursts; low pressure signals hydraulic line leaks or pump cavitation. |
| **RPM** | revolutions/minute | 1,000 – 5,000 RPM | 5,000 – 7,000 RPM | Above 7,000 RPM | Exceeding RPM limits causes rotor imbalance and accelerates bearing degradation. |
| **Vibration** | mm/s (Velocity) | Below 2.0 mm/s | 2.0 – 5.0 mm/s | Above 5.0 mm/s | Increased vibration is the primary signature of spindle shaft misalignment or gear tooth binding. |
| **Power Draw** | kW (Kilowatt) | Dependent on load | +15% above nominal | +30% above nominal | High power draw at low RPM indicates electric winding insulation breakdown or binding resistance. |

---

## 3. Machine Problem Explanations (Root Causes)

When sensors report values outside nominal bounds, the AutoForge Rules Engine runs diagnostic checks to identify the root cause of the anomaly. The table below lists these diagnoses, their mechanical meanings, physical symptoms, likely causes, and recommended actions:

### Severe Bearing Wear
* **Meaning**: Mechanical bearings supporting rotating shafts have degraded, increasing friction.
* **Symptoms**: High frequency vibration (exceeding 2.0 mm/s), elevated temperature (above 70 °C), and squealing noises.
* **Likely Causes**: Lubricant depletion, grease contamination by metal flakes/water, or exceeding lifetime operating hours.
* **Recommended Action**: Schedule machine shutdown, check grease quality, and replace worn bearings immediately.

### Spindle Shaft Misalignment
* **Meaning**: The rotation axis of the motor is no longer perfectly aligned with the drive assembly.
* **Symptoms**: Increased directional vibration, loss of workpiece dimensions/tolerances, and casing heat.
* **Likely Causes**: Structural impact, loose mounting bolts, or thermal expansion mismatch.
* **Recommended Action**: Halt high-precision operations, perform laser alignment calibration, and torque mounting bolts.

### Cooling System Failure
* **Meaning**: The fluid cooling loop has lost flow or heat exchange capacity.
* **Symptoms**: Rapid, runaway temperature rise (exceeding 80 °C) under standard load, and coolant pressure drops.
* **Likely Causes**: Pump impeller failure, scale blockage in heat exchangers, or radiator fan motor burnout.
* **Recommended Action**: Reduce motor load immediately, check coolant levels, inspect heat exchangers, and test pump motor.

### Hydraulic Line Leakage
* **Meaning**: Loss of hydraulic fluid pressure due to a physical breach in hoses, seals, or fittings.
* **Symptoms**: Sluggish cylinder/actuator response, hydraulic pressure dropping below 10 bar, and fluid pooling.
* **Likely Causes**: O-ring seal dry-rot, pressure surges exceeding hose ratings, or hose abrasion.
* **Recommended Action**: Depressurize system, identify the leaking hose or fitting, and replace seals/hoses.

### Motor Coil Winding Short
* **Meaning**: Electric coil insulation inside the stator has degraded, causing current to bypass windings.
* **Symptoms**: Sudden power spikes (kW) at low speeds, electrical breakers tripping, and local hot spots.
* **Likely Causes**: Overloading history, moisture ingress, or aging insulation.
* **Recommended Action**: Perform winding insulation resistance test (megger test) and replace motor or stator coils.

### Mechanical Gear Binding
* **Meaning**: Physical interference in gear teeth mesh, causing high mechanical resistance.
* **Symptoms**: Sluggish start-up, elevated power draw (kW), gear casing vibration, and metallic fragments in oil.
* **Likely Causes**: Broken gear teeth, shaft misalignment, or metal debris contamination.
* **Recommended Action**: Drain gear oil, inspect tooth contact pattern, clean casing of metal particles, and verify shaft alignment.

---

## 4. Diagnostic Confidence Interpretations

Every diagnosis is accompanied by a **Diagnostic Confidence Score** (expressed as a percentage). This score represents how strongly the sensor evidence supports the rule-based diagnosis.

* **0% – 40% (Weak Evidence)**:
  * *Meaning*: Only a single sensor is slightly out of bounds. The signature is weak.
  * *Operational Action*: Monitor telemetry. No immediate dispatch required. Perform sensor calibration at next routine check.
* **40% – 70% (Moderate Evidence)**:
  * *Meaning*: Multiple sensors show alignment with failure symptoms.
  * *Operational Action*: Prioritize inspection. Schedule an on-site check within the next 24-48 hours.
* **70% – 100% (Strong Evidence)**:
  * *Meaning*: Telemetry signature matches known failure rules.
  * *Operational Action*: Act immediately. Dispatch maintenance engineers to replace or repair components before failure.

---

## 5. Insight Generation Rules

Insights displayed below charts are narrative summaries automatically generated from active datasets using rule-based templates:

### Trend Chart Insight Rule
* **Rule**: Evaluates the difference in problem rates between the first third and the last third of the active time window.
* **Formula**:
  $$\Delta_{\text{rate}} = \text{Average Rate}_{\text{recent}} - \text{Average Rate}_{\text{early}}$$
* **Template**:
  * If $|\Delta_{\text{rate}}| < 0.5\%$: *"Across the observed period, the factory processed {Total Events} events, detecting {Total Problems} machine problems. The overall machine problem rate has remained stable at {Current Rate}%, indicating steady shop floor conditions."*
  * If $\Delta_{\text{rate}} \ge 0.5\%$: *"Across the observed period, the factory processed {Total Events} events, detecting {Total Problems} machine problems. The machine problem rate has increased by {Delta}% compared to the start of the period. Current rate: {Current Rate}%. Suggests worsening component wear or hydraulic drift. Immediate scheduling of inspection cards is recommended."*
  * If $\Delta_{\text{rate}} \le -0.5\%$: *"Across the observed period, the factory processed {Total Events} events, detecting {Total Problems} machine problems. The machine problem rate has decreased by {Delta}% compared to the start of the period. Current rate: {Current Rate}%. Indicates recent maintenance runs or calibration procedures have successfully stabilized the fleet."*

### Energy Chart Insight Rule
* **Rule**: Aggregates total energy consumption across all machine classes and identifies the top energy consumer.
* **Template**:
  *" {Top Machine Type} machines consumed {Top Energy Value} kWh during the selected period, accounting for approximately {Percentage}% of total factory energy usage. Spindles and hydraulic pumps make up the remaining share. Continuous monitoring of {Top Machine Type} wear could yield the highest cost-reduction opportunities."*

### Root Cause Chart Insight Rule
* **Rule**: Identifies the diagnosed problem with the highest incident count and computes its proportion of total diagnosed cases.
* **Template**:
  *`" {Top Cause} is the leading source of machine distress, accounting for {Count} incidents ({Percentage}% of total diagnosed cases) with {Confidence Class} ({Confidence}% confidence). Prioritizing repair orders for this failure mode will yield the highest drop in production risk."*
