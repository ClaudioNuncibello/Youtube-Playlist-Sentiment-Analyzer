from __future__ import print_function
from tracemalloc import start
from pyspark.sql.functions import count, when, col, date_format, from_json
from elasticsearch import Elasticsearch
from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
import json
from pyspark import SparkContext
import pyspark.sql.types as tp
from pyspark.ml import Pipeline
from pyspark.ml.feature import HashingTF, IDF, Tokenizer, StopWordsRemover
from pyspark.ml.classification import LogisticRegression

kafkaServer = "kafkaServer:9092"
topic = "comments"

# create traingin set
# myProject = tp.StructType([
#     tp.StructField(name='videoId', dataType=tp.StringType(), nullable=True),
#     tp.StructField(name='videoTitle', dataType=tp.StringType(), nullable=True),
#     tp.StructField(name='created_at',
#                    dataType=tp.TimestampType(), nullable=True),
#     tp.StructField(name='comment', dataType=tp.StringType(), nullable=True),
# ])

# create schema for training set
schema = tp.StructType([
    tp.StructField(name='textId', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='text', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='sentiment', dataType=tp.IntegerType(), nullable=True),
 ])

# create spark session
sparkConf = SparkConf()
sc = SparkContext(appName="TapSentiment", conf=sparkConf)
spark = SparkSession(sc)

sc.setLogLevel("ERROR")

print("Sto leggendo il traingin set...")
training_set = spark.read.csv(
    'clear_training.csv', schema=schema, header=True, sep=','
)
print("Finito.")

#create DataFrame
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .load()
df = df.selectExpr("CAST(value AS STRING)")

query = df \
    .writeStream \
    .format("console") \
    .start()
query.awaitTermination()





