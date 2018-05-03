import os
import sys
from os.path import dirname, abspath
# import modules defined at ../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import json
from objects import spec_run


try:
    with open("gui/properties.json") as properties_file:
        properties = json.load(properties_file)
except:
    with open("properties.json") as properties_file:
        properties = json.load(properties_file)

run_list = ['Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3', 'Run1', 'Run2', 'Run3']

class MainWindow(Frame):
    def __init__(self, *args, **kwargs):
        self.RUN_CONFIG = [os.path.dirname(os.path.abspath('../example_config.json')) + '/example_config.json']
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
        menubar.add_cascade(label=properties["commands"]["file"]["title"], menu=filemenu)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["import_runlist"], command=self.import_runlist)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["import_runtypes"], command=self.import_runtypes)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["load_group"], command=self.load_group)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["save_as"], command=self.save_as)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["new_run"], command=self.create_new_run)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["run_group"], command=self.run_group)
        filemenu.add_separator()
        filemenu.add_command(label=properties["commands"]["file"]["items"]["exit"], command=self.on_close)

        # Edit Menu
        editmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=properties["commands"]["edit"]["title"], menu=editmenu)
        editmenu.add_command(label=properties["commands"]["edit"]["items"][0], command='')
        editmenu.add_command(label=properties["commands"]["edit"]["items"][1], command='')

        # Help Menu
        helpmenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label=properties["commands"]["help"]["title"], menu=helpmenu)
        helpmenu.add_command(label=properties["commands"]["help"]["items"][0], command='')
        helpmenu.add_command(label=properties["commands"]["help"]["items"][1], command='')

        # Publish Menu
        self.master.config(menu=menubar)

        self.counter = 1

        # Create scroll list
        self.listbox = Listbox(self, width=20, height=self.height, relief="sunken", font="Arial")
        self.list_scrollbar = Scrollbar(self)
        self.listbox.config(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side="left", expand=True, fill="both")
        self.list_scrollbar.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Button-3>", self.popup_window)

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

    def create_new_run(self):
        """
        create a new window for choosing a runtype
        """
        self.new_run_window = Toplevel(self)
        self.new_run_window.title("Choose Runtype")
        self.new_run_window.minsize(width=25, height=20)
        runtypes = return_run_types()[0]
        var = StringVar()
        for type in runtypes:
            chk = Radiobutton(self.new_run_window, text=type, value=type, variable=var)
            chk.pack(anchor='w', expand=NO, padx=60)
        Button(self.new_run_window, text='Confirm', command=lambda: self.add_new_run(var.get())).pack(anchor='s')

    def add_new_run(self, runtype):
        """
        add a new run into the end of runlist
        :param runtype: string
        """
        self.new_run_window.destroy()
        self.listbox.insert(END, runtype)

    def save_group(self):
        # save stuff
        pass

    def load_group(self):
        filetuples = filedialog.askopenfilenames(title="Select file",
                                               filetypes=(("JSON file", "*.json"), ("All files", "*.*")))
        # json file loaded
        pass

    def save_as(self):
        pass

    def import_runlist(self):
        """
        load config file
        """
        filetuples = filedialog.askopenfilenames(title="Select file",
                                                 filetypes=(("JSON file", "*.json"), ("All files", "*.*")))
        if filetuples:
            self.RUN_CONFIG.append(filetuples[0])

    def import_runtypes(self):
        # NOT NEEDED
        pass

    def run_group(self):
        # call CLI function
        pass

    def on_close(self):
        if messagebox.askyesno("Exit", "Are you sure to exit?"):
            self.quit()

    def popup_window(self, event):
        """
        create a popup window for right clicking on an item in listbox
        allow to delete or duplicate the selected item
        """
        popup_menu = Menu(self.listbox, tearoff=0)
        # item = self.listbox.get(self.listbox.curselection())
        popup_menu.add_command(label='Delete', command=lambda: self.listbox.delete(self.listbox.curselection()))
        popup_menu.add_command(label='Duplicate', command=lambda: self.listbox.insert(END, self.listbox.get(self.listbox.curselection())))
        popup_menu.tk_popup(event.x_root, event.y_root)


def return_run_types():
    path_to_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'example_tate_config.json')
    with open(path_to_json, 'r') as json_file:
        parsed = json.load(json_file)
        return [parsed["TemplateData"].keys()]


if __name__ == '__main__':
    master = Tk()
    MainWindow(master).pack(fill="both", expand=True)
    master.mainloop()
