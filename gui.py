import io
import tkinter as tk
import tkinter.ttk as ttk
import urllib.request
from tkinter import messagebox
from tkinter.filedialog import asksaveasfile, askopenfile
from urllib import error
import pyglet
import ctypes
from PIL import ImageTk, Image
from pokemon import *
import socket
import webbrowser
import requests

# import fonts used in a program
try:
    pokemon_font_path = os.path.abspath("Fonts\\Pokemon Solid.ttf")
    default_font_path = os.path.abspath("Fonts\\IBMPlexMono-Light.ttf")
    pyglet.font.add_file(pokemon_font_path)
    pyglet.font.add_file(default_font_path)
    pokemon_font = "Pokemon Solid"
    default_font = "IBMPlexMono-Light"
except FileNotFoundError:
    default_font = "Arial"
    pokemon_font = "Arial"

generations = ["I - Kanto", "II - Johto", "III - Hoenn", "IV - Sinnoh", "V - Unova", "VI - Kalos", "VII - Alola",
               "VIII - Galar"]

type_color = {
    "Normal": "#A8A77A",
    "Fire": "#EE8130",
    "Water": "#6390F0",
    "Electric": "#F7D02C",
    "Grass": "#7AC74C",
    "Ice": "#96D9D6",
    "Fighting": "#C22E28",
    "Poison": "#A33EA1",
    "Ground": "#E2BF65",
    "Flying": "#A98FF3",
    "Psychic": "#F95587",
    "Bug": "#A6B91A",
    "Rock": "#B6A136",
    "Ghost": "#735797",
    "Dragon": "#6F35FC",
    "Dark": "#705746",
    "Steel": "#B7B7CE",
    "Fairy": "#D685AD"
}


def stat_color(value):
    if 0 < value < 60:
        return "#ff0000"
    elif 60 <= value < 80:
        return "#ff4c00"
    elif 80 <= value < 100:
        return "#ff9800"
    elif 100 <= value < 115:
        return "#fffe00"
    elif 115 <= value < 125:
        return "#8aff00"
    elif 125 <= value < 140:
        return "#52ff00"
    elif 140 <= value < 160:
        return "#2aff08"
    else:
        return "#02ffff"


