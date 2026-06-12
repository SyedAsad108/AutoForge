import abc
import random
from typing import Dict, Any, List
from simulator.utils.constants import STATUS_HEALTHY, STATUS_WARNING, STATUS_CRITICAL, STATUS_OFFLINE
from simulator.utils.logger import setup_logger
from simulator.telemetry.anomalies import AnomalyType

logger = setup_logger("BaseMachine")

class BaseMachine(abc.ABC):
    """
    Abstract base class for all industrial machines in the simulator.
    """
    def __init__(self, machine_id: str):
        self.machine_id = machine_id
        self.status = STATUS_HEALTHY
        self.degradation_level = 0.0  # 0.0 to 1.0
        self.current_anomaly = AnomalyType.NONE
        self.anomaly_severity = 0.0 # 0.0 to 1.0

    @property
    @abc.abstractmethod
    def machine_type(self) -> str:
        """Returns the machine type string."""
        pass

    @property
    @abc.abstractmethod
    def possible_anomalies(self) -> List[AnomalyType]:
        """Returns a list of anomalies this machine can experience."""
        pass

    def update_state(self):
        """
        Updates the internal state of the machine.
        Simulates natural degradation and anomaly progression.
        """
        # Baseline simple degradation
        self.degradation_level += 0.001

        # Anomaly progression
        if self.current_anomaly != AnomalyType.NONE:
            self.anomaly_severity += random.uniform(0.01, 0.05)
            self.degradation_level += self.anomaly_severity * 0.005  # Anomaly accelerates degradation
        else:
            # Simple chance to develop an anomaly (1%)
            if random.random() < 0.01:
                if self.possible_anomalies:
                    self.current_anomaly = random.choice(self.possible_anomalies)
                    logger.warning(f"Machine {self.machine_id} ({self.machine_type}) developed anomaly: {self.current_anomaly.value}")

        # Cap values
        self.degradation_level = min(1.0, self.degradation_level)
        self.anomaly_severity = min(1.0, self.anomaly_severity)

        # Update status based on progressive state transitions
        self._evaluate_status()
        
        # Machine specific behavior update
        self._update_telemetry_state()

    def _evaluate_status(self):
        """Evaluates and transitions the machine status."""
        old_status = self.status

        if self.status == STATUS_OFFLINE:
            return

        if self.degradation_level >= 0.80 or self.anomaly_severity >= 0.80:
            self.status = STATUS_CRITICAL
        elif self.degradation_level >= 0.50 or self.anomaly_severity >= 0.50:
            self.status = STATUS_WARNING
        else:
            self.status = STATUS_HEALTHY

        if old_status != self.status:
            logger.info(f"Machine {self.machine_id} transitioned status: {old_status} -> {self.status}")

    @abc.abstractmethod
    def _update_telemetry_state(self):
        """Updates internal telemetry variables based on degradation and anomalies."""
        pass

    @abc.abstractmethod
    def generate_telemetry(self) -> Dict[str, Any]:
        """Generates the current telemetry payload as a dictionary."""
        pass
