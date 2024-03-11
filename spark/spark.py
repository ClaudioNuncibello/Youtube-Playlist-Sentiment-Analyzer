from __future__ import print_function
from tracemalloc import start
from xml.etree.ElementTree import Comment
from xmlrpc.client import Boolean
from pyspark.sql.functions import count, when, col, date_format, from_json, window
from elasticsearch import Elasticsearch
from pyspark.sql.session import SparkSession
from pyspark.conf import SparkConf
from pyspark import SparkContext
import pyspark.sql.types as tp
from pyspark.sql.functions import udf
from pyspark.sql.functions import avg
from pyspark.sql.types import FloatType
#sentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# Nltk
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Configurazione di Kafka
kafkaServer = "kafkaServer:9092"
topic = "comments"

# Configurazione di Elasticsearch
elastic_host = "http://elasticsearch:9200"
elastic_index = "videos"
es_mapping = {
    "mappings": {
        "properties": {
            "videoTitle": {
                "type": "text"
            },
            "created_at": {
                "type": "date",
                "format": "yyyy-MM-dd'T'HH:mm:ss"
            },
            "comment": {
                "type": "text",
                "fielddata": True
            },
            "sentiment_score": {
                "type": "float"
            }
        }
    }
}


# Configurazione di Spark
spark = SparkSession.builder \
    .appName("TapSentiment") \
    .getOrCreate()
spark.sparkContext.setLogLevel("ERROR")


es = Elasticsearch(hosts=elastic_host, verify_certs=False)
response = es.indices.create(
    index=elastic_index,
    body=es_mapping,
    ignore=400
)

if 'acknowledged' in response:
    if response['acknowledged'] == True:
        print("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])



# Inizializzazione di NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Funzioni per il preprocessing del testo
def preprocess_text(text):
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word.isalnum()]
    stop_words = set(stopwords.words('italian'))
    tokens = [word for word in tokens if word.lower() not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return tokens

def analyze_sentiment(text):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(text)
    return sentiment_score['compound']

# UDF per l'analisi del sentiment
sentiment_udf = udf(analyze_sentiment, FloatType())

# Schema per i dati
myProject = tp.StructType([
    tp.StructField(name='videoId', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='videoTitle', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='created_at', dataType=tp.StringType(), nullable=True),
    tp.StructField(name='comment', dataType=tp.StringType(), nullable=True),
])

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .load()

# Cast dei messaggi ricevuti da Kafka con lo schema fornito
df = df.selectExpr("CAST(value AS STRING)")\
        .select(from_json("value", myProject).alias("data"))\
        .select("data.*")

#sentiment analysis trasform
df = df.withColumn("sentiment_score", sentiment_udf(df["comment"]))

#send to elastic
def send_batch_to_elasticsearch(df, epoch_id):
    try:
        rows = df.collect()
        for row in rows:
            es.index(index=elastic_index, body=row.asDict(), ignore=400)
        print("dati inviati ad elastic")
    except Exception as e:
        print(f"Errore durante l'invio dei dati a Elasticsearch: {e}")


# write to elastic
query = df \
    .writeStream \
    .foreachBatch(send_batch_to_elasticsearch) \
    .start()
    
query.awaitTermination()