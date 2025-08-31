import json
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests

def get_ollama_response():
    """
    Legge il contesto, le istruzioni e la domanda da Contesto.json,
    li invia a Ollama e visualizza la risposta.
    """
    input_file = "Contesto.json"
    
    if not os.path.exists(input_file):
        messagebox.showerror("Errore", f"File '{input_file}' non trovato.")
        return None

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            dati_input = json.load(f)
        
        # Estrai i campi dal file JSON
        istruzioni = dati_input.get("istruzioni_per_l_ia", "")
        domanda = dati_input.get("domanda_utente", "Rispondi al contesto fornito.")
        contexto_testuale = dati_input.get("contesto", "")

        # Costruisci il prompt per Ollama
        prompt_completo = (
            f"{istruzioni}\n\n"
            f"Contesto: {contexto_testuale}\n\n"
            f"Domanda: {domanda}"
        )
        
        # Chiama l'API di Ollama
        api_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",  # Sostituisci con il modello che preferisci
            "prompt": prompt_completo,
            "stream": False
        }
        
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(api_url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            risposta_ollama = response.json().get("response", "Nessuna risposta da Ollama.")
            return risposta_ollama
        else:
            return (f"Errore nella chiamata all'API di Ollama. Status Code: {response.status_code}\n"
                    f"Risposta: {response.text}")
            
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante l'elaborazione o la chiamata a Ollama:\n{e}")
        return None

# --- Costruzione GUI per Ollama Go ---
root = tk.Tk()
root.title("Ollama RAG")

tk.Label(root, text="Risposta da Ollama:").pack(pady=5)
output_text = scrolledtext.ScrolledText(root, width=80, height=20, wrap=tk.WORD)
output_text.pack(pady=10, padx=10)

def display_response():
    response = get_ollama_response()
    if response:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, response)
        
btn_go = tk.Button(root, text="Genera Risposta con Ollama", command=display_response)
btn_go.pack(pady=10)

display_response() # Lancia la funzione all'avvio

root.mainloop()