from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timedelta
import random


url = "http://localhost:8086"
token = "my-super-secret-token"
org = "iot_org"
bucket = "energy_data"


# Device configuration
devices = {
    "tv": {"name": "TV", "max_power": 150 / 360},
    "fridge": {"name": "Refrigerator", "max_power": 200 / 360},
    "laptop": {"name": "Laptop", "max_power": 85 / 360},
    "smartphone": {"name": "Smartphone", "max_power": 15 / 360},
    "lights": {"name": "Lights", "max_power": 60 / 360}
}

# Функция для генерации реалистичных данных потребления энергии
def generate_power_data(device_id, device):
    if random.random() > 0.9 and device_id != "fridge":
        return 0
        
    max_power = device["max_power"]
    
    # Device-specific power patterns
    if device_id == "fridge":
        # Fridge cycles between high and low power
        if random.random() > 0.8:
            power = random.uniform(0.1, 0.3) * max_power
        else:
            power = random.uniform(0.7, 1.0) * max_power
    elif device_id == "tv":
        # TV either on at high power or completely off
        if random.random() > 0.3:
            power = random.uniform(0.7, 0.9) * max_power
        else:
            power = 0
    else:
        # Other devices have more random patterns
        power = random.uniform(0.1, 1.0) * max_power
        
    # Round to integer watts
    #power = round(power)
    return power



with InfluxDBClient(url=url, token=token, org=org) as client:
    write_api = client.write_api(write_options=SYNCHRONOUS)
    current_time = datetime(2025, 5, 22, 18)
    last = current_time.hour
    end_time = datetime(2025, 5, 22, 20)
    while current_time < end_time:
        for device_id, device in devices.items():
            # Генерируем значение мощности
            power = generate_power_data(device_id, device)
            data_point = (
                Point("mqtt_consumer")
                .tag("project", "iot_energy_monitoring")
                .tag("topic", f"home/energy/{device_id}/power")
                .field("value", power * 1.11)
                .time(int(current_time.timestamp()), write_precision='s')
            )
            write_api.write(bucket=bucket, org=org, record=data_point)
        if current_time.hour != last:
            print(f"Hour №{current_time.hour}.")
            last = current_time.hour
        current_time += timedelta(minutes=1)