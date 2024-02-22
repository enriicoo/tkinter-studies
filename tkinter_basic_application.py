import os  # Standard library imports
import re
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import timeit
import time
import warnings
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
from tkinter.ttk import Progressbar
from tkinter import PhotoImage, Label
from PIL import Image, ImageTk

class StuffClass:
    def __init__(self, numbers=None, debug_mode=False, threads=1):
        self.total = 0
        self.partial = 0
        self.errors = 0
        self.dummy_a = 0
        self.debugger = debug_mode
        self.numbers = numbers
        self.threads = threads
        self.lock = threading.Lock()
        self.results = []

        if numbers is not None and not all(isinstance(num, (int, float)) for num in numbers):
            raise ValueError("All items in 'numbers' must be integers or floats")

    def run(self):
        try:
            start_time = timeit.default_timer()
            self.partial = 0
            self.total = 0
            self.action_step1(self.numbers)
            self.action_step2()
            end_time = timeit.default_timer()
            print(f'Total: {self.errors} errors.')
            execution_time = end_time - start_time
            print(f"\nThe script took {int(execution_time)} seconds.")
        except Exception as e:
            print('Non-specific error in the process.')
            raise InterruptedError("Error", str(e) + "\n" + traceback.format_exc())

    def action_step1(self, numbers):
        def process_numbers(start, end):
            local_results = [(num, num**2) for num in numbers[start:end]]
            self.total = len(local_results)
            with self.lock:
                self.results = local_results.copy()

        n = len(numbers)
        part = n // self.threads
        threads = []

        for i in range(self.threads):
            start = i * part
            end = n if i + 1 == self.threads else (i + 1) * part
            t = threading.Thread(target=process_numbers, args=(start, end))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
        for num, squared in self.results:
            time.sleep(1)
            print(f"{num} squared is {squared}")
            self.partial = self.partial + 1

    @staticmethod
    def action_step2():
        print('End of process.')

