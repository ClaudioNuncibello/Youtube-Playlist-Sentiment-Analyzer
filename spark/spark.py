from __future__ import print_function
from tracemalloc import start
from xmlrpc.client import Boolean
from pyspark.sql.functions import count, when, col, date_format, from_json
from elasticsearch import Elasticsearch
from pyspark import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.ml import Pipeline
from pyspark.ml.feature import HashingTF, IDF, Tokenizer, StopWordsRemover, Word2Vec, RegexTokenizer
from pyspark.ml.classification import LogisticRegression



kafkaServer = "kafkaServer:9092"
topic = "comments"

#create dataset structure
myProject = tp.StructType([
    tp.StructField(name='videoId', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='videoTitle', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='created_at',
                   dataType=tp.TimestampType(), nullable=True),
    tp.StructField(name='comment', dataType=tp.StringType(), nullable=True),
])

# create schema for training set
schema = tp.StructType([
    tp.StructField(name='textId', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='comment', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='sentiment', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='positive', dataType=tp.IntegerType(), nullable=True),
    tp.StructField(name='neagtive', dataType=tp.IntegerType(), nullable=True),
    tp.StructField(name='neutral', dataType=tp.IntegerType(), nullable=True)
 ])

 # create spark session
sparkConf = SparkConf()
sc = SparkContext(appName="TapSentiment", conf=sparkConf)
spark = SparkSession(sc)
sc.setLogLevel("ERROR")

 # read the training set 
training_set = spark.read.csv('clear_training.csv',
                         schema=schema,
                         header=True,
                         sep=',')
  

stage_1 = RegexTokenizer(inputCol= 'comment' , outputCol= 'tokens', pattern= '\\W')
stage_2 = StopWordsRemover(inputCol= 'tokens', outputCol= 'filtered_words')
stage_3 = Word2Vec(inputCol= 'filtered_words', outputCol= 'vector', vectorSize= 100)
model = LogisticRegression(featuresCol= 'vector', labelCol= 'positive')
pipeline = Pipeline(stages= [stage_1, stage_2, stage_3, model])

# fit the pipeline model with the training data
pipelineFit = pipeline.fit(training_set)

modelSummary=pipelineFit.stages[-1].summary
print ("Model Accuracy:")
print(modelSummary.accuracy)

# Read the stream from kafka
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .load()

# Cast the message received from kafka with the provided schema
df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", myProject).alias("data")) \
    .select("data.*")

# Apply the machine learning model and select only the interesting columns
df = pipelineFit.transform(df) \
    .select("videoId", "videoTitle","created_at", "comment", "prediction")

query = df \
    .writeStream \
    .format("console") \
    .start()
query.awaitTermination()