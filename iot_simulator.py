"""
HealthSync — IoT Device Simulator
===================================
Simulates 5 IoT health devices continuously generating realistic sensor data
and pushing readings to the backend API at configurable intervals.

Devices simulated:
  1. Smart Watch Pro       → heart_rate, hrv, steps, calories, stress_level
  2. Blood Pressure Cuff   → systolic_bp, diastolic_bp
  3. Pulse Oximeter        → spo2, heart_rate
  4. Smart Thermometer     → temperature
  5. Sleep Tracker Band    → sleep_hours, hrv

Features:
  - Physiologically realistic data with correlated noise
  - Simulated anomalies / health events (fever, tachycardia, low SpO2)
  - Configurable push interval per device
  - Colored terminal logging
  - Graceful shutdown on Ctrl+C

Requirements:
    pip install requests colorama

Run:
    python iot_simulator.py
"""

import time
import random
import math
import json
import threading
from datetime import datetime
from typing import Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from colorama import Fore, Style, init
    init()
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BACKEND_URL = "http://localhost:5000/api"
PUSH_INTERVAL_SECONDS = 5       # Default interval between readings
ANOMALY_PROBABILITY = 0.05      # 5% chance of generating an anomaly per reading
SIMULATION_DURATION = None      # None = run forever; set to int for seconds

