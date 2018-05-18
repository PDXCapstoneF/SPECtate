#!/usr/bin/python3

from run_manager import RunManager
from tooltip import Tooltip
import os
import pathlib
import sys
import copy
import json
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import webbrowser


# import modules defined at ../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../src/')  # @todo: avoid PYTHONPATH
from src.benchmark_run import SpecJBBRun
from src.run_generator import RunGenerator

try:
    with open("gui/properties.json") as properties_file:
        properties = json.load(properties_file)
except FileNotFoundError:
    with open("properties.json") as properties_file:
        properties = json.load(properties_file)


class MainWindow(Frame):
    def __init__(self, *args, **kwargs):
        self.THEME = "light"
        self.colors = properties["main_window"]["themes"][self.THEME]
        self.font = "Calibri"
        Frame.__init__(self, *args, **kwargs)
        self.entries, self.arg_label, self.tater, self.new_theme_window, self.menu_bar = None, None, None, None, None
        self.run_manager = RunManager(config_file=None)
        self.width = properties["main_window"]["width"]
        self.height = properties["main_window"]["height"]
        self.master.title(properties["program_name"])

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
        self.listbox = Listbox(self.left_frame, width=20, height=self.height, relief=GROOVE, font="Arial",
                               selectmode=SINGLE, bg=self.colors["listbox_bg"], fg=self.colors["listbox_fg"])
        self.list_scrollbar = Scrollbar(self)
        self.listbox.config(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.config(orient=VERTICAL, command=self.listbox.yview) # bg=self.colors["scrollbar"]
        self.listbox.pack(side="left", expand=True, fill="both")
        self.list_scrollbar.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind('<2>' if self.master.tk.call('tk', 'windowingsystem') == 'aqua' else '<3>', self.popup_window)
        self.listbox.bind("<ButtonPress-1>", self.on_run_press)
        self.listbox.bind("<ButtonRelease-1>", self.on_run_motion)
        self.listbox.configure(exportselection=False)

        # Create popup menu
        self.popup_menu = Menu(self.listbox, tearoff=0)
        self.popup_menu.add_command(label='Delete', command=lambda: self.delete_selected(self.listbox.curselection()))
        self.popup_menu.add_command(label='Duplicate',
                                    command=lambda: self.duplicate_selected(self.listbox.curselection()))
        self.popup_menu.add_command(label='Run',
                                    command=lambda: self.do_runs(self.listbox.curselection()))

        # Create canvas
        self.canvas = Canvas(self.right_frame, width=80, height=self.height, bg=self.colors['canvas'], relief=GROOVE)
        self.canvas.config(scrollregion=(0, 0, 300, 650), highlightthickness=0)
        self.canvas.pack(side="right", expand=True, fill="both")

        # Update gui with contents from run manager
        self.update()

    def update(self):
        """
        Updates listbox.
        :return: none
        """
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
        # @todo
        Will be a naming convention for creating a run tag.
        :return:
        """
        pass

    def do_runs(self, selection):
        for item in selection:
            run = self.run_manager.do_run(tag=self.listbox.get(item))

    def theme_window(self):
        """
        create a new window for choosing a theme (copy-paste)
        """
        button_results = None
        self.new_theme_window = Toplevel(self)
        self.new_theme_window.title("Select Theme")
        self.new_theme_window.minsize(width=25, height=20)
        var = StringVar(value="0")
        for idx, theme in enumerate(properties["main_window"]["themes"].keys()):
            chk = Radiobutton(self.new_theme_window,
                              text=theme,
                              variable=var,
                              value=theme)
            chk.pack(anchor='w', padx=60)
        button = Button(self.new_theme_window,
                        text='Confirm',
                        variable=button_results,
                        command=lambda: self.set_theme(var))
        button.pack(anchor='s')
        # self.update()

    def set_theme(self, theme):
        theme = theme.get()
        for key, val in properties["main_window"]["themes"].items():
            if key == theme:
                self.colors = properties["main_window"]["themes"][theme]
                self.new_theme_window.destroy()
                self.update()
                self.listbox.configure(bg=properties["main_window"]["themes"][theme]["listbox_bg"],
                                       fg=properties["main_window"]["themes"][theme]["listbox_fg"],
                                       selectbackground=properties["main_window"]["themes"][theme]["listbox_select_bg"])
                return True
        else:
            return False

    def publish_menu(self):
        self.menu_bar = Menu(self.master)

        # File Menu
        file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["file"]["title"], menu=file_menu)
        file_menu.add_command(label=properties["commands"]["file"]["items"]["new_run"],
                              command=lambda: self.create_new_run(),  accelerator="Ctrl+n")
        file_menu.add_command(label=properties["commands"]["file"]["items"]["new_runtype"],
                              command='', accelerator="Ctrl+t")  # @todo
        file_menu.add_command(label=properties["commands"]["file"]["items"]["save"],
                              command=self.save, accelerator="Ctrl+s")
        file_menu.add_command(label=properties["commands"]["file"]["items"]["save_as"], command=self.save_as)
        file_menu.add_command(label=properties["commands"]["file"]["items"]["import_config"],
                              command=lambda: self.load_file(type="RunList"))
        file_menu.add_command(label=properties["commands"]["file"]["items"]["import_jar"],
                              command=lambda: self.load_file(type="SPECjbb"))
        file_menu.add_separator()
        file_menu.add_command(label=properties["commands"]["file"]["items"]["exit"], command=self.on_close,
                              accelerator="Ctrl+q")

        # Edit Menu
        edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["edit"]["title"], menu=edit_menu)

        # @todo: implement or remove.
        edit_menu.add_command(label=properties["commands"]["edit"]["items"]["undo"], command='')
        edit_menu.add_command(label=properties["commands"]["edit"]["items"]["redo"], command='')

        # Benchmark Menu
        benchmark_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["benchmark"]["title"], menu=benchmark_menu)
        benchmark_menu.add_command(label=properties["commands"]["benchmark"]["items"]["run_all"],
                                   command=lambda: self.run_manager.do_run(runs_list=list(self.listbox.get(0, END))),
                                   accelerator="Ctrl+r")

        # View Menu
        edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["view"]["title"], menu=edit_menu)
        edit_menu.add_command(label=properties["commands"]["view"]["items"]["theme"],
                              command=lambda: self.theme_window())

        # Help Menu
        help_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label=properties["commands"]["help"]["title"], menu=help_menu)
        help_menu.add_command(label=properties["commands"]["help"]["items"]["wiki"],
                              command=lambda: webbrowser.open("https://github.com/PDXCapstoneF/SPECtate/wiki"))
        help_menu.add_command(label=properties["commands"]["help"]["items"]["issues"],
                              command=lambda: webbrowser.open("https://github.com/PDXCapstoneF/SPECtate/issues/new"))

        # Publish Menu
        self.master.config(menu=self.menu_bar)

        # Shortcut commands
        self.master.bind('<Control-n>', lambda event: self.create_new_run())
        self.master.bind('<Control-s>', lambda event: self.save())
        self.master.bind('<Control-r>', lambda event: self.run_manager.do_run())
        self.master.bind('<Control-q>', lambda event: self.on_close())

    def make_arg_form(self, fields, args_list):
        self.entries = {}
        if self.canvas is not None:
            self.canvas.destroy()
            try:
                self.tater = PhotoImage(file="tater.pgm").zoom(5).subsample(50)
            except:
                self.tater = PhotoImage(file="gui/tater.pgm").zoom(5).subsample(50)
            self.canvas = Canvas(self.right_frame,
                                 width=80,
                                 height=self.height,
                                 bg=self.colors["canvas_bg"],
                                 #bg=self.colors['canvas'],
                                 relief=GROOVE)
            self.canvas.pack(side="right", expand=True, fill="both")
        if fields is None:
            self.canvas.create_image(5, 5, image=self.tater, anchor='nw', state=NORMAL)  # Label
            self.arg_label = Label(self.canvas,
                                   text="Well this is weird... I don't have anything to show you.",
                                   # relief=SUNKEN,
                                   #bg="red",
                                   #fg="red",
                                   highlightbackground=self.colors["highlightcolorbg"],  # dark = black
                                   font=("Calibri", 12),
                                   width=64,
                                   justify=LEFT)
            self.arg_label.grid(row=50, column=1, sticky=W)

        if fields is not None:
            idx = 0
            for key, value in fields.items():
                form = Entry(self.canvas,
                                  insertofftime=500,
                                  font=("Calibri", 12),
                                  width=70,
                                  relief=RIDGE,
                                  highlightcolor=self.colors["highlightcolor"],  # dark = black, light =
                                  highlightbackground=self.colors["highlightcolorbg"],  # dark = black, light =
                                  bg=self.colors["text_bg"],  # good
                                  fg=self.colors['text_fg'],
                                  justify=CENTER)
                if args_list is None:
                    form.insert(INSERT, "default")
                else:
                    form.insert(INSERT, args_list[key])
                self.entries[key] = form
                var = StringVar()
                var.set(key)

                # Label
                self.arg_label = Label(self.canvas,
                                       textvariable=var,
                                       relief=RAISED,
                                       font=("Calibri", 12),
                                       # bg="black",
                                       bg=self.colors["label_bg"],
                                       fg=self.colors["label_fg"],
                                       width=15,
                                       justify=LEFT)
                form.grid(row=idx, column=1, sticky=W)
                self.arg_label.grid(row=idx, column=0, sticky=W)
                Tooltip(self.arg_label, text=value)
                idx += 1

    def on_select(self, event):
        selection = event.widget.curselection()
        current_run_tag = self.listbox.get(ACTIVE)
        is_changed = False
        if selection:
            content = event.widget.get(selection[0])
            if self.run_manager.compare_tags(a=self.run_manager.get_current_run(), b=self.run_manager.get_run_from_list(content)):
                print("MainWindow continues to edit the same run.")
            else:
                if self.entries:
                    current_run = self.run_manager.get_run_from_list(current_run_tag)
                    args_list = {}
                    args_list["args"] = {}
                    for key in self.entries:
                        if self.entries[key].get() != str(current_run["args"][key]):
                            print(self.entries[key].get(), current_run["args"][key])
                            is_changed = True
                        args_list["args"][key] = self.entries[key].get()
                    self.run_manager.update_run(current_run_tag, args_list)
                    if is_changed:
                        self.listbox.itemconfig(self.listbox.index(ACTIVE), {'fg': 'blue'})
                print("MainWindow switched to new run.")
                self.run_manager.set_current_run(content)
            self.make_arg_form(fields=self.run_manager.get_template_type_args(self.run_manager.get_run_from_list(content)),
                               args_list=self.run_manager.get_run_from_list(content)["args"])

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
                self.listbox.insert(END, inserted["tag"])

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
        if messagebox.askyesno("Save", "Would you like to save?"):
            self.save()

    def create_new_run(self):
        """
        create a new window for choosing a runtype
        """
        button_results = None
        self.new_theme_window = Toplevel(self)
        self.new_theme_window.title("Choose Runtype")
        self.new_theme_window.minsize(width=25, height=20)
        runtypes = self.run_manager.get_template_types()[0]
        var = StringVar(value="0")
        for idx, runtype in enumerate(runtypes):
            chk = Radiobutton(self.new_theme_window,
                              text=runtype,
                              variable=var,
                              value=runtype)
            chk.pack(anchor='w', padx=60)
        button = Button(self.new_theme_window,
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
        self.new_theme_window.destroy()
        run = self.run_manager.create_run(runtype)
        self.listbox.insert(END, run)
        # self.run_manager.insert_into_config_list("RunList", run)

    def save_group(self):
        # @todo: is this needed?
        # save stuff
        pass

    def load_file(self, type=None):
        """
        Import either the path to a SPECjbb jar file, or run configuration file.
        :param type:
        :return:
        """
        filepath = filedialog.askopenfilename(title="Select file",
                                              filetypes=(("JSON file", "*.json"),
                                                         ("Java jar file", "*.jar"),
                                                         ("All files", "*.*"),))
        if filepath:
            extension = pathlib.Path(filepath).suffix
            print("Extension: {}".format(extension))
            if "json" in extension and type == "RunList":
                self.run_manager.set_config(filepath, "RunList")
            if "jar" in extension and type == "SPECjbb":
                self.run_manager.set_config(filepath, "SPECjbb")
            self.prompt_save()
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
            self.run_manager.set_run_index(run_tag=x, to_index=i+1)
            self.on_select(event)
        elif i > self.curIndex:
            x = copy.deepcopy(self.listbox.get(i))
            self.listbox.delete(i)
            self.listbox.insert(i-1,x)
            self.run_manager.set_run_index(run_tag=x, to_index=i-1)
            self.on_select(event)


if __name__ == '__main__':
    master = Tk()
    MainWindow(master).pack(fill="both", expand=True)
    master.mainloop()
