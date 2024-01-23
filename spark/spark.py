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
#topic = "tap"


# create traingin set
# tap = tp.StructType([
#     tp.StructField(name='ente', dataType=tp.StringType(), nullable=True),
#     tp.StructField(name='name', dataType=tp.StringType(), nullable=True),
#     tp.StructField(name='bird', dataType=tp.StringType(), nullable=True),
# ])

# create spark session
sparkConf = SparkConf()
sc = SparkContext(appName="TapSentiment", conf=sparkConf)
spark = SparkSession(sc)

sc.setLogLevel("ERROR")

#create DataFrame
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", "myProjet") \
    .load()
df = df.selectExpr("CAST(value AS STRING)")

query = df \
    .writeStream \
    .format("console") \
    .start()
query.awaitTermination()





