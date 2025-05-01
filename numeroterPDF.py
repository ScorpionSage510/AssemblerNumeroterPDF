
import threading
from tkinterdnd2 import TkinterDnD, DND_FILES
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import re

# Fonction pour vérifier si une page est déjà numérotée
def is_page_numbered(page_text):
    import re
    return bool(re.search(r"Page\s+\d+\s+/\s+\d+", page_text))

# Fonction pour ajouter les numéros de page à un fichier PDF
def add_page_numbers(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if is_page_numbered(text):
            writer.add_page(page)
        else:
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            width, height = letter
            page_number = f"Page {i + 1} / {len(reader.pages)}"
            can.drawString(width * 0.25, 20, page_number)  # 1/4 de la largeur
            can.save()
            
            packet.seek(0)
            new_pdf = PdfReader(packet)
            page.merge_page(new_pdf.pages[0])
            writer.add_page(page)

    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)

# Fonction pour fusionner plusieurs fichiers PDF
def merge_pdfs(files, output_path):
    writer = PdfWriter()
    total_pages = 0
    total_files = len(files)
    
    for idx, file in enumerate(files):
        reader = PdfReader(file)
        total_pages += len(reader.pages)
        for page in reader.pages:
            writer.add_page(page)

        # Mise à jour de la barre de progression
        progress_bar['value'] = ((idx + 1) / total_files) * 100
        progress_bar.update()  # Met à jour l'interface pour que la barre d'avancement s'affiche correctement

    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    return total_pages

# Génération d'un nom de fichier unique
def generate_unique_filename(base_name, directory):
    base, ext = os.path.splitext(base_name)
    counter = 1
    unique_name = base_name
    while os.path.exists(os.path.join(directory, unique_name)):
        unique_name = f"{base} ({counter}){ext}"
        counter += 1
    return os.path.join(directory, unique_name)

# Fonction pour traiter les fichiers dans un thread
def process_files():
    if not selected_files:
        messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
        return

    merged_file = "merged_temp.pdf"
    output_filename = output_name.get().strip()
    if not output_filename:
        output_filename = "merged_numbered.pdf"
    if output_filename[-4:] != ".pdf":
        output_filename += ".pdf"
    output_file = generate_unique_filename(output_filename, os.getcwd())

    # Démarre le processus dans un thread séparé pour ne pas bloquer l'interface
    processing_thread = threading.Thread(target=process_files_in_thread, args=(merged_file, output_file))
    processing_thread.start()

def process_files_in_thread(merged_file, output_file):
    try:
        # Fusionner les fichiers et ajouter les numéros de page
        total_pages = merge_pdfs(selected_files, merged_file)
        add_page_numbers(merged_file, output_file)
        os.remove(merged_file)
        
        # Mise à jour de la barre de progression (qui est gérée dans le thread principal)
        messagebox.showinfo("Succès", f"{len(selected_files)} fichiers fusionnés ({total_pages} pages) et numérotés : {output_file}")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du traitement : {e}")

# Gestion des fichiers glissés
def drop(event):
    # Nettoyage initial pour enlever les accolades
    raw_data = event.data.strip("{}")
    # Séparer les chemins bruts (peuvent être mal formés)
    files = raw_data.split('}')  # Sépare si plusieurs blocs existent
    files = raw_data.split('{')  # Sépare si plusieurs blocs existent
    cleaned_files = []

    for raw_file in files:
        # Reconstruit correctement les chemins en fusionnant les parties
        if raw_file.strip():
            cleaned_files.append(raw_file.strip().replace("{","").replace("}",""))
    print(cleaned_files)
    add_files(cleaned_files)

# Ajouter les fichiers sélectionnés à la liste
def add_files(files):
    global selected_files
    selected_files = files  # Remplace la liste actuelle par celle des nouveaux fichiers
    update_summary()

# Mettre à jour le résumé des fichiers
def update_summary():
    total_pages = sum(len(PdfReader(file).pages) for file in selected_files)
    summary_label.config(text=f"{len(selected_files)} fichiers sélectionnés, {total_pages} pages au total")

# Sélection de fichiers via le dialogue
def open_files():
    files = filedialog.askopenfilenames(filetypes=[("Fichiers PDF", "*.pdf")])
    if files:
        add_files(files)

# Fonction de réinitialisation
def reset_files():
    global selected_files
    selected_files = []  # Vide la liste des fichiers sélectionnés
    update_summary()
    progress_bar['value'] = 0  # Réinitialise la barre de progression
    messagebox.showinfo("Réinitialisation", "Les fichiers ont été réinitialisés.")

# Interface graphique
root = TkinterDnD.Tk()
root.title("Fusion et Numérotation de Pages PDF")

selected_files = []

frame = tk.Frame(root, width=400, height=300, bg="lightgray")
frame.pack_propagate(False)
frame.pack(padx=20, pady=20)

label = tk.Label(frame, text="Glissez et déposez vos fichiers PDF ici\nou cliquez pour les sélectionner", bg="lightgray", wraplength=300)
label.pack(expand=True)

button_select = tk.Button(frame, text="Sélectionner des fichiers", command=open_files)
button_select.pack(pady=5)

summary_label = tk.Label(frame, text="0 fichiers sélectionnés, 0 pages au total", bg="lightgray")
summary_label.pack(pady=5)

output_name_label = tk.Label(frame, text="Nom du fichier de sortie (sans .pdf) :", bg="lightgray")
output_name_label.pack()

output_name = tk.Entry(frame)
output_name.pack()

button_process = tk.Button(frame, text="Valider", command=process_files, bg="green", fg="white")
button_process.pack(pady=10)

# Ajouter une barre de progression
progress_label = tk.Label(frame, text="Progression", bg="lightgray")
progress_label.pack(pady=5)

progress_bar = ttk.Progressbar(frame, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

# Bouton de réinitialisation
button_reset = tk.Button(frame, text="Réinitialiser", command=reset_files, bg="red", fg="white")
button_reset.pack(pady=5)

# Support de glisser-déposer
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', drop)

root.mainloop()
