"""
TODO:
Afficher le nombre de page total

python -m nuitka --standalone --enable-plugin=tk-inter --windows-disable-console --windows-icon-from-ico="app_icon.ico" numeroterpdf.py

python -m nuitka --standalone --onefile --enable-plugin=tk-inter --windows-icon-from-ico="app_icon.ico" numeroterpdf.py
--windows-disable-console

"""

# -*- coding: utf-8 -*- # Encodoing utf-8 pour les accents
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import os
import threading
import time
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
import re

# --- Constantes ---
APP_TITLE = "PDF Fusion & Numérotation Pro v2.1 (Style Icône)"
DEFAULT_OUTPUT_FILENAME = "fusion_resultat.pdf"
ICON_FILE = "app_icon.ico" # Chemin vers votre icône
ESTIMATED_PROCESSING_RATE_BPS = 512 * 1024

# --- Couleurs pour le style (inspirées de l'icône) ---
COLOR_PRIMARY_ACCENT = "#20C2FF" # Cyan / Bleu clair vibrant
COLOR_SECONDARY_ACCENT = "#1E90FF" # Bleu plus soutenu (pour hover/active)
COLOR_BACKGROUND = "#FFFFFF"     # Fond principal blanc
COLOR_WIDGET_BACKGROUND = "#F0F5FA" # Fond légèrement bleuté/gris clair pour listes, entrées
COLOR_TEXT_DARK = "#212529"      # Texte principal sombre (presque noir)
COLOR_TEXT_LIGHT = "#FFFFFF"     # Texte sur les boutons colorés
COLOR_BORDER = "#A0B0C0"        # Bordure neutre/grise
COLOR_DISABLED_BG = "#D5E0EB"    # Fond pour éléments désactivés
COLOR_DISABLED_FG = "#78899A"    # Texte pour éléments désactivés
COLOR_PROGRESS_BAR = COLOR_PRIMARY_ACCENT # Couleur de la barre de progression

# --- Exception Personnalisée ---
class ProcessingInterruptedException(Exception):
    pass

# --- Logique Métier (INCHANGÉE PAR RAPPORT À LA VERSION PRÉCÉDENTE) ---
def is_page_numbered(page_text):
    return bool(re.search(r"Page\s+\d+\s+/\s+\d+", page_text, re.IGNORECASE))

def add_page_numbers(input_stream, output_pdf_path, progress_callback=None, stop_event=None):
    # ... (code inchangé) ...
    try:
        reader = PdfReader(input_stream)
        writer = PdfWriter()
        total_pages_doc = len(reader.pages)
        if total_pages_doc == 0:
            raise ValueError("Le document source pour la numérotation ne contient aucune page.")
        for i, page in enumerate(reader.pages):
            if stop_event and stop_event.is_set():
                raise ProcessingInterruptedException("Numérotation interrompue par l'utilisateur.")
            packet = BytesIO()
            original_page_width = float(page.mediabox.width)
            original_page_height = float(page.mediabox.height)
            can = canvas.Canvas(packet, pagesize=(original_page_width, original_page_height))
            page_number_text = f"Page {i + 1} / {total_pages_doc}"
            text_width = can.stringWidth(page_number_text, "Helvetica", 9)
            x_position = (original_page_width - text_width) / 2
            y_position = 20
            can.setFont("Helvetica", 9)
            can.drawString(x_position, y_position, page_number_text)
            can.save()
            packet.seek(0)
            new_pdf_reader = PdfReader(packet)
            overlay_page = new_pdf_reader.pages[0]
            page.merge_page(overlay_page)
            writer.add_page(page)
            if progress_callback:
                progress = 50 + ((i + 1) / total_pages_doc) * 50
                progress_callback(progress)
        if not writer.pages:
             raise ValueError("Aucune page n'a été générée pendant la numérotation.")
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)
    except ProcessingInterruptedException: raise
    except Exception as e:
        print(f"Erreur dans add_page_numbers: {e}")
        raise

