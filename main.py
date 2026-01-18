import random
import tkinter as tk
from tkinter import messagebox
import pulp
import os
import sys

def build_weight_matrix(names, prefs):
    n = len(names)
    index = {names[i]: i for i in range(n)}
    w = [[0] * n for _ in range(n)]
    for a, lst in prefs.items():
        i = index[a]
        for b in lst:
            if b in index:
                j = index[b]
                w[i][j] = 1
    return w


def solve_partition(names, w, N):
    n = len(names)
    G = (n + N - 1) // N

    prob = pulp.LpProblem("max_internal_preferences", pulp.LpMaximize)
    x = {(i, g): pulp.LpVariable(f"x_{i}_{g}", cat="Binary") for i in range(n) for g in range(G)}
    y = {(i, j, g): pulp.LpVariable(f"y_{i}_{j}_{g}", cat="Binary")
         for i in range(n) for j in range(n) if i != j for g in range(G)}

    for i in range(n):
        prob += pulp.lpSum([x[(i, g)] for g in range(G)]) == 1

    for g in range(G):
        prob += pulp.lpSum([x[(i, g)] for i in range(n)]) <= N

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for g in range(G):
                prob += y[(i, j, g)] <= x[(i, g)]
                prob += y[(i, j, g)] <= x[(j, g)]
                prob += y[(i, j, g)] >= x[(i, g)] + x[(j, g)] - 1

    prob += pulp.lpSum(w[i][j] * y[(i, j, g)] for i in range(n) for j in range(n) if i != j for g in range(G))

    cbc_path = None
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = os.path.join(sys._MEIPASS, "pulp", "solverdir", "cbc")
        if sys.platform.startswith("win"):
            cbc_path = os.path.join(base, "win", "i64", "cbc.exe")
        elif sys.platform.startswith("darwin"):
            cbc_path = os.path.join(base, "osx", "cbc")
        elif sys.platform.startswith("linux"):
            cbc_path = os.path.join(base, "linux", "cbc")
        
    if cbc_path and os.path.exists(cbc_path):
        solver = pulp.COIN_CMD(path=cbc_path, msg=False)
    else:
        solver = pulp.PULP_CBC_CMD(msg=False)

    prob.solve(solver)

    groups = {g: [] for g in range(G)}
    for i in range(n):
        for g in range(G):
            if pulp.value(x[(i, g)]) == 1:
                groups[g].append(names[i])
    return groups

