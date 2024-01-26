#!/bin/bash

# Esegui i comandi Docker build in ordine

# 1. Build per Logstash
cd logstash
docker build . --tag logstash:tap
cd ..

# 2. Build per Kafka
cd kafka
docker build . --tag kafka:tap
cd ..

# 3. Build per Spark
cd spark
docker build . --tag spark:tap
cd ..
