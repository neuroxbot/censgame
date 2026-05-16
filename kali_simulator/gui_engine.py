"""
Grey Hack Style GUI Engine
Рисует весь интерфейс внутри одного окна на Canvas.
Никаких реальных окон OS, только эмуляция внутри Python.
"""
import tkinter as tk
from tkinter import font as tkfont
import math
import time
from typing import Dict, List, Tuple, Optional, Callable, Any

class Color:
    """Палитра в стиле Cyberpunk/Kali"""
    BG = "#0d1117"
    FG = "#00ff41"  # Хакерский зеленый
    FG_DIM = "#008f11"
    ACCENT = "#00bfff"
    ERROR = "#ff3333"
    WARN = "#ffcc00"
    WINDOW_BG = "#161b22"
    WINDOW_BORDER = "#30363d"
    TEXT_CURSOR = "#00ff41"

class CRTFilter:
    """Эффект ЭЛТ-монитора (scanlines, мерцание)"""
    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.scanlines = []
        self.create_scanlines()
        
    def create_scanlines(self):
        """Создает полосы сканирования"""
        for y in range(0, self.height, 4):
            line = self.canvas.create_rectangle(
                0, y, self.width, y + 2,
                fill="#000000", stipple="gray50", tags="scanline"
            )
            self.scanlines.append(line)
            
    def flicker(self):
        """Эффект легкого мерцания"""
        # Можно добавить анимацию яркости
        pass

class Window:
    """Виртуальное окно внутри эмулятора"""
    def __init__(self, engine: 'GUIEngine', title: str, x: int, y: int, w: int, h: int):
        self.engine = engine
        self.title = title
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.z_order = 0
        self.active = False
        self.dragging = False
        self.drag_offset = (0, 0)
        self.content_widget = None
        self.close_callback: Optional[Callable] = None
        
        # ID элементов canvas
        self.bg_id = None
        self.border_id = None
        self.title_bar_id = None
        self.title_text_id = None
        self.close_btn_id = None
        self.content_frame = None
        
        self.draw()
        
    def draw(self):
        """Отрисовка окна"""
        tag = f"win_{id(self)}"
        
        # Фон окна
        self.bg_id = self.engine.canvas.create_rectangle(
            self.x, self.y, self.x + self.w, self.y + self.h,
            fill=Color.WINDOW_BG, outline=Color.WINDOW_BORDER, width=2,
            tags=[tag, "window"]
        )
        
        # Заголовок
        self.title_bar_id = self.engine.canvas.create_rectangle(
            self.x, self.y, self.x + self.w, self.y + 25,
            fill="#21262d", outline="",
            tags=[tag, "title_bar"]
        )
        
        # Текст заголовка
        self.title_text_id = self.engine.canvas.create_text(
            self.x + 10, self.y + 12,
            text=self.title, anchor="w",
            fill=Color.FG, font=("Consolas", 10, "bold"),
            tags=[tag, "title_text"]
        )
        
        # Кнопка закрытия [X]
        self.close_btn_id = self.engine.canvas.create_rectangle(
            self.x + self.w - 20, self.y + 5, self.x + self.w - 5, self.y + 20,
            fill="#da3633", outline="",
            tags=[tag, "close_btn"]
        )
        self.engine.canvas.create_text(
            self.x + self.w - 12, self.y + 12,
            text="×", anchor="center",
            fill="white", font=("Arial", 14, "bold"),
            tags=[tag, "close_text"]
        )
        
        self.update_z_order(1)
        
    def update_z_order(self, new_order: int):
        """Поднимает окно на передний план"""
        tag = f"win_{id(self)}"
        self.engine.canvas.tag_raise(tag)
        self.z_order = new_order
        self.active = True
        
    def move(self, dx: int, dy: int):
        """Перемещение окна"""
        self.x += dx
        self.y += dy
        tag = f"win_{id(self)}"
        self.engine.canvas.move(tag, dx, dy)
        
    def resize(self, w: int, h: int):
        """Изменение размера (упрощено)"""
        self.w = max(w, 200)
        self.h = max(h, 150)
        self.destroy()
        self.draw()
        if self.content_widget:
            self.content_widget.place(x=5, y=30, width=self.w-10, height=self.h-35)
            
    def destroy(self):
        """Удаление окна"""
        tag = f"win_{id(self)}"
        self.engine.canvas.delete(tag)
        if self.content_widget:
            self.content_widget.destroy()
            
    def set_content(self, widget: tk.Widget):
        """Устанавливает виджет содержимого"""
        if self.content_widget:
            self.content_widget.destroy()
        self.content_widget = widget
        if widget:
            widget.place(in_=self.engine.root, 
                        x=self.engine.root.winfo_x() + self.x + 5,
                        y=self.engine.root.winfo_y() + self.y + 30,
                        width=self.w - 10, height=self.h - 35)

