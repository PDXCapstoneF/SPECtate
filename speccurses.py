from __future__ import print_function

import os
import curses
import json
import os.path


import objects
from objects import spec_decoder, spec_encoder, spec_config, spec_run

TAB = 9
ENTER = 10
ESC = 27
DOWN = 258
UP = 259
LEFT = 260
RIGHT = 261
HOME = 262
BACK = 263
DEL = 330
PGDN = 338
PGUP = 339
END = 360

STARTY = 2
xoffset = 5

run_types = ['composite', 'distributed_ctrl_txl', 'distributed_sut', 'multi']

def _remove_control_chars(s):
    if(isinstance(s, str)):
        return ''.join([i if ord(i) < 128 else '' for i in s])
    return _remove_control_chars(s.decode())

def display_run(stdscr, runinfo, y=STARTY + 2):
    """
    Displays a single run within a config file
    :param stdscr: The current screen
    :param runinfo: The 'spec_run' to display
    :param y: The current y value
    :return: The new y value, as well as the max length of any property in the current run
    """
    mem = [attr for attr in dir(runinfo) if not callable(getattr(runinfo, attr)) and not attr.startswith("__")]
    valueoffset = len(max(mem, key=len)) + 2
    for name in mem:
        if (name == 'properties'):
            stdscr.addstr(y, xoffset, name)
        else:
            stdscr.addstr(y, xoffset, "{}:".format(name))
            stdscr.addstr(y, xoffset + valueoffset, str(getattr(runinfo, name)))
        y += 1
    return y, valueoffset


def select_from(stdscr, x, y, value, list):
    """
    Allows user to select from a list of valid options
    :param stdscr: The current screen
    :param x: The start x position to begin printing
    :param y: The start y position to begin pritning
    :param value: The current value chosen
    :param list: A list of values to choose from
    :return: A value within :param list
    """
    k = 0
    pad = curses.newpad(1, 100)
    height, width = stdscr.getmaxyx()
    idx = list.index(value)
    while (k != ENTER and k != ord('q')):
        pad.clear()
        draw_status_bar(stdscr, "Press 'q' to exit and 'UP' or 'DOWN' to select a value")
        if (k == curses.KEY_UP and idx > 0):
            idx -= 1
        elif (k == curses.KEY_DOWN and idx < len(list) - 1):
            idx += 1
        value = list[idx]
        pad.addstr(0, 0, str(value))
        stdscr.move(y, x + len(str(value)))
        pad.refresh(0, 0, y, x, y, width - x)
        k = stdscr.getch()
    return value


def input_text(stdscr, x, y, value, validator):
    """
     Allows user to input text and returns the result
    :param stdscr: The current screen
    :param x: The start x position to begin printing
    :param y: The start y position to begin pritning
    :param value: The current value chosen
    :param validator: A validator to ensure only proper keys are entered.
    :return: A validated value
    """
    k = 0
    value = list(str(value))
    idx = len(value)
    height, width = stdscr.getmaxyx()
    xmax = width * 2
    pad = curses.newpad(1, xmax)
    cursorx =  min(x + len(value), width - 1)

    while (k != ENTER):
        pad.clear()
        if (k == BACK and idx > 0):
            if (idx < len(value)):
                value = value[:idx - 1] + value[idx:]
            else:
                value = value[:idx - 1]
            idx -= 1
            if(cursorx > x):
                cursorx -= 1
        elif (k >= 20 and k <= 126 and validator(k)):
            if (idx == len(value)):
                value += chr(k)
                if(idx >= xmax):
                    xmax += width
                    pad = curses.newpad(1, xmax)
            else:
                value.insert(idx, chr(k))
            idx += 1
            if (cursorx < (width - 1)):
                cursorx += 1
        elif (k == DEL and idx < len(value)):
            if (idx > 1):
                value = value[:idx] + value[idx + 1:]
            else:
                value = value[1:]
        elif (k == curses.KEY_LEFT and idx > 0):
            idx -= 1
            if (cursorx > x):
                cursorx -= 1
        elif (k == curses.KEY_RIGHT and idx < len(value)):
            idx += 1
            if (cursorx < (width - 1)):
                cursorx += 1
        elif(k == curses.KEY_HOME and idx > 0):
            idx = 0
            cursorx = x
        elif (k == curses.KEY_END and idx < len(value)):
            idx = len(value)
            cursorx = min(len(value) + x, width - 1)

        stdscr.move(y, cursorx)
        pad.addstr(0, 0, "".join(value))
        if(idx != (cursorx - x)):
            #[0 1 2 3 4 5 6 7]
            #   o   W
            #   o X
            #               I
            # I - ((W - o) - (W - X))
            pad.refresh(0, idx - ((width - 1 - x) - (width - 1 - cursorx)), y, x, y, width - 1)
        else:
            pad.refresh(0, 0, y, x, y, width - 1)
        k = stdscr.getch()
    return str("".join(value))


