"""
import time
import datetime
import json
import random
import paho.mqtt.client as mqtt

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

def publish_device_data(device_id, power, stamp, status="on"):
    # Publish power consumption
    power_topic = f"{MQTT_TOPIC_PREFIX}/{device_id}/power"
    power_payload = json.dumps({
        "value": power,
        "unit": "watts",
        "timestamp": stamp
    })
    client.publish(power_topic, power_payload)
    
    # Publish device status
    status_topic = f"{MQTT_TOPIC_PREFIX}/{device_id}/status"
    status_payload = json.dumps({
        "status": status,
        "timestamp": stamp
    })
    client.publish(status_topic, status_payload)
    
    # print(f"Published {device_id}: {power}W, Status: {status}")

try:
    print("IoT Energy Simulator running. Press CTRL+C to exit.")
    
    start = datetime.datetime(2025, 3, 1)

    while start.day != 4:
        for device_id, device in devices.items():
            # Skip random devices sometimes to simulate devices being off
            if random.random() > 0.9 and device_id != "fridge":
                publish_device_data(device_id, 0, start.timestamp(), "off")
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
            power = round(power)
            status = "on" if power > 0 else "off"
            
            publish_device_data(device_id, power, start.timestamp(), status)
        
        # Wait before next update
        start += datetime.timedelta(seconds=5)

    print("Simulator stopped")
    client.loop_stop()
    client.disconnect()
        
except KeyboardInterrupt:
    print("Simulator stopped")
    client.loop_stop()
    client.disconnect()

"""

from datetime import datetime, timedelta
import random
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import json

# InfluxDB connection parameters
url = "http://localhost:8086"
token = "my-super-secret-token"
org = "iot_org"
bucket = "energy_data"         

# Устройства
device_ids = ["tv", "fridge", "laptop", "smartphone", "lights"]

# Типичные диапазоны мощности для устройств (в ваттах)
power_ranges = {
    "tv": (80, 150),
    "fridge": (100, 200),
    "laptop": (40, 90),
    "smartphone": (5, 15),
    "lights": (20, 60)
}

# Функция для генерации реалистичных данных потребления энергии
def generate_power_data(device_id, timestamp):
    min_power, max_power = power_ranges[device_id]
    
    # Добавляем суточные паттерны использования
    hour = timestamp.hour
    
    # Коэффициенты использования в зависимости от времени суток
    usage_factor = 1.0
    
    # Ночное время (меньше использования)
    if 0 <= hour < 6:
        usage_factor = 0.3
    # Утро (высокое использование)
    elif 6 <= hour < 9:
        usage_factor = 1.2
    # День (среднее использование)
    elif 9 <= hour < 17:
        usage_factor = 0.8
    # Вечер (пиковое использование)
    elif 17 <= hour < 23:
        usage_factor = 1.5
    
    # Особые паттерны для разных устройств
    if device_id == "fridge":
        # Холодильник работает постоянно с небольшими колебаниями
        usage_factor = 0.9 + random.random() * 0.2
    elif device_id == "tv":
        # ТВ чаще используется вечером и в выходные
        if timestamp.weekday() >= 5:  # Выходные
            usage_factor *= 1.3

    if timestamp.month == 3:
        usage_factor += 1
    
    # Генерируем значение мощности с учетом коэффициента использования
    power = int(min_power + (max_power - min_power) * random.random() * usage_factor)
    
    return power

# Создаем клиент InfluxDB
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Определяем временной диапазон для генерации данных
end_time = datetime(2025, 4, 21)
start_time = end_time - timedelta(days=30)  # Данные за последние 60 дней

# Интервал между точками данных (в минутах)
interval_minutes = 15

# Генерируем и записываем данные
current_time = start_time
batch_size = 10
points_batch = []

print(f"Начинаем генерацию данных с {start_time} по {end_time}")

# while current_time < end_time:
for device_id in device_ids:
    # Генерируем значение мощности
    power = generate_power_data(device_id, current_time)
    
    # Создаем точку данных для InfluxDB
    point = Point("mqtt_consumer") \
        .tag("device", device_id) \
        .field("value", power) \
        .field("unit", "watts") \
        .time(current_time)
    
    points_batch.append(point)

# Записываем пакет данных, когда он достигает определенного размера
if len(points_batch) >= batch_size:
    write_api.write(bucket=bucket, record=points_batch)
    print(f"Записано {len(points_batch)} точек данных до {current_time}")
    points_batch = []

# Увеличиваем время
current_time += timedelta(minutes=interval_minutes)

# Записываем оставшиеся точки
if points_batch:
    write_api.write(bucket=bucket, record=points_batch)
    print(f"Записано {len(points_batch)} точек данных до {current_time}")

# Закрываем клиент
client.close()

print("Генерация исторических данных завершена!")