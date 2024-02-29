import csv
import re
import string
import nltk
from nltk.corpus import stopwords
import os

nltk.download('stopwords')


def clean_text(text):
    # Rimuovi la punteggiatura
    text = re.sub(f"[{re.escape(string.punctuation)}]", "", text)
    
    # Rimuovi le stopword
    stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [word.lower() for word in words if word.lower() not in stop_words]
    
    # Rimuovi link, menzioni e hashtag
    words = [re.sub(r'http\S+', '', word) for word in words]  # Rimuovi link
    words = [re.sub(r'@\w+', '', word) for word in words]     # Rimuovi menzioni
    words = [re.sub(r'#\w+', '', word) for word in words]     # Rimuovi hashtag
    
    # Ricrea il testo pulito
    cleaned_text = ' '.join(words)
    return cleaned_text


def leggi_csv(file_path):
    dati = []
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        reader = csv.DictReader(file)
        
        for riga in reader:
            # Verifica se il campo 'selected_text' è vuoto e salta la riga in tal caso
            if not riga['selected_text']:
                continue
            
            # Rimuovi le colonne specificate
            colonne_da_rimuovere = ['text', 'Time of Tweet', 'Age of User', 'Country', 'Population -2020', 'Land Area', 'Density']
            for colonna in colonne_da_rimuovere:
                riga.pop(colonna, None)

            # Aggiungi colonne per i sentimenti distinti
            riga['positive'] = 0
            riga['negative'] = 0
            riga['neutral'] = 0

            # Imposta il valore appropriato a 1 nella colonna corrispondente al sentiment originale
            if riga['sentiment'] == 'positive':
                riga['positive'] = 1
            elif riga['sentiment'] == 'negative':
                riga['negative'] = 1
            elif riga['sentiment'] == 'neutral':
                riga['neutral'] = 1

            # Applica la pulizia del testo
            riga['selected_text'] = clean_text(riga['selected_text'])

            dati.append(riga)

    return dati


def scrivi_csv(dati, output_file):
    # Assicurati che la cartella 'spark' esista, altrimenti creala
    output_folder = os.path.dirname(output_file)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(output_file, 'w', encoding='utf-8', newline='') as file:
        colonne = ['textID', 'selected_text','sentiment', 'positive', 'negative', 'neutral']
        writer = csv.DictWriter(file, fieldnames=colonne)

        writer.writeheader()
        for riga in dati:
            # Solo le colonne specificate verranno scritte nel file CSV
            writer.writerow({colonna: riga[colonna] for colonna in colonne})



#main
output_file = 'spark/clear_training.csv'
output_temp = '/Users/claudio/Documents/universita/tap/progetto/clear_temp.csv'
file_path = '/Users/claudio/Documents/universita/tap/progetto/spark/train.csv'
dati = leggi_csv(file_path)
scrivi_csv(dati, output_temp)
finale = leggi_csv(output_temp)
scrivi_csv(finale, output_file)
