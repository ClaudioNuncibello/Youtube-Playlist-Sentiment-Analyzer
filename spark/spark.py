from __future__ import print_function
from tracemalloc import start
from xmlrpc.client import Boolean
from pyspark.sql.functions import count, when, col, date_format, from_json
from elasticsearch import Elasticsearch
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from sparknlp.base import DocumentAssembler, Finisher, Pipeline
from sparknlp.annotator import (
    SentenceDetector,
    Tokenizer,
    Lemmatizer,
    SentimentDetector
)
import pyspark.sql.functions as F
import sparknlp

kafkaServer = "kafkaServer:9092"
topic = "comments"
spark = sparknlp.start()

# Step 1: Transforms raw texts to `document` annotation
document_assembler = DocumentAssembler() \
    .setInputCol("text") \
    .setOutputCol("document")
# Step 2: Sentence Detection
sentence_detector = SentenceDetector() \
    .setInputCols(["document"]) \
    .setOutputCol("sentence")
# Step 3: Tokenization
tokenizer = Tokenizer() \
    .setInputCols(["sentence"]) \
    .setOutputCol("token")
# Step 4: Lemmatization
lemmatizer = Lemmatizer() \
    .setInputCols(["token"]) \
    .setOutputCol("lemma") \
    .setDictionary("lemmas_small.txt", key_delimiter="->", value_delimiter="\t")
# Step 5: Sentiment Detection
sentiment_detector = SentimentDetector() \
    .setInputCols(["lemma", "sentence"]) \
    .setOutputCol("sentiment_score") \
    .setDictionary("default-sentiment-dict.txt", ",")
# Step 6: Finisher
finisher = Finisher() \
    .setInputCols(["sentiment_score"]) \
    .setOutputCols(["sentiment"])

# Define the pipeline
pipeline = Pipeline(stages=[
    document_assembler,
    sentence_detector,
    tokenizer,
    lemmatizer,
    sentiment_detector,
    finisher
])

# create dataset structure
myProject = tp.StructType([
    tp.StructField(name='videoId', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='videoTitle', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='created_at', dataType=tp.TimestampType(), nullable=True),
    tp.StructField(name='comment', dataType=tp.StringType(), nullable=True),
])

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
df = df.withColumnRenamed("comment", "text")

# Apply the pipeline
result = pipeline.fit(df).transform(df)

# Write the result to console
query = result \
    .writeStream \
    .format("console") \
    .start()

# Wait for the query to terminate
query.awaitTermination()

# #prova
# data = spark.createDataFrame(
#     [
#         [
#             "I recommend others to avoid because it is too expensive"
#         ]
#     ]
# ).toDF("text") # use the column name `text` defined in the pipeline as input
# # Fit-transform to get predictions
# result = pipeline.fit(data).transform(data).show(truncate = 50)
