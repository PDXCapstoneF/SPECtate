import tkinter as tk
import tkinter.ttk as ttk


class Tooltip:
    """this class allows us to add tooltips to objects inside a widget
    """
    def __init__(self,
                 widget,
                 bg='#FFFFEA',
                 pad=(5, 3, 5, 3),
                 text='widget info',
                 waittime=100,
                 wraplength=250):
        self.waittime = waittime  # in milliseconds
        self.wraplength = wraplength  # in pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.onEnter)
        self.widget.bind("<Leave>", self.onLeave)
        self.widget.bind("<ButtonPress>", self.onLeave)
        self.bg = bg
        self.pad = pad
        self.id = None
        self.tw = None

    def onEnter(self, event=None):
        """schedule an event(tooltip) when the cursor enters the object
        """
        self.schedule()

    def onLeave(self, event=None):
        """unschedule and hide the tooltip when the cursor leaves the object
        """
        self.unschedule()
        self.hide()

    def schedule(self):
        """make sure the event is unscheduled and then invoke callback function
        """
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        """unschedule the event if it exists
        """
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show(self, event=None):
        """display the tooltip in a clear format
        """
        def tip_pos_calculator(widget,
                               label,
                               tip_delta=(10, 5),
                               pad=(5, 3, 5, 3)):
            """calculate the appropriate position for the tooltip
            """
            c = widget
            s_width, s_height = c.winfo_screenwidth(), c.winfo_screenheight()
            width, height = (pad[0] + label.winfo_reqwidth() + pad[2],
                             pad[1] + label.winfo_reqheight() + pad[3])
            mouse_x, mouse_y = c.winfo_pointerxy()
            x1, y1 = mouse_x + tip_delta[0], mouse_y + tip_delta[1]
            x2, y2 = x1 + width, y1 + height
            x_delta = x2 - s_width
            if x_delta < 0:
                x_delta = 0
            y_delta = y2 - s_height
            if y_delta < 0:
                y_delta = 0
            offscreen = (x_delta, y_delta) != (0, 0)
            if offscreen:
                if x_delta:
                    x1 = mouse_x - tip_delta[0] - width
                if y_delta:
                    y1 = mouse_y - tip_delta[1] - height
            offscreen_again = y1 < 0  # out on the top
            if offscreen_again:
                # No further checks will be done.
                # TIP:
                # A further mod might automatically augment the
                # wrap length when the tooltip is too high to be
                # kept inside the screen.
                y1 = 0
            return x1, y1

        bg = self.bg
        pad = self.pad
        widget = self.widget
        # creates a top-level window
        self.tw = tk.Toplevel(widget.master)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        win = tk.Frame(self.tw, background=bg, borderwidth=0)
        label = ttk.Label(
            win,
            text=self.text,
            justify=tk.LEFT,
            background=bg,
            relief=tk.SOLID,
            borderwidth=0,
            wraplength=self.wraplength)
        label.grid(
            padx=(pad[0], pad[2]), pady=(pad[1], pad[3]), sticky=tk.NSEW)
        win.grid()
        x, y = tip_pos_calculator(widget, label)
        self.tw.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        """hide and destroy the event(tooltip)
        """
        if self.tw:
            self.tw.destroy()
        self.tw = None
