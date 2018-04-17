from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from multiListBox import *
import json
import mainCLI

with open("properties.json") as properties_file:
    properties = json.load(properties_file)


class MainWindow(Frame):
    def __init__(self):
        super().__init__()
        self.master.title(properties["program_name"])
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.minsize(width=properties["main_window"]["width"], height=properties["main_window"]["height"])
        menubar = Menu(self.master)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label=properties["commands"]["create"], command=self.create_group)
        filemenu.add_command(label=properties["commands"]["save"], command=self.save_group)
        filemenu.add_command(label=properties["commands"]["load"], command=self.load_group)
        filemenu.add_command(label=properties["commands"]["run"], command=self.run_group)
        filemenu.add_separator()
        filemenu.add_command(label=properties["commands"]["exit"], command=self.on_close)
        menubar.add_cascade(label=properties["commands"]["file"], menu=filemenu)
        self.master.config(menu=menubar)

        list_group = MultiColumnListbox()

    def create_group(self):
        # create stuff
        pass

    def save_group(self):
        # save stuff
        pass

    def load_group(self):
        filetuples = filedialog.askopenfilenames(title="Select file",
                                               filetypes=(("JSON file", "*.json"), ("All files", "*.*")))
        # json file loaded
        pass

    def run_group(self):
        # call CLI function
        pass

    def on_close(self):
        if messagebox.askyesno("Exit", "Are you sure to exit?"):
            self.quit()


if __name__ == '__main__':
    master = Tk()
    MainWindow()
    master.mainloop()
