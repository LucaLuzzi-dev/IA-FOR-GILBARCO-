import fitz  # PyMuPDF
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import io
import pytesseract
import pandas as pd
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch

# Inizializza il modello di image captioning solo una volta all'avvio dell'applicazione
try:
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base", torch_dtype=torch.float16).to("xpu" if torch.xpu.is_available() else "cpu")
    print("Modello BLIP caricato con successo.")
except Exception as e:
    messagebox.showerror("Errore", f"Impossibile caricare il modello di image captioning:\n{e}")
    processor = None
    model = None

# --- Nuove finestre di dialogo ---

def chiedi_opzioni_descrizione():
    """Mostra una finestra di dialogo per scegliere tra descrizione automatica e manuale,
    con l'opzione di validazione per la descrizione automatica."""
    opzioni = tk.Toplevel()
    opzioni.title("Opzioni di Descrizione Immagine")

    descrizione_automatica = tk.BooleanVar(value=True)
    valida_automatica = tk.BooleanVar(value=True)
    risposta_salvata = tk.BooleanVar(value=False)

    def on_conferma():
        risposta_salvata.set(True)
        opzioni.destroy()

    tk.Label(opzioni, text="Scegli il tipo di descrizione per le immagini:").pack(padx=10, pady=5)
    
    # Radio buttons per la scelta
    tk.Radiobutton(opzioni, text="Descrizione Automatica", variable=descrizione_automatica, value=True).pack(anchor="w", padx=20)
    tk.Radiobutton(opzioni, text="Descrizione Manuale", variable=descrizione_automatica, value=False).pack(anchor="w", padx=20)

    # Checkbox per la validazione, visibile solo con descrizione automatica
    valida_checkbox = tk.Checkbutton(opzioni, text="Richiedi validazione (mostra didascalia prima di accettarla)", variable=valida_automatica)
    valida_checkbox.pack(anchor="w", padx=40)
    
    def toggle_valida_checkbox():
        if descrizione_automatica.get():
            valida_checkbox.pack(anchor="w", padx=40)
        else:
            valida_checkbox.pack_forget()
    
    descrizione_automatica.trace("w", lambda *args: toggle_valida_checkbox())
    
    tk.Button(opzioni, text="Conferma", command=on_conferma).pack(pady=10)

    # Attendere la chiusura della finestra per ottenere le variabili
    opzioni.grab_set()
    opzioni.wait_window()
    
    return descrizione_automatica.get(), valida_automatica.get()

def chiedi_validazione(img_bytes, didascalia):
    """Mostra immagine e didascalia all'utente per la validazione."""
    top = tk.Toplevel()
    top.title("Valida la Descrizione Automatica")
    
    img_data = Image.open(io.BytesIO(img_bytes))
    img_data.thumbnail((400, 400))
    tk_img = ImageTk.PhotoImage(img_data)
    
    panel = tk.Label(top, image=tk_img)
    panel.pack(padx=10, pady=10)
    panel.image = tk_img
    
    tk.Label(top, text="Didascalia Automatica:").pack(pady=5)
    text_widget = tk.Text(top, height=5, width=60)
    text_widget.insert(tk.END, didascalia)
    text_widget.pack(padx=10, pady=5)
    
    # Bottone per accettare o rifiutare
    accettato = tk.BooleanVar(value=False)
    
    def on_accetta():
        accettato.set(True)
        top.destroy()

    tk.Button(top, text="Accetta e Salva", command=on_accetta).pack(pady=5)
    
    top.grab_set()
    top.wait_window()
    
    return accettato.get()

def chiedi_descrizione_manuale(img_bytes):
    """Crea una finestra per mostrare un'immagine e chiedere una descrizione all'utente."""
    top = tk.Toplevel()
    top.title("Descrivi l'immagine")
    
    img_data = Image.open(io.BytesIO(img_bytes))
    img_data.thumbnail((400, 400))
    tk_img = ImageTk.PhotoImage(img_data)
    
    panel = tk.Label(top, image=tk_img)
    panel.pack(padx=10, pady=10)
    panel.image = tk_img
    
    tk.Label(top, text="Inserisci una descrizione per questa immagine:").pack(pady=5)
    entry_desc = tk.Entry(top, width=60)
    entry_desc.pack(padx=10, pady=5)
    
    descrizione = tk.StringVar()
    def salva_desc():
        descrizione.set(entry_desc.get())
        top.destroy()
    
    tk.Button(top, text="Salva", command=salva_desc).pack(pady=5)
    
    top.grab_set()
    top.wait_window()
    
    return descrizione.get()

