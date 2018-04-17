from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from multiListBox import *
import properties
import sys, os.path
sys.path.append(os.path.abspath('../'))
import dialogue as d

class MainWindow(Frame):
    def __init__(self):
        super().__init__()
        self.master.title("Spec Configurator")
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.minsize(width=d.read_json('properties.json')["main_window"]["width"],
                            height=d.read_json('properties.json')["main_window"]["height"])
        menubar = Menu(self.master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Create Group", command=self.create_group)
        filemenu.add_command(label="Save Group", command=self.save_group)
        filemenu.add_command(label="Load Group", command=self.load_group)
        filemenu.add_command(label="Run Group", command=self.run_group)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=filemenu)
        self.master.config(menu=menubar)

        list_group = MultiColumnListbox()

    def create_group(self):
        # call CLI function
        pass

    def save_group(self):
        pass

    def load_group(self):
        filetuples = filedialog.askopenfilenames(title="Select file",
                                               filetypes=(("JSON file", "*.json"), ("All files", "*.*")))
        # pass file onto CLI function
        pass

    def run_group(self):
        # call CLI function
        pass

    def on_close(self):
        if messagebox.askyesno("Exit", "Are you sure to exit?"):
            self.quit()


if __name__ == '__main__':
    master = Tk()
    master.resizable(0,0)
    MainWindow()
    master.mainloop()
