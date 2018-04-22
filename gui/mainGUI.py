import os
import sys
sys.path.append('..')
# sys.path.append('/SPECtate/')
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import json
from multiListBox import MultiColumnListbox

import mainCLI as cli
from functools import partial


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
        filemenu.add_separator()
        filemenu.add_command(label=properties["commands"]["cascades"]["file"]["items"][4], command=self.on_close)

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

    def create_group(self):
        temp_options = ['option_a', 'option_b', 'option_c']
        user_input = self.create_form(temp_options, vertical=True)
        # print(user_input)
        # call CLI function with user_input

    def create_form(self, options, vertical=True):
        """
        Renders a basic form for user to fill in entries. Can be rendered
        vertically or horizontally.
        :param options: list
        :param vertical: bool
        """
        # self.grid() // is this needed?

        def display_user_input(entries=None):
            for idx, i in enumerate(entries):
                value = entries[idx].get()
                print("value of entry %s is %s" % (i, value))

        # Can obviously be done better, but it works for now
        def render_vertical(options):
            """
            Populate vertical form for user input, (nX2 [rowXcolumn]) dimensions.
            :param options: list
            :return: [Entry]
            """
            main = Toplevel(self)
            main.grid()
            entries = []

            # Generate tk.Label(s) & tk.Entry(s) for the form
            for i in range(len(options)):
                label = Label(main, text=options[i])
                label.grid(row=i, column=0)
                entry = Entry(main)  # textvariable=val (capture user input)
                entry.grid(row=i, column=1)
                entries.append(entry)

            # Submit button with hook to display user input (doesn't work)
            my_button = Button(main, text="Submit", command=partial(display_user_input, entries))
            my_button.grid(row=len(options), column=1)

            return entries

        return render_vertical(options)
        #display_user_input(entries)

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
