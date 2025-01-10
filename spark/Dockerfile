FROM bitnami/spark:latest
USER root

# Richtiger SQL-Modus für MariaDB
ENV sql_mode="ANSI_QUOTES"

# Kopiere Spark-Anwendung
COPY spark-test.py /app/

# MariaDB JDBC Treiber herunterladen
ADD https://downloads.mariadb.com/Connectors/java/connector-java-3.5.1/mariadb-java-client-3.5.1.jar /opt/bitnami/spark/jars/
RUN chmod 644 /opt/bitnami/spark/jars/mariadb-java-client-3.5.1.jar

# Setze Arbeitsverzeichnis
WORKDIR /app

# Starte Spark-Anwendung
CMD ["spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0", \
     "--master", "local[*]", \
     "--driver-class-path", "/opt/bitnami/spark/jars/mariadb-java-client-3.5.1.jar", \
     "--jars", "/opt/bitnami/spark/jars/mariadb-java-client-3.5.1.jar", \
     "spark-speed-layer.py"]

     