import tkinter.font as tkfont
import tkinter.ttk as ttk


class MultiColumnListbox(object):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self):
        self.tree = None
        self._setup_widgets()
        self._build_tree()

    def _setup_widgets(self):
        s = "List of groups"
        msg = ttk.Label(wraplength="4i", justify="left", anchor="n",
            padding=(10, 2, 10, 6), text=s)
        msg.pack(fill='x')
        container = ttk.Frame()
        container.pack(fill='both', expand=True)
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(columns=test_header, show="headings")
        vsb = ttk.Scrollbar(orient="vertical",
            command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal",
            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
            xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=container)
        vsb.grid(column=1, row=0, sticky='ns', in_=container)
        hsb.grid(column=0, row=1, sticky='ew', in_=container)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

    def _build_tree(self):
        for col in test_header:
            self.tree.heading(col, text=col.title(),
                command=lambda c=col: sort_by(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkfont.Font().measure(col.title()))

        for item in test_list:
            self.tree.insert('', 'end', values=item)
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkfont.Font().measure(val)
                if self.tree.column(test_header[ix],width=None)<col_w:
                    self.tree.column(test_header[ix], width=col_w)


def sort_by(tree, col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    # if the data to be sorted is numeric
    if col.title() == "Number Of Instances":
        data.sort(key=lambda x: float(x[0]), reverse=descending)
    else:
        data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sort_by(tree, col, int(not descending)))


# some test data ...
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