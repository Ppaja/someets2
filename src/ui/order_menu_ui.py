# src/ui/order_menu_ui.py
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk 

class OrderMenuOverlay:
    """
    Ein modernes, Always-on-Top Overlay für das Bestellmenü im Spiel.
    Ersetzt das Standard-Tkinter-Fenster für eine bessere Immersion.
    """
    def __init__(self, parent, restaurant_name, required_items, menu, on_confirm_callback, on_cancel_callback):
        self.parent = parent
        self.required_items = required_items
        self.menu = menu
        self.on_confirm_callback = on_confirm_callback
        self.on_cancel_callback = on_cancel_callback

        # --- Fenster-Setup ---
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.wm_attributes("-topmost", True)
        self.window.configure(bg="#1c1c1e")

        width, height = 500, 700 
        x = (self.parent.winfo_screenwidth() // 2) - (width // 2)
        y = (self.parent.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

        # --- Schriftarten ---
        self.title_font = tkfont.Font(family="SF Pro Display", size=24, weight="bold")
        self.item_font = tkfont.Font(family="SF Pro Display", size=14)
        self.total_font = tkfont.Font(family="SF Pro Display", size=16, weight="bold")
        self.button_font = tkfont.Font(family="SF Pro Display", size=14, weight="bold")

        # --- UI Elemente ---
        self.item_quantities = {item['name']: tk.IntVar(value=0) for item in self.menu}
        self.current_total_cost = 0.0
        self.total_cost_display = tk.StringVar(value="0.00€")

        self._create_widgets(restaurant_name)
        self.update_total()

    def _create_widgets(self, restaurant_name):
        # --- Header (Titel & Kundenbestellung) ---
        header_frame = tk.Frame(self.window, bg="#1c1c1e")
        header_frame.pack(fill="x", side="top", pady=(20, 10), padx=20)
        
        tk.Label(header_frame, text=restaurant_name, font=self.title_font, bg="#1c1c1e", fg="white").pack()

        required_frame = tk.Frame(header_frame, bg="#2c2c2e", relief="sunken", borderwidth=1)
        required_frame.pack(fill="x", pady=10)
        tk.Label(required_frame, text="Bestellung vom Kunden:", font=self.item_font, bg="#2c2c2e", fg="#a0a0a0").pack(anchor="w", padx=10, pady=(5,0))
        
        required_list_text = "\n".join([f"• {qty}x {name}" for name, qty in self.required_items.items()])
        tk.Label(required_frame, text=required_list_text, font=self.item_font, bg="#2c2c2e", fg="white", justify="left").pack(anchor="w", padx=20, pady=(0,10))

        # --- Footer (Gesamtpreis & Buttons) ---
        footer_frame = tk.Frame(self.window, bg="#1c1c1e")
        footer_frame.pack(fill="x", side="bottom", pady=20, padx=20)

        total_label = tk.Label(footer_frame, text="Gesamt:", font=self.total_font, bg="#1c1c1e", fg="white")
        total_label.pack(side="left")
        
        total_value_label = tk.Label(footer_frame, textvariable=self.total_cost_display, font=self.total_font, bg="#1c1c1e", fg="#34c759")
        total_value_label.pack(side="left", padx=5)

        confirm_button = tk.Button(footer_frame, text="Kaufen", command=self._confirm, font=self.button_font, bg="#34c759", fg="black", relief="flat", borderwidth=0, padx=20, pady=5)
        confirm_button.pack(side="right")
        
        cancel_button = tk.Button(footer_frame, text="Abbrechen", command=self._cancel, font=self.button_font, bg="#555555", fg="white", relief="flat", borderwidth=0, padx=10, pady=5)
        cancel_button.pack(side="right", padx=10)

        # --- NEU: Scrollbarer Bereich für das Menü ---
        main_frame = tk.Frame(self.window, bg="#1c1c1e")
        main_frame.pack(fill="both", expand=True, padx=20)

        self.menu_canvas = tk.Canvas(main_frame, bg="#1c1c1e", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.menu_canvas.yview)
        self.scrollable_frame = tk.Frame(self.menu_canvas, bg="#1c1c1e")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.menu_canvas.configure(
                scrollregion=self.menu_canvas.bbox("all")
            )
        )

        self.menu_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.menu_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.menu_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Mausrad-Scrollen binden
        self.menu_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Menüpunkte in den neuen scrollbaren Frame einfügen
        for item in self.menu:
            self._create_menu_item_widget(self.scrollable_frame, item)

    def _on_mousewheel(self, event):
        self.menu_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _create_menu_item_widget(self, parent, item):
        item_frame = tk.Frame(parent, bg="#1c1c1e")
        item_frame.pack(fill="x", pady=5)

        item_name = item['name']
        item_price = item['price']
        
        label_text = f"{item_name} ({item_price:.2f}€)"
        tk.Label(item_frame, text=label_text, font=self.item_font, bg="#1c1c1e", fg="white").pack(side="left")

        control_frame = tk.Frame(item_frame, bg="#1c1c1e")
        control_frame.pack(side="right")

        tk.Button(control_frame, text="-", command=lambda name=item_name: self.change_quantity(name, -1), width=2, bg="#444", fg="white", relief="flat").pack(side="left")
        tk.Label(control_frame, textvariable=self.item_quantities[item_name], width=3, font=self.item_font, bg="#2c2c2e", fg="white").pack(side="left", padx=5)
        tk.Button(control_frame, text="+", command=lambda name=item_name: self.change_quantity(name, 1), width=2, bg="#444", fg="white", relief="flat").pack(side="left")

    def change_quantity(self, item_name, delta):
        current_val = self.item_quantities[item_name].get()
        new_val = max(0, current_val + delta)
        self.item_quantities[item_name].set(new_val)
        self.update_total()

    def update_total(self):
        total = 0.0
        for item in self.menu:
            quantity = self.item_quantities[item['name']].get()
            total += quantity * item['price']
        
        self.current_total_cost = total
        self.total_cost_display.set(f"{total:.2f}€")

    def _confirm(self):
        selected_items = {name: var.get() for name, var in self.item_quantities.items() if var.get() > 0}
        total_cost_float = self.current_total_cost
        
        self.on_confirm_callback(selected_items, total_cost_float)
        self.window.destroy()

    def _cancel(self):
        self.on_cancel_callback()
        self.window.destroy()

    def show(self):
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()