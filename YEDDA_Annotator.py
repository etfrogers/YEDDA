#!/usr/bin/env python
#  -*- coding: utf-8 -*-
# @Author: Jie Yang from SUTD
# @Date:   2016-Jan-06 17:11:59
# @Last Modified by:   Jie Yang,     Contact: jieynlp@gmail.com
# @Last Modified time: 2018-03-05 17:41:03

# coding=utf-8

import os.path
import pickle
import platform
import tkFileDialog
import tkFont
import tkMessageBox
from Tkinter import *
from collections import deque
from ttk import *  # Frame, Button, Label, Style, Scrollbar

from utils.recommend import *


# noinspection PyPep8Naming
class YeddaFrame(Frame):
    # noinspection PyMissingConstructor
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = "YEDDA-V1.0 Annotator"
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        self.debug = False
        self.reprocess_whole_file = True
        self.recommendFlag = False
        self.history = deque(maxlen=20)
        self.currentContent = deque(maxlen=1)
        self.pressCommand = {'a': "Artifical",
                             'b': "Event",
                             'c': "Fin-Concept",
                             'd': "Location",
                             'e': "Organization",
                             'f': "Person",
                             'g': "Sector",
                             'h': "Other"
                             }
        self.allKey = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.controlCommand = {'q': "unTag", 'ctrl+z': 'undo'}
        self.label_entry_list = []
        self.shortcut_label_list = []
        # default GUI display parameter
        if len(self.pressCommand) > 20:
            self.textRow = len(self.pressCommand)
        else:
            self.textRow = 12
        self.textColumn = 5
        self.onlyNP = False  # for exporting sequence 
        self.keep_recommend = True

        self.configFile = "config.pkl"
        self.entity_regex = re.compile(r'<([\w-]+?)>(.*?)</\1>', flags=re.DOTALL)
        self.inside_nest_entity_regex = re.compile(r'\[@\[@(?!\[@).*?#.*?\*\]#')
        # configure color
        self.entityColor = "SkyBlue1"
        self.insideNestEntityColor = "light slate blue"
        self.selectColor = 'light salmon'
        self.textFontStyle = "Times"
        self.fontWeight = "normal"
        self.initUI()

    # noinspection PyAttributeOutsideInit
    def initUI(self):

        self.parent.title(self.Version)
        self.pack(fill=BOTH, expand=True)

        for idx in range(0, self.textColumn):
            self.columnconfigure(idx, weight=2)
        # self.columnconfigure(0, weight=2)
        self.columnconfigure(self.textColumn + 2, weight=1)
        self.columnconfigure(self.textColumn + 4, weight=1)
        for idx in range(0, 16):
            self.rowconfigure(idx, weight=1)

        self.lbl = Label(self, text="File: no file is opened")
        self.lbl.grid(sticky=W, pady=4, padx=5)
        self.fnt = tkFont.Font(family=self.textFontStyle, size=self.textRow, underline=0)
        self.text = Text(self, font=self.fnt, selectbackground=self.selectColor)
        self.text.grid(row=1, column=0, columnspan=self.textColumn, rowspan=self.textRow, padx=12, sticky=E + W + S + N)

        self.sb = Scrollbar(self)
        self.sb.grid(row=1, column=self.textColumn, rowspan=self.textRow, padx=0, sticky=E + W + S + N)
        self.text['yscrollcommand'] = self.sb.set
        self.sb['command'] = self.text.yview
        # self.sb.pack()

        open_btn = Button(self, text="Open", command=self.onOpen)
        open_btn.grid(row=1, column=self.textColumn + 1)

        remap_button = Button(self, text="ReMap", command=self.do_remap_of_shortcuts)
        remap_button.grid(row=4, column=self.textColumn + 1, pady=4)

        quit_button = Button(self, text="Quit", command=self.quit)
        quit_button.grid(row=6, column=self.textColumn + 1, pady=4)

        self.cursorName = Label(self, text="Cursor: ", foreground="black", font=(self.textFontStyle, 14, self.fontWeight))
        self.cursorName.grid(row=9, column=self.textColumn + 1, pady=4)
        self.cursorIndex = Label(self, text=("row: %s\ncol: %s" % (0, 0)), foreground="red",
                                 font=(self.textFontStyle, 14, self.fontWeight))
        self.cursorIndex.grid(row=10, column=self.textColumn + 1, pady=4)

        # for press_key in self.pressCommand.keys():
        for idx in range(0, len(self.allKey)):
            press_key = self.allKey[idx]

            # self.text.bind(press_key, lambda event, arg=press_key:self.textReturnEnter(event,arg))
            self.text.bind(press_key, self.textReturnEnter)
            simplePressKey = "<KeyRelease-" + press_key + ">"
            self.text.bind(simplePressKey, self.deleteTextInput)
            if self.OS != "windows":
                controlPlusKey = "<Control-Key-" + press_key + ">"
                self.text.bind(controlPlusKey, self.keepCurrent)
                altPlusKey = "<Command-Key-" + press_key + ">"
                self.text.bind(altPlusKey, self.keepCurrent)

        self.text.bind('<Control-Key-z>', self.go_back_in_history)
        # disable the default  copy behaviour when right click.
        # For MacOS, right click is button 2, other systems are button3
        self.text.bind('<Button-2>', self.rightClick)
        self.text.bind('<Button-3>', self.rightClick)

        self.text.bind('<Double-Button-1>', self.doubleLeftClick)
        self.text.bind('<ButtonRelease-1>', self.singleLeftClick)

        self.show_shortcut_map()

        # cursor index show with the left click

    def singleLeftClick(self, event):
        if self.debug:
            print "Action Track: singleLeftClick"
        cursor_index = self.text.index(INSERT)
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    # TODO: select entity by double left click
    def doubleLeftClick(self, event):
        if self.debug:
            print "Action Track: doubleLeftClick"
        pass
        # cursor_index = self.text.index(INSERT)
        # start_index = ("%s - %sc" % (cursor_index, 5))
        # end_index = ("%s + %sc" % (cursor_index, 5))
        # self.text.tag_add('SEL', '1.0',"end-1c")

    # Disable right click default copy selection behaviour
    def rightClick(self, event):
        if self.debug:
            print "Action Track: rightClick"
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            content = self.text.get('1.0', "end-1c").encode('utf-8')
            self.write_file(self.fileName, content, cursor_index)
        except TclError:
            pass

    def onOpen(self):
        ftypes = [('all files', '.*'), ('text files', '.txt'), ('ann files', '.ann')]
        dlg = tkFileDialog.Open(self, filetypes=ftypes)
        # file_opt = options =  {}
        # options['filetypes'] = [('all files', '.*'), ('text files', '.txt')]
        # dlg = tkFileDialog.askopenfilename(**options)
        fl = dlg.show()
        if fl != '':
            self.text.delete("1.0", END)
            text = self.readFile(fl)
            self.text.insert(END, text)
            self.setNameLabel("File: " + fl)
            self.autoLoadNewFile(self.fileName, "1.0")
            # self.setDisplay()
            # self.initAnnotate()
            self.text.mark_set(INSERT, "1.0")
            self.setCursorLabel(self.text.index(INSERT))

    def readFile(self, filename):
        with open(filename, "rU") as f:
            text = f.read()
        self.fileName = filename
        return text

    def setFont(self, value):
        _family = self.textFontStyle
        _size = value
        _weight = self.fontWeight
        _underline = 0
        fnt = tkFont.Font(family=_family, size=_size, weight=_weight, underline=_underline)
        Text(self, font=fnt)

    def setNameLabel(self, new_file):
        self.lbl.config(text=new_file)

    def setCursorLabel(self, cursor_index):
        if self.debug:
            print "Action Track: setCursorLabel"
        row_column = cursor_index.split('.')
        cursor_text = ("row: %s\ncol: %s" % (row_column[0], row_column[-1]))
        self.cursorIndex.config(text=cursor_text)

    def textReturnEnter(self, event):
        press_key = event.char
        if self.debug:
            print "Action Track: textReturnEnter"
        self.pushToHistory()
        print "event: ", press_key
        # content = self.text.get()
        self.add_remove_tag(press_key.lower())
        # self.deleteTextInput()
        return press_key

    def go_back_in_history(self, event):
        if self.debug:
            print "Action Track: go_back_in_history"
        if len(self.history) > 0:
            historyCondition = self.history.pop()
            # print "history condition: ", historyCondition
            historyContent = historyCondition[0]
            # print "history content: ", historyContent
            cursorIndex = historyCondition[1]
            # print "get history cursor: ", cursorIndex
            self.write_file(self.fileName, historyContent, cursorIndex)
        else:
            print "History is empty!"
        self.text.insert(INSERT, 'p')  # add a word as pad for key release delete

    def keepCurrent(self, event):
        if self.debug:
            print "Action Track: keepCurrent"
        print("keep current, insert:%s" % INSERT)
        print "before:", self.text.index(INSERT)
        self.text.insert(INSERT, 'p')
        print "after:", self.text.index(INSERT)

    def getText(self):
        textContent = self.text.get("1.0", "end-1c")
        textContent = textContent.encode('utf-8')
        return textContent

    def add_remove_tag(self, command):
        if self.debug:
            print "Action Track: add_remove_tag"
        content = self.getText()
        print("Command:" + command)
        try:
            firstSelection_index = self.text.index(SEL_FIRST)
            cursor_index = self.text.index(SEL_LAST)
            aboveHalf_content = self.text.get('1.0', firstSelection_index)
            followHalf_content = self.text.get(firstSelection_index, "end-1c")
            selected_string = self.text.selection_get()
            match = self.entity_regex.match(selected_string)
            if match is not None:
                # if have selected entity
                new_string = match.group(2)
                tag_name = match.group(1)
                followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
                selected_string = new_string
                # cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
                cursor_index = cursor_index.split('.')[0] + "." + str(
                    int(cursor_index.split('.')[1]) - (len(tag_name)*2 + 5))
            afterEntity_content = followHalf_content[len(selected_string):]

            if command == "q":
                print 'q: remove entity label'
            else:
                if len(selected_string) > 0:
                    selected_string, cursor_index = self.add_tag_around_string(selected_string, command, cursor_index)
            content = aboveHalf_content + selected_string + afterEntity_content
            content = content.encode('utf-8')
            self.write_file(self.fileName, content, cursor_index)
        except TclError:
            # no text selected - use item under cursor
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content = self.text.get('1.0', str(int(line_id) - 1) + '.end')
            belowLine_content = self.text.get(str(int(line_id) + 1) + '.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span = (-1, -1)
            line_before_entity = line
            line_after_entity = ""
            for match in self.entity_regex.finditer(line):
                if match.span()[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    matched_groups = match.groups()
                    break
            if matched_span[1] > 0:
                new_string = matched_groups[1]
                old_entity_type = matched_groups[0]
                line_before_entity = line[:matched_span[0]]
                line_after_entity = line[matched_span[1]:]
                selected_string = new_string
                entity_content = selected_string
                cursor_index = line_id + '.' + str(int(matched_span[1]) - (len(old_entity_type)*2 + 5))
                if command == "q":
                    print 'q: remove entity label'
                elif command == 'y':
                    print "y: comfirm recommend label"
                    old_key = self.pressCommand.keys()[self.pressCommand.values().index(old_entity_type)]
                    entity_content, cursor_index = self.add_tag_around_string(selected_string, old_key, cursor_index)
                else:
                    if len(selected_string) > 0:
                        if command in self.pressCommand:
                            entity_content, cursor_index = self.add_tag_around_string(selected_string, command, cursor_index)
                        else:
                            return
                line_before_entity += entity_content
            if aboveLine_content != '':
                aboveHalf_content = aboveLine_content + '\n' + line_before_entity
            else:
                aboveHalf_content = line_before_entity

            if belowLine_content != '':
                followHalf_content = line_after_entity + '\n' + belowLine_content
            else:
                followHalf_content = line_after_entity

            content = aboveHalf_content + followHalf_content
            content = content.encode('utf-8')
            self.write_file(self.fileName, content, cursor_index)

    def deleteTextInput(self, event):
        if self.debug:
            print "Action Track: deleteTextInput"
        get_insert = self.text.index(INSERT)
        print "delete insert:", get_insert
        insert_list = get_insert.split('.')
        last_insert = insert_list[0] + "." + str(int(insert_list[1]) - 1)
        get_input = self.text.get(last_insert, get_insert).encode('utf-8')
        # print "get_input: ", get_input
        aboveHalf_content = self.text.get('1.0', last_insert).encode('utf-8')
        followHalf_content = self.text.get(last_insert, "end-1c").encode('utf-8')
        if len(get_input) > 0:
            followHalf_content = followHalf_content.replace(get_input, '', 1)
        content = aboveHalf_content + followHalf_content
        self.write_file(self.fileName, content, last_insert)

    def add_tag_around_string(self, content, replaceType, cursor_index):
        if replaceType in self.pressCommand:
            new_content = "<" + self.pressCommand[replaceType] + ">" + content + \
                          "</" + self.pressCommand[replaceType] + ">"
            newcursor_index = cursor_index.split('.')[0] + "." + str(
                int(cursor_index.split('.')[1]) + len(self.pressCommand[replaceType]) + 5)
        else:
            print "Invalid command!"
            print "cursor index: ", self.text.index(INSERT)
            return content, cursor_index
        return new_content, newcursor_index

    def write_file(self, fileName, content, newcursor_index):
        if self.debug:
            print "Action track: write_file"

        if len(fileName) > 0:
            if ".ann" in fileName:
                new_name = fileName
            else:
                new_name = fileName + '.ann'
            with open(new_name, 'w') as ann_file:
                ann_file.write(content)

            # print "Writen to new file: ", new_name
            self.autoLoadNewFile(new_name, newcursor_index)
            # self.generateSequenceFile()
        else:
            print "Don't write to empty file!"

    def autoLoadNewFile(self, fileName, newcursor_index):
        if self.debug:
            print "Action Track: autoLoadNewFile"
        if len(fileName) > 0:
            self.text.delete("1.0", END)
            text = self.readFile(fileName)
            self.text.insert("end-1c", text)
            self.setNameLabel("File: " + fileName)
            self.text.mark_set(INSERT, newcursor_index)
            self.text.see(newcursor_index)
            self.setCursorLabel(newcursor_index)
            self.apply_tag_colors()

    def apply_tag_colors(self):
        if self.debug:
            print "Action Track: apply_tag_colors"
        self.text.config(insertbackground='red', insertwidth=4, font=self.fnt)

        countVar = StringVar()
        currentCursor = self.text.index(INSERT)
        lineStart = currentCursor.split('.')[0] + '.0'
        lineEnd = currentCursor.split('.')[0] + '.end'

        if self.reprocess_whole_file:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
        while True:
            self.text.tag_configure("category", background=self.entityColor)
            pos = self.text.search(self.force_newline_matching(self.entity_regex.pattern),
                                   "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            # This sets the next place the regex will search from. Searching from just after the start allows for
            # overlapping matches to work. Previously it searched from the end of the previous match
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, 1))

            first_pos = pos
            last_pos = "%s + %sc" % (pos, countVar.get())

            self.text.tag_add("category", first_pos, last_pos)

        # color the most inside span for nested span, scan from begin to end again
        if self.reprocess_whole_file:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
        while True:
            self.text.tag_configure("insideEntityColor", background=self.insideNestEntityColor)
            pos = self.text.search(self.inside_nest_entity_regex.pattern, "matchEnd", "searchLimit",
                                   count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))
            first_pos = "%s + %sc" % (pos, 2)
            last_pos = "%s + %sc" % (pos, str(int(countVar.get()) - 1))
            self.text.tag_add("insideEntityColor", first_pos, last_pos)

    @staticmethod
    def force_newline_matching(pattern):
        return "***:(?s)" + pattern

    def pushToHistory(self):
        if self.debug:
            print "Action Track: pushToHistory"
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    def pushToHistoryEvent(self, event):
        if self.debug:
            print "Action Track: pushToHistoryEvent"
        currentList = []
        content = self.getText()
        cursorPosition = self.text.index(INSERT)
        # print "push to history cursor: ", cursorPosition
        currentList.append(content)
        currentList.append(cursorPosition)
        self.history.append(currentList)

    # update shortcut map
    def do_remap_of_shortcuts(self):
        if self.debug:
            print "Action Track: do_remap_of_shortcuts"
        seq = 0
        new_dict = {}
        listLength = len(self.label_entry_list)
        delete_num = 0
        for key in sorted(self.pressCommand):
            label = self.label_entry_list[seq].get()
            if len(label) > 0:
                new_dict[key] = label
            else:
                delete_num += 1
            seq += 1
        self.pressCommand = new_dict
        for idx in range(1, delete_num + 1):
            self.label_entry_list[listLength - idx].delete(0, END)
            self.shortcut_label_list[listLength - idx].config(text="NON= ")
        with open(self.configFile, 'wb') as fp:
            pickle.dump(self.pressCommand, fp)
        self.show_shortcut_map()
        tkMessageBox.showinfo("Remap Notification",
                              "Shortcut map has been updated!\n\nConfigure file has been saved in File:" +
                              self.configFile)

    # show shortcut map
    def show_shortcut_map(self):
        label_color = "black"
        label_font_size = 14
        if os.path.isfile(self.configFile):
            with open(self.configFile, 'rb') as fp:
                self.pressCommand = pickle.load(fp)

        mapLabel = Label(self, text="Tags", foreground=label_color,
                         font=(self.textFontStyle, label_font_size, self.fontWeight))
        mapLabel.grid(row=0, column=self.textColumn + 2, columnspan=2, rowspan=1, padx=10)
        self.label_entry_list = []
        self.shortcut_label_list = []
        for i, key in enumerate(sorted(self.pressCommand)):
            row = i+1
            # print "key: ", key, "  command: ", self.pressCommand[key]
            shortcut_label = Label(self, text=key.lower() + ": ", foreground=label_color,
                                   font=(self.textFontStyle, label_font_size, self.fontWeight))
            shortcut_label.grid(row=row, column=self.textColumn + 2, columnspan=1, rowspan=1, padx=0)
            self.shortcut_label_list.append(shortcut_label)

            label_entry = Entry(self, foreground=label_color,
                                font=(self.textFontStyle, label_font_size, self.fontWeight))
            label_entry.insert(0, self.pressCommand[key])
            label_entry.grid(row=row, column=self.textColumn + 3, columnspan=1, rowspan=1)
            self.label_entry_list.append(label_entry)
            # print "row: ", row

    def getCursorIndex(self):
        return self.text.index(INSERT)


def main():
    print("SUTDAnnotator launched!")
    print("OS:%s" % (platform.system()))
    root = Tk()
    root.geometry("1300x700+200+200")
    app = YeddaFrame(root)
    app.setFont(12)
    root.mainloop()


if __name__ == '__main__':
    main()