def merge_pdfs(files, output_stream, progress_callback=None, stop_event=None):
    # ... (code inchangé) ...
    try:
        writer = PdfWriter()
        total_files = len(files)
        current_total_pages = 0
        for idx, file_path in enumerate(files):
            if stop_event and stop_event.is_set():
                raise ProcessingInterruptedException("Fusion interrompue par l'utilisateur.")
            try:
                reader = PdfReader(file_path)
                if reader.is_encrypted:
                    try: reader.decrypt('')
                    except Exception:
                        messagebox.showwarning("PDF Chiffré", f"Le fichier {os.path.basename(file_path)} est chiffré et protégé. Il sera ignoré.")
                        if progress_callback:
                             progress = ((idx + 1) / total_files) * 50
                             progress_callback(progress)
                        continue
                num_pages_in_file = len(reader.pages)
                for page in reader.pages:
                    writer.add_page(page)
                current_total_pages += num_pages_in_file
            except FileNotFoundError:
                messagebox.showerror("Erreur Fichier", f"Fichier non trouvé : {os.path.basename(file_path)}. Il sera ignoré.")
                continue
            except Exception as file_error:
                messagebox.showerror("Erreur Fichier", f"Impossible de lire le fichier {os.path.basename(file_path)}: {file_error}. Il sera ignoré.")
                continue
            if progress_callback:
                progress = ((idx + 1) / total_files) * 50
                progress_callback(progress)
        if not writer.pages:
             raise ValueError("Aucune page n'a pu être ajoutée. Vérifiez les fichiers PDF sélectionnés.")
        writer.write(output_stream)
        return current_total_pages
    except ProcessingInterruptedException: raise
    except Exception as e:
        print(f"Erreur dans merge_pdfs: {e}")
        raise

# --- Interface Graphique (Application Class - AVEC STYLE) ---

class PdfToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        # Définit la couleur de fond de la fenêtre principale
        self.root.config(bg=COLOR_BACKGROUND)
        try:
            self.root.iconbitmap(ICON_FILE)
        except tk.TclError:
            print(f"Avertissement : Impossible de charger l'icône '{ICON_FILE}'.")
        except Exception as e:
            print(f"Erreur icône : {e}")

        self.root.geometry("650x600")
        self.root.minsize(550, 450)

        self.selected_files = []
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.start_time = 0

        self.numbering_enabled = tk.BooleanVar(value=True)

        # --- Configuration du Style TTK ---
        self.style = ttk.Style()
        self.style.theme_use('clam') # Base moderne

        # Configurer les couleurs globales
        self.style.configure('.', background=COLOR_BACKGROUND, foreground=COLOR_TEXT_DARK) # Pour tous les widgets ttk
        self.style.configure('TFrame', background=COLOR_BACKGROUND)
        self.style.configure('TLabel', background=COLOR_BACKGROUND, foreground=COLOR_TEXT_DARK)

        # Style des Boutons
        self.style.configure('TButton',
                             background=COLOR_PRIMARY_ACCENT,
                             foreground=COLOR_TEXT_LIGHT,
                             font=('Helvetica', 10, 'bold'),
                             padding=(10, 5), # Plus d'espace intérieur
                             borderwidth=0, # Look plat
                             relief=tk.FLAT) # Important pour borderwidth=0
        self.style.map('TButton',
                       background=[('active', COLOR_SECONDARY_ACCENT), # Hover/Press
                                   ('disabled', COLOR_DISABLED_BG)],
                       foreground=[('disabled', COLOR_DISABLED_FG)])

        # Style des LabelFrame (Cadres avec titre)
        self.style.configure('TLabelframe',
                             background=COLOR_BACKGROUND,
                             borderwidth=1,
                             relief=tk.SOLID) # Bordure visible simple
        self.style.configure('TLabelframe.Label',
                             background=COLOR_BACKGROUND,
                             foreground=COLOR_SECONDARY_ACCENT, # Titre en bleu soutenu
                             font=('Helvetica', 11, 'bold'))

        # Style des Champs de saisie (Entry)
        self.style.configure('TEntry',
                             fieldbackground=COLOR_WIDGET_BACKGROUND, # Fond du champ
                             foreground=COLOR_TEXT_DARK,
                             borderwidth=1,
                             relief=tk.SOLID) # Bordure simple
        self.style.map('TEntry',
                       bordercolor=[('focus', COLOR_PRIMARY_ACCENT)], # Bordure cyan quand focus
                       relief=[('focus', tk.SOLID)])

        # Style des Cases à cocher (Checkbutton)
        # 'indicatorcolor' contrôle la couleur de la case elle-même
        # 'background' et 'foreground' pour le widget entier
        self.style.configure('TCheckbutton',
                             background=COLOR_BACKGROUND,
                             foreground=COLOR_TEXT_DARK,
                             indicatorrelief=tk.FLAT,
                             indicatormargin=-2, # Ajustement fin
                             padding=5)
        self.style.map('TCheckbutton',
                       indicatorcolor=[('selected', COLOR_PRIMARY_ACCENT), # Case cochée en cyan
                                       ('!selected', COLOR_WIDGET_BACKGROUND)], # Case non cochée
                       background=[('active', COLOR_WIDGET_BACKGROUND)]) # Léger fond au survol

        # Style de la Barre de progression
        self.style.configure('Horizontal.TProgressbar',
                             troughcolor=COLOR_WIDGET_BACKGROUND, # Fond de la barre
                             background=COLOR_PROGRESS_BAR,     # Couleur de progression
                             borderwidth=0,
                             relief=tk.FLAT)

        # Style des Scrollbars (pas toujours bien pris en compte par tous les thèmes)
        self.style.configure('TScrollbar',
                             troughcolor=COLOR_WIDGET_BACKGROUND,
                             background=COLOR_BORDER, # La barre elle-même (le "slider")
                             borderwidth=0,
                             arrowcolor=COLOR_SECONDARY_ACCENT, # Couleur des flèches
                             relief=tk.FLAT)
        self.style.map('TScrollbar',
                       background=[('active', COLOR_SECONDARY_ACCENT)]) # Slider actif

        # --- Création des widgets (utilise les styles ttk définis) ---
        self.create_widgets()
        self.update_ui_state()

    def create_widgets(self):
        # --- Cadre principal (utilise TFrame, donc style appliqué) ---
        main_frame = ttk.Frame(self.root, padding="15") # Plus de padding général
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # --- Sélection et Ordre des fichiers (utilise TLabelframe) ---
        select_frame = ttk.LabelFrame(main_frame, text="1. Fichiers à traiter (ordre important)", padding="10")
        select_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 10)) # Espace après
        select_frame.columnconfigure(0, weight=1)
        select_frame.columnconfigure(2, weight=0)

        select_buttons_frame = ttk.Frame(select_frame) # Utilise TFrame stylé
        select_buttons_frame.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10)) # Espace après

        self.btn_select = ttk.Button(select_buttons_frame, text="Ajouter des PDF...", command=self.select_files_dialog)
        self.btn_select.pack(side=tk.LEFT, padx=(0, 5)) # Pas de padx avant le 1er

        self.btn_reset_list = ttk.Button(select_buttons_frame, text="Vider la liste", command=self.reset_file_list)
        self.btn_reset_list.pack(side=tk.LEFT, padx=5)

        list_control_frame = ttk.Frame(select_frame)
        list_control_frame.grid(row=1, column=0, columnspan=3, sticky="nsew")
        list_control_frame.rowconfigure(0, weight=1)
        list_control_frame.columnconfigure(0, weight=1)

        # --- Listbox (Widget TK standard, à styler manuellement) ---
        self.listbox_files = tk.Listbox(list_control_frame,
                                       selectmode=tk.SINGLE,
                                       height=10,
                                       activestyle='dotbox',
                                       bg=COLOR_WIDGET_BACKGROUND, # Fond manuel
                                       fg=COLOR_TEXT_DARK,         # Texte manuel
                                       selectbackground=COLOR_SECONDARY_ACCENT, # Sélection bleu soutenu
                                       selectforeground=COLOR_TEXT_LIGHT,       # Texte sélection blanc
                                       highlightthickness=1,          # Bordure fine
                                       highlightcolor=COLOR_BORDER,     # Couleur bordure normale
                                       highlightbackground=COLOR_WIDGET_BACKGROUND,
                                       borderwidth=0,               # Pas de bordure 3D
                                       relief=tk.FLAT)             # Style plat
        self.listbox_files.grid(row=0, column=0, sticky="nsew")
        self.listbox_files.bind('<<ListboxSelect>>', lambda e: self.update_order_buttons_state())

        # Scrollbars (utilisent TScrollbar stylé)
        scrollbar_y = ttk.Scrollbar(list_control_frame, orient=tk.VERTICAL, command=self.listbox_files.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.listbox_files.config(yscrollcommand=scrollbar_y.set)
        scrollbar_x = ttk.Scrollbar(list_control_frame, orient=tk.HORIZONTAL, command=self.listbox_files.xview)
        scrollbar_x.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.listbox_files.config(xscrollcommand=scrollbar_x.set)

        list_order_buttons = ttk.Frame(list_control_frame)
        list_order_buttons.grid(row=0, column=2, sticky="ns", padx=(10, 0)) # Plus d'espace

        self.btn_up = ttk.Button(list_order_buttons, text="Monter", command=self.move_file_up)
        self.btn_up.pack(padx=2, pady=(0, 3), fill=tk.X) # Espace entre boutons
        self.btn_down = ttk.Button(list_order_buttons, text="Descendre", command=self.move_file_down)
        self.btn_down.pack(padx=2, pady=3, fill=tk.X)

        # --- Options (utilise TLabelframe, TCheckbutton) ---
        options_frame = ttk.LabelFrame(main_frame, text="2. Options", padding="10")
        options_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=10)
        options_frame.columnconfigure(1, weight=1)

        self.chk_numbering = ttk.Checkbutton(options_frame, text="Numéroter les pages (format 'Page X / Y')",
                                             variable=self.numbering_enabled, command=self.update_button_text)
        self.chk_numbering.grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        # --- Nom de sortie (utilise TLabelframe, TLabel, TEntry) ---
        output_frame = ttk.LabelFrame(main_frame, text="3. Fichier de sortie", padding="10")
        output_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=10)
        output_frame.columnconfigure(1, weight=1)

        lbl_output_name = ttk.Label(output_frame, text="Nom :")
        lbl_output_name.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_output_name = ttk.Entry(output_frame, font=('Helvetica', 10)) # Police standard pour entry
        self.entry_output_name.insert(0, os.path.splitext(DEFAULT_OUTPUT_FILENAME)[0])
        self.entry_output_name.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        lbl_output_ext = ttk.Label(output_frame, text=".pdf")
        lbl_output_ext.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        # --- Contrôles Lancement / Interruption (utilise TFrame, TButton) ---
        control_frame = ttk.Frame(main_frame, padding=(10, 5)) # Moins de padding vertical
        control_frame.grid(row=4, column=0, sticky="ew")
        control_frame.columnconfigure((0, 1), weight=1)

        self.btn_process = ttk.Button(control_frame, text="Lancer", command=self.start_processing)
        self.btn_process.grid(row=0, column=0, padx=10, pady=5, sticky="e")

        self.btn_interrupt = ttk.Button(control_frame, text="Interrompre", command=self.request_stop, state=tk.DISABLED)
        self.btn_interrupt.grid(row=0, column=1, padx=10, pady=5, sticky="w")


        # --- Statut et Progression (utilise TFrame, TLabel, TProgressbar) ---
        status_frame = ttk.Frame(main_frame, padding="5")
        status_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0)) # Espace avant
        status_frame.columnconfigure(0, weight=1)

        self.lbl_status = ttk.Label(status_frame, text="Prêt. Sélectionnez des fichiers PDF.", anchor="w") # Align left
        self.lbl_status.grid(row=0, column=0, sticky="ew", padx=5)

        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=300, mode="determinate", style='Horizontal.TProgressbar')
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Initial update
        self.update_file_listbox()
        self.update_button_text()


    # --- Méthodes de l'interface (INCHANGÉES PAR RAPPORT À LA VERSION PRÉCÉDENTE) ---

    def select_files_dialog(self):
        # ... (code inchangé) ...
        files = filedialog.askopenfilenames(
            title="Sélectionnez les fichiers PDF à ajouter",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
        )
        if files:
            added_count = 0
            for f in files:
                if f not in self.selected_files:
                    self.selected_files.append(f)
                    added_count += 1
            if added_count > 0:
                self.update_file_listbox()
                self.update_ui_state()
                self.set_status(f"{added_count} fichier(s) ajouté(s). Total : {len(self.selected_files)}.")
            else:
                self.set_status(f"Aucun nouveau fichier ajouté. Total : {len(self.selected_files)}.")

    def reset_file_list(self):
        # ... (code inchangé) ...
        if not self.selected_files: return
        if messagebox.askyesno("Vider la liste", "Voulez-vous vraiment supprimer tous les fichiers de la liste ?"):
            self.selected_files = []
            self.update_file_listbox()
            self.update_ui_state()
            self.set_status("Liste des fichiers vidée. Prêt.", clear_progress=True)

    def update_file_listbox(self):
        # ... (code inchangé) ...
        self.listbox_files.delete(0, tk.END)
        if not self.selected_files:
            self.listbox_files.insert(tk.END, "  (Aucun fichier sélectionné)")
            self.listbox_files.itemconfig(0, {'fg': COLOR_DISABLED_FG}) # Utiliser couleur désactivée
        else:
            for i, file_path in enumerate(self.selected_files):
                self.listbox_files.insert(tk.END, f"  {i+1}. {os.path.basename(file_path)}")
        self.update_order_buttons_state()

    def update_order_buttons_state(self):
        # ... (code inchangé) ...
        selected_indices = self.listbox_files.curselection()
        can_move_up = False
        can_move_down = False
        if len(selected_indices) == 1:
            idx = selected_indices[0]
            if idx > 0: can_move_up = True
            if idx < len(self.selected_files) - 1: can_move_down = True
        is_processing = self.processing_thread is not None and self.processing_thread.is_alive()
        self.btn_up.config(state=tk.NORMAL if can_move_up and not is_processing else tk.DISABLED)
        self.btn_down.config(state=tk.NORMAL if can_move_down and not is_processing else tk.DISABLED)

    def move_file_up(self):
        # ... (code inchangé) ...
        selected_indices = self.listbox_files.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx > 0:
            self.selected_files[idx], self.selected_files[idx-1] = self.selected_files[idx-1], self.selected_files[idx]
            self.update_file_listbox()
            self.listbox_files.selection_set(idx-1)
            self.listbox_files.activate(idx-1)
            self.listbox_files.see(idx-1)
            self.update_order_buttons_state()

    def move_file_down(self):
        # ... (code inchangé) ...
        selected_indices = self.listbox_files.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx < len(self.selected_files) - 1:
            self.selected_files[idx], self.selected_files[idx+1] = self.selected_files[idx+1], self.selected_files[idx]
            self.update_file_listbox()
            self.listbox_files.selection_set(idx+1)
            self.listbox_files.activate(idx+1)
            self.listbox_files.see(idx+1)
            self.update_order_buttons_state()

    def update_button_text(self):
        # ... (code inchangé) ...
        if self.numbering_enabled.get():
            self.btn_process.config(text="Fusionner ET Numéroter")
        else:
            self.btn_process.config(text="Fusionner Uniquement")

    def update_ui_state(self):
        # ... (code inchangé) ...
        has_files = bool(self.selected_files)
        is_processing = self.processing_thread is not None and self.processing_thread.is_alive()
        state_normal = tk.NORMAL if not is_processing else tk.DISABLED
        state_disabled = tk.DISABLED
        self.btn_select.config(state=state_normal)
        self.btn_reset_list.config(state=tk.NORMAL if has_files and not is_processing else state_disabled)
        self.btn_process.config(state=tk.NORMAL if has_files and not is_processing else state_disabled)
        self.btn_interrupt.config(state=tk.NORMAL if is_processing else state_disabled)
        self.entry_output_name.config(state=state_normal)
        self.chk_numbering.config(state=state_normal)
        self.listbox_files.config(state=state_normal) # Tk Listbox state
        # Also update listbox colors visually if disabled
        if is_processing:
            self.listbox_files.config(bg=COLOR_DISABLED_BG, fg=COLOR_DISABLED_FG, selectbackground=COLOR_DISABLED_BG)
        else:
             self.listbox_files.config(bg=COLOR_WIDGET_BACKGROUND, fg=COLOR_TEXT_DARK, selectbackground=COLOR_SECONDARY_ACCENT)

        self.update_order_buttons_state() # Gère Up/Down

    def set_status(self, message, clear_progress=False):
        # ... (code inchangé) ...
        self.lbl_status.config(text=message)
        if clear_progress:
            self.progress_bar['value'] = 0
            self.progress_bar['maximum'] = 100
        self.root.update_idletasks()

    def update_progress(self, value):
        # ... (code inchangé) ...
        if self.stop_event.is_set():
            raise ProcessingInterruptedException("Traitement interrompu pendant la mise à jour de la progression.")
        self.root.after(0, self._set_progress_and_time, value)

    def _set_progress_and_time(self, value):
        # ... (code inchangé) ...
        if not (0 <= value <= 100): value = max(0, min(100, value))
        self.progress_bar['value'] = value
        time_remaining_str = ""
        if self.start_time > 0 and 1 < value < 100 :
            elapsed_time = time.time() - self.start_time
            estimated_total_time = (elapsed_time / value) * 100
            remaining_seconds = max(0, estimated_total_time - elapsed_time)
            if remaining_seconds < 60: time_remaining_str = f"{remaining_seconds:.0f} sec"
            elif remaining_seconds < 3600: time_remaining_str = f"{remaining_seconds / 60:.0f} min {remaining_seconds % 60:.0f} sec"
            else:
                hours = int(remaining_seconds / 3600); minutes = int((remaining_seconds % 3600) / 60)
                time_remaining_str = f"{hours} h {minutes} min"
            time_remaining_str = f" - Restant: ~{time_remaining_str}"

        current_status = self.lbl_status.cget("text").split('-')[0].strip()
        base_status_keywords = ["Étape", "Fusion", "Numérotation", "Sauvegarde"]
        if any(keyword in current_status for keyword in base_status_keywords):
             self.lbl_status.config(text=f"{current_status} ({value:.0f}%) {time_remaining_str}")
        self.root.update_idletasks()


    def start_processing(self):
        # ... (code inchangé) ...
        if not self.selected_files:
            messagebox.showwarning("Aucun fichier", "Veuillez ajouter au moins un fichier PDF à la liste.", parent=self.root)
            return
        output_base_name = self.entry_output_name.get().strip()
        if not output_base_name: output_base_name = os.path.splitext(DEFAULT_OUTPUT_FILENAME)[0]
        output_filename_with_ext = f"{output_base_name}.pdf"
        initial_dir = os.path.dirname(self.selected_files[0]) if self.selected_files else os.getcwd()
        output_path = filedialog.asksaveasfilename(
            title="Enregistrer le fichier PDF résultant", initialdir=initial_dir, initialfile=output_filename_with_ext,
            defaultextension=".pdf", filetypes=[("Fichiers PDF", "*.pdf")], parent=self.root
        )
        if not output_path:
            self.set_status("Sauvegarde annulée.")
            return
        self.stop_event.clear()
        self.progress_bar['value'] = 0
        self.start_time = time.time()
        self.set_status("Préparation...")
        self.update_ui_state()
        files_to_process = list(self.selected_files)
        perform_numbering = self.numbering_enabled.get()
        self.processing_thread = threading.Thread(
            target=self.process_files_thread_target,
            args=(files_to_process, output_path, perform_numbering, self.stop_event), daemon=True
        )
        self.processing_thread.start()
        self.check_thread()

    def request_stop(self):
        # ... (code inchangé) ...
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set()
            self.set_status("Interruption demandée...")
            self.btn_interrupt.config(state=tk.DISABLED)

    def process_files_thread_target(self, files_to_process, final_output_path, perform_numbering, stop_event):
        # ... (code inchangé) ...
        merged_stream = BytesIO()
        total_pages = 0
        try:
            self.root.after(0, self.set_status, "Étape 1/X : Fusion des fichiers...")
            total_pages = merge_pdfs(files_to_process, merged_stream, self.update_progress, stop_event)
            merged_stream.seek(0)
            if stop_event.is_set(): raise ProcessingInterruptedException("Fusion terminée mais interruption demandée avant numérotation.")
            if perform_numbering:
                self.root.after(0, self.set_status, f"Étape 2/2 : Numérotation des {total_pages} pages...")
                add_page_numbers(merged_stream, final_output_path, self.update_progress, stop_event)
                self.root.after(0, self.on_processing_complete, final_output_path, len(files_to_process), total_pages, True)
            else:
                self.root.after(0, self.set_status, "Étape 1/1 : Sauvegarde du fichier fusionné...")
                self.root.after(0, self._set_progress_and_time, 100)
                with open(final_output_path, 'wb') as f_out: f_out.write(merged_stream.getvalue())
                self.root.after(0, self.on_processing_complete, final_output_path, len(files_to_process), total_pages, False)
        except ProcessingInterruptedException as ie: self.root.after(0, self.on_processing_interrupted, str(ie))
        except Exception as e: self.root.after(0, self.on_processing_error, e)
        finally: merged_stream.close()

    def check_thread(self):
        # ... (code inchangé) ...
        if self.processing_thread is not None and self.processing_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            if self.processing_thread is not None:
                is_interrupted = self.stop_event.is_set() # Check if it was stopped via interruption
                self.processing_thread = None
                self.start_time = 0
                 # If not interrupted and progress not 100, reset progress bar
                if not is_interrupted and self.progress_bar['value'] < 100 :
                      self.progress_bar['value'] = 0
                self.update_ui_state() # Ensure UI is re-enabled


    def on_processing_complete(self, output_file, num_files, num_pages, was_numbered):
        # ... (code inchangé) ...
        self.progress_bar['value'] = 100
        action_str = "fusionné(s)" + (" et numéroté(s)" if was_numbered else "")
        self.set_status("Terminé avec succès.", clear_progress=False)
        self.processing_thread = None; self.start_time = 0
        self.update_ui_state()
        messagebox.showinfo("Succès",
                            f"{num_files} fichier(s) {action_str} ({num_pages} pages au total).\n\n"
                            f"Fichier enregistré sous :\n{output_file}", parent=self.root)

    def on_processing_error(self, error):
        # ... (code inchangé) ...
        error_message = f"Une erreur est survenue :\n\n{error}"
        self.set_status("Erreur.", clear_progress=True)
        self.processing_thread = None; self.start_time = 0
        self.update_ui_state()
        messagebox.showerror("Erreur de traitement", error_message, parent=self.root)

    def on_processing_interrupted(self, message="Traitement interrompu par l'utilisateur."):
        # ... (code inchangé) ...
        self.set_status("Interrompu.", clear_progress=True)
        self.processing_thread = None; self.start_time = 0
        self.update_ui_state()
        messagebox.showwarning("Interruption", message, parent=self.root)


# --- Point d'entrée ---
if __name__ == "__main__":
    root = tk.Tk()
    app = PdfToolApp(root)
    # Pas besoin de lier ListboxSelect ici car on met déjà à jour dans update_file_listbox
    root.mainloop()