from __future__ import print_function

import curses
import json
import os
import os.path
import sys
from traceback import TracebackException

import objects
from objects import spec_decoder, spec_config, spec_run

# KEY_ENTER = 343, but my ENTER key registers as 10 =/
from src.runcontext import runcontext

KEY_ENTER = 10

STARTY = 2
xoffset = 5

run_types = ['composite', 'distributed_ctrl_txl', 'distributed_sut', 'multi']
cur_config = None
cur_path = ""


def _remove_control_chars(s):
    if isinstance(s, str):
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
    mem = [attr for attr in dir(runinfo) if not callable(getattr(runinfo, attr)) and not attr.startswith("_")]
    valueoffset = len(max(mem, key=len)) + 2
    for name in mem:
        if name == 'properties':
            stdscr.addstr(y, xoffset, name)
        else:
            stdscr.addstr(y, xoffset, "{}:".format(name))
            stdscr.addstr(y, xoffset + valueoffset,
                          str(getattr(runinfo, name)))
        y += 1
    return y, valueoffset


def select_from(stdscr, x, y, value, slist, redraw):
    """
    Allows user to select from a list of valid options
    :param stdscr: The current screen
    :param x: The start x position to begin printing
    :param y: The start y position to begin pritning
    :param value: The current value chosen
    :param slist: A list of values to choose from
    :return: A value within :param list
    """
    k = 0
    padwidth = 100
    pad = curses.newpad(1, padwidth)
    height, width = stdscr.getmaxyx()
    try:
        idx = slist.index(value)
    except ValueError:
        stdscr.clear()
        stdscr.refresh()
        curses_safe_addstr(stdscr, 0, 0, str(value))
        curses_safe_addstr(stdscr, 1, 0, str(type(value)))
        curses_safe_addstr(stdscr, 2, 0, ','.join(map(str, slist)))
        curses_safe_addstr(stdscr, 3, 0, ','.join(list(map(str, map(type, slist)))))
        stdscr.getch()
        stdscr.clear()
        stdscr.refresh()

    draw_status_bar(stdscr, "Press 'q' to exit and 'UP' or 'DOWN' to select a value")
    while k != KEY_ENTER and k != ord('q'):
        pad.clear()
        value = str(slist[idx])
        if len(value) + x >= width:
            value = value[:width - x - 1]
        if len(value) > padwidth:
            padwidth = len(value) * 2
            pad = curses.newpad(1, padwidth)
        pad.addstr(0, 0, str(value))
        stdscr.move(y, x + len(str(value)))
        pad.refresh(0, 0, y, x, y, width - x)

        k = stdscr.getch()
        if k == curses.KEY_UP and idx > 0:
            idx -= 1
        elif k == curses.KEY_DOWN and idx < len(slist) - 1:
            idx += 1
        elif k == curses.KEY_RESIZE:
            stdscr.erase()
            height, width = stdscr.getmaxyx()
            redraw(stdscr)
            draw_status_bar(stdscr, "Press 'q' to exit and 'UP' or 'DOWN' to select a value")
    return slist[idx]


