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
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.Version = "YEDDA-V1.0 Annotator"
        self.OS = platform.system().lower()
        self.parent = parent
        self.fileName = ""
        self.debug = False
        self.colorAllChunk = True
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
        self.tagScheme = "BMES"
        self.onlyNP = False  # for exporting sequence 
        self.keep_recommend = True

        '''
        self.segmented: for exporting sequence, if True then split words with space, else split character without space
        For example, if your data is segmented Chinese (or English) with words separated by a space, you need to 
        set this flag as true
        If your data is Chinese without segmentation, you need to set this flag as False
        '''
        self.segmented = True  # False for non-segmentated Chinese, True for English or Segmented Chinese
        self.configFile = "config.pkl"
        self.entity_regex = re.compile(r'\[@.*?#.*?\*\](?!#)')
        self.inside_nest_entity_regex = re.compile(r'\[@\[@(?!\[@).*?#.*?\*\]#')
        self.recommend_regex = re.compile(r'\[\$.*?#.*?\*\](?!#)')
        self.gold_and_recommend_regex = re.compile(r'\[@.*?#.*?\*\](?!#)')
        if self.keep_recommend:
            self.gold_and_recommend_regex = re.compile(r'\[[@$)].*?#.*?\*\](?!#)')
        # configure color
        self.entityColor = "SkyBlue1"
        self.insideNestEntityColor = "light slate blue"
        self.recommendColor = 'lightgreen'
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

        # recommend_on_button = Button(self, text="RMOn", command=self.setInRecommendModel)
        # recommend_on_button.grid(row=2, column=self.textColumn + 1)
        #
        # recommend_off_button = Button(self, text="RMOff", command=self.setInNotRecommendModel)
        # recommend_off_button.grid(row=3, column=self.textColumn + 1)

        remap_button = Button(self, text="ReMap", command=self.renewPressCommand)
        remap_button.grid(row=4, column=self.textColumn + 1, pady=4)

        export_button = Button(self, text="Export", command=self.generateSequenceFile)
        export_button.grid(row=5, column=self.textColumn + 1, pady=4)

        quit_button = Button(self, text="Quit", command=self.quit)
        quit_button.grid(row=6, column=self.textColumn + 1, pady=4)

        self.cursorName = Label(self, text="Cursor: ", foreground="Blue", font=(self.textFontStyle, 14, self.fontWeight))
        self.cursorName.grid(row=9, column=self.textColumn + 1, pady=4)
        self.cursorIndex = Label(self, text=("row: %s\ncol: %s" % (0, 0)), foreground="red",
                                 font=(self.textFontStyle, 14, self.fontWeight))
        self.cursorIndex.grid(row=10, column=self.textColumn + 1, pady=4)

        self.RecommendModelName = Label(self, text="RModel: ", foreground="Blue", font=(self.textFontStyle, 14, self.fontWeight))
        self.RecommendModelName.grid(row=12, column=self.textColumn + 1, pady=4)
        self.RecommendModelFlag = Label(self, text=str(self.recommendFlag), foreground="red",
                                        font=(self.textFontStyle, 14, self.fontWeight))
        self.RecommendModelFlag.grid(row=13, column=self.textColumn + 1, pady=4)

        # recommend_value = StringVar()
        # recommend_value.set("R")
        # a = Radiobutton(self.parent,  text="Recommend",   width=12, variable=recommend_value, value="R")
        # # a.grid(row =1 , column = 2)
        # a.pack(side='left')
        # b = Radiobutton(self.parent, text="NotRecommend",   width=12,  variable=recommend_value, value="N")
        # # b.grid(row =1 , column = 3)
        # b.pack(side='left')

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

        self.setMapShow()

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
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            pass

    def setInRecommendModel(self):
        self.recommendFlag = True
        self.RecommendModelFlag.config(text=str(self.recommendFlag))
        tkMessageBox.showinfo("Recommend Model", "Recommend Model has been activated!")

    def setInNotRecommendModel(self):
        self.recommendFlag = False
        self.RecommendModelFlag.config(text=str(self.recommendFlag))
        content = self.getText()
        content = remove_recommend_content(content, self.recommend_regex)
        self.writeFile(self.fileName, content, '1.0')
        tkMessageBox.showinfo("Recommend Model", "Recommend Model has been deactivated!")

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
            self.writeFile(self.fileName, historyContent, cursorIndex)
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
            if re.match(self.entity_regex, selected_string) is not None:
                # if have selected entity
                new_string_list = selected_string.strip('[@]').rsplit('#', 1)
                new_string = new_string_list[0]
                followHalf_content = followHalf_content.replace(selected_string, new_string, 1)
                selected_string = new_string
                # cursor_index = "%s - %sc" % (cursor_index, str(len(new_string_list[1])+4))
                cursor_index = cursor_index.split('.')[0] + "." + str(
                    int(cursor_index.split('.')[1]) - len(new_string_list[1]) + 4)
            afterEntity_content = followHalf_content[len(selected_string):]

            if command == "q":
                print 'q: remove entity label'
                entity_content = selected_string
            else:
                if len(selected_string) > 0:
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string,
                                                                      command, cursor_index)
            aboveHalf_content += entity_content
            content = self.addRecommendContent(aboveHalf_content, afterEntity_content, self.recommendFlag)
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)
        except TclError:
            # no text selected - use item under cursor
            cursor_index = self.text.index(INSERT)
            [line_id, column_id] = cursor_index.split('.')
            aboveLine_content = self.text.get('1.0', str(int(line_id) - 1) + '.end')
            belowLine_content = self.text.get(str(int(line_id) + 1) + '.0', "end-1c")
            line = self.text.get(line_id + '.0', line_id + '.end')
            matched_span = (-1, -1)
            detected_entity = -1  # detected entity type:－1 not detected, 1 detected manual tag, 2 detected recommend
            for match in self.entity_regex.finditer(line):
                if match.span()[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                    matched_span = match.span()
                    detected_entity = 1
                    break
            if detected_entity == -1:
                for match in self.recommend_regex.finditer(line):
                    if match.span()[0] <= int(column_id) & int(column_id) <= match.span()[1]:
                        matched_span = match.span()
                        detected_entity = 2
                        break
            line_before_entity = line
            line_after_entity = ""
            if matched_span[1] > 0:
                selected_string = line[matched_span[0]:matched_span[1]]
                if detected_entity == 1:
                    new_string_list = selected_string.strip('[@*]').rsplit('#', 1)
                elif detected_entity == 2:
                    new_string_list = selected_string.strip('[$*]').rsplit('#', 1)
                new_string = new_string_list[0]
                old_entity_type = new_string_list[1]
                line_before_entity = line[:matched_span[0]]
                line_after_entity = line[matched_span[1]:]
                selected_string = new_string
                entity_content = selected_string
                cursor_index = line_id + '.' + str(int(matched_span[1]) - (len(new_string_list[1]) + 4))
                if command == "q":
                    print 'q: remove entity label'
                elif command == 'y':
                    print "y: comfirm recommend label"
                    old_key = self.pressCommand.keys()[self.pressCommand.values().index(old_entity_type)]
                    entity_content, cursor_index = self.replaceString(selected_string, selected_string, old_key,
                                                                      cursor_index)
                else:
                    if len(selected_string) > 0:
                        if command in self.pressCommand:
                            entity_content, cursor_index = self.replaceString(selected_string, selected_string, command,
                                                                              cursor_index)
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

            content = self.addRecommendContent(aboveHalf_content, followHalf_content, self.recommendFlag)
            content = content.encode('utf-8')
            self.writeFile(self.fileName, content, cursor_index)

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
        self.writeFile(self.fileName, content, last_insert)

    def replaceString(self, content, string, replaceType, cursor_index):
        if replaceType in self.pressCommand:
            new_string = "[@" + string + "#" + self.pressCommand[replaceType] + "*]"
            newcursor_index = cursor_index.split('.')[0] + "." + str(
                int(cursor_index.split('.')[1]) + len(self.pressCommand[replaceType]) + 5)
        else:
            print "Invalid command!"
            print "cursor index: ", self.text.index(INSERT)
            return content, cursor_index
        content = content.replace(string, new_string, 1)
        return content, newcursor_index

    def writeFile(self, fileName, content, newcursor_index):
        if self.debug:
            print "Action track: writeFile"

        if len(fileName) > 0:
            if ".ann" in fileName:
                new_name = fileName
                ann_file = open(new_name, 'w')
                ann_file.write(content)
                ann_file.close()
            else:
                new_name = fileName + '.ann'
                ann_file = open(new_name, 'w')
                ann_file.write(content)
                ann_file.close()
                # print "Writed to new file: ", new_name
            self.autoLoadNewFile(new_name, newcursor_index)
            # self.generateSequenceFile()
        else:
            print "Don't write to empty file!"

    def addRecommendContent(self, train_data, decode_data, recommendMode):
        if not recommendMode:
            content = train_data + decode_data
        else:
            if self.debug:
                print "Action Track: addRecommendContent, start Recommend entity"
            content = maximum_matching(train_data, decode_data)
        return content

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
            self.setColorDisplay()

    def setColorDisplay(self):
        if self.debug:
            print "Action Track: setColorDisplay"
        self.text.config(insertbackground='red', insertwidth=4, font=self.fnt)

        countVar = StringVar()
        currentCursor = self.text.index(INSERT)
        lineStart = currentCursor.split('.')[0] + '.0'
        lineEnd = currentCursor.split('.')[0] + '.end'

        if self.colorAllChunk:
            self.text.mark_set("matchStart", "1.0")
            self.text.mark_set("matchEnd", "1.0")
            self.text.mark_set("searchLimit", 'end-1c')
            self.text.mark_set("recommend_matchStart", "1.0")
            self.text.mark_set("recommend_matchEnd", "1.0")
            self.text.mark_set("recommend_searchLimit", 'end-1c')
        else:
            self.text.mark_set("matchStart", lineStart)
            self.text.mark_set("matchEnd", lineStart)
            self.text.mark_set("searchLimit", lineEnd)
            self.text.mark_set("recommend_matchStart", lineStart)
            self.text.mark_set("recommend_matchEnd", lineStart)
            self.text.mark_set("recommend_searchLimit", lineEnd)
        while True:
            self.text.tag_configure("catagory", background=self.entityColor)
            self.text.tag_configure("edge", background=self.entityColor)
            pos = self.text.search(self.entity_regex.pattern, "matchEnd", "searchLimit", count=countVar, regexp=True)
            if pos == "":
                break
            self.text.mark_set("matchStart", pos)
            self.text.mark_set("matchEnd", "%s+%sc" % (pos, countVar.get()))

            first_pos = pos
            second_pos = "%s+%sc" % (pos, str(1))
            lastsecond_pos = "%s+%sc" % (pos, str(int(countVar.get()) - 1))
            last_pos = "%s + %sc" % (pos, countVar.get())

            self.text.tag_add("catagory", second_pos, lastsecond_pos)
            self.text.tag_add("edge", first_pos, second_pos)
            self.text.tag_add("edge", lastsecond_pos, last_pos)
            # color recommend type
        while True:
            self.text.tag_configure("recommend", background=self.recommendColor)
            recommend_pos = self.text.search(self.recommend_regex.pattern, "recommend_matchEnd", "recommend_searchLimit",
                                             count=countVar, regexp=True)
            if recommend_pos == "":
                break
            self.text.mark_set("recommend_matchStart", recommend_pos)
            self.text.mark_set("recommend_matchEnd", "%s+%sc" % (recommend_pos, countVar.get()))

            first_pos = recommend_pos
            # second_pos = "%s+%sc" % (recommend_pos, str(1))
            lastsecond_pos = "%s+%sc" % (recommend_pos, str(int(countVar.get())))
            self.text.tag_add("recommend", first_pos, lastsecond_pos)

        # color the most inside span for nested span, scan from begin to end again  
        if self.colorAllChunk:
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
    def renewPressCommand(self):
        if self.debug:
            print "Action Track: renewPressCommand"
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
        self.setMapShow()
        tkMessageBox.showinfo("Remap Notification",
                              "Shortcut map has been updated!\n\nConfigure file has been saved in File:" +
                              self.configFile)

    # show shortcut map
    def setMapShow(self):
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

    def generateSequenceFile(self):
        if (".ann" not in self.fileName) and (".txt" not in self.fileName):
            out_error = "Export only works on filename ended in .ann or .txt!\nPlease rename file."
            print out_error
            tkMessageBox.showerror("Export error!", out_error)

            return -1
        fileLines = open(self.fileName, 'rU').readlines()
        lineNum = len(fileLines)
        new_filename = self.fileName.split('.ann')[0] + '.anns'
        seqFile = open(new_filename, 'w')
        for line in fileLines:
            if len(line) <= 2:
                seqFile.write('\n')
                continue
            else:
                if not self.keep_recommend:
                    line = remove_recommend_content(line, self.recommend_regex)
                wordTagPairs = get_word_tag_pairs(line, self.segmented, self.tagScheme, self.onlyNP, self.gold_and_recommend_regex)
                for wordTag in wordTagPairs:
                    seqFile.write(wordTag)
                # use null line to seperate sentences
                seqFile.write('\n')
        seqFile.close()
        print "Exported file into sequence style in file: ", new_filename
        print "Line number:", lineNum
        showMessage = "Exported file successfully!\n\n"
        showMessage += "Tag scheme: " + self.tagScheme + "\n\n"
        showMessage += "Keep Recom: " + str(self.keep_recommend) + "\n\n"
        showMessage += "Text Seged: " + str(self.segmented) + "\n\n"
        showMessage += "Line Number: " + str(lineNum) + "\n\n"
        showMessage += "Saved to File: " + new_filename
        tkMessageBox.showinfo("Export Message", showMessage)


def get_word_tag_pairs(taged_sentence, segmented=True, tag_scheme="BMES", only_np=False, entity_re=r'\[\@.*?\#.*?\*\]'):
    new_sent = taged_sentence.strip('\n').decode('utf-8')
    filter_list = re.findall(entity_re, new_sent)
    new_sent_length = len(new_sent)
    chunk_list = []
    start_pos = 0
    end_pos = 0
    if len(filter_list) == 0:
        single_chunk_list = [new_sent, 0, len(new_sent), False]
        chunk_list.append(single_chunk_list)
        # print single_chunk_list
        single_chunk_list = []
    else:
        for pattern in filter_list:
            # print pattern
            single_chunk_list = []
            start_pos = end_pos + new_sent[end_pos:].find(pattern)
            end_pos = start_pos + len(pattern)
            single_chunk_list.append(pattern)
            single_chunk_list.append(start_pos)
            single_chunk_list.append(end_pos)
            single_chunk_list.append(True)
            chunk_list.append(single_chunk_list)
            single_chunk_list = []
    # chunk_list format:
    full_list = []
    for idx in range(0, len(chunk_list)):
        if idx == 0:
            if chunk_list[idx][1] > 0:
                full_list.append([new_sent[0:chunk_list[idx][1]], 0, chunk_list[idx][1], False])
                full_list.append(chunk_list[idx])
            else:
                full_list.append(chunk_list[idx])
        else:
            if chunk_list[idx][1] == chunk_list[idx - 1][2]:
                full_list.append(chunk_list[idx])
            elif chunk_list[idx][1] < chunk_list[idx - 1][2]:
                print "ERROR: found pattern has overlap!", chunk_list[idx][1], ' with ', chunk_list[idx - 1][2]
            else:
                full_list.append(
                    [new_sent[chunk_list[idx - 1][2]:chunk_list[idx][1]], chunk_list[idx - 1][2], chunk_list[idx][1],
                     False])
                full_list.append(chunk_list[idx])

        if idx == len(chunk_list) - 1:
            if chunk_list[idx][2] > new_sent_length:
                print "ERROR: found pattern position larger than sentence length!"
            elif chunk_list[idx][2] < new_sent_length:
                full_list.append([new_sent[chunk_list[idx][2]:new_sent_length], chunk_list[idx][2], new_sent_length, False])
            else:
                continue
    return turn_full_list_to_output_pair(full_list, segmented, tag_scheme, only_np)


def turn_full_list_to_output_pair(full_list, segmented=True, tag_scheme="BMES", only_np=False):
    pair_list = []
    for eachList in full_list:
        if eachList[3]:
            cont_label_list = eachList[0].strip('[@$]').rsplit('#', 1)
            if len(cont_label_list) != 2:
                print "Error: sentence format error!"
            label = cont_label_list[1].strip('*')
            if segmented:
                cont_label_list[0] = cont_label_list[0].split()
            if only_np:
                label = "NP"
            out_list = output_with_tag_scheme(cont_label_list[0], label, tag_scheme)
            for eachItem in out_list:
                pair_list.append(eachItem)
        else:
            if segmented:
                eachList[0] = eachList[0].split()
            for idx in range(0, len(eachList[0])):
                basic_content = eachList[0][idx]
                if basic_content == ' ':
                    continue
                pair = basic_content + ' ' + 'O\n'
                pair_list.append(pair.encode('utf-8'))
    return pair_list


def output_with_tag_scheme(input_list, label, tag_scheme="BMES"):
    output_list = []
    list_length = len(input_list)
    if tag_scheme == "BMES":
        if list_length == 1:
            pair = input_list[0] + ' ' + 'S-' + label + '\n'
            output_list.append(pair.encode('utf-8'))
        else:
            for idx in range(list_length):
                if idx == 0:
                    pair = input_list[idx] + ' ' + 'B-' + label + '\n'
                elif idx == list_length - 1:
                    pair = input_list[idx] + ' ' + 'E-' + label + '\n'
                else:
                    pair = input_list[idx] + ' ' + 'M-' + label + '\n'
                output_list.append(pair.encode('utf-8'))
    else:
        for idx in range(list_length):
            if idx == 0:
                pair = input_list[idx] + ' ' + 'B-' + label + '\n'
            else:
                pair = input_list[idx] + ' ' + 'I-' + label + '\n'
            output_list.append(pair.encode('utf-8'))
    return output_list


def remove_recommend_content(content, recommend_re=r'\[\$.*?\#.*?\*\](?!\#)'):
    output_content = ""
    last_match_end = 0
    for match in re.finditer(recommend_re, content):
        matched = content[match.span()[0]:match.span()[1]]
        words = matched.strip('[$]').split("#")[0]
        output_content += content[last_match_end:match.span()[0]] + words
        last_match_end = match.span()[1]
    output_content += content[last_match_end:]
    return output_content


def decompose_command(command_string):
    command_list = []
    each_command = []
    num_select = ''
    for idx in range(0, len(command_string)):
        if command_string[idx].isdigit():
            num_select += command_string[idx]
        else:
            each_command.append(num_select)
            each_command.append(command_string[idx])
            command_list.append(each_command)
            each_command = []
            num_select = ''
    # print command_list
    return command_list


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
