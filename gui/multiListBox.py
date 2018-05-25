import tkinter.font as tkfont
import tkinter.ttk as ttk


class MultiColumnListbox(object):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, master, container, headers, data, col_width):
        self.master = master
        self.container = container
        self.col_width = col_width
        self.tree = None
        self.headers = headers
        self.data = data
        self.build_tree()

    def build_tree(self):
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(self.container, columns=self.headers, show="headings")
        vsb = ttk.Scrollbar(self.container, orient="vertical",
            command=self.tree.yview)
        hsb = ttk.Scrollbar(self.container, orient="horizontal",
            command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set,
            xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self.container)
        vsb.grid(column=1, row=0, sticky='ns', in_=self.container)
        hsb.grid(column=0, row=1, sticky='ew', in_=self.container)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        for col in self.headers:
            self.tree.heading(col, text=col.title(), command=lambda c=col: sort_by(self.tree, c, 0))
            # adjust the column's width to the header string
            min_w = tkfont.Font().measure(col.title()) + 40
            if self.col_width < min_w:
                self.tree.column(col, width=min_w)
            else:
                self.tree.column(col, width=self.col_width)
        self.populate(self.data)

    def populate(self, data):
        self.tree.delete(*self.tree.get_children())
        for item in data:
            self.tree.insert('', 'end', values=item)
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                min_w = tkfont.Font().measure(val)
                if self.tree.column(self.headers[ix], width=None) < min_w:
                    self.tree.column(self.headers[ix], width=min_w + 30)


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