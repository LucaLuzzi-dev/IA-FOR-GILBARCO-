# -*- coding: utf-8 -*-
import re
import csv

def parse_codice_civile(input_file, output_file):
   
    try: 
        with open(input_file, 'r', encoding='cp1252',errors = 'ignore') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Errore: il file '{input_file}' non  stato trovato.")
        return

    # Espressione regolare per trovare gli articoli.
    # Spiega la regex:
    # '^Art.\s+(\d+)\.': cerca la stringa "Art. " all'inizio di una riga, seguita da uno o pió spazi,
    #                    poi da uno o pió numeri (\d+), e infine un punto.
    #                    Il numero viene catturato in un gruppo (\d+).
    # '(.+?)(?=\nArt.\s+\d+\.|\Z)': cattura il testo dell'articolo.
    #                                (.+?): cattura qualsiasi carattere (.+) in modo non avido (?).
    #                                (?=...): ä un "lookahead positivo" che non consuma il testo.
    #                                         Cerca la posizione che precede l'inizio del prossimo articolo
    #                                         oppure la fine del file (\Z).
    pattern = r'^Art\.\s+(\d+)\.\s*(.*?)(?=\nArt\.\s+\d+\.|\Z)'
    
    # Flags: re.DOTALL per far sç che il punto (.) includa anche i newline.
    articles = re.findall(pattern, text, re.MULTILINE | re.DOTALL)

    if not articles:
        print("Nessun articolo trovato. Controlla il formato del file di testo.")
        return

    # Prepara i dati per il CSV
    data = []
    for article_number, article_text in articles:
        # Pulisci il testo dell'articolo da spazi extra o newline
        cleaned_text = ' '.join(article_text.strip().split())
        data.append({'numero': article_number, 'testo': cleaned_text})

    # Scrivi i dati nel file CSV
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['numero', 'testo']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)

    print(f"Processo completato! Il file '{output_file}' ä stato creato con successo.")

# Sostituisci 'codice_civile.txt' con il nome del tuo file di testo
# e 'codice_civile.csv' con il nome che vuoi dare al file CSV di output.
input_file_name = 'C:\\vdbase\\dati\\cc1942.txt'
output_file_name = 'C:\\vdbase\\dati\\codice_civile.csv'

parse_codice_civile(input_file_name, output_file_name)
