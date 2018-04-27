import os
import sys
sys.path.append('..')
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import json
from gui.multiListBox import MultiColumnListbox
import mainCLI as cli

with open("properties.json") as properties_file:
    properties = json.load(properties_file)


class MainWindow(Frame):
    def __init__(self):
        super().__init__()
        self.master.title(properties["program_name"])
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.minsize(width=properties["main_window"]["width"], height=properties["main_window"]["height"])

        menubar = Menu(self.master)

        # File Menu
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=properties["commands"]["cascades"]["file"]["title"], menu=filemenu)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][0], command=self.create_group)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][1], command=self.save_group)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][2], command=self.run_group)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][3], command=self.load_group)
        # Doesn't work yet.
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][4], command='')
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][5], command='')
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][6], command='')
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][7], command='')
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][8], command='')
        filemenu.add_separator()
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][9], command='')

        # Edit Menu
        editmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=properties["commands"]["cascades"]["edit"]["title"], menu=editmenu)
        editmenu.add_command(label=properties["commands"]["cascades"]["edit"]["items"][0], command='')
        editmenu.add_command(label=properties["commands"]["cascades"]["edit"]["items"][1], command='')

        # Help Menu
        helpmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=properties["commands"]["cascades"]["help"]["title"], menu=helpmenu)
        helpmenu.add_command(label=properties["commands"]["cascades"]["help"]["items"][0], command='')
        helpmenu.add_command(label=properties["commands"]["cascades"]["help"]["items"][1], command='')

        # Publish Menu
        self.master.config(menu=menubar)
        list_group = MultiColumnListbox()

    # def run_window(self):
    #     run_types = return_run_types()[0]
    #
    #     print(run_types)
    #     main = Toplevel(self)
    #     main.grid()
    #
    #     v = StringVar()
    #     v.set("L")  # initialize
    #     for key in run_types:
    #         b = Radiobutton(main, text=key,
    #                         variable=v, value=key)
    #         b.pack(anchor=W)
    #     my_button = Button(main, text="Submit", command='')
    #     my_button.pack()
    #     # my_button.grid(5, column=1)


    def create_group(self):
        # create a group
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


def return_run_types():
    path_to_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'runtype_options.json')
    with open(path_to_json, 'r') as json_file:
        parsed = json.load(json_file)
        return [parsed.keys()]


if __name__ == '__main__':
    master = Tk()
    MainWindow()
    master.mainloop()