class PreferenceApp:
    def __init__(self, root, names, M):
        self.root = root
        self.names = names
        self.M = M
        self.order = names[:]
        random.shuffle(self.order)
        self.index = 0
        self.prefs = {n: [] for n in names}
        self.current_person = None
        self.show_next_person()

    def center_window(self, window, width=500, height=350):
        window.update_idletasks()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def show_next_person(self):
        if self.index >= len(self.order):
            self.root.destroy()
            return

        self.current_person = self.order[self.index]
        self.index += 1

        self.window = tk.Toplevel(self.root)
        self.window.title(f"Turno de {self.current_person}")
        self.center_window(self.window, 500, 350)

        tk.Label(self.window, text=f"{self.current_person}, selecciona {self.M} preferencias").pack(pady=5)

        # Entrada de búsqueda
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_listbox)
        search_entry = tk.Entry(self.window, textvariable=self.search_var)
        search_entry.pack(pady=5)

        # Frame para listas
        lists_frame = tk.Frame(self.window)
        lists_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Listbox de candidatos
        left_frame = tk.Frame(lists_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        tk.Label(left_frame, text="Disponibles").pack()
        self.listbox = tk.Listbox(left_frame, height=10)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-1>", self.add_selection)

        # Listbox de seleccionados
        right_frame = tk.Frame(lists_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)

        tk.Label(right_frame, text="Seleccionados").pack()
        self.selected_listbox = tk.Listbox(right_frame, height=10)
        self.selected_listbox.pack(fill="both", expand=True)

        btn_remove = tk.Button(right_frame, text="Eliminar seleccionado", command=self.remove_selection)
        btn_remove.pack(pady=5)

        # Confirmar
        self.confirm_btn = tk.Button(self.window, text="Confirmar", state="disabled", command=self.confirm)
        self.confirm_btn.pack(pady=10)

        self.selected = []
        self.update_listbox()
        self.window.grab_set()
        search_entry.focus()

    def update_listbox(self, *args):
        search_term = self.search_var.get().lower()
        self.listbox.delete(0, tk.END)
        for name in self.names:
            if name == self.current_person:
                continue
            if name not in self.selected:
                if name.lower().startswith(search_term):
                    self.listbox.insert(tk.END, name)

    def add_selection(self, event=None):
        if len(self.selected) >= self.M:
            messagebox.showwarning("Límite alcanzado", f"Solo puedes elegir {self.M} personas.")
            return
        sel = self.listbox.get(tk.ACTIVE)
        if sel and sel not in self.selected:
            self.selected.append(sel)
            self.selected_listbox.insert(tk.END, sel)
            self.update_listbox()  # refrescar disponibles
        if len(self.selected) == self.M:
            self.confirm_btn.config(state="normal")

    def remove_selection(self):
        sel_idx = self.selected_listbox.curselection()
        if not sel_idx:
            return
        idx = sel_idx[0]
        name = self.selected[idx]
        self.selected.pop(idx)
        self.selected_listbox.delete(idx)
        self.update_listbox()
        self.confirm_btn.config(state="disabled")

    def confirm(self):
        if len(self.selected) != self.M:
            messagebox.showerror("Error", f"Debes seleccionar exactamente {self.M} personas.")
            return
        self.prefs[self.current_person] = self.selected[:]
        self.window.destroy()
        self.show_next_person()


class SetupApp:
    def __init__(self, root):
        self.root = root
        self.names = []
        self.N = None
        self.M = None

        self.window = tk.Toplevel(self.root)
        self.window.title("Configuracion inicial")
        self.center_window(self.window, 520, 320)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        tk.Label(self.window, text="Nombres (separados por comas):").pack(pady=5)
        self.names_var = tk.StringVar()
        self.names_entry = tk.Entry(self.window, textvariable=self.names_var, width=60)
        self.names_entry.pack(pady=5)

        tk.Label(self.window, text="Tamano de cada grupo (N):").pack(pady=5)
        self.n_var = tk.StringVar()
        self.n_entry = tk.Entry(self.window, textvariable=self.n_var, width=10)
        self.n_entry.pack(pady=5)

        tk.Label(self.window, text="Numero de preferencias por persona (M):").pack(pady=5)
        self.m_var = tk.StringVar()
        self.m_entry = tk.Entry(self.window, textvariable=self.m_var, width=10)
        self.m_entry.pack(pady=5)

        self.confirm_btn = tk.Button(self.window, text="Continuar", command=self.confirm)
        self.confirm_btn.pack(pady=15)

        self.window.grab_set()
        self.names_entry.focus()

    def center_window(self, window, width=500, height=350):
        window.update_idletasks()
        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def confirm(self):
        names = [n.strip() for n in self.names_var.get().split(",") if n.strip()]
        if len(names) < 2:
            messagebox.showerror("Error", "Ingresa al menos dos nombres.")
            return

        try:
            n_val = int(self.n_var.get())
            m_val = int(self.m_var.get())
        except ValueError:
            messagebox.showerror("Error", "N y M deben ser numeros enteros.")
            return

        if n_val <= 0 or m_val <= 0:
            messagebox.showerror("Error", "N y M deben ser mayores que cero.")
            return
        if m_val >= len(names):
            messagebox.showerror("Error", "M debe ser menor que la cantidad de nombres.")
            return

        self.names = names
        self.N = n_val
        self.M = m_val
        self.window.destroy()

    def on_close(self):
        self.window.destroy()


def main():
    root = tk.Tk()
    root.withdraw()

    setup = SetupApp(root)
    root.wait_window(setup.window)
    if not setup.names or setup.N is None or setup.M is None:
        root.destroy()
        return

    app = PreferenceApp(root, setup.names, setup.M)
    root.mainloop()
    prefs = app.prefs

    w = build_weight_matrix(setup.names, prefs)
    groups = solve_partition(setup.names, w, setup.N)

    # Mostrar grupos en una ventana
    groups_root = tk.Tk()
    groups_root.title("Grupos Óptimos")
    groups_root.update_idletasks()
    sw = groups_root.winfo_screenwidth()
    sh = groups_root.winfo_screenheight()
    width = 400
    height = 300
    x = (sw // 2) - (width // 2)
    y = (sh // 2) - (height // 2)
    groups_root.geometry(f"{width}x{height}+{x}+{y}")

    text = tk.Text(groups_root, wrap="word")
    text.pack(fill="both", expand=True, padx=10, pady=10)
    for g, members in groups.items():
        text.insert(tk.END, f"Grupo {g+1}: {', '.join(members)}\n")
    text.config(state="disabled")  # hacer solo lectura

    btn = tk.Button(groups_root, text="Cerrar", command=groups_root.destroy)
    btn.pack(pady=5)

    groups_root.mainloop()

if __name__ == "__main__":

    main()
