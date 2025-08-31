import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import time
import os
import json
import subprocess
import webbrowser
import socket

class VDBaseManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestione Database Vettoriale Qdrant")
        self.geometry("600x500")
        self.withdraw()
        
        self.show_splash_screen()
        
    def show_splash_screen(self):
        splash_root = tk.Toplevel(self)
        splash_root.title("Caricamento...")
        splash_root.overrideredirect(True)
        
        try:
            image_path = "img/2.jpg"
            original_image = Image.open(image_path)

            screen_width = splash_root.winfo_screenwidth()
            new_width = int(screen_width * 0.66)
            original_width, original_height = original_image.size
            new_height = int(new_width * original_height / original_width)

            resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            x = (screen_width / 2) - (new_width / 2)
            y = (splash_root.winfo_screenheight() / 2) - (new_height / 2)
            splash_root.geometry(f"{new_width}x{new_height}+{int(x)}+{int(y)}")
            
            photo = ImageTk.PhotoImage(resized_image)
            splash_label = tk.Label(splash_root, image=photo)
            splash_label.image = photo
            
        except FileNotFoundError:
            messagebox.showerror("Errore", "Immagine dello splash screen non trovata: img/2.jpg")
            self.quit()
        
        splash_label.pack()
        splash_root.update()
        time.sleep(3)
        splash_root.destroy()
        
        self.deiconify()
        self.create_widgets()
        self.add_footer()

    def create_widgets(self):
        
        # New frame for the header with logo and title
        header_frame = tk.Frame(self)
        header_frame.pack(side=tk.TOP, fill="x", padx=10, pady=10)

        try:
            logo_path = "img/1.webp"
            original_logo = Image.open(logo_path)
            resized_logo = original_logo.resize((50, 50))
            logo_photo = ImageTk.PhotoImage(resized_logo)
            logo_label = tk.Label(header_frame, image=logo_photo)
            logo_label.image = logo_photo
            logo_label.pack(side=tk.LEFT)
        except FileNotFoundError:
            messagebox.showerror("Errore", "Immagine del logo non trovata: img/1.webp")
            
        tk.Label(header_frame, text="Gestione Database Vettoriale Qdrant", font=("Helvetica", 16, "bold")).pack(side=tk.LEFT, padx=10)
        
        # Central frame for the main buttons
        main_frame = tk.Frame(self)
        main_frame.pack(pady=20, fill="x")

        button_width = 30 

        #insert_button = tk.Button(main_frame, text="Inserimento in Dbase Vettoriale", command=self.dummy_function, width=button_width)
        #insert_button.pack(pady=5)

        search_button = tk.Button(main_frame, text="Ricerca", command=self.run_search_script, width=button_width)
        search_button.pack(pady=5)

        ollama_go_button = tk.Button(main_frame, text="OLLAMA GO!", command=self.run_ollama_script, width=button_width)
        ollama_go_button.pack(pady=5)

        setup_button = tk.Button(main_frame, text="Setup", command=self.open_config_file, width=button_width)
        setup_button.pack(pady=5)

        utensili_frame = tk.LabelFrame(self, text="Utensili")
        utensili_frame.pack(pady=20, padx=20, fill="x")

        self.utensili_variable = tk.StringVar(self)
        self.utensili_variable.set("Seleziona uno strumento")

        utensili_menu = tk.OptionMenu(
            utensili_frame,
            self.utensili_variable,
            "Funzione CSV/XLS to JSONL",
            "Funzione PDF to JSONL",
            "Funzione TXT to CSV",
            "Funzione TXT to JSONL (Semantico)",
            "Funzione JSONL to Vector DB",
            "Gestione Dbase Vettoriale",
            "Download JSONL da Dbase"
        )
        utensili_menu.config(width=30)
        utensili_menu.pack(pady=10, padx=10)

        self.utensili_variable.trace_add("write", self.handle_utensili_selection)
        
        status_frame = tk.LabelFrame(self, text="Stato del Sistema")
        status_frame.pack(pady=10, padx=20, fill="x")
        
        network_status_frame = tk.Frame(status_frame)
        network_status_frame.pack(side=tk.LEFT, padx=10, pady=5)
        self.network_led = tk.Label(network_status_frame, text="●", font=("Arial", 24), fg="red")
        self.network_led.pack(side=tk.LEFT)
        tk.Label(network_status_frame, text="Rete").pack(side=tk.LEFT, padx=5)

        docker_status_frame = tk.Frame(status_frame)
        docker_status_frame.pack(side=tk.LEFT, padx=10, pady=5)
        self.docker_led = tk.Label(docker_status_frame, text="●", font=("Arial", 24), fg="red")
        self.docker_led.pack(side=tk.LEFT)
        tk.Label(docker_status_frame, text="Docker").pack(side=tk.LEFT, padx=5)
        
        self.model_label = tk.Label(status_frame, text="", justify=tk.LEFT)
        self.model_label.pack(side=tk.RIGHT, padx=10, pady=5)

        self.check_status()

    def add_footer(self):
        try:
            footer_frame = tk.Frame(self)
            footer_frame.pack(side=tk.BOTTOM, pady=10)

            image_path = "img/1.webp"
            original_image = Image.open(image_path)
            resized_image = original_image.resize((150, 150))
            photo = ImageTk.PhotoImage(resized_image)

            footer_label = tk.Label(
                footer_frame,
                image=photo,
                text="",
                compound=tk.TOP,
                font=("Helvetica", 10, "bold")
            )
            footer_label.image = photo
            footer_label.pack()
            # The original footer has been removed as the logo is now in the header.
            # This method has been updated to prevent the footer from appearing at the bottom.
            # You can re-enable this section if you want the footer back.
            pass

        except FileNotFoundError:
            messagebox.showerror("Errore", "Immagine del footer non trovata: img/1.webp")
            self.quit()
    
    def handle_utensili_selection(self, *args):
        selected_option = self.utensili_variable.get()
        if selected_option == "Funzione CSV/XLS to JSONL":
            self.run_external_script("csvtojsonl2.py")
        elif selected_option == "Funzione PDF to JSONL":
            self.run_external_script("pdf2jsonl.py")
        elif selected_option == "Funzione TXT to CSV":
            self.run_external_script("txttocsv.py")
        elif selected_option == "Funzione TXT to JSONL (Semantico)":
            self.run_external_script("txttojsonl_semantic.py")
        elif selected_option == "Funzione JSONL to Vector DB":
            self.run_external_script("jsonltovect3.py")
        elif selected_option == "Gestione Dbase Vettoriale":
            self.run_external_script("delete collection.py")
        elif selected_option == "Download JSONL da Dbase":
            messagebox.showinfo("Funzione non implementata", "Questa funzione è ora gestita nell'interfaccia di ricerca.")
            self.utensili_variable.set("Seleziona uno strumento")
        elif selected_option != "Seleziona uno strumento":
            messagebox.showinfo("Funzione Selezionata", f"Hai selezionato: {selected_option}")

    def run_external_script(self, script_name):
        try:
            subprocess.Popen(["python", script_name])
        except FileNotFoundError:
            messagebox.showerror("Errore", f"Il file '{script_name}' non è stato trovato. Assicurati che si trovi nella stessa cartella dell'interfaccia principale.")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nell'esecuzione dello script:\n{e}")

    def run_search_script(self):
        self.run_external_script("ricerca3.py")

    def run_ollama_script(self):
        self.run_external_script("ollama_go.py")

    def open_config_file(self):
        config_file_path = "config.json"
        if not os.path.exists(config_file_path):
            try:
                default_config = {
                    "model_path": "models/multilingual-e5-large",
                    "qdrant_url": "http://localhost:6333"
                }
                with open(config_file_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                messagebox.showinfo("Configurazione", f"File di configurazione '{config_file_path}' non trovato. Ne è stato creato uno nuovo.")
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile creare il file di configurazione: {e}")
        
        try:
            webbrowser.open(config_file_path)
        except Exception as e:
                messagebox.showerror("Errore", f"Impossibile aprire il file di configurazione: {e}")

    def dummy_function(self):
        messagebox.showinfo("Funzione non implementata", "Questa funzione non è ancora stata implementata.")

    def check_network(self):
        try:
            socket.create_connection(("www.google.com", 80), timeout=3)
            return True
        except OSError:
            return False

    def check_docker(self):
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def check_status(self):
        if self.check_network():
            self.network_led.config(fg="green")
        else:
            self.network_led.config(fg="red")
        
        if self.check_docker():
            self.docker_led.config(fg="green")
        else:
            self.docker_led.config(fg="red")
        
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            model_path = config.get("model_path", "N/A")
            model_name = os.path.basename(model_path)
            if "large" in model_name.lower():
                dimensions = "1024"
            elif "base" in model_name.lower():
                dimensions = "768"
            else:
                dimensions = "Sconosciute"
            
            self.model_label.config(text=f"Modello: {model_name}\nDimensioni: {dimensions}")
        except FileNotFoundError:
            self.model_label.config(text="Modello: N/A\nDimensioni: N/A")
        except json.JSONDecodeError:
            self.model_label.config(text="Errore nel file config.json")
            
        self.after(5000, self.check_status)

if __name__ == "__main__":
    app = VDBaseManager()
    app.mainloop()