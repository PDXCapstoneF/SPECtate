import os
import sys
import json
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import uuid

# import modules defined at ../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../src/')  # @todo: avoid PYTHONPATH
from src.validate import *

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
        Frame.__init__(self, *args, **kwargs)
        self.form, self.arg_label, self.tater, self.new_run_window = None, None, None, None
        self.run_manager = RunManager(config_file=None)
        self.run_manager.get_run_from_list("specjbb")
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
        self.left_frame.pack(side=LEFT,
                             fill=BOTH,
                             expand=YES)
        self.right_frame.pack(side=RIGHT,
                              fill=BOTH,
                              expand=YES)
        # Create scroll list
        self.listbox = Listbox(self.left_frame, width=20, height=self.height, relief=GROOVE, font="Arial",
                               selectmode=EXTENDED)
        self.list_scrollbar = Scrollbar(self)
        self.listbox.config(yscrollcommand=self.list_scrollbar.set)
        self.list_scrollbar.config(orient=VERTICAL, command=self.listbox.yview)
        self.listbox.pack(side="left", expand=True, fill="both")
        self.list_scrollbar.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        self.listbox.bind("<Button-3>", self.popup_window)

        # Create canvas
        self.canvas = Canvas(self.right_frame, width=80, height=self.height, bg=self.colors['canvas'], relief=GROOVE)
        self.canvas.config(scrollregion=(0, 0, 300, 650), highlightthickness=0)
        self.canvas.pack(side="right", expand=True, fill="both")

        # Add items to the listbox
        i = 0

        run_list = self.run_manager.get_run_list_tags()
        while i < len(run_list):
            self.listbox.insert(i, run_list[i])
            i += 1

    def publish_menu(self):
        self.menubar = Menu(self.master)

        # File Menu
        filemenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=properties["commands"]["file"]["title"], menu=filemenu)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["new_run"],
                             command=lambda: self.create_new_run())
        filemenu.add_command(label=properties["commands"]["file"]["items"]["new_runtype"], command='')
        filemenu.add_command(label=properties["commands"]["file"]["items"]["save"], command=lambda: self.create_new_run)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["save_as"], command=lambda: self.save_as)
        filemenu.add_command(label=properties["commands"]["file"]["items"]["import_config"], command=lambda: self.import_runlist)
        filemenu.add_separator()
        filemenu.add_command(label=properties["commands"]["file"]["items"]["exit"], command=self.on_close)

        # Edit Menu
        editmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=properties["commands"]["edit"]["title"], menu=editmenu)
        editmenu.add_command(label=properties["commands"]["edit"]["items"]["undo"], command='')
        editmenu.add_command(label=properties["commands"]["edit"]["items"]["redo"], command='')

        # Help Menu
        helpmenu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label=properties["commands"]["help"]["title"], menu=helpmenu)
        helpmenu.add_command(label=properties["commands"]["help"]["items"]["wiki"], command='')
        helpmenu.add_command(label=properties["commands"]["help"]["items"]["exit"], command='')

        # Publish Menu
        self.master.config(menu=self.menubar)

    def make_arg_form(self, fields):
        entries = {}
        if self.canvas is not None:
            self.canvas.destroy()
            self.tater = PhotoImage(file="tater.pgm").zoom(5).subsample(50)
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
            self.arg_label.pack(pady=0, padx=150, fill=X, side=TOP, anchor='nw')
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
                self.arg_label.pack(pady=idx, padx=50, fill=X, side=TOP, anchor='w')
                self.form.pack(pady=idx, padx=100, fill=X, side=TOP, anchor='w')
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
        create a popup window for right clicking on an item in listbox
        allow to delete or duplicate the selected item
        """
        popup_menu = Menu(self.listbox, tearoff=0)
        # item = self.listbox.get(self.listbox.curselection())
        popup_menu.add_command(label='Delete', command=lambda: self.listbox.delete(self.listbox.curselection()))
        popup_menu.add_command(label='Duplicate',
                               command=lambda: self.listbox.insert(END, self.listbox.get(self.listbox.curselection())))
        popup_menu.tk_popup(event.x_root, event.y_root)

    def save_as(self):
        pass

    def on_close(self):
        if messagebox.askyesno("Exit", "Are you sure to exit?") == True:
            if messagebox.askyesno("Save", "Would you like to save before exitting?") == True:
                self.save_as()
            self.quit()
        else:
            return

    def create_new_run(self):
        """
        create a new window for choosing a runtype
        """
        print("Im in create_new_run")
        self.button_results = None
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
                        variable=self.button_results,
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
        self.run_manager.insert_into_config_list("RunList", run)

    def save_group(self):
        # save stuff
        pass

    def load_group(self):
        file_tuples = filedialog.askopenfilenames(title="Select file",
                                                  filetypes=(("JSON file", "*.json"), ("All files", "*.*")))
        # json file loaded
        print("I should do something with: " % file_tuples)

    def import_runlist(self):
        """
        load config file
        """
        file_tuples = filedialog.askopenfilenames(title="Select file",
                                                  filetypes=(("JSON file", "*.json"), ("All files", "*.*")))
        if file_tuples:
            self.run_manager.RUN_CONFIG = file_tuples[0]


class RunManager:
    def __init__(self, config_file=None):
        self.current_run = None
        self.template_fields = ["args", "annotations", "default_props", "types", "translations"]
        self.backup_filename = "output.back.json"
        if config_file is None:
            self.RUN_CONFIG = os.path.dirname(os.path.abspath('../example_config.json')) + '/example_config.json'
        elif config_file is not None:
            self.RUN_CONFIG = config_file
        try:
            with open(self.RUN_CONFIG) as file:
                parsed = json.load(file)
                self.validated_runs = validate(parsed)
        except IOError:
            print("Error: {} does not exist.\nPlease supply a valid onfiguration file.".format(self.RUN_CONFIG))
        if not self.initialized():
            print("Run configuration not loaded. Please supply a valid configuration file.")

    def initialized(self):
        """
        Checks that the current runs in memory are not NULL and are set to a correct type.
        A precaution for preventing key errors from arising in other methods.
        :return: Bool
        """
        return True if (self.validated_runs is not None and isinstance(self.validated_runs, dict)) else False

    def write_to_file(self, fname):
        with open(fname, 'w') as fh:
            json.dump(self.validated_runs, fh)

    def insert_into_config_list(self, key, data):
        # @todo: test
        """
        This method can insert a template or run into
        `TemplateData` or `RunList`, respectively.
        :param key: str
        :param data: dict
        :return: dict
        """
        if key not in ["TemplateData", "RunList"] or data is None or not isinstance(data, dict):
            return None
        if self.initialized:
            try:
                if key == "TemplateData":
                    self.validated_runs[key][data["RunType"]] = data
                elif key == "RunList":
                    # @todo: verify that I actually update by uncommenting these lines.
                    self.validated_runs["RunList"].append(data)
                    return True
            except Exception:  # not a valid run
                return None

    def create_run(self, run_type):
        """
        Creates a run to insert into run_list. Values will be initialized to a default value.
        :param run_type: str
        :return: str
        """
        if run_type not in self.get_template_types()[0]:
            print("Run type not found.")
            return None
        run_type_copy = self.validated_runs["TemplateData"][run_type]
        new_args = dict()

        for arg in run_type_copy["args"]:
            if run_type_copy["types"][arg] == "string":
                new_args[arg] = "0"
            if run_type_copy["types"][arg] == "integer":
                new_args[arg] = 0
        run_type_copy["args"] = new_args
        run_type_copy["args"]["Tag"] = ("{}-{}".format(run_type, str(uuid.uuid4())[:8]))
        print("Run type copy upon creation: {}".format(run_type_copy))
        self.insert_into_config_list(key="RunList", data=run_type_copy)
        return run_type_copy["args"]["Tag"]

    def duplicate_run(self, from_tag, new_tag_name):
        # @todo: test
        """
        Insert into run_list a copy of an existing run having the Tag `from_tag`.
        `new_tag_name` will override the tag in the copy.
        :param from_tag: str
        :param new_tag_name: str
        :return:
        """
        if self.initialized():
            run = self.get_run_from_list(from_tag)
            if run is not None and isinstance(run, dict) and "Tag" in run:
                run["Tag"] = new_tag_name
                self.insert_into_config_list("RunList", run)

    def get_template_fields(self):
        """
        Returns fields for the structure of a run template,
        (e.g. `args`, `annotations` `translations`, ...)
        :return: list
        """
        return self.template_fields

    def get_run_list(self):
        """
        Returns runs from run list.
        :return: list
        """
        if self.initialized:
            return self.validated_runs["RunList"]

    def get_run_list_tags(self):
        # @todo: test
        """
        Returns the tags of all runs currently in the run list.
        :return: list
        """
        if self.initialized:
            return [(lambda x: x["args"]["Tag"])(x) for x in self.get_run_list()]

    def set_current_run(self, new_run_tag):
        # @todo: test
        """
        Sets the current run to track.
        :param new_run_tag:
        :return: string
        """
        self.current_run = new_run_tag
        return self.current_run

    def get_current_run(self):
        # @todo: test
        """
        Used to track which run user is currently editing in the MainWindow.
        :return: string
        """
        if self.initialized:
            return self.current_run

    def get_run_from_list(self, tag_to_find):
        # @todo: test
        """
        Search for run in run list by tag, having the key value `tag_to_find`.
        :param tag_to_find: a string (run tag) to look for
        :return: dict
        """
        if self.initialized:
            if isinstance(tag_to_find, str):
                for run in self.get_run_list():
                    if tag_to_find in run["args"]["Tag"]:
                        return run

    def get_template_types(self):
        """
        Returns available template types (e.g. ["HBIR", "HBIR_RT", ...]
        :return: list
        """
        if self.initialized:
            return [self.validated_runs["TemplateData"].keys()]

    def get_template_type_args(self, run_type):
        """
        Searches the config file for args pertaining to `run_type`.
        It also returns each arg's annotation, in the form: {'arg_x': 'annotation_x', ...}
        :param run_type: dict or str
        :return: dict
        """
        if self.initialized:
            if not run_type:
                return None
            if isinstance(run_type, dict):
                run_type = run_type["template_type"]
            if isinstance(run_type, str):
                if run_type not in self.validated_runs["TemplateData"].keys():
                    print("{} not found.".format(run_type))
                    return None
                results = dict()
                for i in self.validated_runs["TemplateData"][run_type]["args"]:
                    results[i] = self.validated_runs["TemplateData"][run_type]["annotations"][i]
                return results

    def compare_tags(self, a, b):
        """
        Compares run tag `a` with run tag `b`.
        :param a: dict or str
        :param b: dict or str
        :return: Bool
        """
        if a or b is None:
            return False
        if isinstance(a, dict):
            if isinstance(b, dict):
                return a["args"]["Tag"] == b["args"]["Tag"]
            elif isinstance(b, str):
                return a["args"]["Tag"] == b
        elif isinstance(a, str):
            if isinstance(b, dict):
                return a == b["args"]["Tag"]
            if isinstance(b, str):
                return a == b


if __name__ == '__main__':
    master = Tk()
    MainWindow(master).pack(fill="both", expand=True)
    master.mainloop()