def input_text(stdscr, x, y, value, validator, redraw):
    """
     Allows user to input text and returns the result
    :param redraw: A function to redraw the previous screen in case of a resize
    :param stdscr: The current screen
    :param x: The start x position to begin printing
    :param y: The start y position to begin pritning
    :param value: The current value chosen
    :param validator: A validator to ensure only proper keys are entered.
    :return: A validated value
    """
    def _resize(screen):
        screen.erase()
        stdscr.refresh()
        redraw(stdscr)
        h, w = stdscr.getmaxyx()
        x = w * 2
        p = curses.newpad(1, x)
        stdscr.refresh()
        return w, x, p
    k = 0
    value = list(str(value))
    idx = len(value)
    width, xmax, pad = _resize(stdscr)
    cursorx = min(x + len(value), width - 1)

    while k != KEY_ENTER:
        pad.clear()
        if k == curses.KEY_BACKSPACE and idx > 0:
            if idx < len(value):
                value = value[:idx - 1] + value[idx:]
            else:
                value = value[:idx - 1]
            idx -= 1
            if cursorx > x:
                cursorx -= 1
        elif 20 <= k <= 126 and validator(k):
            if idx == len(value):
                value += chr(k)
                if idx >= xmax:
                    xmax += width
                    pad = curses.newpad(1, xmax)
            else:
                value.insert(idx, chr(k))
            idx += 1
            if cursorx < (width - 1):
                cursorx += 1
        elif k == curses.KEY_DC and idx < len(value):
            if idx > 1:
                value = value[:idx] + value[idx + 1:]
            else:
                value = value[1:]
        elif k == curses.KEY_LEFT and idx > 0:
            idx -= 1
            if cursorx > x:
                cursorx -= 1
        elif k == curses.KEY_RIGHT and idx < len(value):
            idx += 1
            if cursorx < (width - 1):
                cursorx += 1
        elif k == curses.KEY_HOME and idx > 0:
            idx = 0
            cursorx = x
        elif k == curses.KEY_END and idx < len(value):
            idx = len(value)
            cursorx = min(len(value) + x, width - 1)
        elif k == curses.KEY_RESIZE:
            width, xmax, pad = _resize(stdscr)
            cursorx = min(x + len(value), width - 1)

        stdscr.move(y, cursorx)
        pad.addstr(0, 0, "".join(value))
        if idx != (cursorx - x):
            # [0 1 2 3 4 5 6 7]
            #   o   W
            #   o X
            #               I
            # I - ((W - o) - (W - X))
            pad.refresh(0, idx - ((width - 1 - x) -
                                  (width - 1 - cursorx)), y, x, y, width - 1)
        else:
            pad.refresh(0, 0, y, x, y, width - 1)
        k = stdscr.getch()
    return str("".join(value))


#
def draw_save_config(stdscr):
    """
    Saves a config file and displays whether or not it was successful
    :param stdscr:
    :param config: The spec_config
    :param path: The path to save the file to
    :return: nothing
    """
    global cur_config
    try:
        cur_config.save(cur_path)
    except:
        draw_show_message(stdscr, 'Unable to save to {}'.format(cur_path))
        return True
    finally:
        cur_config = None
    draw_show_message(stdscr, 'Saved to {}'.format(cur_path))
    return True


def draw_edit_props(stdscr, p):
    def _resize(std):
        h, w = stdscr.getmaxyx()
        sy = draw_title(std)
        draw_status_bar(std, "Press 'q' to exit or 'ENTER' to edit a value")
        np, sx = pad_props(std, p)
        curses_safe_addstr(std, h - 3, 0, p[index].desc)
        np.refresh(index - (cury - sy), 0, sy, xoffset, h - 5, w - xoffset - 1)

        return np, sx, sy, w, h

    index = 0
    cury = STARTY + 2
    k = 0

    pad, startx, starty, width, height = _resize(stdscr)
    while k != ord('q'):

        if k == curses.KEY_DOWN and index < len(p) - 1:
            index += 1
            if cury < height - 5:
                cury += 1
            else:
                pad.refresh(index - (cury - starty), 0, starty,
                            xoffset, height - 5, width - xoffset - 1)
        elif k == curses.KEY_UP and index > 0:
            index -= 1
            if cury > starty:
                cury -= 1
            else:
                pad.refresh(index - (cury - starty), 0, starty,
                            xoffset, height - 5, width - xoffset - 1)
        elif k == KEY_ENTER:
            if p[index].valid_opts:
                value = select_from(stdscr, xoffset + startx, cury, p[index].value, p[index].valid_opts, _resize)
                p[index].value = value
            else:
                value = input_text(stdscr, xoffset + startx, cury, p[index].value, p[index].input_validator, _resize)
                if not p[index].value_validator(value):
                    draw_show_message(stdscr, p[index].help_text)
                else:
                    p[index].value = value
        elif k == curses.KEY_RESIZE:
            stdscr.erase()
        stdscr.clear()
        stdscr.refresh()
        pad, startx, starty, width, height = _resize(stdscr)
        stdscr.move(cury, xoffset)
        k = stdscr.getch()
    return True


