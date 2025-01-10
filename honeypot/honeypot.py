import json
import random
import time
from datetime import datetime
from confluent_kafka import Producer

# Beispieldaten für Logs
COUNTRIES = ['Germany', 'China', 'Russia', 'USA', 'Brazil', 'India']
USERNAMES = ['admin', 'root', 'user', 'test', 'oracle', 'mysql', 'postgres', 'example', 'lorem','quark']
PASSWORDS = ['123456', 'password', 'admin', 'root123', 'qwerty', '111111', 'foo', 'bar', 'passwortvergessen', 'i<3bigdataengineering']
IP_RANGES = {
    'Germany': '91.0.0.0/24',
    'China': '114.0.0.0/24',
    'Russia': '95.0.0.0/24',
    'USA': '104.0.0.0/24',
    'Brazil': '177.0.0.0/24',
    'India': '115.0.0.0/24'
}



# Funktion, die zum Land passende IP-Adresse generiert
def generate_ip(network):
    base_ip = network.split('/')[0]
    base_parts = [int(x) for x in base_ip.split('.')]
    return f"{base_parts[0]}.{base_parts[1]}.{base_parts[2]}.{random.randint(0,255)}"

# Funktion, die zufälligen Logeintrag generiert
def generate_log_entry():
    country = random.choice(COUNTRIES)
    current_time = datetime.now()
    
    return {
        "timestamp": int(current_time.timestamp()),  # Unix timestamp aus current_time
        "datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),  # Formatierte Zeit aus current_time
        "ip": generate_ip(IP_RANGES[country]),
        "country": country,
        "username": random.choice(USERNAMES),
        "password": random.choice(PASSWORDS),
        "success": random.random() < 0.01 # Erfolgsquote bei 1 % aller Zugriffe
    }

# Kafka-Producer lokal, noch anpassen!!!!
def kafka_producer():
    conf = {
        'bootstrap.servers': 'kafka-cluster:9092',  # Address of your Kafka broker(s)
        'security.protocol': 'SASL_PLAINTEXT',  # Use SASL over plain text connection
        'sasl.mechanism': 'PLAIN',  # Can also use 'SCRAM-SHA-256' or 'SCRAM-SHA-512'
        'sasl.username': 'user1',  # Your SASL username
        'sasl.password': 'qXRWNkq5gr',  # Your SASL password
        'client.id': 'python-producer',
    }
    return Producer(conf)

# Fehlermeldung
def delivery_callback(err, msg):
    if err:
        print(f'Fehler beim Senden: {err}')
    else:
        print(f'Nachricht erfolgreich gesendet: {msg.topic()} [{msg.partition()}]')

# Hauptfunktion, die Logeinträge generiert und an Kafka sendet


producer = kafka_producer()
topic = "ssh-logs"
counter = 0
try:
    while True:
        try:
            counter +=1
            log_entry = generate_log_entry()
            producer.produce(
                topic,
                key=log_entry['ip'],
                value=json.dumps(log_entry),
                callback=delivery_callback  # Callback für Erfolg/Fehler
            )
            producer.poll(0)  # Triggert Callbacks
            print(f"Sent: {log_entry} counter: {counter}")
            time.sleep(random.uniform(0.1, 2))
            
        except BufferError:
            print("Lokaler Buffer voll - warte kurz")
            producer.flush()
            time.sleep(1)
            
        except Exception as e:
            print(f"Fehler beim Senden: {str(e)}")
            time.sleep(1)  # Kurz warten bei Fehlern
            
except KeyboardInterrupt:
    print("Stopping producer...")

finally:
    if producer:
        producer.flush(timeout=5)  # Warte max 5 Sekunden auf ausstehende Nachrichten
        producer.close()  