class TerminalWidget(tk.Frame):
    """Виджет терминала внутри виртуального окна"""
    def __init__(self, parent, shell_instance):
        super().__init__(parent, bg=Color.BG, highlightthickness=0)
        self.shell = shell_instance
        
        # Текстовое поле
        self.text = tk.Text(self, bg=Color.BG, fg=Color.FG,
                           insertbackground=Color.TEXT_CURSOR,
                           font=("Consolas", 11), wrap=tk.WORD,
                           relief=tk.FLAT, padx=5, pady=5)
        self.text.pack(fill=tk.BOTH, expand=True)
        
        # Настройка тегов для цветов
        self.text.tag_config("prompt", foreground=Color.ACCENT)
        self.text.tag_config("error", foreground=Color.ERROR)
        self.text.tag_config("output", foreground=Color.FG_DIM)
        
        # Привязки событий
        self.text.bind("<Return>", self.on_enter)
        self.text.bind("<Key>", self.on_key)
        
        self.command_buffer = ""
        self.history = []
        self.history_idx = -1
        
        self.print_welcome()
        
    def print_welcome(self):
        welcome = """Kali Linux Simulator v2.0 [Grey Hack Edition]
Type 'help' for commands. Try 'nmap', 'hack', 'run script.kl'
"""
        self.text.insert(tk.END, welcome, "output")
        self.show_prompt()
        
    def show_prompt(self):
        prompt = f"\n┌─[root@kali]{self.shell.fs.cwd}]\n└─# "
        self.text.insert(tk.END, prompt, "prompt")
        self.text.mark_set("input_start", "end-1c")
        self.text.see(tk.END)
        
    def on_key(self, event):
        # Запрет редактирования истории
        if self.text.index("insert") < self.text.index("input_start"):
            return "break"
            
    def on_enter(self, event):
        # Получаем команду
        input_start = self.text.index("input_start")
        input_end = self.text.index("end-1c")
        
        if input_start == input_end:
            self.show_prompt()
            return "break"
            
        cmd = self.text.get(input_start, input_end).strip()
        self.history.append(cmd)
        self.history_idx = len(self.history)
        
        # Выполняем команду
        output = self.shell.execute_command(cmd)
        
        if output:
            if "error" in output.lower() or "not found" in output.lower():
                self.text.insert(tk.END, output + "\n", "error")
            else:
                self.text.insert(tk.END, output + "\n", "output")
                
        self.show_prompt()
        return "break"
        
    def write(self, text: str, tag: str = "output"):
        self.text.insert(tk.END, text, tag)
        self.text.see(tk.END)

class FileManagerWidget(tk.Frame):
    """Виджет файлового менеджера"""
    def __init__(self, parent, fs_instance):
        super().__init__(parent, bg=Color.WINDOW_BG, highlightthickness=0)
        self.fs = fs_instance
        
        # Панель навигации
        nav_frame = tk.Frame(self, bg=Color.WINDOW_BORDER)
        nav_frame.pack(fill=tk.X, padx=2, pady=2)
        
        self.path_var = tk.StringVar(value=fs_instance.cwd)
        path_entry = tk.Entry(nav_frame, textvariable=self.path_var,
                             bg=Color.BG, fg=Color.FG,
                             font=("Consolas", 10), relief=tk.FLAT)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        path_entry.bind("<Return>", lambda e: self.navigate())
        
        btn_up = tk.Button(nav_frame, text="↑", command=self.go_up,
                          bg=Color.ACCENT, fg="black", relief=tk.FLAT)
        btn_up.pack(side=tk.RIGHT, padx=2, pady=2)
        
        # Список файлов
        self.file_list = tk.Listbox(self, bg=Color.BG, fg=Color.FG,
                                   font=("Consolas", 10), selectbackground=Color.ACCENT,
                                   selectforeground="black", relief=tk.FLAT,
                                   highlightthickness=0)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.file_list.bind("<Double-Button-1>", self.on_double_click)
        
        self.refresh()
        
    def refresh(self):
        self.file_list.delete(0, tk.END)
        try:
            items = self.fs.ls(detailed=True)
            for item in items:
                name = item.get('name', '')
                ftype = item.get('type', 'file')
                icon = "📁" if ftype == 'dir' else "📄"
                self.file_list.insert(tk.END, f"{icon} {name}")
        except Exception as e:
            self.file_list.insert(tk.END, f"Error: {e}")
            
    def navigate(self):
        path = self.path_var.get()
        try:
            self.fs.cd(path)
            self.path_var.set(self.fs.cwd)
            self.refresh()
        except Exception as e:
            pass
            
    def go_up(self):
        self.fs.cd("..")
        self.path_var.set(self.fs.cwd)
        self.refresh()
        
    def on_double_click(self, event):
        selection = self.file_list.curselection()
        if not selection:
            return
        idx = selection[0]
        # Упрощенная логика перехода
        self.navigate()