# Calls display_run, and allows user to select and edit any of the run options
def draw_edit_run(stdscr, runinfo):
    def _resize(std):
        ey, ex = display_run(std, runinfo, draw_title(std))
        draw_status_bar(std, "Press 'q' to exit or 'ENTER' to edit a value")
        return ey, ex

    k = 0
    y = STARTY + 2
    cury = y
    array = [attr for attr in dir(runinfo) if not callable(getattr(runinfo, attr)) and not attr.startswith("_")]
    endy, startx = _resize(stdscr)

    while k != ord('q'):  # 27 == 'ESC'
        if k == curses.KEY_DOWN and cury < (endy - 1):
            cury = cury + 1
        elif k == curses.KEY_UP and cury > y:
            cury = cury - 1
        elif k == KEY_ENTER:
            name = array[cury - y]
            if name == 'verbose' or name == 'skip_report' or name == 'ignore_kit_validation':
                value = select_from(stdscr, xoffset + startx, cury, getattr(runinfo, name), [True, False], _resize)
                setattr(runinfo, name, value)
            elif name == 'report_level':
                value = select_from(stdscr, xoffset + startx, cury, getattr(runinfo, name), [0, 1, 2], _resize)
                setattr(runinfo, name, value)
            elif name == 'run_type':
                value = select_from(stdscr, xoffset + startx, cury, getattr(runinfo, name), run_types, _resize)
                setattr(runinfo, name, value)
            elif name == 'properties':
                draw_edit_props(stdscr, runinfo.properties.get_all())
            elif name == 'jdk':
                value = input_text(stdscr, xoffset + startx, cury, getattr(runinfo, name),
                                   lambda x: True,_resize)  # start editing at end of value
                if not os.path.exists(value):
                    draw_show_message(stdscr, "Warning: jdk path not found")
                setattr(runinfo, name, value)
            elif name == 'num_runs' or name == 'numa_nodes':
                value = input_text(stdscr, xoffset + startx, cury, getattr(runinfo, name),
                                   objects.number_validator,_resize)  # start editing at end of value
                setattr(runinfo, name, value)
            else:
                value = input_text(stdscr, xoffset + startx, cury, getattr(runinfo, name),
                                   lambda x: True,_resize)  # start editing at end of value
                if(name == 'spec_dir'):
                    cur_config.set_spec_dir(value)
                else:
                    setattr(runinfo, name, value)
        elif k == curses.KEY_RESIZE:
            stdscr.erase()


        stdscr.clear()
        stdscr.refresh()
        endy, startx = _resize(stdscr)
        stdscr.move(cury, xoffset)
        stdscr.refresh()
        k = stdscr.getch()
    return runinfo

def draw_generic_get_input(stdscr, message, validator = lambda x:True):
    def _resize(std):
        y = draw_title(std)
        s = curses_safe_addstr(std, y, xoffset, message)
        if isinstance(s, str):
            return len(s)
        return y, 0

    stdscr.clear()
    sy, x = _resize(stdscr)
    return input_text(stdscr, sy, x, "", validator, _resize)





def edit_config(stdscr):
    if cur_config is None:
        draw_get_config_path(stdscr)
        draw_load_config(stdscr)
        if cur_config is None:
            return True

    def _draw():
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.refresh()
        sy = draw_title(stdscr)
        curses_safe_addstr(stdscr, sy + len(cur_config.runs), xoffset, "{}. Add new run:".format(len(cur_config.runs) + 1))
        draw_status_bar(stdscr, "Press 'ENTER' to edit a run | Press 'RIGHT' to adjust run position | Press q to quit")
        draw_notice_bar(stdscr, "Press 'C' to change config type: {}".format(cur_config.type))
        if position:
            stdscr.move(cury, xoffset + 2)
        else:
            stdscr.move(cury, xoffset)
        p = pad_runs(stdscr, cur_config.runs)
        p.refresh(index - (cury - sy), 0, sy, xoffset, h - 2, w - xoffset - 1)
        stdscr.refresh()
        return sy, h, w, p, min(sy + len(cur_config.runs), h - 1)

    k = 0

    starty = cury = STARTY + 2
    position = False
    index = 0
    starty, height, width, pad, endy = _draw()
    while k != ord('q'):  # 27 == 'ESC'

        if k == curses.KEY_DOWN:
            if (not position and cury < endy) or (position and cury < endy - 1):
                if position:
                    cur_config.runs[index + 1], cur_config.runs[index] = cur_config.runs[index], cur_config.runs[index + 1]
                cury += 1
                index += 1
            elif (not position and index < len(cur_config.runs) - 1) or (position and index < len(cur_config.runs) - 1):
                if position:
                    cur_config.runs[index + 1], cur_config.runs[index] = cur_config.runs[index], cur_config.runs[index + 1]
                index += 1
        elif k == curses.KEY_UP:
            if cury > starty:
                if position:
                    cur_config.runs[index - 1], cur_config.runs[index] = cur_config.runs[index], cur_config.runs[index - 1]
                cury -= 1
                index -= 1
            elif index > 0:
                if position:
                    cur_config.runs[index - 1], cur_config.runs[index] = cur_config.runs[index], cur_config.runs[index - 1]
                index -= 1
        elif k == curses.KEY_LEFT:
            position = False
        elif k == curses.KEY_RIGHT and index < len(cur_config.runs):
            position = True
        elif k == curses.KEY_DC and index < len(cur_config.runs):
            position = False
            draw_status_bar(stdscr, "Remove run {} from this config? (y/N)".format(cur_config.runs[index].tag))
            resp = stdscr.getch()
            if resp == ord('y') or resp == ord('Y'):
                del cur_config.runs[index]
        elif k == KEY_ENTER:
            position = False
            if index == len(cur_config.runs):
                newrun = spec_run()
                origtag = newrun.tag
                offset = 1
                while any(x.tag == newrun.tag for x in cur_config.runs):
                    newrun.tag = "{}-{}".format(origtag, offset)
                    offset += 1
                for r in cur_config.runs:
                    if r.spec_dir != "":
                        newrun.spec_dir = r.spec_dir
                        break
                cur_config.runs.append(newrun)
            cur_config.runs[index] = draw_edit_run(stdscr, cur_config.runs[index])
        elif k == ord('c') or k == ord('C'):
            cur_config.switch_type()
        elif k == curses.KEY_RESIZE:
            stdscr.erase()

        starty, height, width, pad, endy = _draw()

        k = stdscr.getch()
    draw_save_config(stdscr)
    return True


