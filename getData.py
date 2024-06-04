import argparse
import os
import json
import requests
import googleapiclient.discovery
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time

# Load environment variables
load_dotenv('.env')
API_KEY = os.getenv('API_KEY')
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# authenticate to the API
def get_authenticated_service():
    return build(API_SERVICE_NAME, API_VERSION, developerKey=API_KEY, cache_discovery=False)


# send data to logstash
def send_to_logstash(data):
    logstash_url = 'http://localhost:9090'

    try:
        response = requests.post(logstash_url, json=data)
        if response.status_code == 200:
            print("Dati inviati a Logstash con successo.")
        else:
            print("Errore durante l'invio dei dati a Logstash. Codice di risposta:",
                  response.status_code)
    except requests.exceptions.RequestException as e:
        print("Errore durante l'invio dei dati a Logstash:", str(e))


# Retrieve all videos in a YouTube playlist
def playlist_videos(youtube):

    playlist_id_ita = "PL_xGnDm5NCoN-EdtcyMhzGmhEtBWmhVLm"
    playlist_items = []
    next_page_token = None
    while True:
        playlist_items_response = youtube.playlistItems().list(
            part='snippet',
            playlistId = playlist_id_ita,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        playlist_items.extend(playlist_items_response['items'])
        next_page_token = playlist_items_response.get('nextPageToken')

        if not next_page_token:
            break
    return playlist_items


# Fetch video statistics and comments for videos in a YouTube playlist
def statistic_videos(youtube):

    youtubeAPI = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, developerKey=API_KEY)

    playlist_items = playlist_videos(youtube)
    comments = []

    # Carica gli ID dei commenti già inviati
    try:
        with open('comment_ids.json', 'r') as file:
            sent_comment_ids = json.load(file)
    except FileNotFoundError:
        sent_comment_ids = []

    for item in playlist_items:
        video_id = item['snippet']['resourceId']['videoId']
        video_title = item['snippet']['title']

        try:
            request = youtubeAPI.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100
            )
            response = request.execute()

            for comment_thread in response.get('items', []):
                comment_id = comment_thread['snippet']['topLevelComment']['id']
                
                # Verifica se il commento è già stato inviato
                if comment_id not in sent_comment_ids:
                    comment = comment_thread['snippet']['topLevelComment']['snippet']
                    comment_item = {
                        'videoId': video_id,
                        'videoTitle': video_title,
                        'created_at': comment['publishedAt'],
                        'comment': comment['textDisplay'],
                        'timestamp_comment': comment['publishedAt'],
                    }
                    comments.append(comment_item)
                    # Aggiungi l'ID del commento alla lista dei commenti inviati
                    sent_comment_ids.append(comment_id)
        except HttpError as e:
            error_message = json.loads(e.content)['error']['message']
            if 'disabled comments' in error_message:
                print(
                    f"I commenti sono disabilitati per il video con ID '{video_id}'.")
            else:
                print(
                    f"Errore durante il recupero dei commenti per il video con ID '{video_id}':", error_message)

    # Salva gli ID dei commenti già inviati
    with open('comment_ids.json', 'w') as file:
        json.dump(sent_comment_ids, file)

    send_to_logstash(comments)
    #print(comments)


# Intervallo di tempo tra ogni esecuzione in secondi
intervallo_tempo = 10

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    youtube = get_authenticated_service()

    # Loop infinito per eseguire il monitoraggio in tempo reale
    while True:
        try:
            statistic_videos(youtube)
        except HttpError as e:
            print('Si è verificato un errore HTTP %d:\n%s' %
                  (e.resp.status, e.content))
        
        # Attendere prima di eseguire nuovamente
        time.sleep(intervallo_tempo)
