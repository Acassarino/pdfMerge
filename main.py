import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, MULTIPLE
from tkinter.ttk import Progressbar
import fitz  # PyMuPDF
import os
import threading
from PIL import Image, ImageTk
import io

class PDFMergerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF Merger - Ordina pagine")
        self.pdf_pages = []  # lista di tuple: (filepath, page_index, label)

        self.btn_load = tk.Button(master, text="Carica PDF", command=self.load_pdfs)
        self.btn_load.pack(pady=5)

        self.listbox = Listbox(master, selectmode=MULTIPLE, width=80)
        self.listbox.pack(padx=10, pady=5)
        self.listbox.bind("<Double-Button-1>", self.preview_page)

        self.btn_frame = tk.Frame(master)
        self.btn_frame.pack(pady=5)

        self.btn_up = tk.Button(self.btn_frame, text="⬆ Sposta Su", command=self.move_up)
        self.btn_up.grid(row=0, column=0, padx=5)

        self.btn_down = tk.Button(self.btn_frame, text="⬇ Sposta Giù", command=self.move_down)
        self.btn_down.grid(row=0, column=1, padx=5)

        self.btn_remove = tk.Button(self.btn_frame, text="🗑 Rimuovi Pagina", command=self.remove_page)
        self.btn_remove.grid(row=0, column=2, padx=5)

        self.btn_remove_all = tk.Button(self.btn_frame, text="🗑 Rimuovi Tutti", command=self.remove_all_pages)
        self.btn_remove_all.grid(row=0, column=3, padx=5)

        self.btn_merge = tk.Button(master, text="📄 Genera PDF", command=self.start_merge_pdfs)
        self.btn_merge.pack(pady=10)

        self.status = tk.Label(master, text="", fg="blue")
        self.status.pack()

        self.progress = Progressbar(master, orient="horizontal", mode="determinate", length=400)
        self.progress.pack(pady=5)

        self.footer = tk.Label(master, text="PDF Merger v1.0 - Andrea Cassarino - ing.acassarino@gmail.com", anchor='e')
        self.footer.pack(side="bottom", anchor="se", padx=5, pady=5)

    def load_pdfs(self):
        filepaths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        for path in filepaths:
            reader = fitz.open(path)
            for i in range(len(reader)):
                label = f"{os.path.basename(path)} - Pagina {i+1}"
                self.pdf_pages.append((path, i, label))
                self.listbox.insert(tk.END, label)

    def move_up(self):
        selected = self.listbox.curselection()
        for i in selected:
            if i == 0:
                continue
            self.pdf_pages[i-1], self.pdf_pages[i] = self.pdf_pages[i], self.pdf_pages[i-1]
            self.refresh_listbox()
            self.listbox.selection_set(i-1)
            break

    def move_down(self):
        selected = self.listbox.curselection()
        for i in selected:
            if i == len(self.pdf_pages) - 1:
                continue
            self.pdf_pages[i+1], self.pdf_pages[i] = self.pdf_pages[i], self.pdf_pages[i+1]
            self.refresh_listbox()
            self.listbox.selection_set(i+1)
            break

    def remove_page(self):
        selected = list(self.listbox.curselection())
        if not selected:
            return
        for i in reversed(selected):
            del self.pdf_pages[i]
        self.refresh_listbox()

    def remove_all_pages(self):
        self.pdf_pages.clear()
        self.refresh_listbox()

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for _, _, label in self.pdf_pages:
            self.listbox.insert(tk.END, label)

    def preview_page(self, event):
        selected = self.listbox.curselection()
        if not selected:
            return

        index = selected[0]
        path, page_index, label = self.pdf_pages[index]

        try:
            doc = fitz.open(path)
            page = doc.load_page(page_index)
            zoom = 2
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))

            # Ridimensionamento
            screen_w = self.master.winfo_screenwidth()
            screen_h = self.master.winfo_screenheight()
            max_w, max_h = screen_w - 100, screen_h - 100
            if image.width > max_w or image.height > max_h:
                image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)

        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile caricare l'anteprima:\n{str(e)}")
            return

        preview_win = tk.Toplevel(self.master)
        preview_win.title(label)

        canvas = tk.Canvas(preview_win)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(preview_win, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor='nw')

        lbl = tk.Label(frame, image=photo)
        lbl.image = photo
        lbl.pack()

        preview_win.geometry(f"{image.width + 40}x{image.height + 40}")

    def start_merge_pdfs(self):
        # Avviare il thread separato per la fusione dei PDF
        merge_thread = threading.Thread(target=self.merge_pdfs)
        merge_thread.start()

    def merge_pdfs(self):
        if not self.pdf_pages:
            messagebox.showwarning("Attenzione", "Nessuna pagina da unire.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")])
        if not output_path:
            return

        # Aggiorna la UI con messaggio e barra di progresso
        self.update_status("Sto generando il PDF...", 0)

        doc = fitz.open()

        for i, (path, index, _) in enumerate(self.pdf_pages):
            src = fitz.open(path)
            page = src.load_page(index)
            doc.insert_pdf(src, from_page=index, to_page=index)  # Usa insert_pdf per copiare la pagina

            # Aggiorna la progress bar
            self.update_progress(i + 1, len(self.pdf_pages))

        doc.save(output_path)
        doc.close()

        # Aggiorna la UI con il risultato
        self.update_status("Unione completata!", 0)
        messagebox.showinfo("Successo", f"PDF creato:\n{output_path}")

    def update_status(self, text, progress_value):
        self.status.config(text=text)
        self.progress["value"] = progress_value
        self.master.update_idletasks()

    def update_progress(self, value, maximum):
        self.progress["maximum"] = maximum
        self.progress["value"] = value
        self.master.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFMergerApp(root)
    root.mainloop()