import tkinter as tk
from tkinter import messagebox
from qdrant_client import QdrantClient
import json
import os
from urllib.parse import urlparse

# Funzione per leggere la configurazione
def get_qdrant_client():
    config_file_path = "config.json"
    if not os.path.exists(config_file_path):
        messagebox.showerror("Errore di configurazione", f"File '{config_file_path}' non trovato.")
        return None
    
    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        
        qdrant_url = config.get("qdrant_url")
        if not qdrant_url:
            messagebox.showerror("Errore di configurazione", "Chiave 'qdrant_url' non trovata in config.json.")
            return None
        
        url_parts = urlparse(qdrant_url)
        host = url_parts.hostname
        port = url_parts.port
        
        if not host or not port:
            messagebox.showerror("Errore di configurazione", f"Formato URL non valido: '{qdrant_url}'. Dovrebbe essere 'http://hostname:port'.")
            return None
            
        return QdrantClient(host=host, port=port)
    
    except json.JSONDecodeError as e:
        messagebox.showerror("Errore di configurazione", f"Errore di lettura del file JSON: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Errore", f"Errore di inizializzazione Qdrant: {e}")
        return None

# Initialize Qdrant client
client = get_qdrant_client()
if not client:
    exit()

def aggiorna_collezioni():
    """Updates the listbox with available collections."""
    try:
        collezioni = client.get_collections().collections
        nomi_collezioni = [col.name for col in collezioni]
        listbox_collezioni.delete(0, tk.END)
        if nomi_collezioni:
            for nome in nomi_collezioni:
                listbox_collezioni.insert(tk.END, nome)
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile recuperare le collezioni: {e}")

def cancella_collezione():
    """Deletes the selected collection."""
    selezione = listbox_collezioni.curselection()
    if not selezione:
        messagebox.showwarning("Attenzione", "Seleziona una collezione da cancellare.")
        return

    collezione_da_cancellare = listbox_collezioni.get(selezione[0])
    
    conferma = messagebox.askyesno(
        "Conferma Cancellazione",
        f"Sei sicuro di voler cancellare la collezione '{collezione_da_cancellare}'? L'operazione è irreversibile!"
    )

    if conferma:
        try:
            client.delete_collection(collection_name=collezione_da_cancellare)
            messagebox.showinfo("Successo", f"La collezione '{collezione_da_cancellare}' è stata cancellata.")
            aggiorna_collezioni()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la cancellazione della collezione:\n{e}")

# Main GUI
root = tk.Tk()
root.title("Gestione Collezioni Qdrant")
root.geometry("400x300")

tk.Label(root, text="Collezioni Qdrant disponibili:", font=("Helvetica", 12)).pack(pady=10)

listbox_collezioni = tk.Listbox(root, selectmode=tk.SINGLE, width=50, height=10)
listbox_collezioni.pack(pady=5)
aggiorna_collezioni()

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

btn_refresh = tk.Button(frame_buttons, text="Aggiorna lista", command=aggiorna_collezioni)
btn_refresh.pack(side=tk.LEFT, padx=5)

btn_delete = tk.Button(frame_buttons, text="Cancella Selezionata", command=cancella_collezione, bg="red", fg="white")
btn_delete.pack(side=tk.LEFT, padx=5)

root.mainloop()
import tkinter as tk
from tkinter import messagebox
from qdrant_client import QdrantClient
import json
import os
from urllib.parse import urlparse

# Funzione per leggere la configurazione
def get_qdrant_client():
    config_file_path = "config.json"
    if not os.path.exists(config_file_path):
        messagebox.showerror("Errore di configurazione", f"File '{config_file_path}' non trovato.")
        return None
    
    try:
        with open(config_file_path, 'r') as f:
            config = json.load(f)
        
        qdrant_url = config.get("qdrant_url")
        if not qdrant_url:
            messagebox.showerror("Errore di configurazione", "Chiave 'qdrant_url' non trovata in config.json.")
            return None
        
        url_parts = urlparse(qdrant_url)
        host = url_parts.hostname
        port = url_parts.port
        
        if not host or not port:
            messagebox.showerror("Errore di configurazione", f"Formato URL non valido: '{qdrant_url}'. Dovrebbe essere 'http://hostname:port'.")
            return None
            
        return QdrantClient(host=host, port=port)
    
    except json.JSONDecodeError as e:
        messagebox.showerror("Errore di configurazione", f"Errore di lettura del file JSON: {e}")
        return None
    except Exception as e:
        messagebox.showerror("Errore", f"Errore di inizializzazione Qdrant: {e}")
        return None

# Initialize Qdrant client
client = get_qdrant_client()
if not client:
    exit()

def aggiorna_collezioni():
    """Updates the listbox with available collections."""
    try:
        collezioni = client.get_collections().collections
        nomi_collezioni = [col.name for col in collezioni]
        listbox_collezioni.delete(0, tk.END)
        if nomi_collezioni:
            for nome in nomi_collezioni:
                listbox_collezioni.insert(tk.END, nome)
    except Exception as e:
        messagebox.showerror("Errore", f"Impossibile recuperare le collezioni: {e}")

def cancella_collezione():
    """Deletes the selected collection."""
    selezione = listbox_collezioni.curselection()
    if not selezione:
        messagebox.showwarning("Attenzione", "Seleziona una collezione da cancellare.")
        return

    collezione_da_cancellare = listbox_collezioni.get(selezione[0])
    
    conferma = messagebox.askyesno(
        "Conferma Cancellazione",
        f"Sei sicuro di voler cancellare la collezione '{collezione_da_cancellare}'? L'operazione è irreversibile!"
    )

    if conferma:
        try:
            client.delete_collection(collection_name=collezione_da_cancellare)
            messagebox.showinfo("Successo", f"La collezione '{collezione_da_cancellare}' è stata cancellata.")
            aggiorna_collezioni()
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la cancellazione della collezione:\n{e}")

# Main GUI
root = tk.Tk()
root.title("Gestione Collezioni Qdrant")
root.geometry("400x300")

tk.Label(root, text="Collezioni Qdrant disponibili:", font=("Helvetica", 12)).pack(pady=10)

listbox_collezioni = tk.Listbox(root, selectmode=tk.SINGLE, width=50, height=10)
listbox_collezioni.pack(pady=5)
aggiorna_collezioni()

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

btn_refresh = tk.Button(frame_buttons, text="Aggiorna lista", command=aggiorna_collezioni)
btn_refresh.pack(side=tk.LEFT, padx=5)

btn_delete = tk.Button(frame_buttons, text="Cancella Selezionata", command=cancella_collezione, bg="red", fg="white")
btn_delete.pack(side=tk.LEFT, padx=5)

root.mainloop()