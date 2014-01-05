#!/usr/bin/env python3
# -*- coding: utf-8 -*-

PROGRAM = "2do"
VERSION = "v1.1-dev"
DOCHELP = """
{0} {1}
--
This software is a simple todo list manager.
It's written in Python using Tkinter and Sqlite.
--
Author: Julien Pecqueur
Home: http://github.com/jpec/2do.py
Email: jpec@julienpecqueur.net
License: GPL
--
Keyboard shortcuts:
 <n> create new task
 <c> copy task to a new task
 <e> edit task
 <s> toggle status (done / todo)
 <u> toggle urgent flag
 <a> toggle archive (archive / unarchive)
 <v> toggle view mode (view archive bin / view tasks)
 <f> focur on search box (return to search)
 <h> display help
""".format(PROGRAM, VERSION)


#---------------------------------------------------------------------
# PATHS FOR DB FILE
#---------------------------------------------------------------------

# If system is Window :
SDBFILE_NT = "c:/todo.sqlite"

# If system is Unix :
SDBFILE_UX = "~/.todo.sqlite"


#---------------------------------------------------------------------
# SOURCE CODE
#---------------------------------------------------------------------

from sqlite3 import connect
from os import name as uname
from os.path import isfile
from os.path import expanduser
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from tkinter.messagebox import askyesno
from tkinter.ttk import Button, Frame, Entry



