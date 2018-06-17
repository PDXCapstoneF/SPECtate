import curses


class runcontext:

    def __init__(self, stdscr, xoffset, draw):
        height, width = stdscr.getmaxyx()
        self.stdscr = stdscr
        self.pad = curses.newpad(height, 10000)
        self.height = height
        self.width = width
        self.index = 0
        self.starty = 2
        self.xoffset = xoffset
        self.maxy = self.height - self.starty
        self.logmax = self.maxy - self.starty
        self.draw = draw
        self.thread = None

    def _resize(self, stdscr):
        self.stdscr.clear()
        self.stdscr.refresh()
        h, self.width = stdscr.getmaxyx()
        self.starty = self.draw(stdscr)
        self.stdscr.refresh()
        self.height = h
        self.maxy = self.height - self.starty
        self.logmax = self.maxy - self.starty
        if self.index > 0:
            self._refresh(self.index % self.logmax)

    def _refresh(self, c):
        self.pad.refresh(0, 0, self.maxy - c, self.xoffset, self.maxy,
                         self.width - self.xoffset - 1)
        if c < self.logmax - 1:
            self.pad.refresh(c + 1, 0, self.starty, self.xoffset,
                             (self.maxy - c), self.width - self.xoffset - 1)

    def handle_out(self, msg):
        while True:
            try:
                msg = runcontext._remove_control_chars(msg)
                c = self.index % self.logmax
                self.pad.addstr(c, 0, msg)  # c == new bottom
                self._refresh(c)
                self.index += 1
                break
            except curses.error:
                pass
            k = self.stdscr.getch()
            if not k == curses.KEY_RESIZE:
                break
            self.stdscr.erase()
            self._resize(self.stdscr)

    @staticmethod
    def _remove_control_chars(s):
        if isinstance(s, str):
            return ''.join([i if ord(i) < 128 else '' for i in s])
        return runcontext._remove_control_chars(s.decode())
