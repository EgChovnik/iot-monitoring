import time
import json
import random
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = "home/energy"

# Device configuration
devices = {
    "tv": {"name": "TV", "max_power": 150},
    "fridge": {"name": "Refrigerator", "max_power": 200},
    "laptop": {"name": "Laptop", "max_power": 85},
    "smartphone": {"name": "Smartphone", "max_power": 15},
    "lights": {"name": "Lights", "max_power": 60}
}

# Connect to MQTT broker
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

def publish_device_data(device_id, power, status="on", current_time=time.time()):
    # Publish power consumption
    power_topic = f"{MQTT_TOPIC_PREFIX}/{device_id}/power"
    power_payload = json.dumps({
        "value": power,
        "timestamp": current_time.timestamp() * 1000
    })
    client.publish(power_topic, power_payload)
    
    print(f"Published {device_id}: {power}W, Status: {status}, Time: {current_time}")

try:
    print("IoT Energy Simulator running. Press CTRL+C to exit.")
    
    # Определяем временной диапазон для генерации данных
    end_time = datetime(2025, 5, 21, 23, 54, 0)
    # start_time = end_time - timedelta(days=10)  # Данные за последние 60 дней
    start_time = end_time
    # Интервал между точками данных (в минутах)
    interval_minutes = 15
    # Генерируем и записываем данные
    current_time = start_time

    #while current_time < end_time:
    for device_id, device in devices.items():
        # Skip random devices sometimes to simulate devices being off
        if random.random() > 0.9 and device_id != "fridge":
            publish_device_data(device_id, 0, "off", current_time)
            # Увеличиваем время
            # current_time += timedelta(minutes=interval_minutes)
            continue
            
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
        power = int(round(power))
        status = "on" if power > 0 else "off"

        publish_device_data(device_id, power, status, current_time)
    # Увеличиваем время
    # current_time += timedelta(minutes=interval_minutes)

        
except KeyboardInterrupt:
    print("Simulator stopped")
    client.loop_stop()
    client.disconnect()