class app(object):

    "Classe app for 2do"

    def __init__(self, program, version, dochelp):
        "Initialize the class"
        # open/create the database
        self.db = self.openDb()
        # init variables
        self.program = program
        self.version = version
        self.dochelp = dochelp
        self.task = None
        self.tasks = dict()
        self.sksat = dict()
        self.archives = None
        if self.db:
            # launch app
            self.ui = self.drawUi()
            self.log("Loading data…")
            # load tasks
            self.load(self.archives)
            self.log("Data loaded !")
            self.ui.lb.focus_set()
            self.log("Press <h> to display help…")
            self.ui.lb.selection_set(END)
            # loop
            self.ui.mainloop()
            # close database
            self.db.close()
        else:
            print("Database error !")


    def evtVis(self, event):
        "Event toggle tasks/archive mode"
        self.vis()


    def vis(self):
        "Toggle tasks/archives mode"
        if not self.archives:
            # tasks mode
            self.reload(True)
            self.ui.tb.vis.configure(text="View tasks")
            self.ui.tb.arc.configure(text="Reactive")
            self.ui.tb.new.configure(state=DISABLED)
            self.ui.tb.dup.configure(state=DISABLED)
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.don.configure(state=DISABLED)
            self.ui.tb.urg.configure(state=DISABLED)
            self.ui.tb.src.configure(state=DISABLED)
            self.log("Displaying the archives bin…")
        else:
            # archives mode
            self.reload(False)
            self.ui.tb.vis.configure(text="View bin")
            self.ui.tb.arc.configure(text="Archive")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.dup.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.don.configure(state=NORMAL)
            self.ui.tb.urg.configure(state=NORMAL)
            self.ui.tb.src.configure(state=NORMAL)
            self.log("Displaying the tasks…")


    def evtDis(self, event):
        "Focus on search box"
        self.ui.tb.src.focus()
        

    def evtNew(self, event):
        "Event create new task"
        if not self.archives:
            self.new()


    def new(self, task=None):
        "Create a new task"
        self.log("Appending new task…")
        if not task:
            task = askstring("New task ?", "Enter the new task :")
        if task:
            id = self.addTask(task)
            if id:
                self.log("Task {0} added !".format(id))
                self.reload(self.archives, task=id)
            else:
                self.log("Cannot save the task !")


    def evtDup(self, event):
        "Event duplicate a task"
        if not self.archives:
            self.dup()


    def dup(self):
        "Duplicate a task"
        tasks = self.ui.lb.curselection()
        for task in tasks:
            id = self.tasks[str(task)]
            old = self.getTaskInfos(id)            
            self.log("Duplicating task {0}…".format(id))
            self.new(old['task'])


    def getTaskInfos(self, id):
        "Get task's infos"
        sql = "SELECT id, task, active, done, urgent FROM tasks WHERE id = ? ;"
        r = self.db.execute(sql, (id, ))
        t = dict()
        for id, task, active, done, urgent in r.fetchall():
            t['id'] = id
            t['task'] = task
            t['active'] = int(active)
            t['done'] = int(done)
            t['urgent'] = int(urgent)
            return(t)


    def evtEdi(self, event):
        "Event edit task(s)"
        if not self.archives:
            self.edi()


    def edi(self):
        "Edit task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            old = self.getTask(id)
            self.log("Editing task {0}…".format(id))
            new = askstring("Edit task ?", "Enter the new task :", initialvalue=old)
            if new:
                self.editTask(id, new)
                self.log("Task {0} edited !".format(id))
        self.reload(self.archives, task=id)


    def evtArc(self, event):
        "Event toggle archive flag"
        self.arc()


    def arc(self):
        "Toggle archive flag for task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            lb = self.getTask(id)
            if self.isNotArchive(id) and \
               askyesno("Archive ?", "Do yo want to archive following task ?\n' {0} '".format(lb)):
                self.activeTask(id, 0)
                self.log("Task {0} archived !".format(id))
            else:
                self.activeTask(id, 1)
                self.log("Task {0} un-archived !".format(id))
        self.reload(self.archives)


    def evtDon(self, event):
        "Event toggle done flag"
        if not self.archives:
            self.don()


    def don(self):
        "Toggle done flag for task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            if self.isDone(id):
                self.doneTask(id, 0)
                self.log("Task {0} un-done !".format(id))
            else:
                self.doneTask(id, 1)
                self.log("Task {0} done !".format(id))
        self.reload(self.archives, task=id)


    def evtUrg(self, event):
        "Event toggle urgent flag"
        if not self.archives:
            self.urg()


    def urg(self):
        "Toggle urgent flag for task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            if self.isUrgent(id):
                self.urgentTask(id, 0)
                self.log("Task {0} is not urgent !".format(id))
            else:
                self.urgentTask(id, 1)
                self.log("Task {0} is urgent !".format(id))
        self.reload(self.archives, task=id)


    def reload(self, archives=False, selection=END, task=None):
        "Reload tasks/archives list"
        self.ui.lb.delete(0, END)
        self.tasks = dict()
        self.sksat = dict()
        if archives:
            self.load(True)
        else:
            self.load(False)
        self.archives = archives
        self.ui.lb.focus_set()
        if task:
            selection = self.sksat[task] 
        elif len(selection) > 1 and selection != END:
            selection = selection[-1:]
        self.ui.lb.selection_set(selection)
        return(True)


    def evtSrc(self, evt):
        "Event search"
        self.src()


    def src(self):
        "Search tasks"
        mask = self.mask.get()
        if mask == "":
            mask = "%"
            self.mask.set(mask)
        if not self.archives:
            self.reload(False, END, None)
            self.log("Only tasks matching '{0}' are displayed !".format(mask))


    def evtHel(self, evt):
        "Event display help"
        t = "{0} {1}".format(self.program, self.version)
        showinfo(t, self.dochelp)


    def log(self, msg):
        "Display log in status bar"
        self.ui.sb.log.configure(text="> {0}".format(msg))


    def isNewDb(self, dbfile):
        "Return True if the database doesn't exist"
        if isfile(dbfile):
            return(False)
        else:
            return(True)


    def getDbFile(self):
        "Return database file"
        if 'nt' == uname:
            return(SDBFILE_NT)
        else:
            return(SDBFILE_UX)


    def openDb(self):
        "Open the database"
        path = expanduser(self.getDbFile())
        print(path)
        new = self.isNewDb(path)
        db = connect(path)
        if not new:
            return(db)
        elif new and self.createTables(db):
            return(db)
        else:
            return(None)


    def createTables(self, db):
        "Create the database's tables"
        sql = "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, "\
              +"task TEXT, active INT, done INT, urgent INT);"
        db.execute(sql)
        db.commit()
        self.db = db
        return(True)


    def addTask(self, task):
        "Add the task in the database"
        sql = "INSERT INTO tasks (task, active, done, urgent) VALUES (?, 1, 0, 0);"
        id = self.db.execute(sql, (task, )).lastrowid
        self.db.commit()
        return(id)


    def activeTask(self, id, active):
        "Set active flag for the task"
        sql = "UPDATE tasks SET active = ? WHERE id = ? ;"
        self.db.execute(sql, (active, id))
        self.db.commit()
        return(True)


    def doneTask(self, id, done):
        "Set done flag for the task"
        sql = "UPDATE tasks SET done = ? WHERE id = ? ;"
        self.db.execute(sql, (done, id))
        self.db.commit()
        return(True)


    def urgentTask(self, id, urgent):
        "Set urgent flag for the task"
        sql = "UPDATE tasks SET urgent = ? WHERE id = ? ;"
        self.db.execute(sql,(urgent, id))
        self.db.commit()
        return(True)


    def editTask(self, id, new):
        "Update the task"
        sql = "UPDATE tasks SET task = ? WHERE id = ? ;"
        self.db.execute(sql, (new, id))
        self.db.commit()
        return(True)


    def getTasks(self, archives, mask="%"):
        "Get the tasks list"
        if archives:
            sql = "SELECT id, task, active, done, urgent FROM tasks WHERE active = ? AND task LIKE ?;"
            r = self.db.execute(sql, (0, mask))
        else:
            sql = "SELECT id, task, active, done, urgent FROM tasks WHERE active = ? AND task LIKE ? ORDER BY task, id;"
            r = self.db.execute(sql, (1, mask))
        return(r.fetchall())


    def getTaskInfos(self, id):
        "Get task's infos"
        sql = "SELECT id, task, active, done, urgent FROM tasks WHERE id = ? ;"
        r = self.db.execute(sql, (id, ))
        t = dict()
        for id, task, active, done, urgent in r.fetchall():
            t['id'] = id
            t['task'] = task
            t['active'] = int(active)
            t['done'] = int(done)
            t['urgent'] = int(urgent)
            return(t)


    def getTask(self, id):
        "Get a task"
        t = self.getTaskInfos(id)
        return(t['task'])


    def isUrgent(self, id):
        "Get urgent flag for the task"
        t = self.getTaskInfos(id)
        return(t['urgent'])


    def isDone(self, id):
        "Get done flag for the task"
        t = self.getTaskInfos(id)
        return(t['done'])


    def isNotArchive(self, id):
        "Get the *active* flag for the task"
        t = self.getTaskInfos(id)
        return(t['active'])


    def load(self, archives):
        "Load the tasks list"
        l = self.getTasks(archives, self.mask.get())
        i = 0
        for id, task, active, done, urgent in l:
            if archives:
                lbl = "[{0}] {1}".format(id, task)
            else:
                lbl = "{0}".format(task)
            self.ui.lb.insert(id, lbl)
            if int(done) > 0:
                self.ui.lb.itemconfig(i, fg='grey')
            elif int(urgent) > 0:
                self.ui.lb.itemconfig(i, fg='red')
            else:
                self.ui.lb.itemconfig(i, fg='black')
            self.tasks[str(i)] = id
            self.sksat[id] = str(i)
            i = i+1
        return(True)


    def drawUi(self):
        "Draw the UI"
        ui = Tk()
        ui.title("{0} {1}".format(self.program, self.version))
        # toolbar
        ui.tb = Frame(ui)
        ui.tb.pack(anchor='nw')
        # tools
        ui.tb.new = Button(ui.tb, text="New", width=8, command=self.new)
        ui.tb.new.grid(row=1, column=0, padx=2, pady=2)
        ui.tb.dup = Button(ui.tb, text="Copy", width=8, command=self.dup)
        ui.tb.dup.grid(row=1, column=1, padx=2, pady=2)
        ui.tb.edi = Button(ui.tb, text="Edit", width=8, command=self.edi)
        ui.tb.edi.grid(row=1, column=2, padx=2, pady=2)
        ui.tb.arc = Button(ui.tb, text="Archive", width=8, command=self.arc)
        ui.tb.arc.grid(row=1, column=5, padx=2, pady=2)
        ui.tb.don = Button(ui.tb, text="Status", width=8, command=self.don)
        ui.tb.don.grid(row=1, column=3, padx=2, pady=2)
        ui.tb.urg = Button(ui.tb, text="Urgent", width=8, command=self.urg)
        ui.tb.urg.grid(row=1, column=4, padx=2, pady=2)
        ui.tb.vis = Button(ui.tb, text="View bin", width=10, command=self.vis)
        ui.tb.vis.grid(row=1, column=6, padx=2, pady=2)
        ui.tb.lbl = Label(ui.tb, text="Search", width=6)
        ui.tb.lbl.grid(row=2, column=0, padx=2, pady=2)
        self.mask = StringVar()
        self.mask.set("%")
        ui.tb.src = Entry(ui.tb, width=62, textvariable=self.mask)
        ui.tb.src.grid(row=2, column=1, columnspan=6, padx=2, pady=2)
        # listbox
        ui.lb = Listbox(ui, selectmode=EXTENDED)
        ui.lb.pack(expand=True, fill='both')
        # statusbar
        ui.sb = Frame(ui)
        ui.sb.pack(anchor='sw')
        ui.sb.log = Label(ui.sb)
        ui.sb.log.pack(expand=True, fill='both')
        ui.lb.bind("<n>", self.evtNew)
        ui.lb.bind("<c>", self.evtDup)
        ui.lb.bind("<e>", self.evtEdi)
        ui.lb.bind("<a>", self.evtArc)
        ui.lb.bind("<v>", self.evtVis)
        ui.lb.bind("<s>", self.evtDon)
        ui.lb.bind("<u>", self.evtUrg)
        ui.lb.bind("<h>", self.evtHel)
        ui.lb.bind("<f>", self.evtDis)
        ui.tb.src.bind("<Return>", self.evtSrc)
        ui.lb.bind("<Double-Button-1>", self.evtEdi)
        ui.lb.bind("<Button-2>", self.evtUrg)
        ui.lb.bind("<Double-Button-3>", self.evtDon)
        return(ui)



if __name__ == '__main__':
    # start the program
    run = app(PROGRAM, VERSION, DOCHELP)
