from typing import Dict, Type
from simulator.machines.base_machine import BaseMachine
from simulator.machines.conveyor_motor import ConveyorMotor
from simulator.machines.hydraulic_press import HydraulicPress
from simulator.machines.cnc_machine import CNCMachine
from simulator.machines.robotic_arm import RoboticArm
from simulator.machines.turbine import IndustrialTurbine
from simulator.machines.cooling_system import CoolingSystem
from simulator.machines.welding_unit import WeldingUnit
from simulator.machines.assembly_robot import AssemblyRobot

class MachineRegistry:
    """Registry pattern to map machine types to their corresponding classes."""
    
    _registry: Dict[str, Type[BaseMachine]] = {
        "conveyor_motor": ConveyorMotor,
        "hydraulic_press": HydraulicPress,
        "cnc_machine": CNCMachine,
        "robotic_arm": RoboticArm,
        "industrial_turbine": IndustrialTurbine,
        "cooling_system": CoolingSystem,
        "welding_unit": WeldingUnit,
        "assembly_robot": AssemblyRobot
    }

    @classmethod
    def get_machine_class(cls, machine_type: str) -> Type[BaseMachine]:
        if machine_type not in cls._registry:
            raise ValueError(f"Unknown machine type: {machine_type}")
        return cls._registry[machine_type]
