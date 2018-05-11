#!/usr/bin/python3

from run_manager import RunManager
import os
import sys
import json
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import webbrowser


# import modules defined at ../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../src/')  # @todo: avoid PYTHONPATH

try:
    with open("gui/properties.json") as properties_file:
        properties = json.load(properties_file)
except FileNotFoundError:
    with open("properties.json") as properties_file:
        properties = json.load(properties_file)


class MainWindow(Frame):
    def __init__(self, *args, **kwargs):
        self.colors = {'canvas': 'white',
                       'label': 'white',
                       'frame': 'white',
                       'entry': 'white',
                       'text': 'white'}
        self.font = "Calibri"
        Frame.__init__(self, *args, **kwargs)
        self.form, self.arg_label, self.tater, self.new_run_window, self.menu_bar = None, None, None, None, None
        self.run_manager = RunManager(config_file=None)
        self.width = properties["main_window"]["width"]
        self.height = properties["main_window"]["height"]
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.master.minsize(width=self.width, height=self.height)
        self.master.geometry("%dx%d" % (self.width, self.height))

        self.publish_menu()

        self.left_frame = Frame(self.master, background=self.colors['frame'],
                                borderwidth=5, relief=RIDGE,
                                height=250,
                                width=50)
        self.right_frame = Frame(self.master, background=self.colors['frame'],
                                 borderwidth=5, relief=RIDGE,
                                 height=250,
                                 width=50)
        self.left_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        self.right_frame.pack(side=RIGHT, fill=BOTH, expand=YES)

        # Create scroll list
        self.listbox = Listbox(self.left_frame, width=20, height=self.height, relief=GROOVE, font=("Arial", 14),
                               selectmode=EXTENDED)
        self.list_scrollbar = Scrollbar(self)
        self.listbox.config(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.config(orient=VERTICAL, command=self.listbox.yview)
        self.listbox.pack(side="left", expand=True, fill="both")
        self.list_scrollbar.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind('<2>' if self.master.tk.call('tk', 'windowingsystem') == 'aqua' else '<3>', self.popup_window)
        self.listbox.bind("<ButtonPress-1>", self.on_run_press)
        self.listbox.bind("<B1-Motion>", self.on_run_motion)
        # self.listbox.bind("<ButtonRelease-1>", self.reorder_runs)

        # Create popup menu
        self.popup_menu = Menu(self.listbox, tearoff=0)
        self.popup_menu.add_command(label='Delete', command=lambda: self.delete_selected(self.listbox.curselection()))
        self.popup_menu.add_command(label='Duplicate',
                                    command=lambda: self.duplicate_selected(self.listbox.curselection()))

        # Create canvas
        self.canvas = Canvas(self.right_frame, width=80, height=self.height, bg=self.colors['canvas'], relief=GROOVE)
        self.canvas.config(scrollregion=(0, 0, 300, 650), highlightthickness=0)
        self.canvas.pack(side="right", expand=True, fill="both")

        # Update gui with contents from run manager
        self.update()

    def update(self):
        self.master.title(properties["program_name"] + " - " + self.run_manager.RUN_CONFIG)
        self.listbox.delete(0, END)
        i = 0
        run_list = self.run_manager.get_run_list_tags()
        if run_list is not None:
            while i < len(run_list):
                self.listbox.insert(i, run_list[i])
                i += 1

    def create_tag(self):
        """
        Will be a naming convention for creating a run tag.
        :return:
        """
        pass

    def publish_menu(self):
        self.menu_bar = Menu(self.master)

        # File Menu
        file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["file"]["title"], menu=file_menu)
        file_menu.add_command(label=properties["commands"]["file"]["items"]["new_run"],
                              command=self.create_new_run)
        file_menu.add_command(label=properties["commands"]["file"]["items"]["new_runtype"], command='')
        file_menu.add_command(label=properties["commands"]["file"]["items"]["save"],
                              command=self.save)
        file_menu.add_command(label=properties["commands"]["file"]["items"]["save_as"], command=self.save_as)
        file_menu.add_command(label=properties["commands"]["file"]["items"]["import_config"],
                              command=self.import_runlist)
        file_menu.add_separator()
        file_menu.add_command(label=properties["commands"]["file"]["items"]["exit"], command=self.on_close)

        # Edit Menu
        edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["edit"]["title"], menu=edit_menu)
        edit_menu.add_command(label=properties["commands"]["edit"]["items"]["undo"], command='')
        edit_menu.add_command(label=properties["commands"]["edit"]["items"]["redo"], command='')

        # Help Menu
        help_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["help"]["title"], menu=help_menu)
        help_menu.add_command(label=properties["commands"]["help"]["items"]["wiki"],
                              command=lambda: webbrowser.open("https://github.com/PDXCapstoneF/SPECtate/wiki"))
        help_menu.add_command(label=properties["commands"]["help"]["items"]["issues"],
                              command=lambda: webbrowser.open("https://github.com/PDXCapstoneF/SPECtate/issues/new"))

        # Publish Menu
        self.master.config(menu=self.menu_bar)

    def make_arg_form(self, fields):
        entries = {}
        if self.canvas is not None:
            self.canvas.destroy()
            try:
                self.tater = PhotoImage(file="tater.pgm").zoom(5).subsample(50)
            except:
                self.tater = PhotoImage(file="gui/tater.pgm").zoom(5).subsample(50)
            self.canvas = Canvas(self.right_frame,
                                 width=80,
                                 height=self.height,
                                 bg=self.colors['canvas'],
                                 relief=GROOVE)
            self.canvas.pack(side="right", expand=True, fill="both")
        if fields is None:
            self.canvas.create_image(5, 5, image=self.tater, anchor='nw', state=NORMAL)  # Label
            self.arg_label = Label(self.canvas,
                                   text="Well this is weird... I don't have anything to show you.",
                                   # relief=SUNKEN,
                                   font=("Calibri", 12),
                                   width=64,
                                   justify=LEFT)
            self.arg_label.grid(row=50, column=1, sticky=W)

        if fields is not None:
            for idx, i in enumerate(fields):
                self.form = Entry(self.canvas,
                                  insertofftime=500,
                                  font=("Calibri", 12),
                                  bg=self.colors['text'],
                                  width=8,
                                  relief=RIDGE, highlightcolor='black',
                                  fg='black',
                                  justify=CENTER)
                self.form.insert(INSERT, "default")
                entries[i] = self.form
                var = StringVar()
                var.set(fields[i])

                # Label
                self.arg_label = Label(self.canvas,
                                       textvariable=var,
                                       relief=RAISED,
                                       font=("Calibri", 12),
                                       width=64,
                                       justify=LEFT)
                self.form.grid(row=idx, column=0, sticky=W)
                self.arg_label.grid(row=idx, column=1, sticky=W)

        return entries

    def on_select(self, event):
        selection = event.widget.curselection()
        if selection:
            content = event.widget.get(selection[0])
            if self.run_manager.compare_tags(a=self.run_manager.get_current_run(), b=self.run_manager.get_run_from_list(content)):
                print("MainWindow continues to edit the same run.")
            else:
                print("MainWindow switched to new run.")
                self.run_manager.set_current_run(content)
            self.make_arg_form(fields=self.run_manager.get_template_type_args(self.run_manager.get_run_from_list(content)))

    def popup_window(self, event):
        """
        Create a popup window for right clicking on an item in listbox
        allow to delete or duplicate the selected item
        """
        widget = event.widget
        index = widget.nearest(event.y)
        # check if right click on blank space
        _, yoffset, _, height = widget.bbox(index)
        if event.y > height + yoffset + 5:
            return

        selection = self.listbox.curselection()
        if index not in selection:
            self.listbox.selection_clear(0, END)
        self.listbox.select_set(index)
        self.listbox.activate(index)
        self.popup_menu.tk_popup(event.x_root, event.y_root)

    def delete_selected(self, selection):
        # for item in selection[::-1]:
        #     # @todo: RunManager call here
        #     self.listbox.delete(item)
        # iterate from end to beginning, loop
        for item in selection[::-1]:
            removed = self.run_manager.remove_run(tag_to_remove=self.listbox.get(item))
            self.listbox.delete(item)

    def duplicate_selected(self, selection):
        for item in selection:
            inserted = self.run_manager.duplicate_run(from_tag=self.listbox.get(item))
            if inserted is not None and isinstance(inserted, dict):
                self.listbox.insert(END, inserted["args"]["Tag"])

    def save(self):
        self.run_manager.write_to_file()

    def save_as(self):
        filepath = filedialog.asksaveasfilename(title="Select file",
                                                filetypes=(("JSON file", "*.json"), ("All files", "*.*")),
                                                defaultextension=".json")
        if filepath:
            if filepath == self.run_manager.RUN_CONFIG:
                self.save()
            else:
                self.run_manager.write_to_file(filepath)

    def on_close(self):
        if messagebox.askyesno("Exit", "Are you sure to exit?"):
            self.prompt_save()
            self.quit()
        else:
            return

    def prompt_save(self):
        if messagebox.askyesno("Save", "Would you like to save before exiting?"):
            self.save()

    def create_new_run(self):
        """
        create a new window for choosing a runtype
        """
        button_results = None
        self.new_run_window = Toplevel(self)
        self.new_run_window.title("Choose Runtype")
        self.new_run_window.minsize(width=25, height=20)
        runtypes = self.run_manager.get_template_types()[0]
        var = StringVar(value="0")
        for idx, runtype in enumerate(runtypes):
            chk = Radiobutton(self.new_run_window,
                              text=runtype,
                              variable=var,
                              value=runtype)
            chk.pack(anchor='w', padx=60)
        button = Button(self.new_run_window,
                        text='Confirm',
                        variable=button_results,
                        command=lambda: self.add_new_run(var))
        button.pack(anchor='s')

    def add_new_run(self, runtype):
        """
        add a new run into the end of runlist
        :param runtype: string
        """
        # @todo: create the run object. Then call self.run_man to add to list.
        runtype = runtype.get()
        self.new_run_window.destroy()
        run = self.run_manager.create_run(runtype)
        self.listbox.insert(END, run)
        # self.run_manager.insert_into_config_list("RunList", run)

    def save_group(self):
        # @todo: is this needed?
        # save stuff
        pass

    def import_runlist(self):
        """
        load config file
        """
        filepath = filedialog.askopenfilename(title="Select file",
                                              filetypes=(("JSON file", "*.json"), ("All files", "*.*")),
                                              defaultextension=".json")
        if filepath:
            if filepath != self.run_manager.RUN_CONFIG:
                self.prompt_save()
                self.run_manager = RunManager(config_file=filepath)
                self.update()

    def on_run_press(self, event):
        """
        Select the index when pressing the left mouse
        """
        self.curIndex = -1
        widget = event.widget
        index = widget.nearest(event.y)
        # check if the click on blank space
        _, yoffset, _, height = widget.bbox(index)
        if event.y > height + yoffset + 5:
            return
        self.curIndex = self.listbox.nearest(event.y)

    def on_run_motion(self, event):
        """
        move the selected item to the new mouse position
        """
        if self.curIndex == -1:
            return
        i = self.listbox.nearest(event.y)
        if i < self.curIndex:
            x = copy.deepcopy(self.listbox.get(i))
            self.listbox.delete(i)
            self.listbox.insert(i+1,x)
            self.run_manager.update_run_index(index=i+1, tag_to_remove=self.listbox.get(x))
        elif i > self.curIndex:
            x = copy.deepcopy(self.listbox.get(i))
            self.listbox.delete(i)
            self.listbox.insert(i-1,x)
            self.run_manager.update_run_index(index=i-1, tag_to_remove=self.listbox.get(x))


if __name__ == '__main__':
    master = Tk()
    MainWindow(master).pack(fill="both", expand=True)
    master.mainloop()
