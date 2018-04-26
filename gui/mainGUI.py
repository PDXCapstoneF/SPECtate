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

run_list = ['Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3']


class MainWindow(Frame):
    def __init__(self, *args, **kwargs):
        Frame.__init__(self, *args, **kwargs)
        self.width = properties["main_window"]["width"]
        self.height = properties["main_window"]["height"]
        self.master.title(properties["program_name"])
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.minsize(width=self.width, height=self.height)
        self.master.geometry("%dx%d" % (self.width, self.height))

        menubar = Menu(self.master)

        # File Menu
        filemenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=properties["commands"]["cascades"]["file"]["title"], menu=filemenu)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][0], command=self.create_group)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][1], command=self.save_group)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][2], command=self.run_group)
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][3], command=self.load_group)
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

        self.counter = 1

        # Create scroll list
        self.listbox = Listbox(self, width=20, height=self.height, relief="sunken", font="Arial")
        self.list_scrollbar = Scrollbar(self)
        self.listbox.config(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side="left", expand=True, fill="both")
        self.list_scrollbar.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Create canvas
        self.canvas = Canvas(self, width=80, height=self.height, bg="white", relief="sunken")
        self.canvas.config(scrollregion=(0, 0, 300, 650), highlightthickness=0)
        self.canvas.pack(side="left", expand=True, fill="both")

        # Create a dummy text inside canvas
        self.form = Text(self.canvas, height=self.height, font="Arial")
        self.form.insert("end", "Click to see...")
        self.form.pack(expand=True, fill="both")

        # Add items to the listbox
        i = 0
        while i < len(run_list):
            self.listbox.insert(i, run_list[i])
            i += 1

    def on_select(self, event):
        selection = event.widget.curselection()
        if selection:
            content = event.widget.get(selection[0])
            if self.counter == 1:
                self.form.delete(1.0, "end") # CLEAR THE TEXT WHICH IS DISPLAYED AT FIRST RUNNING
                self.form.insert("end", content)
                self.counter += 1 #ONE ITEM HAS BEEN SELECTED AND PRINTED SUCCESSFULLY
            elif self.counter > 1:
                self.form.delete(1.0, "end")
                self.form.insert("end", content)
                self.counter = 1 # RESET THE COUNTER SO THAT NEXT SELECTED ITEM DISPLAYS PROPERLY

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
    MainWindow(master).pack(fill="both", expand=True)
    master.mainloop()
