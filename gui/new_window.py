#!/usr/bin/python3

from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from multiListBox import MultiColumnListbox
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


class NewWindow(Frame):
    def __init__(self, master):
        super().__init__()
        self.THEME = "light"
        self.colors = properties["main_window"]["themes"][self.THEME]
        self.font = "Calibri"
        self.template_name, self.form, self.add_arg_label = None, None, None
        self.master = master
        self.width = 600
        self.height = 300
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

        self.add_arg_label = Label(self.master,
                                   text="Add New Argument",
                                   font=("Calibri", 12),
                                   bg=self.colors["label_bg"],
                                   fg=self.colors["label_fg"],
                                   width=20,
                                   justify=CENTER)
        self.add_arg_label.grid(row=1, columnspan=2)

        test_header = ['Group name', 'Number of instances']
        test_list = [
            ('AAAA', 5),
            ('ZZZZ', 8),
            ('CCCC', 6),
            ('DDDD', 2),
            ('EEEE', 11),
            ('FFFF', 13),
            ('GGGG', 9),
            ('HHHH', 12),
            ('IIII', 20)
        ]
        self.list_arg = MultiColumnListbox(test_header, test_list)