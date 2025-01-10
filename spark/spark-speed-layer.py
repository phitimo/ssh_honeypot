from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def write_to_mariadb(batch_df, batch_id, table_name):
    batch_df.write.jdbc(url='jdbc:mariadb://mariadb:3306/db', table=table_name, properties={'user': 'bde', 'password': 'bde'}, mode="append")
    
    
# Spark-Session starten
spark = SparkSession.builder \
    .appName("SSH-Honeypot-Analytics") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

# Schema für JSON aus Kafka definieren
schema = StructType([
    StructField("timestamp", LongType(), True),
    StructField("datetime", StringType(), True),
    StructField("ip", StringType(), True),
    StructField("country", StringType(), True),
    StructField("username", StringType(), True),
    StructField("password", StringType(), True),
    StructField("success", BooleanType(), True)
])

kafka_broker = "kafka-cluster:9092,kafka-cluster.default.svc.cluster.local:9020"
kafka_topic = "ssh-logs"

# Kafka-Stream lesen
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_broker) \
    .option("subscribe", kafka_topic) \
    .option("kafka.group.id", "spark_consumer") \
    .option("kafka.security.protocol", "SASL_PLAINTEXT") \
    .option("kafka.sasl.mechanism", "PLAIN") \
    .option("kafka.sasl.jaas.config", "org.apache.kafka.common.security.plain.PlainLoginModule required username='user1' password='qXRWNkq5gr';") \
    .load()


parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
       
query1 =  parsed_df.writeStream.foreachBatch(lambda batch_df, batch_id: write_to_mariadb(batch_df, batch_id, "login_attempts")).outputMode("append").option("sql.quote.identifier", "`").start()

attempts_germany = parsed_df.filter(col("country") == "Germany")

query2 = attempts_germany.writeStream.foreachBatch(lambda batch_df, batch_id: write_to_mariadb(batch_df, batch_id, "login_attempts_germany")).outputMode("append").option("sql.quote.identifier", "`").start()
       
query1.awaitTermination()
query2.awaitTermination()


