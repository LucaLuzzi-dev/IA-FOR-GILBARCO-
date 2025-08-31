import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import json

def carica_file():
    file_path = filedialog.askopenfilename(
        title="Seleziona file Excel o CSV",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv")]
    )
    if not file_path:
        return
    
    try:
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nel caricamento file:\n{e}")
        return

    colonne = df.columns.tolist()
    messagebox.showinfo("Info colonne", f"Colonne trovate:\n{', '.join(colonne)}")

    col_text = simpledialog.askstring("Input", "Inserisci il nome della colonna da usare come testo (case-sensitive):")
    if not col_text or col_text not in df.columns:
        messagebox.showerror("Errore", "Colonna testo non valida!")
        return
    
    seleziona_metadati(df, col_text, file_path)

def salva_jsonl(df, col_text, metadati_col):
    jsonl_path = filedialog.asksaveasfilename(
        title="Salva file JSONL",
        defaultextension=".jsonl",
        filetypes=[("JSON Lines", "*.jsonl")]
    )
    if not jsonl_path:
        return
    
    try:
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for _, row in df.iterrows():
                metadata = {k: row[k] for k in metadati_col}
                record = {
                    "text": row[col_text],
                    "metadata": metadata
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nel salvataggio file JSONL:\n{e}")
        return
    
    messagebox.showinfo("Fatto", f"File JSONL salvato in:\n{jsonl_path}")

def seleziona_metadati(df, col_text, file_path):
    top = tk.Toplevel()
    top.title("Seleziona colonne da includere come metadati")
    top.geometry("300x400")

    label = tk.Label(top, text="Seleziona le colonne da includere come metadati:")
    label.pack(pady=5)

    def conferma():
        metadati_col = [c for c, v in vars.items() if v.get()]
        top.destroy()
        salva_jsonl(df, col_text, metadati_col)

    btn = tk.Button(top, text="Conferma e salva JSONL", command=conferma)
    btn.pack(pady=5)

    cols = [c for c in df.columns if c != col_text]

    vars = {}
    for c in cols:
        var = tk.BooleanVar(value=False)
        chk = tk.Checkbutton(top, text=c, variable=var)
        chk.pack(anchor='w')
        vars[c] = var

root = tk.Tk()
root.title("Convertitore Excel/CSV → JSONL")
root.geometry("400x150")

btn = tk.Button(root, text="Carica file Excel/CSV e converti in JSONL", command=carica_file)
btn.pack(expand=True)

root.mainloop()
