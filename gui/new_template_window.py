#!/usr/bin/python3

from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from multiListBox import MultiColumnListbox
import tkinter.ttk as ttk
import os
import json

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


class NewTemplateWindow(Frame):
    def __init__(self, master, run_manager):
        super().__init__()
        self.THEME = "light"
        self.colors = properties["main_window"]["themes"][self.THEME]
        self.font = "Calibri"
        self.template_name, self.form, self.add_arg_button, self.listbox_arg, self.add_prop_button, self.listbox_prop = None, None, None, None, None, None
        self.get_data_dialog = None
        self.headers_arg = ['Name', 'Type', 'Annotation', 'Translation']
        self.headers_prop = ['Key', 'Value']
        self.list_args = []
        self.list_props = []
        self.master = master
        self.run_manager = run_manager
        self.width = 390
        self.height = 550
        self.master.minsize(width=self.width, height=self.height)
        self.master.geometry("%dx%d" % (self.width, self.height))
        self.make_form()

    def make_form(self):
        # Label
        self.template_name = Label(self.master,
                               text="Template Name:",
                               font=("Calibri", 12),
                               # bg="black",
                               bg=self.colors["label_bg"],
                               fg=self.colors["label_fg"],
                               width=15,
                               justify=CENTER)

        self.form = Entry(self.master,
                          insertofftime=500,
                          font=("Calibri", 12),
                          width=30,
                          relief=RIDGE,
                          highlightcolor=self.colors["highlightcolor"],  # dark = black, light =
                          highlightbackground=self.colors["highlightcolorbg"],  # dark = black, light =
                          bg=self.colors["text_bg"],  # good
                          fg=self.colors['text_fg'],
                          justify=CENTER)

        self.template_name.grid(row=0, column=0, sticky=W, padx=5)
        self.form.grid(row=0, column=1, sticky=W)

        self.add_arg_button = Button(self.master,
                                   text="Add New Argument",
                                   relief=RIDGE,
                                   font=("Calibri", 12),
                                   bg=self.colors["label_bg"],
                                   fg=self.colors["label_fg"],
                                   width=20,
                                   justify=CENTER,
                                   command=lambda: self.create_new_arg())
        self.add_arg_button.grid(row=1, columnspan=4)
        container_listbox_arg = ttk.Frame(self.master)
        container_listbox_arg.grid(row=2, columnspan=4)
        self.listbox_arg = MultiColumnListbox(self.master, container_listbox_arg, self.headers_arg, self.list_args, 0)

        self.add_prop_button = Button(self.master,
                                     text="Add New Prop Option",
                                     relief=RIDGE,
                                     font=("Calibri", 12),
                                     bg=self.colors["label_bg"],
                                     fg=self.colors["label_fg"],
                                     width=20,
                                     justify=CENTER,
                                     command=lambda: self.create_new_prop())
        self.add_prop_button.grid(row=3, columnspan=4)
        container_listbox_prop = ttk.Frame(self.master)
        container_listbox_prop.grid(row=4, columnspan=4)
        self.listbox_prop = MultiColumnListbox(self.master, container_listbox_prop, self.headers_prop, self.list_props, 180)

        button_confirm = Button(self.master, text='Confirm',
                                command=lambda: self.save_new_template())
        button_confirm.grid(row=5, columnspan=4, sticky=E, padx=5)

    def save_new_template(self):
        new_template = dict()
        new_template["jar"] = "temp"
        new_template["args"] = []
        new_template["annotations"] = dict()
        new_template["prop_options"] = dict()
        new_template["types"] = dict()
        new_template["translations"] = dict()
        for item in self.list_args:
            new_template["args"].append(item[0])
            new_template["annotations"][item[0]] = item[2]
            new_template["types"][item[0]] = item[1]
            if item[3]:
                new_template["translations"][item[0]] = item[3]
        for item in self.list_props:
            new_template["prop_options"][item[0]] = item[1]
        self.run_manager.create_template({self.template_name: new_template})

    def create_new_arg(self):
        self.get_data_dialog = Toplevel(self)
        self.get_data_dialog.title("Create new argument")
        self.get_data_dialog.minsize(width=25, height=20)
        Label(self.get_data_dialog, text="Name:").grid(row=0)
        Label(self.get_data_dialog, text="Type:").grid(row=1)
        Label(self.get_data_dialog, text="Annotation:").grid(row=2)
        Label(self.get_data_dialog, text="Translation:").grid(row=3)

        arg_name = Entry(self.get_data_dialog)
        arg_type = Entry(self.get_data_dialog)
        arg_annotation = Entry(self.get_data_dialog)
        arg_translation = Entry(self.get_data_dialog)

        arg_name.grid(row=0, column=1)
        arg_type.grid(row=1, column=1)
        arg_annotation.grid(row=2, column=1)
        arg_translation.grid(row=3, column=1)
        button_confirm = Button(self.get_data_dialog, text='Confirm',
                                command=lambda: self.add_new_arg((arg_name.get(), arg_type.get(), arg_annotation.get(), arg_translation.get())))
        button_confirm.grid(row=4, columnspan=2)

    def add_new_arg(self, arg):
        self.list_args.append(arg)
        self.listbox_arg.populate(self.list_args)
        self.get_data_dialog.destroy()
        
    def create_new_prop(self):
        self.get_data_dialog = Toplevel(self)
        self.get_data_dialog.title("Create new prop option")
        self.get_data_dialog.minsize(width=25, height=20)
        Label(self.get_data_dialog, text="Key:").grid(row=0)
        Label(self.get_data_dialog, text="Value:").grid(row=1)

        prop_key = Entry(self.get_data_dialog)
        prop_value = Entry(self.get_data_dialog)

        prop_key.grid(row=0, column=1)
        prop_value.grid(row=1, column=1)
        button_confirm = Button(self.get_data_dialog, text='Confirm',
                                command=lambda: self.add_new_prop((prop_key.get(), prop_value.get())))
        button_confirm.grid(row=2, columnspan=2)

    def add_new_prop(self, prop):
        self.list_props.append(prop)
        self.listbox_prop.populate(self.list_props)
        self.get_data_dialog.destroy()