# Saves a config file and displays whether or not it was successful
def draw_save_config(stdscr, config, path):
    try:
        config.save(path)
    except:
        draw_show_message(stdscr, 'Unable to save to {}'.format(path))
        return
    draw_show_message(stdscr, 'Saved to {}'.format(path))


def draw_edit_props(stdscr, p):
    def _draw():
        stdscr.clear()
        stdscr.refresh()
        draw_title(stdscr)
        draw_status_bar(stdscr, "Press 'q' to exit or 'ENTER' to edit a value")
        stdscr.addstr(height - 3, 0, p[index].desc)
        pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        stdscr.move(cury, xoffset)
        stdscr.refresh()

    index = 0
    starty = STARTY + 2
    cury = starty
    k = 0
    pad, startx = pad_props(stdscr, p)
    height, width = stdscr.getmaxyx()
    while (k != ord('q')):

        if k == curses.KEY_DOWN and index < len(p) - 1:
            index += 1
            if (cury < height - 5):
                cury += 1
            else:
                pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        elif k == curses.KEY_UP and index > 0:
            index -= 1
            if (cury > starty):
                cury -= 1
            else:
                pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        elif k == ENTER:
            if (p[index].valid_opts != []):
                value = select_from(stdscr, xoffset + startx, cury, str(p[index].value), p[index].valid_opts)
                p[index].value = value
            else:
                value = input_text(stdscr, xoffset + startx, cury, p[index].value, p[index].input_validator)
                if (not p[index].value_validator(value)):
                    draw_show_message(stdscr, p[index].help_text)
                else:
                    p[index].value = value
            pad, startx = pad_props(stdscr, p)

        _draw()
        k = stdscr.getch()
    return


# Calls display_run, and allows user to select and edit any of the run options
def draw_edit_run(stdscr, runinfo):
    def _draw():
        stdscr.clear()
        stdscr.refresh()

        ey, ex = display_run(stdscr, runinfo, draw_title(stdscr))
        draw_status_bar(stdscr, "Press 'q' to exit or 'ENTER' to edit a value")

        stdscr.move(cury, xoffset)
        stdscr.refresh()
        return ey, ex

    k = 0
    y = STARTY + 2
    cury = y
    array = [attr for attr in dir(runinfo) if not callable(getattr(runinfo, attr)) and not attr.startswith("__")]
    endy, startx = _draw()
    while (k != ord('q')):  # 27 == 'ESC'
        if k == curses.KEY_DOWN and cury < (endy - 1):
            cury = cury + 1
        elif k == curses.KEY_UP and cury > y:
            cury = cury - 1
        elif k == ENTER:
            name = array[cury - y]
            if (name == 'verbose' or name == 'skip_report' or name == 'ignore_kit_validation'):
                value = select_from(stdscr, xoffset + startx, cury, getattr(runinfo, name), [True, False])
                setattr(runinfo, name, value)
            elif (name == 'report_level'):
                value = select_from(stdscr, xoffset + startx, cury, getattr(runinfo, name), [0, 1, 2])
                setattr(runinfo, name, value)
            elif (name == 'run_type'):
                value = select_from(stdscr, xoffset + startx, cury, getattr(runinfo, name), run_types)
                setattr(runinfo, name, value)
            elif (name == 'properties'):
                draw_edit_props(stdscr, runinfo.properties.get_all())
            elif (name == 'jdk'):
                value = input_text(stdscr, xoffset + startx, cury, getattr(runinfo, name),
                                   lambda x: True)  # start editing at end of value
                if (not os.path.exists(value)):
                    draw_show_message(stdscr, "Warning: jdk path not found")
                setattr(runinfo, name, value)
            elif (name == 'num_runs' or name == 'numa_nodes'):
                value = input_text(stdscr, xoffset + startx, cury, getattr(runinfo, name),
                                   objects.number_validator)  # start editing at end of value
                setattr(runinfo, name, value)
            else:
                value = input_text(stdscr, xoffset + startx, cury, getattr(runinfo, name),
                                   lambda x: True)  # start editing at end of value
                setattr(runinfo, name, value)

        _draw()
        k = stdscr.getch()
    return runinfo


