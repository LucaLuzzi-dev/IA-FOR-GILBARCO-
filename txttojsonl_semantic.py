# txttojsonl_semantic.py
import torch
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from optimum.intel.openvino import OVModelForFeatureExtraction
import numpy as np
import os

# --- Ottimizzazione per GPU Intel Arc ---
# Importa la libreria IPEX per l'accelerazione della GPU Intel
try:
    #import intel_extension_for_pytorch as ipex
    # Imposta il dispositivo su 'xpu' se una GPU Intel è disponibile, altrimenti usa 'cpu'
    device = "GPU" if torch.xpu.is_available() else "cpu"
    print(f"Rilevata GPU Intel. Utilizzando il dispositivo: {device}")
except ImportError:
    # Se la libreria IPEX non è installata, torna alla CPU
    device = "cpu"
    print("intel_extension_for_pytorch non trovato. Utilizzando la CPU.")
except Exception as e:
    # Gestisce altri errori che potrebbero verificarsi durante il rilevamento della GPU
    device = "cpu"
    print(f"Errore nel rilevare la GPU Intel: {e}. Utilizzando la CPU.")

# --- Fine dell'ottimizzazione ---

def convert_txt_to_jsonl_semantic():
    """
    Carica un file di testo e lo converte in JSONL usando il chunking semantico.
    """
    file_txt_path = filedialog.askopenfilename(
        title="Seleziona un file di testo (.txt)",
        filetypes=[("Text files", "*.txt")]
    )
    if not file_txt_path:
        return
        
    file_jsonl_path = filedialog.asksaveasfilename(
        title="Salva il file JSONL (Chunking Semantico)",
        defaultextension=".jsonl",
        filetypes=[("JSON Lines", "*.jsonl")]
    )
    if not file_jsonl_path:
        return

    try:
        # Legge il percorso del modello da config.json
        config_path = "config.json"
        if not os.path.exists(config_path):
            messagebox.showerror("Errore", "Il file config.json non è stato trovato.")
            return

        with open(config_path, "r") as f:
            config = json.load(f)
            model_path = config.get("model_path")
            if not model_path:
                messagebox.showerror("Errore", "La chiave 'model_path' non è presente nel file config.json.")
                return
        
        # Carica il modello di embedding specificato in config.json
        model = SentenceTransformer(model_path)
        
        with open(file_txt_path, 'r', encoding='utf-8') as txt_file:
            full_text = txt_file.read()
        
        sentences = [s.strip() for s in full_text.split('.') if s.strip()]

        if not sentences:
            messagebox.showwarning("Attenzione", "Nessuna frase rilevata nel file.")
            return

        embeddings = model.encode(sentences)
        
        similarities = [cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0] for i in range(len(embeddings) - 1)]
        
        threshold = np.mean(similarities) - np.std(similarities)
        
        chunks = []
        current_chunk = ""
        for i, sentence in enumerate(sentences):
            current_chunk += sentence + ". "
            if i < len(similarities) and similarities[i] < threshold:
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        if current_chunk:
            chunks.append(current_chunk.strip())

        with open(file_jsonl_path, 'w', encoding='utf-8') as jsonl_file:
            for i, chunk in enumerate(chunks):
                record = {
                    "text": chunk,
                    "metadata": {
                        "source_file": file_txt_path,
                        "chunk_type": "semantic",
                        "chunk_number": i + 1
                    }
                }
                jsonl_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                
        messagebox.showinfo("Successo", f"File '{file_txt_path}' convertito in '{file_jsonl_path}' con successo!")

    except Exception as e:
        messagebox.showerror("Errore", f"Si è verificato un errore durante la conversione:\n{e}")

if __name__ == "__main__":
    convert_txt_to_jsonl_semantic()