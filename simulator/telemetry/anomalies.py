from enum import Enum

class AnomalyType(Enum):
    NONE = "none"
    
    # Conveyor Motor
    OVERHEATING = "overheating"
    UNSTABLE_RPM = "unstable_rpm"
    
    # Hydraulic Press
    PRESSURE_DROP = "pressure_drop"
    # Overheating shared
    
    # CNC Machine
    EXCESSIVE_TOOL_WEAR = "excessive_tool_wear"
    VIBRATION_ANOMALY = "vibration_anomaly"
    
    # Robotic Arm
    MOTOR_OVERHEATING = "motor_overheating"
    MOVEMENT_DELAY_SPIKE = "movement_delay_spike"
    
    # Cooling System
    PRESSURE_FLUCTUATION = "pressure_fluctuation"
    COOLANT_REDUCTION = "coolant_reduction"
    
    # Welding Unit
    UNSTABLE_ARC = "unstable_arc"
    ENERGY_SPIKE = "energy_spike"
    
    # Assembly Robot
    ALIGNMENT_DEGRADATION = "alignment_degradation"
    EFFICIENCY_DROP = "efficiency_drop"