class FrontEnd:
    class RootElement:
        def __init__(self, title, geometry='400x500', resizable=(False, False)):
            self.root = tk.Tk()
            self.configure(title, geometry, resizable)

        def configure(self, title, geometry, resizable):
            self.root.title(title)
            self.root.geometry(geometry)
            self.root.resizable(resizable[0], resizable[1])

    class BasicElement:
        def __init__(self, root, label_text, pad_y=5):
            self.root = root
            self.label_text = label_text
            self.label = tk.Label(self.root, text=self.label_text)
            self.label.pack(pady=pad_y)

    class DynamicElement:
        def __init__(self, root, text="", pad_y=5):
            self.label = tk.Label(root, text=text)
            self.label.pack(pady=pad_y)

    class InputElement(BasicElement):
        def __init__(self, root, label_text, entry_text=None):
            super().__init__(root, label_text)  # Call the initializer of the parent class
            self.entry = tk.Entry(root, width=50)
            self.entry.pack(pady=5)
            self.entry.insert(0, entry_text) if entry_text else None

    class BinaryElement(BasicElement):
        def __init__(self, root, label_text, front_end):
            super().__init__(root, label_text)
            self.front_end = front_end  # Save the FrontEnd instance

            self.debug_frame = tk.Frame(root)
            self.debug_frame.pack()

            self.debug_yes = tk.Radiobutton(self.debug_frame, text="Yes", value=True, command=self.set_debug_true)
            self.debug_yes.pack(side='left', padx=5)

            self.debug_no = tk.Radiobutton(self.debug_frame, text="No", value=False, command=self.set_debug_false)
            self.debug_no.pack(side='left', padx=5)

            self.debug_no.select()

        def set_debug_true(self):
            self.front_end.debugger = True

        def set_debug_false(self):
            self.front_end.debugger = False

    class LoadbarElement:
        def __init__(self, root, length, idle_path, running_path, pad_y=5, mode='determinate'):
            self.container = tk.Frame(root)  # Cria um Frame para conter a barra e o GIF
            self.style = ttk.Style()
            self.style.theme_use('clam')
            self.style_name = "TProgressbar"
            self.style.configure(self.style_name, troughcolor='white')

            # A barra de progresso é adicionada ao container
            self.progress = ttk.Progressbar(self.container, length=length, mode=mode, style=self.style_name)
            self.progress.pack(side='left', fill='x', expand=True, padx=10, pady=pad_y)

            # O GifElement agora usa o container como root
            self.gif = FrontEnd.GifElement(self.container, idle_path, running_path, height=60)
            self.gif.label.pack(side='left', padx=10)  # Adiciona o GIF à direita da barra de progresso
            self.container.pack(fill='x', pady=pad_y, padx=20)  # Empacota o container no root

    class GifElement:
        def __init__(self, root, idle_path, running_path, height):
            self.root = root
            self.frames_idle = self.load_frames(idle_path, height)
            self.frames_running = self.load_frames(running_path, height)
            self.current_frames = self.frames_idle
            self.label = Label(self.root, image=self.current_frames[0])
            self.label.pack(side='left', padx=0)
            self.animation_loop = None

        def load_frames(self, gif_path, target_height):
            frames = []
            with Image.open(gif_path) as img:
                for i in range(img.n_frames):
                    img.seek(i)
                    aspect_ratio = img.width / img.height
                    new_width = int(aspect_ratio * target_height)
                    frame = ImageTk.PhotoImage(img.resize((new_width, target_height), Image.Resampling.NEAREST))
                    frames.append(frame)
            return frames

        def animate(self, frame_list, frame_index=0):
            if self.animation_loop:
                self.root.after_cancel(self.animation_loop)
            frame = frame_list[frame_index]
            self.label.config(image=frame)
            frame_index = (frame_index + 1) % len(frame_list)
            self.animation_loop = self.root.after(100, lambda: self.animate(frame_list, frame_index))

        def set_position(self, state):
            if state == 'idle':
                self.animate(self.frames_idle)
            elif state == 'running':
                self.animate(self.frames_running)

        def stop_animation(self):
            if self.animation_loop:
                self.root.after_cancel(self.animation_loop)
                self.animation_loop = None

    class TextRedirector:
        def __init__(self, widget):
            self.widget = widget

        def write(self, string):
            self.widget.insert(tk.END, string)
            self.widget.see(tk.END)  # Scroll to the end of the text widget

        def flush(self):  # Required for the redirection
            pass

    def __init__(self, stuffclass):
        self.stuffclass = stuffclass  # Attributes to transmit variables and inputs between FrontEnd and StuffClass
        self.running = False
        self.debugger = False
        self.process_thread = None
        self.font_name = "Arial"
        self.font_size = 10
        self.tk_root = self.RootElement(title='Stuff Doer', geometry='400x500').root
        self.file_path = "C:/Users/"
        self.path_element = self.InputElement(self.tk_root, entry_text=self.file_path,
                                              label_text= "Directory: (enter a .txt with numbers separated by commas)")
        self.numbers_entry = self.InputElement(self.tk_root, entry_text="1,2,3,4,5",
                                               label_text="Numbers: (enter a list of numbers separated by commas)")
        self.debug_element = self.BinaryElement(self.tk_root, "Do you want debug information?", self)
        self.load_element = self.LoadbarElement(self.tk_root, length=100, pad_y=5, idle_path="idle.gif",
                                                running_path="running.gif")
        self.process_button = tk.Button(self.tk_root, text="Process stuff", command=self.tkinter_process_stuff)
        self.process_button.pack(pady=0)
        self.status_label = self.DynamicElement(self.tk_root)
        self.end_label = self.DynamicElement(self.tk_root)
        self.update_labels()
        self.console = tk.scrolledtext.ScrolledText(self.tk_root, height=10, width=50, font=(self.font_name, 8))
        self.console.place(x=10, y=350, width=380, height=140)
        sys.stdout = self.TextRedirector(self.console)
        self.tk_root.after(1000, self.update_labels)
        self.tk_root.mainloop()

    def update_labels(self):
        total = self.stuffclass.total
        partial = self.stuffclass.partial
        if total == 0 and partial == 0:
            self.load_element.gif.set_position('idle')
            self.load_element.progress['value'] = 0
        elif total != 0 and partial == 0:
            self.status_label.label.config(text=f'Counting: {total} stuff to the moment')
            self.load_element.style.configure("TProgressbar", troughcolor='white',
                                              background='#78d8f0')
            self.load_element.gif.set_position('running')
        elif partial != 0:
            percentages = int(partial * 100 / total)
            self.status_label.label.config(text=f'{partial} from {total} stuff - {percentages}%')
            self.load_element.progress['value'] = percentages
            if total == partial:
                self.status_label.label.config(text=f'Analysis of {total} stuff complete')
                self.load_element.style.configure("TProgressbar", troughcolor='white', background='#0040f0')
                self.load_element.gif.set_position('idle')

        if self.process_thread and not self.process_thread.is_alive():
            self.end_label.label['text'] = 'OK - Process complete'
            self.running = False
        self.tk_root.after(ms=1000, func=self.update_labels)

    def tkinter_process_stuff(self):
        self.file_path = self.path_element.entry.get()
        if not self.file_path and not self.numbers_entry.entry.get():
            messagebox.showerror("Error", "Please provide a directory or a list of numbers.")
            return
        self.status_label.label['text'] = "Waiting..."
        self.end_label.label['text'] = ''

        if self.numbers_entry.entry.get():
            try:
                numbers_list = [int(num.strip()) for num in self.numbers_entry.entry.get().split(',')]
                self.stuffclass.numbers = numbers_list
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numbers.")
                return
        elif self.file_path:
            try:
                with open(self.file_path, 'r') as file:
                    numbers_string = file.read()
                numbers_list = [int(num.strip()) for num in numbers_string.split(',')]
                self.stuffclass.numbers = numbers_list
            except ValueError:
                messagebox.showerror("Error", "The file contains invalid numbers.")
                return
            except FileNotFoundError:
                messagebox.showerror("Error", "The file was not found.")
                return
        self.running = True
        self.process_thread = threading.Thread(target=self.stuffclass.run)
        self.process_thread.start()
        self.update_labels()


FrontEnd(StuffClass())
