import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, MULTIPLE
from PyPDF2 import PdfReader, PdfWriter

class PDFMergerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("PDF Merger - Ordina pagine")
        self.pdf_pages = []  # lista di tuple: (filepath, page_index, label)

        self.btn_load = tk.Button(master, text="Carica PDF", command=self.load_pdfs)
        self.btn_load.pack(pady=5)

        self.listbox = Listbox(master, selectmode=MULTIPLE, width=80)
        self.listbox.pack(padx=10, pady=5)

        self.btn_frame = tk.Frame(master)
        self.btn_frame.pack(pady=5)

        self.btn_up = tk.Button(self.btn_frame, text="⬆ Sposta Su", command=self.move_up)
        self.btn_up.grid(row=0, column=0, padx=5)

        self.btn_down = tk.Button(self.btn_frame, text="⬇ Sposta Giù", command=self.move_down)
        self.btn_down.grid(row=0, column=1, padx=5)

        self.btn_remove = tk.Button(self.btn_frame, text="🗑 Rimuovi Pagina", command=self.remove_page)
        self.btn_remove.grid(row=0, column=2, padx=5)

        self.btn_merge = tk.Button(master, text="📄 Genera PDF", command=self.merge_pdfs)
        self.btn_merge.pack(pady=10)

        # Etichetta versione in basso a destra
        self.footer = tk.Label(master, text="PDF Merger v1.0 - Andrea Cassarino", anchor='e')
        self.footer.pack(side="bottom", anchor="se", padx=10, pady=5)

    def load_pdfs(self):
        filepaths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        for path in filepaths:
            reader = PdfReader(path)
            for i in range(len(reader.pages)):
                label = f"{path.split('/')[-1]} - Pagina {i+1}"
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

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for _, _, label in self.pdf_pages:
            self.listbox.insert(tk.END, label)

    def merge_pdfs(self):
        if not self.pdf_pages:
            messagebox.showwarning("Attenzione", "Nessuna pagina da unire.")
            return

        output_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF file", "*.pdf")])
        if not output_path:
            return

        writer = PdfWriter()
        for path, index, _ in self.pdf_pages:
            reader = PdfReader(path)
            writer.add_page(reader.pages[index])

        with open(output_path, "wb") as f:
            writer.write(f)

        messagebox.showinfo("Successo", f"PDF creato in:\n{output_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFMergerApp(root)
    root.mainloop()