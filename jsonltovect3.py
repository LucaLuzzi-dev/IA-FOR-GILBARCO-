import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from qdrant_client.http.exceptions import UnexpectedResponse

# Importa le librerie necessarie per l'ottimizzazione Intel
import torch
try:
    import intel_extension_for_pytorch as ipex
except ImportError:
    ipex = None

# --- CONFIGURAZIONE BASE ---
def load_config():
    """Carica le configurazioni dal file config.json."""
    config_file_path = "config.json"
    try:
        with open(config_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Errore", f"File di configurazione '{config_file_path}' non trovato.")
        return None
    except json.JSONDecodeError:
        messagebox.showerror("Errore", f"Errore di lettura del file '{config_file_path}'. Controlla il formato JSON.")
        return None

# --- FUNZIONI DI ELABORAZIONE E GUI ---
def get_line_count(file_path):
    """Conta il numero totale di righe in un file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile contare le righe del file:\n{e}")
        return 0

def indicizza_file(file_path, collection_name, batch_size, progress_window, progress_bar, status_label):
    """
    Legge un file JSONL, converte i documenti in vettori e li indicizza in Qdrant.
    """
    config = load_config()
    if not config:
        progress_window.destroy()
        return
        
    qdrant_url = config.get("qdrant_url")
    qdrant_api_key = config.get("qdrant_api_key")
    model_path = config.get("model_path")

    # Inizializza client e modello con gestione degli errori
    try:
        # Rileva il dispositivo (GPU Intel o CPU)
        device = "xpu" if ipex and torch.xpu.is_available() else "cpu"
        print(f"Dispositivo di calcolo per gli embeddings: {device}")

        # Carica il modello e lo sposta sul dispositivo corretto
        model = SentenceTransformer(model_path, device=device)
        model.to(device)

        # Inizializza il client Qdrant
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=30)
        # Verifica la connessione
        client.get_collections()
        
    except Exception as e:
        messagebox.showerror("Errore di Inizializzazione", 
                             f"Impossibile avviare il processo. Dettagli:\n{e}\n\n"
                             f"Verifica la configurazione ('config.json'), "
                             f"il server Qdrant e le librerie Intel.")
        progress_window.destroy()
        return

    # Calcola il numero totale di righe
    total_lines = get_line_count(file_path)
    if total_lines == 0:
        progress_window.destroy()
        return

    progress_bar['maximum'] = total_lines

    # Crea o prepara la collezione
    try:
        if collection_name not in [col.name for col in client.get_collections().collections]:
            status_label.config(text=f"Creazione della collezione '{collection_name}'...")
            progress_window.update()
            client.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=model.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )
            print(f"Collezione '{collection_name}' creata.")
    except Exception as e:
        messagebox.showerror("Errore Qdrant", f"Impossibile creare/verificare la collezione: {e}")
        progress_window.destroy()
        return

    batch = []
    processed_count = 0
    id_counter = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                data = json.loads(line.strip())
                text = data.get("text")
                if not text:
                    continue

                batch.append(data)
                
                if len(batch) >= batch_size:
                    status_label.config(text=f"Processando documenti ({processed_count + len(batch)}/{total_lines})...")
                    progress_window.update()
                    
                    # Genera gli embeddings
                    sentences = [d["text"] for d in batch]
                    embeddings = model.encode(sentences, convert_to_tensor=True, device=device).tolist()
                    
                    points = []
                    for doc, vec in zip(batch, embeddings):
                        points.append(PointStruct(id=id_counter, vector=vec, payload=doc))
                        id_counter += 1

                    client.upsert(collection_name=collection_name, points=points)
                    batch = []
                    processed_count = i + 1
                    
                    progress_bar['value'] = processed_count
                    progress_window.update()

            except Exception as e:
                print(f"Errore durante l'elaborazione del batch: {e}. Saltando...")
                batch = [] # Svuota il batch per evitare ulteriori errori con gli stessi dati
                continue
                
    # Elabora l'ultimo batch
    if batch:
        status_label.config(text="Processando l'ultimo batch...")
        progress_window.update()
        try:
            sentences = [d["text"] for d in batch]
            embeddings = model.encode(sentences, convert_to_tensor=True, device=device).tolist()
            
            points = []
            for doc, vec in zip(batch, embeddings):
                points.append(PointStruct(id=id_counter, vector=vec, payload=doc))
                id_counter += 1
            
            client.upsert(collection_name=collection_name, points=points)
            processed_count += len(batch)
        except Exception as e:
            print(f"Errore durante l'elaborazione dell'ultimo batch: {e}")

    progress_bar['value'] = processed_count
    status_label.config(text=f"Indicizzazione completata ({processed_count}/{total_lines}).")
    progress_window.update()

    messagebox.showinfo("Completato", f"Indicizzazione completata su '{collection_name}'")
    progress_window.destroy()


def scegli_file():
    """Apre una finestra di dialogo per la selezione del file JSONL."""
    file_path = filedialog.askopenfilename(
        title="Seleziona un file JSONL",
        filetypes=[("File JSON Lines", "*.jsonl")]
    )
    if file_path:
        file_path_var.set(file_path)

def avvia_indicizzazione():
    path = file_path_var.get()
    col_name = collection_name_var.get().strip()
    try:
        batch_size = int(batch_size_var.get())
    except ValueError:
        messagebox.showerror("Errore", "Batch size deve essere un numero intero")
        return

    if not path or not col_name:
        messagebox.showerror("Errore", "Selezionare un file e inserire un nome per la collezione.")
        return

    progress_window = tk.Toplevel(root)
    progress_window.title("Indicizzazione in corso...")
    progress_window.geometry("350x120")
    progress_window.resizable(False, False)
    status_label = tk.Label(progress_window, text="Preparazione...", font=("Helvetica", 10))
    status_label.pack(pady=10, padx=10)
    progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
    progress_bar.pack(pady=5, padx=10)

    indicizza_file(path, col_name, batch_size, progress_window, progress_bar, status_label)

# --- Costruzione GUI principale ---
root = tk.Tk()
root.title("Indicizzazione Qdrant")

tk.Label(root, text="File JSONL:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
file_path_var = tk.StringVar()
tk.Entry(root, textvariable=file_path_var, width=50).grid(row=0, column=1, padx=5, pady=5)
tk.Button(root, text="Sfoglia", command=scegli_file).grid(row=0, column=2, padx=5, pady=5)

tk.Label(root, text="Nome collezione:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
collection_name_var = tk.StringVar(value="miei_ticket")
tk.Entry(root, textvariable=collection_name_var, width=50).grid(row=1, column=1, columnspan=2, padx=5, pady=5)

tk.Label(root, text="Dimensione batch:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
batch_size_var = tk.StringVar(value="64")
tk.Entry(root, textvariable=batch_size_var, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)

tk.Button(root, text="Avvia Indicizzazione", command=avvia_indicizzazione, bg="green", fg="white").grid(row=3, column=1, pady=10)

root.mainloop()