def draw_title(stdscr):
    height, width = stdscr.getmaxyx()
    title = "SPECtate - curses"[:width - 1]
    start_x_title = int((width // 2) - (len(title) // 2) - len(title) % 2)

    # Turning on attributes for title
    stdscr.attron(curses.color_pair(2))
    stdscr.attron(curses.A_BOLD)

    stdscr.attron(curses.color_pair(1))
    curses_safe_addstr(stdscr,STARTY, start_x_title, "SPECtate - curses")
    stdscr.attroff(curses.color_pair(1))
    # Turning off attributes for title
    stdscr.attroff(curses.color_pair(2))
    stdscr.attroff(curses.A_BOLD)
    return STARTY + 2  # the current y


def draw_notice_bar(stdscr, noticebarstr):
    height, width = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    if len(noticebarstr) > width:
        noticebarstr = noticebarstr[:width - 1]
    start_x = int((width // 2) - (len(noticebarstr) // 2) - len(noticebarstr) % 2)
    curses_safe_addstr(stdscr,height - 3, start_x, noticebarstr)
    stdscr.attroff(curses.color_pair(3))


def draw_status_bar(stdscr, statusbarstr):
    height, width = stdscr.getmaxyx()
    stdscr.attron(curses.color_pair(3))
    if len(statusbarstr) > width:
        statusbarstr = statusbarstr[:width - 1]
    curses_safe_addstr(stdscr,height - 1, 0, statusbarstr)
    curses_safe_addstr(stdscr,height - 1, len(statusbarstr), " " * (width - len(statusbarstr) - 1))
    stdscr.attroff(curses.color_pair(3))


def draw_show_message(stdscr, msg: str):
    """
    Displays some message and waits for the user to press a key
    :param stdscr: The current window
    :param msg: A message to display
    :return The last char entered, just in case its a RESIZE
    """
    stdscr.clear()
    y = draw_title(stdscr)
    curses_safe_addstr(stdscr, y, xoffset, msg)
    draw_status_bar(stdscr, "Press any key to return")
    stdscr.refresh()
    return stdscr.getch()


def draw_get_config_path(stdscr):
    """
    Asks user for file
    :param stdscr: The current window
    :return: A path to a file
    """
    global cur_path
    cur_path = ""
    stdscr.clear()
    stdscr.refresh()
    def _resize(std):
        sy = draw_title(std)
        draw_status_bar(std, "Please enter the path of a config")

        curses_safe_addstr(std,sy, xoffset, "Config file path:")
        return sy

    y = _resize(stdscr)
    path = input_text(stdscr, xoffset + len("Config file path:") + 1, y, "", lambda x: True, _resize)
    if not os.path.exists(path) and not path.endswith('.json'):
        path += '.json'
    if os.path.isfile(path):
        cur_path = path
    else:
        draw_show_message(stdscr, "File not found")
    return True


def draw_get_path(stdscr):
    """
    Prompts the user for the path to SPECjbb
    :param stdscr:
    :return: A string path
    """
    def _resize(std):
        sy = draw_title(std)
        draw_status_bar(stdscr, "Please enter the path of SPECjbb")

        curses_safe_addstr(std, sy, xoffset, "SPECjbb directory:")
        return sy

    stdscr.clear()
    stdscr.refresh()
    y = _resize(stdscr)
    return input_text(stdscr, xoffset + len("Config file path:") + 1, y, "", lambda x: True, _resize)


def run_config(stdscr):
    """
    Loads and runs a config file
    :param stdscr: The current window
    """
    draw_get_config_path(stdscr)
    draw_load_config(stdscr)
    if cur_config is None:
        return True
    index = 0
    context = runcontext(stdscr, xoffset, draw_title)
    def _handle(msg):
        msg = _remove_control_chars(msg)
        if msg.isspace():
            return
        nonlocal index
        nonlocal cury
        nonlocal pad
        nonlocal maxy
        c = index % logmax
        pad.addstr(c, 0, msg)  # c == new bottom
        pad.refresh(0, 0, maxy - c, xoffset, maxy, width - xoffset - 1)
        if c < logmax - 1:
            pad.refresh(c + 1, 0, cury, xoffset, (maxy - c), width - xoffset - 1)
        # if(index < maxy - cury):
        #   pad.refresh(0, 0, cury, xoffset, cury + c, width - xoffset - 1)
        #  if(c < logmax - 1):
        #     pad.refresh(c + 1, 0, cury, xoffset, cury + c, width - xoffset - 1)
        # else:
        #  if c + cury < maxy:
        #      pad.refresh(0, 0, cury, xoffset, cury + c, width - xoffset - 1)
        # else:
        # print 0 -> c
        # print logmax - (c
        #        pad.refresh(0,0, maxy - c, xoffset, maxy, width - xoffset - 1)
        #       pad.refresh(logmax - c, 0, cury, xoffset, maxy - c - 1, width - xoffset - 1)
        index += 1
        # draw_status_bar(stdscr, 'c={}, index={}, msg="{}'.format(c, index, msg))
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
    result = cur_config.run(context.handle_out, lambda x: x)
    if result == 2:
        cur_config.set_spec_dir(draw_get_path(stdscr))
        result = cur_config.run(_handle, lambda x: x)
        if result == 2:
            draw_status_bar(stdscr, "Invalid SPECjbb path. Press any key to continue")
            return stdscr.getch()

    if result == -1:
        draw_status_bar(stdscr, "An error occured running the benchmark. Press any key to continue")
        return stdscr.getch()
    draw_status_bar(stdscr, "All runs have been completed - Press any key to continue")
    return stdscr.getch()


def create_config(stdscr):
    """
    Requests file name from user, then calls edit_config
    Also clears the screen
    :param stdscr: The current window
    """
    global cur_path
    global cur_config
    def _resize(std):
        sy = draw_title(std)
        curses_safe_addstr(std, sy, xoffset, "Enter config name:")
        return sy
    stdscr.clear()
    stdscr.refresh()
    y = _resize(stdscr)
    path = input_text(stdscr, xoffset + len("Enter config name:") + 1, y, "", lambda x: True, _resize).strip()
    if path.isspace() or path == "":

        draw_show_message(stdscr, "Config name cannot be blank")
        return True
    if os.path.isfile(path):
        stdscr.clear()
        stdscr.refresh()
        y = draw_title(stdscr)
        curses_safe_addstr(stdscr, y, xoffset, "Warning: file {} already exists, overwrite? (y/N)".format(path))

        k = stdscr.getch()
        while k == curses.KEY_RESIZE:
            stdscr.erase()
            y = draw_title(stdscr)
            curses_safe_addstr(stdscr, y, xoffset, "Warning: file {} already exists, overwrite? (y/N)".format(path))
            k = stdscr.getch()
        if k != ord('Y') and k != ord('y'):
            return True

    cur_path = path
    cur_config = spec_config()
    resize_wrapper(stdscr, edit_config)
    return True


def pad_props(stdscr, proplist):
    """
    Builds a pad of all properties in the proplist
    :param stdscr: The current window
    :param proplist: A properties object
    :return: A pad object containing all properties and their values, also returns the x offset where all values start
    """
    height, width = stdscr.getmaxyx()
    if not proplist:
        return curses.newpad(1, width - 1 - xoffset), 0
    pad = curses.newpad(len(proplist) + 1, width - 1 - xoffset)
    valueoffset = len(max(map(lambda x: x.prop, proplist), key=len))
    idx = 0
    for p in proplist:
        pad.addstr(idx, 0, "{}:".format(p.prop))
        pad.addstr(idx, valueoffset, str(p.value))
        idx += 1
    return pad, valueoffset


def pad_runs(stdscr, runlist):
    """
    Builds a pad of all runs (tag names) in the runlist
    :param stdscr: The current window
    :param runlist: A list of runs
    :return: A pad object containing all tag names
    """
    height, width = stdscr.getmaxyx()
    if not runlist:
        return curses.newpad(1, width - 1 - xoffset)
    pad = curses.newpad(len(runlist) + 1, width - 1 - xoffset)
    # add plus one to pad height for edit config to put 'Add run' option
    idx = 0
    for run in runlist:
        pad.addstr(idx, 0, "{}. {}".format(idx + 1, run.tag))
        idx += 1
    return pad


def draw_view_props(stdscr, p):
    def _draw():
        h, w = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.refresh()
        sy = draw_title(stdscr)
        if show_all:
            draw_status_bar(stdscr, "Press 'q' to exit | Press 'a' to hide defaults")
        else:
            draw_status_bar(stdscr, "Press 'q' to exit | Press 'a' to show all properties")
        if len(visprops) > 0:
            curses_safe_addstr(stdscr,h - 3, 0, visprops[index].desc)
        pad.refresh(index - (cury - sy), 0, sy, xoffset, h - 5, w - xoffset - 1)
        stdscr.move(cury, xoffset)
        stdscr.refresh()
        return h, w, sy

    show_all = False
    index = 0
    cury = STARTY + 2
    k = 0
    visprops = p.get_modified()
    pad, startx = pad_props(stdscr, visprops)
    height, width, starty =_draw()


    if len(visprops) == 0:
        pad.addstr(0, 0, "No properties to display")

    while k != ord('q'):

        if k == curses.KEY_DOWN and index < len(visprops) - 1:
            index += 1
            if cury < height - 5:
                cury += 1
            else:
                pad.refresh(index - (cury - starty), 0, starty,
                            xoffset, height - 5, width - xoffset - 1)
        elif k == curses.KEY_UP and index > 0:
            index -= 1
            if cury > starty:
                cury -= 1
            else:
                pad.refresh(index - (cury - starty), 0, starty, xoffset, height - 5, width - xoffset - 1)
        elif k == ord('a') or k == ord('A'):
            show_all = not show_all
            if show_all:
                visprops = p.get_all()
            else:
                visprops = p.get_modified()
            pad, startx = pad_props(stdscr, visprops)

            if len(visprops) == 0:
                pad.addstr(0, 0, "No properties to display")
                index = 0
                cury = starty
            else:
                if index >= len(visprops):
                    index = len(visprops) - 1
                if cury >= starty + len(visprops):
                    cury = len(visprops) - 1
        elif k == curses.KEY_RESIZE:
            stdscr.erase()
        height, width, starty = _draw()
        k = stdscr.getch()
    return True


def draw_view_run(stdscr, runinfo):
    def _draw():
        stdscr.clear()
        stdscr.refresh()
        ey, ex = display_run(stdscr, runinfo, draw_title(stdscr))
        draw_status_bar(
            stdscr, "Press 'q' to exit or 'ENTER' to view run properties")

        return ey, ex

    k = 0
    while k != ord('q'):  # 27 == 'ESC'
        if k == KEY_ENTER:
            draw_view_props(stdscr, runinfo.properties)

        _draw()
        k = stdscr.getch()


def view_runs(stdscr):
    draw_get_config_path(stdscr)
    draw_load_config(stdscr)
    if cur_config is None:
        return True

    def _draw(stdr, py, pd, idx):
        h, w = stdr.getmaxyx()
        stdr.clear()
        stdr.refresh()
        sy = draw_title(stdr)
        draw_status_bar(stdr, "Press 'ENTER' to view a run | Press 'q' to quit")
        stdr.move(py, xoffset)
        pd.refresh(idx - (py - sy), 0, sy, xoffset, h - 2, w - xoffset - 1)
        stdr.refresh()
        return h, w, sy

    k = 0
    cury = STARTY + 2
    index = 0

    pad = pad_runs(stdscr, cur_config.runs)
    height, width, starty = _draw(stdscr, cury, pad, index)
    y = len(cur_config.runs) + starty
    while k != ord('q'):
        if k == curses.KEY_DOWN:
            if cury < y - 1:
                cury += 1
                index += 1
            elif index < len(cur_config.runs) - 1:
                index += 1
        elif k == curses.KEY_UP:
            if cury > starty:
                cury -= 1
                index -= 1
            elif index > 0:
                index -= 1
        elif k == KEY_ENTER:
            draw_view_run(stdscr, cur_config.runs[index])
        elif k == curses.KEY_RESIZE:
            stdscr.erase()
        _draw(stdscr, cury, pad, index)

        k = stdscr.getch()
    return True

def draw_load_config(stdscr):
    global cur_config
    if os.path.exists(cur_path):
        cur_config = load_config(cur_path)
        if cur_config is None:
            draw_show_message(stdscr, "Error loading config file")
        elif not isinstance(cur_config, spec_config):
            draw_show_message(stdscr, "Invalid config file format")
    return True

def load_config(path: str):
    """
    Loads a config file as a spec_config object
    :param path: The path to the config file
    :return: A loaded spec_config or None
    """
    try:
        with open(path, 'r') as f:
            return json.load(f, cls=spec_decoder)
    except:
        return None

opts = [
        run_config,
        create_config,
        edit_config,
        view_runs
    ]
menunames = [
"1. Run a config",
    "2. Create a config",
"3. Edit a config",
"4. View a config"
]
def draw_menu(stdscr):
    k = 0
    cursor_y = STARTY + 2

    def _resize(std):
        height, width = std.getmaxyx()
        sy = dy = draw_title(std)
        # Declaration of strings

        for s in menunames:
            if(len(s) + xoffset >= width):
                s = s[:width - xoffset - 1]
            std.addstr(dy, xoffset, s)
            dy += 1

        return sy, dy - 1


    while k != ord('q'):

        # Initialization
        if k == KEY_ENTER:
            resize_wrapper(stdscr, opts[cursor_y - (STARTY + 2)])
        elif ord('1') <= k <= ord('4'):
            resize_wrapper(stdscr, opts[k - ord('1')])
        elif k == curses.KEY_RESIZE:
            stdscr.erase()


        stdscr.clear()
        stdscr.refresh()

        starty, y = _resize(stdscr)


        if k == curses.KEY_DOWN and cursor_y < y:
            cursor_y += 1
        elif k == curses.KEY_UP and cursor_y > starty:
            cursor_y -= 1

        # Render status bar
        draw_status_bar(stdscr, "Press 'q' to exit | MAIN MENU")

        stdscr.move(cursor_y, xoffset)

        # Refresh the screen
        stdscr.refresh()

        # Wait for next input
        k = stdscr.getch()
    return True

def resize_wrapper(stdscr, child = None, redraw = None):
    if child is None:
        child = draw_menu
    noerror = None
    while True:
        try:
            noerror = child(stdscr)
        except curses.error:
            pass
        except TypeError as e:
            import inspect
            import traceback
            exc_type, exc_obj, exc_tb = sys.exc_info()
            stdscr.clear()
            traceback.format_exc()
            i = 0
            for line in TracebackException(
                    type(exc_type), exc_obj, exc_tb, limit=None).format(chain=True):
                curses_safe_addstr(stdscr, i, 0, str(line))
                i += 1
            curses_safe_addstr(stdscr, 2, 0, str(e))
            stdscr.getch()
        if not noerror is None:
            break
        k = stdscr.getch()
        if not k == curses.KEY_RESIZE:
            break
        stdscr.erase()
        if not redraw is None:
            redraw(stdscr)

def curses_init(stdscr):
    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    resize_wrapper(stdscr, draw_menu)

def curses_safe_addstr(stdscr, y, x, str):
    height, width = stdscr.getmaxyx()
    if width < x or height < y:
        return False
    if len(str) + x > width:
        str = str[:width - x]
    stdscr.addstr(y, x, str)
    return str

def main():
        curses.wrapper(curses_init)



if __name__ == "__main__":
    main()
