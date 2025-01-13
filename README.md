# ssh_honeypot

# SSH Honeypot Analytics
Laborarbeit im Modul Big Data Engineering

[Demo Video](https://youtu.be/MppFt-uCNeg)

## Setup und Installation

### Voraussetzungen
- Kubernetes Cluster (z.B. via Docker Desktop mit WSL2)
- Helm für Kubernetes Deployment
- Python 3.9+
- Docker Desktop

### Installation Schritt für Schritt

1. **Kubernetes Cluster vorbereiten**
   ```bash
   # Prüfen ob Cluster läuft
   kubectl cluster-info
   ```

2. **Kafka installieren**
   ```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm install kafka bitnami/kafka
   ```

3. **MariaDB aufsetzen**
   - Tabellen erstellen:
   ```sql
   CREATE TABLE login_attempts (
       timestamp BIGINT,
       datetime VARCHAR(255),
       ip VARCHAR(255),
       country VARCHAR(255),
       username VARCHAR(255),
       password VARCHAR(255),
       success BOOLEAN
   );

   CREATE TABLE login_attempts_germany (
       timestamp BIGINT,
       datetime VARCHAR(255),
       ip VARCHAR(255),
       country VARCHAR(255),
       username VARCHAR(255),
       password VARCHAR(255),
       success BOOLEAN
   );
   ```
   - Berechtigungen setzen:
   ```sql
   GRANT ALL PRIVILEGES ON db.* TO 'bde'@'%';
   ```
   - ANSI quotes aktivieren in my.cnf:
   ```ini
   sql_mode=ANSI_QUOTES
   ```

### Wichtige Konfigurationsdetails

#### Honeypot Simulator (honeypot.py)
```python
# Konfigurationsparameter
COUNTRIES = ['Germany', 'China', 'Russia', 'USA', 'Brazil', 'India']
IP_RANGES = {
    'Germany': '91.0.0.0/24',
    'China': '114.0.0.0/24',
    'Russia': '95.0.0.0/24',
    'USA': '104.0.0.0/24',
    'Brazil': '177.0.0.0/24',
    'India': '115.0.0.0/24'
}

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

# Kafka Producer Konfiguration
def kafka_producer():
    conf = {
        'bootstrap.servers': 'kafka-cluster:9092',
        'security.protocol': 'SASL_PLAINTEXT',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': 'user1',
        'sasl.password': 'qXRWNkq5gr',
        'client.id': 'python-producer',
    }
    return Producer(conf)
```

#### Spark Speed Layer (spark-speed-layer.py)
```python
# Schema Definition
schema = StructType([
    StructField("timestamp", LongType(), True),
    StructField("datetime", StringType(), True),
    StructField("ip", StringType(), True),
    StructField("country", StringType(), True),
    StructField("username", StringType(), True),
    StructField("password", StringType(), True),
    StructField("success", BooleanType(), True)
])

# Kafka Stream Konfiguration
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_broker) \
    .option("subscribe", kafka_topic) \
    .option("kafka.group.id", "spark_consumer") \
    .option("kafka.security.protocol", "SASL_PLAINTEXT") \
    .option("kafka.sasl.mechanism", "PLAIN") \
    .load()
```

### Deployment

#### Honeypot Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: honeypot-producer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: honeypot-producer
  template:
    metadata:
      labels:
        app: honeypot-producer
    spec:
      containers:
      - name: honeypot-producer
        image: philippt314/honeypot:latest
```

### Bekannte Einschränkungen und Troubleshooting

1. **MariaDB ANSI Quotes**
   - Problem: Spark SQL Statements funktionieren nicht
   - Lösung: ANSI_QUOTES in MariaDB SQL Mode aktivieren

2. **Kafka Group ID**
   - Problem: Doppelte Verarbeitung von Messages
   - Lösung: Gleiche Group ID für alle Speed Layer Pods verwenden

3. **MariaDB Single Instance**
   - Einschränkung: Keine Skalierung der Datenbank
   - Workaround: Persistent Volume für Datensicherheit

### Projektstruktur
```
.
│   client.properties
│   docker-compose.yml
│   Dockerfile
│   honeypot.py
│   kafka-values.yaml
│   readme.md
│   requirements.txt
│
├───honeypot
│       Dockerfile
│       honeypot-deployment.yaml
│       honeypot.py
│       requirements.txt
│
├───mariadb
│       mariadb-values.yaml
│
└───spark
        Dockerfile
        spark-deployment.yaml
        spark-speed-layer.py
```

### Performance-Charakteristiken

- Honeypot: ~30-600 Events/Minute
- Spark Processing: Latenz < 1 Sekunde
- Erfolgsrate Login-Versuche: 1%
- Datenbankschreibrate: Batch-Größe 100-1000 Events
