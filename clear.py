import csv

def leggi_csv(file_path):
    dati = []
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        reader = csv.DictReader(file)
        
        for riga in reader:
            # Rimuovi le colonne specificate
            colonne_da_rimuovere = ['text', 'Time of Tweet', 'Age of User', 'Country', 'Population -2020', 'Land Area', 'Density']
            for colonna in colonne_da_rimuovere:
                riga.pop(colonna, None)

            # Mappa la colonna 'sentiment'
            if riga['sentiment'] == 'neutral':
                riga['sentiment'] = 0
            elif riga['sentiment'] == 'positive':
                riga['sentiment'] = 1
            elif riga['sentiment'] == 'negative':
                riga['sentiment'] = -1

            dati.append(riga)

    return dati

def scrivi_csv(dati, output_file='clear_training.csv'):
    with open(output_file, 'w', encoding='utf-8', newline='') as file:
        colonne = ['textID', 'selected_text', 'sentiment']
        writer = csv.DictWriter(file, fieldnames=colonne)

        writer.writeheader()
        for riga in dati:
            writer.writerow(riga)

# Esempio di utilizzo
file_path = 'spark/train.csv'
dati = leggi_csv(file_path)

# Scrivere i dati risultanti in un nuovo file CSV
scrivi_csv(dati)