class GUIEngine:
    """Основной движок GUI в стиле Grey Hack"""
    def __init__(self, shell_instance):
        self.shell = shell_instance
        self.root = tk.Tk()
        self.root.title("Kali Linux Simulator - Grey Hack Edition")
        self.root.geometry("1024x768")
        self.root.configure(bg=Color.BG)
        self.root.resizable(True, True)
        
        # Полноэкранный режим (опционально)
        # self.root.attributes('-fullscreen', True)
        
        # Canvas для отрисовки интерфейса
        self.canvas = tk.Canvas(self.root, bg=Color.BG, 
                               highlightthickness=0, width=1024, height=768)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # CRT эффект
        self.crt = CRTFilter(self.canvas, 1024, 768)
        
        # Меню задач (Taskbar)
        self.taskbar_y = 738
        self.draw_taskbar()
        
        # Окна
        self.windows: List[Window] = []
        self.active_window: Optional[Window] = None
        
        # Обработчики событий мыши для перетаскивания окон
        self.setup_mouse_handlers()
        
        # Авто-запуск терминала
        self.open_terminal()
        
    def draw_taskbar(self):
        """Рисует панель задач внизу экрана"""
        self.canvas.create_rectangle(
            0, self.taskbar_y, 1024, 768,
            fill="#161b22", outline="#30363d"
        )
        self.canvas.create_text(
            10, self.taskbar_y + 15, text="🐉 Kali", 
            fill=Color.FG, font=("Consolas", 12, "bold"), anchor="w"
        )
        # Часы
        self.clock_id = self.canvas.create_text(
            1014, self.taskbar_y + 15, text="00:00",
            fill=Color.FG, font=("Consolas", 10), anchor="e"
        )
        self.update_clock()
        
    def update_clock(self):
        current = time.strftime("%H:%M")
        self.canvas.itemconfig(self.clock_id, text=current)
        self.root.after(1000, self.update_clock)
        
    def setup_mouse_handlers(self):
        """Настройка обработки мыши для окон"""
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
    def on_mouse_down(self, event):
        """Клик по окну или заголовку"""
        # Поиск окна под курсором (с конца списка, т.к. верхние поверх)
        for win in reversed(self.windows):
            if (win.x <= event.x <= win.x + win.w and
                win.y <= event.y <= win.y + win.h):
                
                # Клик по кнопке закрытия
                if (event.x >= win.x + win.w - 20 and event.x <= win.x + win.w - 5 and
                    event.y >= win.y + 5 and event.y <= win.y + 20):
                    self.close_window(win)
                    return
                    
                # Клик по заголовку - начало перетаскивания
                if event.y <= win.y + 25:
                    win.dragging = True
                    win.drag_offset = (event.x - win.x, event.y - win.y)
                    win.update_z_order(time.time())
                    self.active_window = win
                    return
                    
                # Активация окна
                win.update_z_order(time.time())
                self.active_window = win
                return
                
    def on_mouse_drag(self, event):
        """Перетаскивание окна"""
        if self.active_window and self.active_window.dragging:
            dx = event.x - self.active_window.drag_offset[0] - self.active_window.x
            dy = event.y - self.active_window.drag_offset[1] - self.active_window.y
            self.active_window.move(dx, dy)
            
    def on_mouse_up(self, event):
        """Отпускание мыши"""
        if self.active_window:
            self.active_window.dragging = False
            
    def open_terminal(self):
        """Открывает новое окно терминала"""
        win = Window(self, "Terminal", 50, 50, 600, 400)
        term_widget = TerminalWidget(self.root, self.shell)
        win.set_content(term_widget)
        self.windows.append(win)
        self.active_window = win
        
    def open_file_manager(self):
        """Открывает файловый менеджер"""
        win = Window(self, "File Manager", 100, 100, 500, 350)
        fm_widget = FileManagerWidget(self.root, self.shell.fs)
        win.set_content(fm_widget)
        self.windows.append(win)
        
    def close_window(self, win: Window):
        """Закрывает окно"""
        if win.close_callback:
            win.close_callback()
        win.destroy()
        self.windows.remove(win)
        if self.active_window == win:
            self.active_window = None
            
    def run(self):
        """Запуск главного цикла"""
        self.root.mainloop()

def launch_gui(shell_instance):
    """Точка входа для запуска GUI"""
    engine = GUIEngine(shell_instance)
    engine.run()
