import json
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter
from urllib.parse import urlparse

# --- CONFIGURAZIONE BASE E INIZIALIZZAZIONE DA config.json ---
def get_config():
    config_file_path = "config.json"
    if not os.path.exists(config_file_path):
        messagebox.showerror("Errore di configurazione", f"File '{config_file_path}' non trovato.")
        return None
    
    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        messagebox.showerror("Errore di configurazione", f"Errore di lettura del file JSON: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante la lettura del file di configurazione: {e}")
        return None

config = get_config()
if not config:
    exit()

try:
    # Inizializzazione da config.json
    model_path = config.get("model_path")
    qdrant_url = config.get("qdrant_url")
    
    if not model_path:
        messagebox.showerror("Errore di configurazione", "Chiave 'model_path' non trovata in config.json.")
        exit()
    if not qdrant_url:
        messagebox.showerror("Errore di configurazione", "Chiave 'qdrant_url' non trovata in config.json.")
        exit()
        
    url_parts = urlparse(qdrant_url)
    host = url_parts.hostname
    port = url_parts.port

    model = SentenceTransformer(model_path)
    client = QdrantClient(host=host, port=port)

except Exception as e:
    messagebox.showerror("Errore", f"Errore di inizializzazione: {e}")
    exit()

# --- FUNZIONE DI RICERCA ---
def ricerca_e_salva():
    query = entry_query.get()
    collezione = collection_name_var.get()
    
    if not query.strip():
        messagebox.showwarning("Attenzione", "Inserisci una query.")
        return
    if not collezione or collezione == "Nessuna collezione trovata":
        messagebox.showwarning("Attenzione", "Seleziona una collezione valida.")
        return
    
    try:
        threshold_str = entry_threshold.get()
        threshold = float(threshold_str)
        if not (0.0 <= threshold <= 1.0):
            messagebox.showwarning("Attenzione", "La soglia deve essere un valore tra 0.0 e 1.0.")
            return
    except ValueError:
        messagebox.showwarning("Attenzione", "La soglia deve essere un numero valido.")
        return
        
    try:
        query_vector = model.encode(query).tolist()
        
        # Uso del score_threshold invece del limite fisso di risultati
        search_result = client.search(
            collection_name=collezione,
            query_vector=query_vector,
            score_threshold=threshold,
            limit=50
        )
        
        output_text.delete(1.0, tk.END)
        risultati = []
        if not search_result:
            output_text.insert(tk.END, "Nessun risultato trovato sopra la soglia specificata.")
        else:
            for i, hit in enumerate(search_result):
                testo = hit.payload.get('text', 'Nessun testo trovato')
                metadati = {k: v for k, v in hit.payload.items() if k != 'text'}
                
                output_text.insert(tk.END, f"Risultato {i+1} (Score: {hit.score:.2f}):\n")
                output_text.insert(tk.END, f"Testo: {testo}\n")
                output_text.insert(tk.END, f"Metadati: {metadati}\n\n")
                
                risultati.append({
                    'score': hit.score,
                    'text': testo,
                    'metadata': metadati
                })
            
        # Creazione del file risultati_ricerca.json (come prima)
        with open("risultati_ricerca.json", "w", encoding="utf-8") as f:
            json.dump(risultati, f, ensure_ascii=False, indent=4)
            
        # --- AGGIUNTA NUOVA FUNZIONALITÀ: CREAZIONE DI CONTESTO.JSON ---
        istruzioni = "Ecco un JSON con dei risultati. Analizza il contenuto e fanne un riassunto discorsivo e originale. Non limitarti a elencare i punti, ma crea un testo fluido che ne spieghi il significato in modo coerente per rispondere alla domanda dell'utente"
        
        contesto_json = {
            "istruzioni_per_l_ia": istruzioni,
            "domanda_utente": query,
            "contesto": risultati
        }
        
        with open("Contesto.json", "w", encoding="utf-8") as f:
            json.dump(contesto_json, f, ensure_ascii=False, indent=4)
        
        messagebox.showinfo("Successo", "Ricerca completata e risultati salvati in 'risultati_ricerca.json' e 'Contesto.json'")
        
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante la ricerca:\n{e}")

# --- FUNZIONE DI ESPORTAZIONE ---
def esporta_jsonl():
    """
    Esporta i documenti di una collezione Qdrant in un file JSONL.
    """
    collezione = collection_name_var.get()
    if not collezione or collezione == "Nessuna collezione trovata":
        messagebox.showwarning("Attenzione", "Seleziona una collezione valida da esportare.")
        return

    output_path = filedialog.asksaveasfilename(
        title=f"Esporta la collezione '{collezione}' in JSONL",
        defaultextension=".jsonl",
        filetypes=[("File JSON Lines", "*.jsonl")]
    )
    if not output_path:
        return

    try:
        # Aumentato il limite per lo scrolling per poter esportare più dati in una singola chiamata
        punti = client.scroll(
            collection_name=collezione,
            scroll_filter=Filter(),
            limit=10000,
            with_payload=True
        )
        
        with open(output_path, "w", encoding="utf-8") as f:
            for punto in punti[0]:
                payload = punto.payload
                record = {
                    "text": payload.get('text'),
                    "metadata": {k: v for k, v in payload.items() if k != 'text'}
                }
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        messagebox.showinfo("Successo", f"Esportazione completata. Dati salvati in:\n{output_path}")

    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante l'esportazione dei dati:\n{e}")

# --- Costruzione GUI ---
root = tk.Tk()
root.title("Ricerca Semantica Qdrant")

def aggiorna_collezioni():
    try:
        collezioni = client.get_collections().collections
        nomi_collezioni = [col.name for col in collezioni]
        menu = collection_dropdown["menu"]
        menu.delete(0, "end")
        for nome in nomi_collezioni:
            menu.add_command(label=nome, command=lambda value=nome: collection_name_var.set(value))
        if nomi_collezioni:
            collection_name_var.set(nomi_collezioni[0])
        else:
            collection_name_var.set("Nessuna collezione trovata")
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile recuperare le collezioni: {e}")
        collection_name_var.set("Errore connessione")

tk.Label(root, text="Query:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_query = tk.Entry(root, width=50)
entry_query.grid(row=0, column=1, padx=5)

tk.Label(root, text="Collezione:").grid(row=1, column=0, sticky="e", pady=5)
collection_name_var = tk.StringVar()
collection_dropdown = tk.OptionMenu(root, collection_name_var, "")
collection_dropdown.grid(row=1, column=1, sticky="w", padx=5)
aggiorna_collezioni()

tk.Label(root, text="Soglia di Rilevanza (0.0 - 1.0):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
entry_threshold = tk.Entry(root, width=10)
entry_threshold.insert(0, "0.5") # Valore predefinito
entry_threshold.grid(row=2, column=1, sticky="w", padx=5)

btn_search = tk.Button(root, text="Cerca e salva risultati", command=ricerca_e_salva)
btn_search.grid(row=3, column=1, pady=10)

btn_esporta = tk.Button(root, text="Esporta collezione in JSONL", command=esporta_jsonl)
btn_esporta.grid(row=4, column=1, pady=10)

tk.Label(root, text="Risultati:").grid(row=5, column=0, sticky="nw", padx=5, pady=5)
output_text = scrolledtext.ScrolledText(root, width=70, height=15)
output_text.grid(row=5, column=1, padx=5, pady=5)

root.mainloop()