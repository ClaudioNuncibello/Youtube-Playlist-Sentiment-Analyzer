import argparse
import os
import json
from urllib import response
import requests
import googleapiclient.discovery
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

    playlist_items = []
    next_page_token = None
    while True:
        playlist_items_response = youtube.playlistItems().list(
            part='snippet',
            playlistId= "PL_xGnDm5NCoOh8jSRpwk_ve9xTGI4t4nj",
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
    videos = []
    comments= []

    for item in playlist_items:
        video_id = item['snippet']['resourceId']['videoId']
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id = video_id
        ).execute()

        for item in video_response.get('items', []):
            video_title = item['snippet']['title']
            video_statistics = item.get('statistics', {})
            views = video_statistics.get('viewCount', 0)
            likes = video_statistics.get('likeCount', 0)
            dislikes = video_statistics.get('dislikeCount', 0)

            video_item = {
                'Id_videos': video_id,
                'videoTitle': video_title,
                'views': views,
                'likes': likes,
                'dislikes': dislikes,
            }
            videos.append(video_item)
        

        try:
                request = youtubeAPI.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=100
                )
                response = request.execute()

                for comment_thread in response.get('items', []):
                    comment = comment_thread['snippet']['topLevelComment']['snippet']
                    comment_item = {
                        'videoId': video_id,
                        'videoTitle': video_title,
                        'created_at': comment['publishedAt'],
                        'comment': comment['textDisplay']
                    }
                    comments.append(comment_item)
        except HttpError as e:
            error_message = json.loads(e.content)['error']['message']
            if 'disabled comments' in error_message:
                print(
                    f"I commenti sono disabilitati per il video con ID '{video_id}'.")
            else:
                print(
                    f"Errore durante il recupero dei commenti per il video con ID '{video_id}':", error_message)

    for comment in comments:
         send_to_logstash(comments)
        
    for video_id in videos:
        send_to_logstash(videos)


# main
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    youtube = get_authenticated_service()
    try:
        statistic_videos(youtube)
    except HttpError as e:
        print('Si è verificato un errore HTTP %d:\n%s' %
              (e.resp.status, e.content))

              