def edit_config(stdscr, config=None, path=""):
    if (config is None):
        config, path = draw_get_config_path(stdscr)
        if (config is None):
            return

    def _draw():
        stdscr.clear()
        stdscr.refresh()
        starty = draw_title(stdscr)
        stdscr.addstr(starty + len(config.runs), xoffset, "{}. Add new run:".format(len(config.runs) + 1))
        draw_status_bar(stdscr, "Press 'ENTER' to edit a run | Press 'RIGHT' to adjust run position | Press q to quit")
        if (position):
            stdscr.move(cury, xoffset + 2)
        else:
            stdscr.move(cury, xoffset)
        pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
        stdscr.refresh()
        return starty, pad

    def _getpad():
        p = pad_runs(stdscr, config.runs)
        p.addstr(len(config.runs), 0, "{}. {}".format(len(config.runs), "Add new run"))
        return p, min(starty + len(config.runs), height - 1)

    k = 0
    height, width = stdscr.getmaxyx()
    starty = cury = STARTY + 2
    position = False
    index = 0
    pad, endy = _getpad()
    _draw()
    while (k != ord('q')):  # 27 == 'ESC'

        if k == curses.KEY_DOWN:
            if ((not position and cury < endy) or (position and cury < endy - 1)):
                if (position):
                    config.runs[index + 1], config.runs[index] = config.runs[index], config.runs[index + 1]
                    pad, endy = _getpad()
                    pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
                cury += 1
                index += 1
            elif ((not position and index < len(config.runs) - 1) or (position and index < len(config.runs) - 1)):
                if (position):
                    config.runs[index + 1], config.runs[index] = config.runs[index], config.runs[index + 1]
                    pad, endy = _getpad()
                    pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
                index += 1
        elif k == curses.KEY_UP:
            if (cury > starty):
                if (position):
                    config.runs[index - 1], config.runs[index] = config.runs[index], config.runs[index - 1]
                    pad, endy = _getpad()
                    pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
                cury -= 1
                index -= 1
            elif (index > 0):
                if (position):
                    config.runs[index - 1], config.runs[index] = config.runs[index], config.runs[index - 1]
                    pad, endy = _getpad()
                    pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
                index -= 1
        elif (k == curses.KEY_LEFT):
            position = False
        elif (k == curses.KEY_RIGHT and index < len(config.runs)):
            position = True
        elif (k == DEL and index < len(config.runs) - 1):
            position = False
            draw_status_bar(stdscr, "Remove run {} from this config? (y/N)".format(config.runs[index]))
            resp = stdscr.getch()
            if (resp == ord('y') or resp == ord('Y')):
                del config.runs[index]
                pad, endy = _getpad()
        elif k == ENTER:
            position = False
            if (index == len(config.runs)):
                config.runs.append(spec_run())
            config.runs[index] = draw_edit_run(stdscr, config.runs[index])
            pad, endy = _getpad()

        _draw()

        k = stdscr.getch()
    draw_save_config(stdscr, config, path)
    return


def draw_title(stdscr):
    height, width = stdscr.getmaxyx()
    title = "SPECtate - curses"[:width - 1]
    start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)

    # Turning on attributes for title
    stdscr.attron(curses.color_pair(2))
    stdscr.attron(curses.A_BOLD)

    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(STARTY, start_x_title, "SPECtate - curses")
    stdscr.attroff(curses.color_pair(1))
    # Turning off attributes for title
    stdscr.attroff(curses.color_pair(2))
    stdscr.attroff(curses.A_BOLD)
    return STARTY + 2  # the current y