# Device configurations
DEVICES = [
    {
        "id": "dev_001",
        "name": "Smart Watch Pro",
        "type": "smartwatch",
        "color": Fore.GREEN,
        "interval": 5,
        "metrics": ["heart_rate", "hrv", "steps", "calories", "stress_level"],
    },
    {
        "id": "dev_002",
        "name": "Blood Pressure Cuff",
        "type": "blood_pressure",
        "color": Fore.RED,
        "interval": 30,  # BP measured less frequently
        "metrics": ["systolic_bp", "diastolic_bp"],
    },
    {
        "id": "dev_003",
        "name": "Pulse Oximeter",
        "type": "pulse_ox",
        "color": Fore.CYAN,
        "interval": 3,   # Continuous monitoring
        "metrics": ["spo2", "heart_rate"],
    },
    {
        "id": "dev_004",
        "name": "Smart Thermometer",
        "type": "thermometer",
        "color": Fore.YELLOW,
        "interval": 60,  # Measured hourly
        "metrics": ["temperature"],
    },
    {
        "id": "dev_005",
        "name": "Sleep Tracker Band",
        "type": "sleep_band",
        "color": Fore.MAGENTA,
        "interval": 300, # Every 5 minutes during sleep
        "metrics": ["sleep_hours", "hrv"],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# REALISTIC SENSOR DATA GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════
class SensorSimulator:
    """
    Maintains internal state for each metric to simulate continuous,
    physiologically realistic sensor readings with smooth transitions.
    """

    def __init__(self):
        # Internal state (running averages that drift over time)
        self.state = {
            "heart_rate": 72,
            "spo2": 97.5,
            "temperature": 36.6,
            "systolic_bp": 120,
            "diastolic_bp": 78,
            "steps": 0,            # Accumulates throughout the day
            "sleep_hours": 7.0,
            "hrv": 58,
            "stress_level": 40,
            "calories": 0,         # Accumulates throughout the day
            "hydration_glasses": 0,
        }
        self.anomaly_active = False
        self.anomaly_type = None
        self.anomaly_remaining = 0
        self._step_increment = random.randint(50, 200)  # Steps per reading

    def _drift(self, current: float, target: float, noise: float, speed: float = 0.1) -> float:
        """Smooth drift toward a target with random noise."""
        return current + speed * (target - current) + random.gauss(0, noise)

    def _maybe_trigger_anomaly(self):
        """Randomly trigger a health anomaly event."""
        if self.anomaly_active:
            self.anomaly_remaining -= 1
            if self.anomaly_remaining <= 0:
                self.anomaly_active = False
                self.anomaly_type = None
                print(f"  {Fore.GREEN}[ANOMALY RESOLVED] Returning to normal.{Style.RESET_ALL}")
            return

        if random.random() < ANOMALY_PROBABILITY:
            anomalies = [
                ("tachycardia", 4),
                ("bradycardia", 3),
                ("low_spo2", 5),
                ("fever", 6),
                ("high_stress", 8),
                ("high_bp", 4),
            ]
            self.anomaly_type, self.anomaly_remaining = random.choice(anomalies)
            self.anomaly_active = True
            print(f"  {Fore.RED}⚠ [ANOMALY TRIGGERED] {self.anomaly_type} — will last {self.anomaly_remaining} readings{Style.RESET_ALL}")

    def get_reading(self, metric: str) -> Optional[float]:
        """Generate a single realistic reading for the given metric."""
        self._maybe_trigger_anomaly()

        if metric == "heart_rate":
            target = 72
            if self.anomaly_type == "tachycardia":
                target = random.randint(100, 140)
            elif self.anomaly_type == "bradycardia":
                target = random.randint(38, 52)
            self.state["heart_rate"] = self._drift(self.state["heart_rate"], target, 3.0)
            return int(round(self.state["heart_rate"]))

        elif metric == "spo2":
            target = 97.5
            if self.anomaly_type == "low_spo2":
                target = random.uniform(88, 93)
            self.state["spo2"] = self._drift(self.state["spo2"], target, 0.5)
            return round(max(85, min(100, self.state["spo2"])), 1)

        elif metric == "temperature":
            target = 36.6
            if self.anomaly_type == "fever":
                target = random.uniform(38.0, 39.2)
            self.state["temperature"] = self._drift(self.state["temperature"], target, 0.15)
            return round(max(35.0, min(40.0, self.state["temperature"])), 1)

        elif metric == "systolic_bp":
            target = 120
            if self.anomaly_type == "high_bp":
                target = random.randint(145, 165)
            self.state["systolic_bp"] = self._drift(self.state["systolic_bp"], target, 4.0)
            return int(round(max(70, min(200, self.state["systolic_bp"]))))

        elif metric == "diastolic_bp":
            target = 78
            if self.anomaly_type == "high_bp":
                target = random.randint(92, 105)
            self.state["diastolic_bp"] = self._drift(self.state["diastolic_bp"], target, 3.0)
            return int(round(max(40, min(130, self.state["diastolic_bp"]))))

        elif metric == "steps":
            # Steps accumulate throughout the day
            hour = datetime.now().hour
            # More steps during active hours (6am–9pm)
            if 6 <= hour <= 21:
                self.state["steps"] += self._step_increment + random.randint(-30, 50)
            return int(max(0, self.state["steps"]))

        elif metric == "sleep_hours":
            # Sleep hours are measured retrospectively
            return round(random.uniform(5.0, 9.0), 1)

        elif metric == "hrv":
            target = 58
            if self.anomaly_type == "high_stress":
                target = random.randint(20, 35)
            self.state["hrv"] = self._drift(self.state["hrv"], target, 3.0)
            return int(round(max(15, min(100, self.state["hrv"]))))

        elif metric == "stress_level":
            target = 40
            if self.anomaly_type == "high_stress":
                target = random.randint(70, 90)
            self.state["stress_level"] = self._drift(self.state["stress_level"], target, 5.0)
            return round(max(0, min(100, self.state["stress_level"])), 1)

        elif metric == "calories":
            # Calories accumulate based on activity
            self.state["calories"] += random.randint(10, 40)
            return int(self.state["calories"])

        elif metric == "hydration_glasses":
            # Increment randomly throughout the day
            if random.random() < 0.15:  # 15% chance per reading to drink
                self.state["hydration_glasses"] += 1
            return round(self.state["hydration_glasses"], 1)

        return None


# ═══════════════════════════════════════════════════════════════════════════════
# DEVICE THREAD — Each device runs in its own thread
# ═══════════════════════════════════════════════════════════════════════════════
class IoTDevice(threading.Thread):
    """
    Simulates a single IoT health device.
    Runs in a separate thread, generating and pushing data at its configured interval.
    """

    def __init__(self, device_config: dict, simulator: SensorSimulator, stop_event: threading.Event):
        super().__init__(daemon=True)
        self.config = device_config
        self.simulator = simulator
        self.stop_event = stop_event
        self.readings_sent = 0

    def run(self):
        print(f"{self.config['color']}  [START] {self.config['name']} ({self.config['id']}) — interval: {self.config['interval']}s{Style.RESET_ALL}")

        while not self.stop_event.is_set():
            # Generate reading
            payload = {
                "device_id": self.config["id"],
                "timestamp": datetime.now().isoformat(),
            }
            for metric in self.config["metrics"]:
                value = self.simulator.get_reading(metric)
                if value is not None:
                    payload[metric] = value

            self.readings_sent += 1

            # Log the reading
            values_str = " | ".join([f"{k}: {v}" for k, v in payload.items() if k not in ("device_id", "timestamp")])
            print(f"{self.config['color']}  [{self.config['name']}] #{self.readings_sent:04d} → {values_str}{Style.RESET_ALL}")

            # Push to backend
            if REQUESTS_AVAILABLE:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/vitals",
                        json=payload,
                        headers={"Content-Type": "application/json", "Authorization": "Bearer demo_token"},
                        timeout=5,
                    )
                    if response.status_code != 201:
                        print(f"{Fore.RED}    ✗ Push failed: {response.status_code} — {response.text[:100]}{Style.RESET_ALL}")
                except requests.exceptions.ConnectionError:
                    print(f"{Fore.YELLOW}    ⚠ Backend not reachable. Running in simulation-only mode.{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}    ✗ Error: {str(e)[:80]}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}    ⚠ 'requests' not installed. Simulating locally only.{Style.RESET_ALL}")

            # Wait for next interval
            self.stop_event.wait(self.config["interval"])

        print(f"{self.config['color']}  [STOP] {self.config['name']} — Total readings: {self.readings_sent}{Style.RESET_ALL}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — Launch all device simulators
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "=" * 60)
    print(f"  {Fore.CYAN}HealthSync IoT Device Simulator{Style.RESET_ALL}")
    print("=" * 60)
    print(f"  Backend URL:    {BACKEND_URL}")
    print(f"  Anomaly Rate:   {ANOMALY_PROBABILITY * 100}%")
    print(f"  Devices:        {len(DEVICES)}")
    print(f"  Duration:       {'Infinite' if SIMULATION_DURATION is None else f'{SIMULATION_DURATION}s'}")
    print("=" * 60 + "\n")

    if not REQUESTS_AVAILABLE:
        print(f"{Fore.YELLOW}  ⚠ 'requests' library not installed. Data will be simulated but not pushed.{Style.RESET_ALL}")
        print(f"  Install with: pip install requests\n")

    # Shared simulator instance (maintains state continuity across devices)
    simulator = SensorSimulator()
    stop_event = threading.Event()

    # Create and start device threads
    threads = []
    for device_config in DEVICES:
        device = IoTDevice(device_config, simulator, stop_event)
        threads.append(device)
        device.start()

    print(f"\n  {Fore.GREEN}All {len(threads)} devices started. Press Ctrl+C to stop.{Style.RESET_ALL}\n")

    # Run for specified duration or until interrupted
    try:
        if SIMULATION_DURATION:
            stop_event.wait(SIMULATION_DURATION)
        else:
            while not stop_event.is_set():
                stop_event.wait(1)
    except KeyboardInterrupt:
        print(f"\n\n  {Fore.YELLOW}Shutting down...{Style.RESET_ALL}")

    # Signal all threads to stop
    stop_event.set()

    # Wait for threads to finish
    for t in threads:
        t.join(timeout=5)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  {Fore.CYAN}Simulation Complete{Style.RESET_ALL}")
    print(f"{'=' * 60}")
    total_readings = sum(t.readings_sent for t in threads)
    print(f"  Total readings generated: {total_readings}")
    for t in threads:
        print(f"    {t.config['name']:30s} → {t.readings_sent:5d} readings")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