class MainWindow(tk.Tk):
    __config_file = "startup.config"
    __modes = ["pokemon", "weakness"]
    __pepedex_image = "Images\\pepedex.png"
    __icon_image = "Images/logo.ico"
    __program_id = f"{socket.gethostname()}.PepeDex.version1"

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.bind("<F11>", lambda e: self.__toggle_fullscreen())
        self.bind("<Escape>", lambda e: self.__quit_fullscreen())
        self.protocol("WM_DELETE_WINDOW", self.__on_close)
        self.state("zoomed")
        self.fullscreen = False
        self.winfo_toplevel().title("PepeDex")
        self.geometry("1000x550")
        self.minsize(1000, 500)

        # setting app id so that icon is displayed on the task bar
        app_id = self.__program_id
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        try:
            icon_path = os.path.abspath(self.__icon_image)
            self.iconbitmap(icon_path)
        except (OSError, FileNotFoundError):
            print("Failed loading icon")

        # LOADING LAST SAVED VALUES IF THEY EXIST

        entry_message = "Welcome to PepeDex! Use 'Help' (Ctrl-H) if you are stuck"
        default_values = self.__on_start()
        default_mode = "pokemon"
        default_name = ""
        default_primary = ""
        default_secondary = ""
        default_generation = ""
        default_sort = 0

        if default_values is not None and len(default_values) == 6:
            default_mode = default_values[0] if default_values[0] in self.__modes else "pokemon"
            possible_types = [""] + Types.get_types_string_list()
            default_name = default_values[1]
            default_primary = default_values[2] if default_values[2] in possible_types else ""
            default_secondary = default_values[3] if default_values[3] in possible_types else ""
            default_generation = default_values[4] if default_values[4] in generations else ""
            default_sort = default_values[5] if default_values[5] in ["0", "1"] else "0"
            default_sort = int(default_sort)
            entry_message = f"Welcome back to PepeDex! Loaded Pokemon filters and opened " \
                            f"{proper_word(default_mode)} mode"

        # CREATING MENU

        self.main_menu = tk.Menu(self)
        self.file_menu = tk.Menu(self.main_menu, tearoff=0, border=8, relief="flat")
        self.file_menu.add_command(label="Open", command=self.__on_open, accelerator="Ctrl-O")
        self.bind("<Control-o>", lambda e: self.__on_open())
        self.file_menu.add_command(label="Save", command=self.__on_save, accelerator="Ctrl-S")
        self.bind("<Control-s>", lambda e: self.__on_save())
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quit", command=self.__on_close, accelerator="Ctrl-Q")
        self.bind("<Control-q>", lambda e: self.__on_close())
        self.main_menu.add_cascade(label=" File ", menu=self.file_menu)
        self.help_window = False
        self.main_menu.add_command(label="Help", command=self.__display_help)
        self.bind("<Control-h>", lambda e: self.__display_help())
        self.config(menu=self.main_menu)

        # LOGO

        try:
            image_path = os.path.abspath(self.__pepedex_image)
            self.img = ImageTk.PhotoImage(Image.open(image_path))
            program_name = tk.Label(self, height=100, image=self.img, borderwidth=4, relief='sunken')
            program_name.config(background='#cf291d')
            program_name.pack(side=tk.TOP, fill='x')
        except (OSError, FileNotFoundError):
            print("Failed to load logo")

        # BUTTONS TO SWITCH MODES

        self.mode_switcher = tk.Frame(self)
        self.mode_switcher.pack(side=tk.TOP, fill='x')
        self.mode_switcher.grid_columnconfigure(0, weight=1)
        self.mode_switcher.grid_columnconfigure(1, weight=1)
        self.pokemon_button = tk.Button(self.mode_switcher, text="Pokemons",
                                        command=lambda: self.__switch_modes("pokemon", False),
                                        font=(default_font, 10, "bold"),
                                        background="#e0e0e0")
        self.pokemon_button.bind("<Return>", lambda e: self.__switch_modes("pokemon", False))
        self.pokemon_button.grid(row=0, column=0, ipadx=5, sticky="nsew")
        self.weakness_button = tk.Button(self.mode_switcher, text="Weakness Calculator",
                                         command=lambda: self.__switch_modes("weakness", False),
                                         font=(default_font, 10, "bold"),
                                         background="#e0e0e0")
        self.weakness_button.bind("<Return>", lambda e: self.__switch_modes("weakness", False))
        self.weakness_button.grid(row=0, column=1, ipadx=5, sticky="nsew")

        # FRAMES WITH FUNCTIONS

        self.mode = default_mode

        self.pokemon_mode = PokemonModeFrame(self, default_name, default_primary, default_secondary, default_generation,
                                             default_sort)
        self.weakness_mode = WeaknessModeFrame(self)
        self.__switch_modes(self.mode, True)

        # STATUS BAR

        self.status = tk.Label(self, text=entry_message, anchor='w', font=(default_font, 10))
        self.status.config(background="#000000", foreground="white")
        self.status.pack(side=tk.BOTTOM, fill='x')

    def __switch_modes(self, mode, initial):
        self.mode = mode
        if mode == "pokemon":
            self.pokemon_button.config(state="disabled")
            self.pokemon_button.config(relief="sunken")
            self.weakness_button.config(state="normal")
            self.weakness_button.config(relief="raised")
            self.weakness_mode.pack_forget()
            self.pokemon_mode.pack(fill="both", expand=True)
            self.pokemon_mode.name_text.focus()
        elif mode == "weakness":
            self.pokemon_button.config(state="normal")
            self.pokemon_button.config(relief="raised")
            self.weakness_button.config(state="disabled")
            self.weakness_button.config(relief="sunken")
            self.pokemon_mode.pack_forget()
            self.weakness_mode.pack(fill="both", expand=True)
            self.weakness_mode.comboboxes[0].focus()

        # if this method is called with a button press it changes status bar
        if not initial:
            self.status.config(text=f"Switched to {proper_word(mode)} mode")

    def __on_close(self):
        if tk.messagebox.askyesno("Quit", "Do you want to close PepeDex?"):
            checked_name = re.sub(":", "", self.pokemon_mode.name_text.get())
            to_save = [self.mode, checked_name, self.pokemon_mode.primary_var.get(),
                       self.pokemon_mode.secondary_var.get(), self.pokemon_mode.generation_var.get(),
                       str(self.pokemon_mode.check_var.get())]
            try:
                file_path = os.path.abspath(self.__config_file)
                with open(file_path, "w") as file:
                    file.write(":".join(to_save))
            except OSError:
                raise
            self.destroy()

    def __on_start(self):
        try:
            path = os.path.abspath(self.__config_file)
            with open(path, "r") as file:
                default_values = file.readline()
            return default_values.split(":")
        except (OSError, FileNotFoundError):
            return None

    def __on_save(self):
        try:
            file = asksaveasfile(defaultextension=".txt", filetypes=(("Text file", "*.txt"), ("All Files", "*.*")))
            if file is not None:
                pokemon_team_types = []
                for combobox in self.weakness_mode.comboboxes:
                    pokemon_team_types.append(combobox.get())
                file.write(":".join(pokemon_team_types))
                file.close()
                self.status.config(text=f"Saved your team to {file.name}")
        except OSError:
            self.status.config(text="Failed to save your team")
        except UnicodeError:
            self.status.config(text="Incorrect file")

    def __on_open(self):
        try:
            file = askopenfile(defaultextension=".txt")
            if file is not None:
                pokemon_team_types = file.read().split(":")
                file.close()
                if len(pokemon_team_types) == 12:
                    for index in range(12):
                        self.weakness_mode.comboboxes[index].set(pokemon_team_types[index])
                    self.weakness_mode.calculate()
                    self.status.config(text=f"Loaded your team from {file.name}")
                else:
                    self.status.config(text="Failed to load your team. Chosen file doesn't contain saved team")
        except OSError:
            self.status.config(text="Failed to load your team. Couldn't open a file")
        except UnicodeError:
            self.status.config(text="Incorrect file")

    def __toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.attributes("-fullscreen", self.fullscreen)

    def __quit_fullscreen(self):
        self.fullscreen = False
        self.attributes("-fullscreen", self.fullscreen)

    def __display_help(self):
        if not self.help_window:
            self.status.config(text="Help window opened")
            self.help_window = True
            HelpWindow(self)


class WeaknessModeFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # SETTING FRAME WITH COMBOBOXES TO CHOOSE FROM

        tk.Label(self, text="Choose your Pokemon types:", font=(default_font, 10, "bold"),
                 background="#fffe85").grid(row=0, column=0, sticky='nsew')
        self.combobox_frame = tk.Frame(self, borderwidth=1, relief='solid', background="white")
        self.combobox_frame.grid(row=1, column=0, sticky='nsew')
        self.combobox_frame.grid_columnconfigure(0, weight=1)
        self.combobox_frame.grid_columnconfigure(1, weight=1)
        self.combobox_frame.grid_columnconfigure(2, weight=1)
        self.combobox_frame.grid_rowconfigure(7, weight=1)

        for i in range(6):
            pokemon_number_label = tk.Label(self.combobox_frame, text=f"Pokemon no. {i + 1}:", font=(default_font, 10),
                                            background="white")
            pokemon_number_label.grid(row=i, column=0, sticky='nsew', pady=5)

        type_values = [""] + Types.get_types_string_list()
        self.comboboxes = []
        for i in range(12):
            combobox = ttk.Combobox(self.combobox_frame, state="readonly", values=type_values, font=(default_font, 10))
            combobox.bind("<Left>", lambda e: self.master.pokemon_button.focus())
            combobox.bind("<Right>", lambda e: self.calculate_button.focus())
            combobox.grid(row=i // 2, column=1 + i % 2, sticky='nsew', padx=5)
            self.comboboxes.append(combobox)
        self.calculate_button = tk.Button(self.combobox_frame, text="Calculate", command=lambda: self.calculate(),
                                          font=(default_font, 10, "bold"), background="#e37171")
        self.calculate_button.grid(row=6, columnspan=3, pady=20, ipadx=45, ipady=5)
        self.calculate_button.bind("<Return>", lambda e: self.calculate())

        self.clear_button = tk.Button(self.combobox_frame, text="Clear", command=lambda: self.clear(),
                                      font=(default_font, 10, "bold"), background="white", border=4)
        self.clear_button.grid(row=7, columnspan=3, pady=30, ipadx=45, ipady=5, sticky='s')
        self.clear_button.bind("<Return>", lambda e: self.clear())

        # FRAME WITH INFORMATION ABOUT DEFENCE

        defence_label = tk.Label(self, text="Defense:", font=(default_font, 10, "bold"), background="#a2a7e8")
        defence_label.grid(row=0, column=1, sticky='nsew')
        self.defence_frame = WeaknessLabels(self, [], [], [], [])
        self.defence_frame.grid(row=1, column=1, sticky='nsew')

        # FRAME WITH INFORMATION ABOUT OFFENSE

        offense_label = tk.Label(self, text="Offense:", font=(default_font, 10, "bold"), background="#f08686")
        offense_label.grid(row=0, column=2, sticky='nsew')
        self.offence_frame = WeaknessLabels(self, [], [], [], [])
        self.offence_frame.grid(row=1, column=2, sticky='nsew')

    def calculate(self):
        types = []
        for index in range(len(self.comboboxes)):
            if index % 2 == 0 and self.comboboxes[index].get() == \
                    self.comboboxes[index + 1].get() or self.comboboxes[index].get() == "":
                continue
            else:
                types.append(self.comboboxes[index].get())
        if len(types) > 0:
            self.master.status.config(text="Calculating strong and weak sides of your team")
            defence = Types.calculate_defence(types)
            offence = Types.calculate_offence(types)
            self.defence_frame.destroy()
            self.defence_frame = WeaknessLabels(self, defence[3], defence[2], defence[1], defence[0])
            self.defence_frame.grid(row=1, column=1, sticky='nsew')

            self.offence_frame.destroy()
            self.offence_frame = WeaknessLabels(self, offence[3], offence[2], offence[1], offence[0])
            self.offence_frame.grid(row=1, column=2, sticky='nsew')
            self.master.status.config(text="Calculated strong and weak sides of your team")
        else:
            self.master.status.config(text="Provide atleast one type")

    def clear(self):
        for combobox in self.comboboxes:
            combobox.set("")
        self.defence_frame.destroy()
        self.defence_frame = WeaknessLabels(self, [], [], [], [])
        self.defence_frame.grid(row=1, column=1, sticky='nsew')

        self.offence_frame.destroy()
        self.offence_frame = WeaknessLabels(self, [], [], [], [])
        self.offence_frame.grid(row=1, column=2, sticky='nsew')

        self.master.status.config(text="Cleared Weakness mode")


class WeaknessLabels(tk.Frame):
    def __init__(self, master, great, good, bad, terrible):
        super().__init__(master, borderwidth=1, relief='solid', background="white")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        row = 0
        elements = 0
        tk.Label(self, text="Great against:", font=(default_font, 10),
                 background="white").grid(row=row, column=0, sticky='nsew', columnspan=3)
        row += 1
        for typ in great:
            tk.Label(self, text=typ, background=type_color[typ], foreground='white',
                     font=(default_font, 10, "bold")).grid(row=row, column=elements % 3, sticky='nsew')
            elements += 1
            if elements % 3 == 0:
                row += 1

        row += 1
        elements = 0
        tk.Label(self, text="Good against:", font=(default_font, 10), background="white").grid(
            row=row, column=0, sticky='nsew', columnspan=3)
        row += 1
        for typ in good:
            tk.Label(self, text=typ, background=type_color[typ], foreground='white',
                     font=(default_font, 10, "bold")).grid(row=row, column=elements % 3, sticky='nsew')
            elements += 1
            if elements % 3 == 0:
                row += 1

        row += 1
        elements = 0
        tk.Label(self, text="Bad against:", font=(default_font, 10), background="white").grid(
            row=row, column=0, sticky='nsew', columnspan=3)
        row += 1
        for typ in bad:
            tk.Label(self, text=typ, background=type_color[typ], foreground='white',
                     font=(default_font, 10, "bold")).grid(row=row, column=elements % 3, sticky='nsew')
            elements += 1
            if elements % 3 == 0:
                row += 1

        row += 1
        elements = 0
        tk.Label(self, text="Terrible against:", font=(default_font, 10), background="white").grid(
            row=row, column=0, sticky='nsew', columnspan=3)
        row += 1
        for typ in terrible:
            tk.Label(self, text=typ, background=type_color[typ], foreground='white',
                     font=(default_font, 10, "bold")).grid(row=row, column=elements % 3, sticky='nsew')
            elements += 1
            if elements % 3 == 0:
                row += 1


class PokemonModeFrame(tk.Frame):
    def __init__(self, master, name, primary, secondary, generation, order):
        super().__init__(master)

        filter_frame = tk.Frame(self, highlightbackground="black", highlightthickness=1, background="white")
        filter_frame.config(width=60)
        filter_frame.pack(side=tk.RIGHT, fill="y")
        filter_frame.grid_rowconfigure(7, weight=1)

        name_label = tk.Label(filter_frame, text="Name:", anchor="w", background="white", font=(default_font, 9))
        name_label.grid(row=0, column=0, ipady=5)
        self.name_text = tk.Entry(filter_frame, font=(default_font, 9))
        self.name_text.insert(0, name)
        self.name_text.grid(row=0, column=1, sticky="e")
        self.name_text.bind("<Return>", lambda e: self.__change_pokemons(False))
        self.name_text.bind("<Left>", lambda e: self.__focus_first_label())

        types = [""] + Types.get_types_string_list()

        self.primary_var = tk.StringVar(value=primary)
        primary_label = tk.Label(filter_frame, text="Primary Type:", anchor="w", background="white",
                                 font=(default_font, 9))
        primary_label.grid(row=1, column=0, ipady=5)
        self.primary_list = ttk.Combobox(filter_frame, state="readonly", values=types, textvariable=self.primary_var,
                                         font=(default_font, 9))
        self.primary_list.bind("<Left>", lambda e: self.__focus_first_label())
        self.primary_list.grid(row=1, column=1, sticky="e")

        self.secondary_var = tk.StringVar(value=secondary)
        secondary_label = tk.Label(filter_frame, text="Secondary Type:", anchor="w", background="white",
                                   font=(default_font, 9))
        secondary_label.grid(row=2, column=0, ipady=5)
        self.secondary_list = ttk.Combobox(filter_frame, state="readonly", values=types,
                                           textvariable=self.secondary_var, font=(default_font, 9))
        self.secondary_list.bind("<Left>", lambda e: self.__focus_first_label())
        self.secondary_list.grid(row=2, column=1, sticky="e")

        self.generation_var = tk.StringVar(value=generation)
        generation_label = tk.Label(filter_frame, text="Generation:", anchor="w", background="white",
                                    font=(default_font, 9))
        generation_label.grid(row=3, column=0, ipady=5)
        self.generation_list = ttk.Combobox(filter_frame, state="readonly", values=[""] + generations,
                                            textvariable=self.generation_var, font=(default_font, 9))
        self.generation_list.bind("<Left>", lambda e: self.__focus_first_label())
        self.generation_list.grid(row=3, column=1, sticky="e")

        order_label = tk.Label(filter_frame, text="Order by:", background="white", font=(default_font, 9))
        order_label.grid(row=4, columnspan=2)
        self.check_var = tk.IntVar(value=order)
        dex_check = tk.Checkbutton(filter_frame, text="Dex Number", variable=self.check_var, onvalue=0,
                                   background="white", font=(default_font, 9))
        dex_check.bind("<Return>", lambda e: self.check_var.set(0))
        dex_check.bind("<Left>", lambda e: self.__focus_first_label())
        dex_check.grid(row=5, column=0)
        name_check = tk.Checkbutton(filter_frame, text="Name", variable=self.check_var, onvalue=1, background="white",
                                    font=(default_font, 9))
        name_check.bind("<Return>", lambda e: self.check_var.set(1))
        name_check.bind("<Left>", lambda e: self.__focus_first_label())
        name_check.grid(row=5, column=1)

        search_button = tk.Button(filter_frame, text="Search", width=20, command=lambda: self.__change_pokemons(False),
                                  font=(default_font, 9, "bold"), background="#e37171")
        search_button.bind("<Return>", lambda e: self.__change_pokemons(False))
        search_button.bind("<Left>", lambda e: self.__focus_first_label())
        search_button.grid(row=6, column=0, columnspan=2, pady=15)

        clear_button = tk.Button(filter_frame, text="Clear", width=20, command=lambda: self.__clear_pokemons(),
                                 font=(default_font, 9, "bold"), background="white", border=4)
        clear_button.bind("<Return>", lambda e: self.__clear_pokemons())
        clear_button.bind("<Left>", lambda e: self.__focus_first_label())
        clear_button.grid(row=7, column=0, columnspan=2, pady=30, sticky='s')

        image_path = os.path.abspath("Images\\pokeball.png")
        self.img = ImageTk.PhotoImage(Image.open(image_path))
        self.pokeball_filler = tk.Label(self, image=self.img, borderwidth=1, relief='solid',
                                        height=self.winfo_height())
        self.pokeball_filler.config(background='#d63429')

        self.content_frame = ScrollablePokemonFrame(self)
        self.__change_pokemons(True)
        self.content_frame.pack(side=tk.RIGHT, fill="both")

        self.pokeball_filler.pack(side=tk.LEFT, fill='both', expand=True)

    def __change_pokemons(self, initial):
        name = self.name_text.get()
        primary = self.primary_var.get()
        secondary = self.secondary_var.get()
        generation = self.generation_var.get()
        order = self.check_var.get()
        if name == "":
            name = None
        if primary == "":
            primary = None
        if secondary == "":
            secondary = None
        if generation == "":
            generation = None
        else:
            generation = (generation.split())[0]
        if not initial:
            self.master.status.config(text="Filtering Pokemons")
        self.content_frame.reattach_pokemons(Pokemons.get_filtered_pokemons(name, primary,
                                                                            secondary, generation, order))
        if not initial:
            self.master.status.config(text="Filtered Pokemons")

    def __clear_pokemons(self):
        self.check_var.set(0)
        self.primary_list.set("")
        self.secondary_list.set("")
        self.name_text.delete(0, 'end')
        self.generation_list.set("")
        self.master.status.config(text="Clearing Pokemon filters")
        self.pokeball_filler.config(background='#d63429')
        self.__change_pokemons(False)
        self.master.status.config(text="Cleared Pokemon filters")

    def __focus_first_label(self):
        if len(self.content_frame.labels) > 0:
            self.content_frame.labels[0].focus()


class ScrollablePokemonFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master, width=750)
        self.pokemons = []
        self.canvas = tk.Canvas(self, width=745)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.config(background='#eb3226')
        self.frame_canvas_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw",
                                                         width=750)
        self.canvas.bind("<Configure>", lambda e: self.__configure())
        self.canvas.config(background='#eb4034')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame.bind('<Enter>', lambda e: self.__bound_to_mousewheel())
        self.scrollable_frame.bind('<Leave>', lambda e: self.__unbound_to_mousewheel())

        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.labels = []

    def __attach_pokemons(self):
        for i in range(len(self.pokemons)):
            label = tk.Label(self.scrollable_frame, text=self.pokemons[i].name, width=50, anchor='w', borderwidth=2,
                             relief='raised', takefocus=1)
            label.config(font=("Sans", 15))  # changing font causes tkinter to bug out - scroll down after 'clear'
            self.labels.append(label)
            if len(self.pokemons[i].types) > 0:
                default_background = type_color[self.pokemons[i].types[0].name]
                default_foreground = 'white'
                label.config(background=default_background, foreground=default_foreground)
                label.bind('<Enter>', lambda e, ind=i, db=default_foreground, df=default_background: self.__bound_label(
                    ind, db, df))
                label.bind("<Button-1>",
                           lambda e, poke=self.pokemons[i], color=default_background:
                           self.__open_window_and_change_color(poke, color))
                label.bind("<Return>",
                           lambda e, poke=self.pokemons[i], color=default_background:
                           self.__open_window_and_change_color(poke, color))
                label.bind("<Left>", lambda e: self.master.master.weakness_button.focus())
                label.bind("<Right>", lambda e: self.master.name_text.focus())
                label.bind('<Leave>',
                           lambda e, ind=i, db=default_background, df=default_foreground: self.__unbound_label(ind,
                                                                                                               db,
                                                                                                               df))
                label.bind("<FocusIn>", lambda e, ind=i, db=default_foreground,
                                               df=default_background: self.__bound_label_and_move(ind, db, df))
                label.bind("<FocusOut>", lambda e, ind=i, db=default_background,
                                                df=default_foreground: self.__unbound_label_and_move(ind, db, df))
            else:
                print(f"{self.pokemons[i]} has no type assigned by api.")
            label.grid(row=i, column=0)

    def reattach_pokemons(self, pokemons):
        for label in self.labels:
            label.destroy()
        self.labels = []
        self.pokemons = pokemons
        self.__attach_pokemons()
        self.scrollable_frame.update_idletasks()
        self.__configure()

    def __bound_label(self, index, db, df):
        self.labels[index].config(background=db, foreground=df)

    def __bound_label_and_move(self, index, db, df):
        self.canvas.bind_all("<Up>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Down>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.canvas.yview_moveto(self.labels[index].winfo_y() / self.scrollable_frame.winfo_height())
        self.__bound_label(index, db, df)

    def __unbound_label(self, index, db, df):
        self.labels[index].config(background=db, foreground=df)

    def __unbound_label_and_move(self, index, db, df):
        self.canvas.unbind_all("<Up>")
        self.canvas.unbind_all("<Down>")
        self.__unbound_label(index, db, df)

    def __open_window_and_change_color(self, pokemon, color):
        self.master.pokeball_filler.config(background=color)
        PokemonInfoWindow(self.master.master, pokemon).focus()

    def __bound_to_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self.__on_mousewheel)

    def __unbound_to_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def __on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def __configure(self):
        min_height = self.scrollable_frame.winfo_reqheight()
        if self.winfo_height() >= min_height:
            new_height = self.winfo_height()
            self.scrollbar.pack_forget()
            self.scrollable_frame.unbind('<Enter>')
        else:
            new_height = min_height
            self.scrollbar.pack(side='right', fill='y')
            self.scrollable_frame.bind('<Enter>', lambda e: self.__bound_to_mousewheel())

        self.canvas.itemconfigure(self.frame_canvas_id, height=new_height)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class PokemonInfoWindow(tk.Toplevel):
    def __init__(self, master, pokemon):
        super().__init__(master)
        self.geometry("700x500")
        self.winfo_toplevel().title(pokemon.name)
        self.protocol("WM_DELETE_WINDOW", self.__on_close)
        self.bind("<Control-q>", lambda e: self.__on_close())
        self.minsize(700, 500)
        try:
            icon_path = os.path.abspath('Images/logo.ico')
            self.iconbitmap(icon_path)
        except (OSError, FileNotFoundError):
            print("Failed loading icon")

        color = type_color[pokemon.types[0].name]

        self.canvas = tk.Canvas(self)
        self.frame = tk.Frame(self.canvas)
        self.frame.config(background=color)

        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.grid(row=0, column=1, sticky='ns')

        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.hsb.grid(row=1, column=0, sticky='ew')

        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.window = self.canvas.create_window(0, 0, window=self.frame, anchor="nw", tags="self.frame")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.frame.bind("<Configure>", lambda e: self.__on_frame_configure())
        self.canvas.bind("<Configure>", lambda e: self.__on_canvas_configure())
        self.frame.bind('<Enter>', lambda e: self.__bound_to_mousewheel())
        self.frame.bind('<Leave>', lambda e: self.__unbound_to_mousewheel())
        self.bind("<FocusOut>", lambda e: self.__on_lost_focus())
        self.bind("<FocusIn>", lambda e: self.__on_focus())

        artwork = pokemon.sprites["other"]["official-artwork"]["front_default"]
        if artwork is not None:
            try:
                raw_artwork = urllib.request.urlopen(artwork).read()
                read_artwork = Image.open(io.BytesIO(raw_artwork))
                self.image_artwork = ImageTk.PhotoImage(read_artwork)
                self.artwork = tk.Label(self.frame, image=self.image_artwork, borderwidth=2, relief='solid',
                                        background="white")
                self.artwork.pack(side='top')
            except urllib.error.URLError:
                print("Failed to load artwork image. Connect to the Internet")

        self.desc = tk.Label(self.frame, text=pokemon.description, font=(default_font, 16, "normal", "italic"),
                             wraplength=self.winfo_width() - 100,
                             justify="center",
                             background="white")
        self.desc.pack(side='top', fill='x')

        # SHORT POKEMON INFORMATION

        self.short_pokemon_info = tk.Frame(self.frame)
        self.short_pokemon_info.pack(side='top', fill='x')
        self.short_pokemon_info.grid_columnconfigure(1, weight=2)
        self.short_pokemon_info.grid_columnconfigure(2, weight=1)
        self.short_pokemon_info.grid_columnconfigure(3, weight=1)
        self.short_pokemon_info.grid_columnconfigure(4, weight=1)

        front_sprite = pokemon.sprites["front_default"]
        if front_sprite is not None:
            try:
                raw_sprite = urllib.request.urlopen(front_sprite).read()
                read_sprite = Image.open(io.BytesIO(raw_sprite))
                self.image_sprite = ImageTk.PhotoImage(read_sprite)
                self.sprite = tk.Label(self.short_pokemon_info, image=self.image_sprite, borderwidth=1, relief='solid')
                self.sprite.grid(row=0, column=0, rowspan=2, sticky='nsew')
            except urllib.error.URLError:
                print("Failed to load sprite image. Connect to the Internet")

        self.name_label = tk.Label(self.short_pokemon_info, text=pokemon.name, anchor='center', borderwidth=1,
                                   relief='solid', height=6, font=(default_font, 12, "bold"))
        self.name_label.grid(row=0, column=1, sticky='nsew', rowspan=2)
        self.genus_label = tk.Label(self.short_pokemon_info, text=pokemon.genera, anchor='center', borderwidth=1,
                                    relief='solid', height=6, font=(default_font, 12))
        self.genus_label.grid(row=0, column=2, sticky='nsew', rowspan=2)
        self.height = tk.Label(self.short_pokemon_info, text=f"Height: {pokemon.height / 10} m", anchor='center',
                               borderwidth=1,
                               relief='solid', font=(default_font, 12))
        self.height.grid(row=0, column=3, sticky='nsew')
        self.weight = tk.Label(self.short_pokemon_info, text=f"Weight: {pokemon.weight / 10} kg", anchor='center',
                               borderwidth=1,
                               relief='solid', font=(default_font, 12))
        self.weight.grid(row=1, column=3, sticky='nsew')

        self.types = []
        for i in range(len(pokemon.types)):
            type_label = tk.Label(self.short_pokemon_info, text=pokemon.types[i].name, borderwidth=1, relief='solid')
            type_label.config(background=type_color[pokemon.types[i].name], foreground='white',
                              font=(default_font, 12, "bold"))
            self.types.append(type_label)
            type_label.grid(row=i, column=4, sticky="nsew", rowspan=(3 - len(pokemon.types)))

        # START OF THE ABILITIES AND STATS DISPLAY

        self.abilities_stats_info = tk.Frame(self.frame)
        self.abilities_stats_info.pack(side='top', fill='x')
        self.abilities_stats_info.grid_columnconfigure(0, weight=2)
        self.abilities_stats_info.grid_columnconfigure(1, weight=1)
        self.abilities_stats_info.grid_rowconfigure(1, weight=1)

        stats_label = tk.Label(self.abilities_stats_info, text="Stats:", anchor='center',
                               font=(default_font, 12, "bold"), background="white")
        stats_label.grid(row=0, column=1, sticky="ew")

        # DISPLAY ABILITIES

        self.abilities_info = tk.Frame(self.abilities_stats_info)
        self.abilities_info.grid_columnconfigure(1, weight=1)
        self.abilities_info.grid(row=0, column=0, rowspan=2, sticky='nsew')

        abilities_label = tk.Label(self.abilities_info, text="Abilities:", anchor='center',
                                   font=(default_font, 12, "bold"), background="white")
        abilities_label.grid(row=0, column=0, columnspan=2, sticky='nsew')

        for index in range(len(pokemon.abilities)):
            self.abilities_info.grid_rowconfigure(index + 1, weight=1)
            current_ability = pokemon.abilities[index]
            hidden_name = current_ability[0].name
            if current_ability[1]:
                hidden_name += " (Hidden)"
            hidden_name += ":"
            ab_name = tk.Label(self.abilities_info, text=hidden_name, borderwidth=1, relief='solid',
                               font=(default_font, 10))
            ab_name.grid(row=index + 1, column=0, sticky='nsew')
            ab_desc = tk.Label(self.abilities_info, borderwidth=1, relief='solid', wraplength=self.winfo_width() - 350,
                               justify="left", font=(default_font, 10))
            ab_desc.config(text=current_ability[0].description)
            ab_desc.grid(row=index + 1, column=1, sticky='nsew')

        # DISPLAY STATS

        self.stats_info = tk.Frame(self.abilities_stats_info, borderwidth=1, relief='solid')
        self.stats_info.grid_columnconfigure(0, weight=1)
        self.stats_info.grid_columnconfigure(1, weight=1)
        self.stats_info.grid(row=1, column=1, sticky='nsew')

        for index in range(len(pokemon.stats)):
            self.stats_info.grid_rowconfigure(index, weight=1)
            stat_name = tk.Label(self.stats_info, text=proper_word(pokemon.stats[index][0]) + ':', anchor='w',
                                 font=(default_font, 10))
            stat_name.grid(row=index, column=0, sticky='nsew')
            stat_value = tk.Label(self.stats_info, text=pokemon.stats[index][1], anchor="center",
                                  font=(default_font, 10, "bold"))
            stat_value.config(background=stat_color(pokemon.stats[index][1]))
            stat_value.grid(row=index, column=1, sticky="nsew")

        # DISPLAY MOVES

        moves_label = tk.Label(self.frame, text="Moves this Pokemon can learn:", anchor='center',
                               font=(default_font, 12, "bold"), background="white", height=2)
        moves_label.pack(side="top", fill='x')

        sorted_moves = sorted(pokemon.moves, key=lambda m: m.name)

        move_list_frame = tk.Frame(self.frame)
        move_list_frame.grid_columnconfigure(0, weight=2)
        move_list_frame.grid_columnconfigure(1, weight=1)
        move_list_frame.pack(side="top", fill="both")

        for i in range(len(sorted_moves)):
            move = sorted_moves[i]
            move_label = tk.Label(move_list_frame, anchor='w', text=f"{move.name}\t|\tPower: {move.power}"
                                                                    f"\t|\tAccuracy: {move.accuracy}\t"
                                                                    f"|\tPP: {move.pp}\t"
                                                                    f"|\tClass: {move.move_class}",
                                  font=(default_font, 10),
                                  height=3)
            move_label.grid(row=i, column=0, sticky="nsew")
            move_type = tk.Label(move_list_frame, anchor="center", text=f"{move.type}",
                                 font=(default_font, 10, "bold"), background=type_color[move.type], foreground="white")
            move_type.grid(row=i, column=1, sticky="nsew")

        self.master.status.config(text=f"Opened {pokemon.name} window")

    def __on_frame_configure(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def __on_canvas_configure(self):
        min_width = self.frame.winfo_reqwidth()
        min_height = self.frame.winfo_reqheight()

        if self.winfo_width() >= min_width:
            new_width = self.winfo_width()
            self.hsb.grid_remove()
        else:
            new_width = min_width
            self.hsb.grid()

        if self.winfo_height() >= min_height:
            new_height = self.winfo_height()
            self.vsb.grid_remove()
        else:
            new_height = min_height
            self.vsb.grid()

        self.canvas.itemconfig(self.window, width=new_width, height=new_height)

    def __on_close(self):
        self.master.status.config(text=f"Closed {self.name_label.cget('text')} window")
        self.__on_lost_focus()
        self.destroy()

    def __bound_to_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self.__on_mousewheel)

    def __unbound_to_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")

    def __on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def __on_focus(self):
        self.bind("<Up>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.bind("<Down>", lambda e: self.canvas.yview_scroll(1, "units"))
        self.bind("<Left>", lambda e: self.canvas.xview_scroll(-1, "units"))
        self.bind("<Right>", lambda e: self.canvas.xview_scroll(1, "units"))

    def __on_lost_focus(self):
        self.unbind("<Up>")
        self.unbind("<Down>")
        self.unbind("<Left>")
        self.unbind("<Right>")


class HelpWindow(tk.Toplevel):
    __pepedex_image = "Images\\pepedex_gr.png"

    def __init__(self, master):
        super().__init__(master)
        self.geometry("1000x800")
        self.state('zoomed')
        self.protocol("WM_DELETE_WINDOW", self.__on_close)
        self.bind("<Control-q>", lambda e: self.__on_close())
        self.minsize(500, 500)
        self.winfo_toplevel().title("Help - PepeDex")
        try:
            icon_path = os.path.abspath('Images/logo.ico')
            self.iconbitmap(icon_path)
            self.winfo_toplevel().title("PepeDex")
            self.config(background='white')
            image_path = os.path.abspath(self.__pepedex_image)
            self.img = ImageTk.PhotoImage(Image.open(image_path))
            self.program_name = tk.Label(self, height=100, image=self.img, borderwidth=2, relief='solid')
            self.program_name.config(background='white')
            self.program_name.pack(side=tk.TOP, fill='x')
        except (OSError, FileNotFoundError):
            print("Failed loading images")

        self.canvas = tk.Canvas(self)
        self.frame = tk.Frame(self.canvas)

        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fil="y")

        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.hsb.set)
        self.hsb.pack(side="bottom", fill="x")

        self.canvas.pack(side="left", fill="both", expand="True")
        self.window = self.canvas.create_window(0, 0, window=self.frame, anchor="nw")

        self.header = tk.Label(self.frame, wraplength=self.winfo_width() - 100, justify="center",
                               text="Welcome to PepeDex!", font=(pokemon_font, 20, "bold"))
        self.header.grid(row=0, column=0, sticky="ew")

        instructions = "PepeDex is a program that helps you learn about every Pokemon from the last 8 generations" \
                       " (approximately 25 years).\n\n" \
                       "Data of every Pokemon is retrieved from the best Pokemon API available on the Internet for" \
                       " the public usage and it's located under the https://pokeapi.co/ address. " \
                       "If you want to learn more about Pokemons I highly encourage you to check their site and" \
                       " see for yourself how it actually works.\n\n" \
                       "In the 'Pokemons' tab PepeDex lets you search for a specific Pokemon or filter list of every " \
                       "Pokemon by their" \
                       " name, types, generation they were introduced in and sort them by their Dex number" \
                       " or alphabetically by their names. Once you have your desired list of Pokemons on your" \
                       " screen you can then scroll through it and click on appropriate button to open a new " \
                       "window with information about" \
                       " chosen Pokemon eg. their abilities, stats or even see how they look like if the API provided" \
                       " valid url link to their image.\n\n" \
                       "In the 'Weakness Calculator' tab you can calculate which types your team is good against and " \
                       "check if they have any weak sides that you should be aware of. To do that simply pick types " \
                       "corresponding to the types of your Pokemons and press 'Calculate' button. In the 'Defence' " \
                       "section you can check which types deal more damage to you and which types your team is " \
                       "resistant to. In the 'Offense' section you can see which types you will deal more damage to" \
                       " and which types will resist you more effectively.\n\n" \
                       "PepeDex lets you save and open your teams to a text file by using appropriate buttons " \
                       "located in the top menu. " \
                       "If you ever create a team with" \
                       " great resistances and above average type coverage you can just save it for later.\n" \
                       "Main program window supports fullscreen mode - default key is F11. To exit fullscreen mode " \
                       "simply press F11 again or press Escape\n\n\n" \
                       "That should cover everything you need to know to start using PepeDex how it was intended" \
                       " to be used.\n" \
                       "Good luck on your adventure,"
        self.instrucions = tk.Label(self.frame, text=instructions, wraplength=self.winfo_width() - 100, justify="left",
                                    font=(default_font, 15))
        self.instrucions.grid(row=1, column=0, sticky="nsew")

        signature = tk.Label(self.frame, text="~Pepe", anchor="w", font=("Arial", 12, "italic"))
        signature.grid(row=2, column=0, sticky="nsew", padx=20)

        tk.Label(self.frame, wraplength=self.winfo_width() - 100,
                 text="Useful shortcuts: ", font=(pokemon_font, 15, "bold")).grid(
            row=3, column=0, sticky="ew", pady=20)

        shortcuts = "Ctrl-S - Save types located in the Weakness mode to a file (main window)\n" \
                    "Ctrl-O - Open a file with saved types and load them to Weakness mode (main window)\n" \
                    "Ctrl-H - display help window (main window)\n" \
                    "Ctrl-Q - Close currently focused window\n" \
                    "Left/Right arrow - stop focusing comboboxes/pokemon buttons\n"

        self.shortcuts = tk.Label(self.frame, text=shortcuts, anchor='w', wraplength=self.winfo_width() - 100,
                                  justify="left", font=(default_font, 15))
        self.shortcuts.grid(row=4, column=0, sticky="nsew")

        tk.Label(self.frame, wraplength=self.winfo_width() - 100, justify="left", text="Contact: ",
                 font=(pokemon_font, 15, "bold")).grid(row=5, column=0, sticky="ew", pady=20)

        tk.Label(self.frame, text="Email: pppkwapien@gmail.com", anchor='w', wraplength=self.winfo_width() - 100,
                 font=(default_font, 15)).grid(row=6, column=0, sticky="nsew")

        git_frame = tk.Frame(self.frame)

        tk.Label(git_frame, text="GitHub: ", anchor='w', font=(default_font, 15)).grid(row=1, column=0, sticky='w')
        self.github = tk.Label(git_frame, text="PepeKwapien", anchor='w', wraplength=self.winfo_width() - 100,
                               font=(default_font, 15), fg="blue", cursor="hand2")
        self.github.bind("<Button-1>", lambda e: self.__open_github())
        self.github.grid(row=1, column=1, sticky="nsew")

        git_frame.grid(row=7, column=0, sticky='nsew')

        self.frame.bind("<Configure>", lambda e: self.__on_frame_configure())
        self.canvas.bind("<Configure>", lambda e: self.__on_canvas_configure())
        self.frame.bind('<Enter>', lambda e: self.__bound_to_mousewheel())
        self.frame.bind('<Leave>', lambda e: self.__unbound_to_mousewheel())
        self.bind("<FocusOut>", lambda e: self.__on_lost_focus())
        self.bind("<FocusIn>", lambda e: self.__on_focus())

    def __on_frame_configure(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def __on_canvas_configure(self):
        min_width = self.frame.winfo_reqwidth()
        min_height = self.frame.winfo_reqheight() + self.program_name.winfo_height()

        if self.winfo_width() >= min_width:
            new_width = self.winfo_width()
            self.hsb.pack_forget()
        else:
            new_width = min_width
            self.hsb.pack(side="bottom", fill='x')

        if self.winfo_height() >= min_height:
            new_height = self.winfo_height()
            self.vsb.pack_forget()
        else:
            new_height = min_height
            self.vsb.pack(side="right", fill='y')

        self.canvas.itemconfig(self.window, width=new_width, height=new_height)
        self.header.config(wraplength=self.winfo_width() - 100)
        self.instrucions.config(wraplength=self.winfo_width() - 100)

    def __on_close(self):
        self.master.help_window = False
        self.master.status.config(text="Help window closed")
        self.destroy()

    def __bound_to_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self.__on_mousewheel)

    def __unbound_to_mousewheel(self):
        self.canvas.unbind_all("<Up>")
        self.canvas.unbind_all("<Down>")
        self.canvas.unbind_all("<MouseWheel>")

    def __on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def __on_focus(self):
        self.bind("<Up>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.bind("<Down>", lambda e: self.canvas.yview_scroll(1, "units"))

    def __on_lost_focus(self):
        self.unbind("<Up>")
        self.unbind("<Down>")

    def __open_github(self):
        webbrowser.open_new("https://github.com/PepeKwapien")


def start_gui():
    try:
        Types.prepare_types()
        Abilities.prepare_abilities()
        Moves.prepare_moves()
        Pokemons.prepare_pokemons()
        mw = MainWindow()
        mw.mainloop()
    except requests.exceptions.RequestException:
        print("Check your Internet connection!")
    except Exception as e:
        print(e.__str__())
        input("Type anything and press Enter to exit")


if __name__ == '__main__':
    start_gui()