def draw_status_bar(stdscr, statusbarstr):
    height, width = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    if (len(statusbarstr) > width):
        statusbarstr = statusbarstr[:width - 1]
    stdscr.addstr(height - 1, 0, statusbarstr)
    stdscr.addstr(height - 1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
    stdscr.attroff(curses.color_pair(3))


# Displays some message and waits for the user to press a key
def draw_show_message(stdscr, msg):
    stdscr.clear()
    y = draw_title(stdscr)
    stdscr.addstr(y, xoffset, msg)
    draw_status_bar(stdscr, "Press any key to return")
    stdscr.refresh()
    stdscr.getch()


# Asks user for file and loads the json
def draw_get_config_path(stdscr):
    stdscr.clear()
    y = draw_title(stdscr)
    draw_status_bar(stdscr, "Please enter the path of a config")

    stdscr.addstr(y, xoffset, "Config file path:")
    path = input_text(stdscr, xoffset + len("Config file path:") + 1, y, "", lambda x: True)
    if (os.path.isfile(path)):
        if (True):  # do_validate(({'<config>' : path}))):
            config = load_config(path)
            if (config is None):
                import pdb
                pdb.set_trace()
                draw_show_message(stdscr, "Error loading config file")
            elif (not isinstance(config, spec_config)):
                import pdb
                pdb.set_trace()
                draw_show_message(stdscr, "Invalid config file format")
            else:
                return config, path
        else:
            draw_show_message(stdscr, "Invalid config file")
    else:
        draw_show_message(stdscr, "File not found")
    return None, ""


def draw_get_path(stdscr):
    stdscr.clear()
    y = draw_title(stdscr)

    draw_status_bar(stdscr, "Please enter the path of SPECjbb")

    stdscr.addstr(y, xoffset, "SPECjbb directory:")
    return input_text(stdscr, xoffset + len("Config file path:") + 1, y, "", lambda x: True)


# Disable ncurses and calls maincli
def run_config(stdscr):
    config, path = draw_get_config_path(stdscr)
    if (config is None):
        return
    index = 0
    def _handle(msg):
        msg = _remove_control_chars(msg)
        if(msg.isspace()):
            return
        nonlocal index
        nonlocal cury
        nonlocal pad
        nonlocal maxy
        c = index % logmax
        pad.addstr(c, 0, msg) # c == new bottom
        if(index < maxy - cury):
            pad.refresh(0, 0, cury, xoffset, cury + index, width - xoffset - 1)
        else:
          #  if c + cury < maxy:
          #      pad.refresh(0, 0, cury, xoffset, cury + c, width - xoffset - 1)
           # else:
                #print 0 -> c
                #print logmax - (c
                pad.refresh(0,0, maxy - c, xoffset, maxy, width - xoffset - 1)
                pad.refresh(logmax - c, 0, cury, xoffset, maxy - c - 1, width - xoffset - 1)
        index += 1
        draw_status_bar(stdscr, 'c={}, index={}, msg=""'.format(c, index, msg))
        stdscr.refresh()
    stdscr.clear()
    stdscr.refresh()
    height, width = stdscr.getmaxyx()
    cury = draw_title(stdscr)
    maxy = height - cury
    logmax = maxy - cury
    #    def _handle(msg):
    # c = index % maxindex
    #        pad.addstr(0, 0, msg)
    # if cury < maxy:
    #     cury += 1
    #        pad.refresh(0, 0, 20, xoffset, 20, width - xoffset)
    # log[index % maxindex] = msg

    # index += 1

    # starty = y
    # maxy = height - 3
    # log = [height - y - 3]
    # maxindex = len(log)

    pad = curses.newpad(height, width - 1 - xoffset)

    #stdscr.keypad(0)
    #curses.echo()
    #curses.nocbreak()
    #curses.endwin()
    for r in config.runs:
        # draw_status_bar(stdscr, "Starting run '{}'".format(r.tag))

        result = r.run(path, _handle)
        if (result == 2):
            #curses.noecho()
            #curses.cbreak()
            #stdscr.keypad(1)
            path = draw_get_path(stdscr)
            #stdscr.keypad(0)
            #curses.echo()
            #curses.nocbreak()
            #curses.endwin()
            result = r.run(path, _handle)
            if (result == 2):
                #curses.noecho()
                #curses.cbreak()
                #stdscr.keypad(1)
                draw_status_bar(stdscr, "Invalid SPECjbb path. Press any key to continue")
                stdscr.getch()
                return
        if (result == -1):
            #curses.noecho()
            #curses.cbreak()
            #stdscr.keypad(1)
            draw_status_bar(stdscr, "An error occured running the benchmark. Press any key to continue")
            stdscr.getch()
            return
            #curses.echo()
            #curses.nocbreak()
            #curses.endwin()
    #curses.noecho()
    #curses.cbreak()
    #stdscr.keypad(1)
    draw_status_bar(stdscr, "All runs have been completed - Press any key to continue")
    stdscr.getch()


# Requests file name from user, then calls edit_config
# Also clears the screen
def create_config(stdscr):
    stdscr.clear()
    stdscr.refresh()
    y = draw_title(stdscr)
    stdscr.addstr(y, xoffset, "Enter config name:")

    path = input_text(stdscr, xoffset + len("Enter config name:") + 1, y, "", lambda x: True).strip()
    if (path.isspace() or path == ""):
        draw_show_message(stdscr, "Config name cannot be blank")
        return
    if (os.path.isfile(path)):
        stdscr.clear()
        stdscr.refresh()
        y = draw_title(stdscr)
        stdscr.addstr(y, xoffset, "Warning: file {} already exists, overwrite? (y/N)".format(path))
        k = stdscr.getch()
        if (k != ord('Y') and k != ord('y')):
            return

    edit_config(stdscr, spec_config(), path)


def pad_props(stdscr, proplist):
    height, width = stdscr.getmaxyx()
    if (proplist == []):
        return curses.newpad(1, width - 1 - xoffset), 0
    pad = curses.newpad(len(proplist) + 1, width - 1 - xoffset)
    valueoffset = len(max(map(lambda x: x.prop, proplist), key=len))
    # add plus one to pad height for edit config to put 'Add run' option
    idx = 0
    for p in proplist:
        pad.addstr(idx, 0, "{}:".format(p.prop))
        pad.addstr(idx, valueoffset, str(p.value))
        idx += 1
    #    pad.refresh(0,0,y,xoffset,min(height, y + len(runlist)), min(width - 1, xoffset))
    return pad, valueoffset


# Returns a 'pad' containing a list of runs (tag names)
def pad_runs(stdscr, runlist):
    height, width = stdscr.getmaxyx()
    if (runlist == []):
        return curses.newpad(1, width - 1 - xoffset)
    pad = curses.newpad(len(runlist) + 1, width - 1 - xoffset)
    # add plus one to pad height for edit config to put 'Add run' option
    idx = 0
    for run in runlist:
        pad.addstr(idx, 0, "{}. {}".format(idx + 1, run.tag))
        idx += 1
    #    pad.refresh(0,0,y,xoffset,min(height, y + len(runlist)), min(width - 1, xoffset))
    return pad


def draw_view_props(stdscr, p):
    def _draw():
        stdscr.clear()
        stdscr.refresh()
        draw_title(stdscr)
        if (show_all):
            draw_status_bar(stdscr, "Press 'q' to exit | Press 'a' to hide defaults")
        else:
            draw_status_bar(stdscr, "Press 'q' to exit | Press 'a' to show all properties")
        if (len(visprops) > 0):
            stdscr.addstr(height - 3, 0, visprops[index].desc)
        pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        stdscr.move(cury, xoffset)
        stdscr.refresh()

    show_all = False
    index = 0
    starty = STARTY + 2
    cury = starty
    k = 0
    visprops = p.get_modified()
    pad, startx = pad_props(stdscr, visprops)
    if (len(visprops) == 0):
        pad.addstr(0, 0, "No properties to display")
    height, width = stdscr.getmaxyx()
    while (k != ord('q')):

        if k == curses.KEY_DOWN and index < len(visprops) - 1:
            index += 1
            if (cury < height - 5):
                cury += 1
            else:
                pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        elif k == curses.KEY_UP and index > 0:
            index -= 1
            if (cury > starty):
                cury -= 1
            else:
                pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        elif (k == ord('a') or k == ord('A')):
            show_all = not show_all
            if (show_all):
                visprops = p.get_all()
            else:
                visprops = p.get_modified()
            pad, startx = pad_props(stdscr, visprops)

            if (len(visprops) == 0):
                pad.addstr(0, 0, "No properties to display")
                index = 0
                cury = starty
            else:
                if (index >= len(visprops)):
                    index = len(visprops) - 1
                if (cury >= starty + len(visprops)):
                    cury = len(visprops) - 1

        _draw()
        k = stdscr.getch()
    return


def draw_view_run(stdscr, runinfo):
    def _draw():
        stdscr.clear()
        stdscr.refresh()

        ey, ex = display_run(stdscr, runinfo, draw_title(stdscr))
        draw_status_bar(stdscr, "Press 'q' to exit or 'ENTER' to view run properties")

        stdscr.refresh()
        return ey, ex

    k = 0
    _draw()
    while (k != ord('q')):  # 27 == 'ESC'
        if k == ENTER:
            draw_view_props(stdscr, runinfo.properties)

        _draw()
        k = stdscr.getch()


def view_runs(stdscr):
    config, path = draw_get_config_path(stdscr)
    if (config is None):
        return

    def _draw(stdscr, py, pad, index):
        stdscr.clear()
        stdscr.refresh()
        draw_title(stdscr)
        draw_status_bar(stdscr, "Press 'ENTER' to view a run | Press 'q' to quit")
        stdscr.move(py, xoffset)
        pad.refresh(index - (py - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
        stdscr.refresh()

    height, width = stdscr.getmaxyx()
    k = 0
    starty = STARTY + 2
    cury = starty
    index = 0
    y = len(config.runs) + cury
    pad = pad_runs(stdscr, config.runs)
    _draw(stdscr, cury, pad, index)
    while (k != ord('q')):
        if k == curses.KEY_DOWN:
            if (cury < y - 1):
                cury += 1
                index += 1
            elif (index < len(config.runs) - 1):
                # pad scrolling down
                index += 1
                pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 2, width - xoffset - 1)
        elif k == curses.KEY_UP:
            if (cury > starty):
                cury -= 1
                index -= 1
            elif (index > 0):
                index -= 1

        elif k == ENTER:
            draw_view_run(stdscr, config.runs[index])
        _draw(stdscr, cury, pad, index)

        k = stdscr.getch()


# Utilities
def load_config(path):
    try:
        with open(path, 'r') as f:
            return json.load(f, cls=spec_decoder)
    except:
        return None


def draw_menu(stdscr):
    k = 0
    cursor_y = STARTY + 2

    opts = [
        run_config,
        create_config,
        edit_config,
        view_runs
    ]
    current_config = None
    # Clear and refresh the screen for a blank canvas
    stdscr.clear()
    stdscr.refresh()

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    # Loop where k is the last character pressed
    while (k != ord('q')):

        # Initialization
        if (k == ENTER):
            opts[cursor_y - (STARTY + 2)](stdscr)
        elif (k >= ord('1') and k <= ord('4')):
            opts[int(k)](stdscr)

        stdscr.clear()
        stdscr.refresh()

        starty = y = draw_title(stdscr)
        # Declaration of strings
        stdscr.addstr(y, xoffset, "1. Run a config")
        stdscr.addstr(y + 1, xoffset, "2. Create a config")
        stdscr.addstr(y + 2, xoffset, "3. Edit a config")
        stdscr.addstr(y + 3, xoffset, "4. View a config")
        y += 3
        if (k == curses.KEY_DOWN and cursor_y < y):
            cursor_y += 1
        elif (k == curses.KEY_UP and cursor_y > starty):
            cursor_y -= 1

        # Render status bar
        draw_status_bar(stdscr, "Press 'q' to exit | MAIN MENU")

        stdscr.move(cursor_y, xoffset)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        k = stdscr.getch()


def main():
    curses.wrapper(draw_menu)


if __name__ == "__main__":
    main()