def salva_jsonl(df, file_path):
    """Salva il DataFrame in formato JSONL."""
    with open(file_path, 'w', encoding='utf-8') as f:
        df.to_json(f, orient='records', lines=True, force_ascii=False)
    messagebox.showinfo("Successo", f"File salvato con successo:\n{file_path}")

# --- Logica principale ---

def processa_pdf():
    """Funzione principale per il processing del PDF."""
    file_path = filedialog.askopenfilename(
        title="Seleziona un file PDF",
        filetypes=[("PDF files", "*.pdf")]
    )
    if not file_path:
        return

    # Chiede le opzioni di descrizione prima di iniziare
    usa_descrizione_automatica, valida_automatica = chiedi_opzioni_descrizione()
    
    try:
        # Usa PyMuPDF (fitz) che è più compatibile con il codice originale
        doc = fitz.open(file_path)
        pagine_testo = []
        
        for i in range(len(doc)):
            pagina = doc[i]
            testo_pagina = pagina.get_text()
            
            # Estrazione e processamento delle immagini
            immagini = pagina.get_images(full=True)
            for img_info in immagini:
                try:
                    xref = img_info[0]
                    img_bytes = doc.extract_image(xref)["image"]
                    img = Image.open(io.BytesIO(img_bytes))
                    
                    # Tenta l'OCR prima
                    testo_ocr = pytesseract.image_to_string(img)
                    
                    if testo_ocr.strip():
                        testo_pagina += "\n\n[IMMAGINE - TESTO ESTRATTO]\n" + testo_ocr
                    else:
                        # Se l'OCR non trova nulla, usa il flusso di descrizione
                        if usa_descrizione_automatica:
                            if processor and model:
                                inputs = processor(images=img.convert("RGB"), return_tensors="pt").to(model.device, torch.float16)
                                didascalia_ids = model.generate(**inputs)
                                didascalia = processor.decode(didascalia_ids[0], skip_special_tokens=True)
                                
                                # Flusso di validazione
                                if valida_automatica:
                                    if chiedi_validazione(img_bytes, didascalia):
                                        testo_pagina += f"\n\n[IMMAGINE - DESCRIZIONE AUTOMATICA]\n{didascalia}"
                                    else:
                                        descrizione = chiedi_descrizione_manuale(img_bytes)
                                        if descrizione:
                                            testo_pagina += f"\n\n[IMMAGINE - DESCRIZIONE UTENTE]\n{descrizione}"
                                else:
                                    testo_pagina += f"\n\n[IMMAGINE - DESCRIZIONE AUTOMATICA]\n{didascalia}"
                            else:
                                # Fallback se il modello non è stato caricato
                                descrizione = chiedi_descrizione_manuale(img_bytes)
                                if descrizione:
                                    testo_pagina += f"\n\n[IMMAGINE - DESCRIZIONE UTENTE]\n{descrizione}"
                        else: # Descrizione manuale
                            descrizione = chiedi_descrizione_manuale(img_bytes)
                            if descrizione:
                                testo_pagina += f"\n\n[IMMAGINE - DESCRIZIONE UTENTE]\n{descrizione}"
                
                except Exception as e:
                    print(f"Errore nel processare l'immagine: {e}")
                    # In caso di errore, fallback alla richiesta all'utente
                    descrizione = chiedi_descrizione_manuale(img_bytes)
                    if descrizione:
                        testo_pagina += f"\n\n[IMMAGINE - DESCRIZIONE UTENTE]\n{descrizione}"

            pagine_testo.append({
                'text': testo_pagina,
                'page_number': i + 1,
                'source_file': file_path
            })
        doc.close()
        
        df = pd.DataFrame(pagine_testo)
        
        jsonl_path = filedialog.asksaveasfilename(
            title="Salva file JSONL",
            defaultextension=".jsonl",
            filetypes=[("JSON Lines", "*.jsonl")]
        )
        if jsonl_path:
            salva_jsonl(df, jsonl_path)
        
    except Exception as e:
        messagebox.showerror("Errore", f"Errore nel processare il PDF:\n{e}")

# --- Interfaccia grafica ---
root = tk.Tk()
root.title("Convertitore PDF → JSONL")
tk.Button(root, text="Seleziona PDF e Converti", command=processa_pdf).pack(pady=20, padx=20)
root.mainloop()