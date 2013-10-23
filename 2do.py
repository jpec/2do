#!/usr/bin/env python3
# -*- coding: utf-8 -*-

PROGRAM = "2do"
VERSION = "v1.0-beta"
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
 <e> edit task
 <s> toggle status (done / todo)
 <u> toggle urgent flag
 <a> toggle archive (archive / unarchive)
 <v> toggle view mode (view archive bin / view tasks)
 <h> display help
""".format(PROGRAM, VERSION)


#---------------------------------------------------------------------
# PATHS FOR DB FILE
#---------------------------------------------------------------------

# If system is Window :
SDBFILE_NT = "Y:/todo.sqlite"

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
from tkinter.ttk import Button, Frame


def isNewDb(dbfile):
    "Return True if the database doesn't exist"
    if isfile(dbfile):
        return(False)
    else:
        return(True)


def getDbFile():
    "Return database file"
    if 'nt' == uname:
        return(SDBFILE_NT)
    else:
        return(SDBFILE_UX)


def openDb():
    "Open the database"
    path = expanduser(getDbFile())
    print(path)
    new = isNewDb(path)
    db = connect(path)
    if not new:
        return(db)
    elif new and createTables(db):
        return(db)
    else:
        return(None)


def createTables(db):
    "Create the database's tables"
    sql = "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, "\
          +"task TEXT, active INT, done INT, urgent INT);"
    db.execute(sql)
    db.commit()
    return(True)


def addTask(db, task):
    "Add the task in the database"
    sql = "INSERT INTO tasks (task, active, done, urgent) VALUES (?, 1, 0, 0);"
    id = db.execute(sql,(task, )).lastrowid
    db.commit()
    return(id)


def activeTask(db, id, active):
    "Set active flag for the task"
    sql = "UPDATE tasks SET active = ? WHERE id = ? ;"
    db.execute(sql,(active, id))
    db.commit()
    return(True)


def doneTask(db, id, done):
    "Set done flag for the task"
    sql = "UPDATE tasks SET done = ? WHERE id = ? ;"
    db.execute(sql,(done, id))
    db.commit()
    return(True)


def urgentTask(db, id, urgent):
    "Set urgent flag for the task"
    sql = "UPDATE tasks SET urgent = ? WHERE id = ? ;"
    db.execute(sql,(urgent, id))
    db.commit()
    return(True)


def editTask(db, id, new):
    "Update the task"
    sql = "UPDATE tasks SET task = ? WHERE id = ? ;"
    id = db.execute(sql,(new, id))
    db.commit()
    return(True)


def getTasks(db, archives):
    "Get the tasks list"
    sql = "SELECT id, task, active, done, urgent FROM tasks WHERE active = ? ;"
    if archives:
        r = db.execute(sql, (0, ))
    else:
        r = db.execute(sql, (1, ))
    return(r.fetchall())


def getTaskInfos(db, id):
    "Get task's infos"
    sql = "SELECT id, task, active, done, urgent FROM tasks WHERE id = ? ;"
    r = db.execute(sql, (id, ))
    t = dict()
    for id, task, active, done, urgent in r.fetchall():
        t['id'] = id
        t['task'] = task
        t['active'] = int(active)
        t['done'] = int(done)
        t['urgent'] = int(urgent)
        return(t)
    

def getTask(db, id):
    "Get a task"
    t = getTaskInfos(db, id)
    return(t['task'])


def isUrgent(db, id):
    "Get urgent flag for the task"
    t = getTaskInfos(db, id)
    return(t['urgent'])


def isDone(db, id):
    "Get done flag for the task"
    t = getTaskInfos(db, id)
    return(t['done'])


def isNotArchive(db, id):
    "Get the *active* flag for the task"
    t = getTaskInfos(db, id)
    return(t['active'])


def load(app, archives):
    "Load the tasks list"
    l = getTasks(app.db, app.archives)
    i = 0
    for id, task, active, done, urgent in l:
        if int(done) > 0:
            lbl = "{0} (done)".format(task)
        else:
            lbl = "{0}".format(task)
        app.ui.lb.insert(id, lbl)
        if int(done) > 0:
            app.ui.lb.itemconfig(i, fg='grey')
        elif int(urgent) > 0:
            app.ui.lb.itemconfig(i, fg='red')
        else:
            app.ui.lb.itemconfig(i, fg='black')
        app.tasks[str(i)] = id
        i = i+1
    return(True)


def drawUi(app):
    "Draw the UI"
    ui = Tk()
    ui.title("{0} {1}".format(app.program, app.version))
    # toolbar
    ui.tb = Frame(ui)
    ui.tb.pack(anchor='nw')
    # tools
    ui.tb.new = Button(ui.tb, text="New", width=8, command=app.new)
    ui.tb.new.grid(row=1, column=0, padx=2, pady=2)
    ui.tb.edi = Button(ui.tb, text="Edit", width=8, command=app.edi)
    ui.tb.edi.grid(row=1, column=1, padx=2, pady=2)
    ui.tb.arc = Button(ui.tb, text="Archive", width=8, command=app.arc)
    ui.tb.arc.grid(row=1, column=5, padx=2, pady=2)
    ui.tb.don = Button(ui.tb, text="Status", width=8, command=app.don)
    ui.tb.don.grid(row=1, column=2, padx=2, pady=2)
    ui.tb.urg = Button(ui.tb, text="Urgent", width=8, command=app.urg)
    ui.tb.urg.grid(row=1, column=3, padx=2, pady=2)
    ui.tb.vis = Button(ui.tb, text="View bin", width=10, command=app.vis)
    ui.tb.vis.grid(row=1, column=6, padx=2, pady=2)
    # listbox
    ui.lb = Listbox(ui, selectmode=EXTENDED)
    ui.lb.pack(expand=True, fill='both')
    # statusbar
    ui.sb = Frame(ui)
    ui.sb.pack(anchor='sw')
    ui.sb.log = Label(ui.sb)
    ui.sb.log.pack(expand=True, fill='both')
    ui.bind("<n>", app.evtNew)
    ui.bind("<e>", app.evtEdi)
    ui.bind("<a>", app.evtArc)
    ui.bind("<v>", app.evtVis)
    ui.bind("<s>", app.evtDon)
    ui.bind("<u>", app.evtUrg)
    ui.bind("<h>", app.evtHel)
    ui.lb.bind("<Double-Button-1>", app.evtEdi)
    ui.lb.bind("<Button-2>", app.evtUrg)
    ui.lb.bind("<Double-Button-3>", app.evtDon)
    return(ui)


class app(object):
    "Classe app for 2do"

    def __init__(self, program, version, dochelp):
        "Initialize the class"
        # open/create the database
        self.db = openDb()
        # init variables
        self.program = program
        self.version = version
        self.dochelp = dochelp
        self.task = None
        self.tasks = dict()
        self.archives = None
        if self.db:
            # launch app
            self.ui = drawUi(self)
            self.log("Loading data…")
            # load tasks
            load(self, self.archives)
            self.log("Data loaded !")
            self.ui.lb.focus_set()
            self.log("Press <h> to display help…")
            self.ui.lb.selection_set(END)
            # loop
            self.ui.mainloop()
            # close database
            self.db.close()
        else:
            print("Database error !")


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
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.don.configure(state=DISABLED)
            self.ui.tb.urg.configure(state=DISABLED)
            self.log("Displaying the archives bin…")
        else:
            # archives mode
            self.reload(False)
            self.ui.tb.vis.configure(text="View bin")
            self.ui.tb.arc.configure(text="Archive")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.don.configure(state=NORMAL)
            self.ui.tb.urg.configure(state=NORMAL)
            self.log("Displaying the tasks…")


    def evtNew(self, event):
        "Event create new task"
        if not self.archives:
            self.new()


    def new(self):
        "Create a new task"
        self.log("Appending new task…")
        task = askstring("New task ?", "Enter the new task :")
        if task:
            id = addTask(self.db, self.task)
            if id:
                self.log("Task {0} added !".format(id))
                self.reload(self.archives)
            else:
                self.log("Cannot save the task !")


    def evtEdi(self, event):
        "Event edit task(s)"
        if not self.archives:
            self.edi()


    def edi(self):
        "Edit task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            old = getTask(self.db, self.id)
            self.log("Editing task {0}…".format(id))
            new = askstring("Edit task ?", "Enter the new task :", initialvalue=old)
            if new:
                editTask(self.db, self.id, new)
                self.log("Task {0} edited !".format(id))
        self.reload(self.archives)


    def evtArc(self, event):
        "Event toggle archive flag"
        self.arc()


    def arc(self):
        "Toggle archive flag for task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            if isNotArchive(self.db, self.id) and \
               askyesno("Archive ?", "Do yo want to archive task {0} ?".format(id)):
                activeTask(self.db, self.id, 0)
                self.log("Task {0} archived !".format(id))
            else:
                activeTask(self.db, self.id, 1)
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
            id = self.tasks[task]
            if isDone(self.db, self.id):
                doneTask(self.db, self.id, 0)
                self.log("Task {0} un-done !".format(id))
            else:
                doneTask(self.db, self.id, 1)
                self.log("Task {0} done !".format(id))
        self.reload(self.archives)


    def evtUrg(self, event):
        "Event toggle urgent flag"
        if not self.archives:
            self.urg()


    def urg(self):
        "Toggle urgent flag for task(s)"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            if isUrgent(self.db, self.id):
                urgentTask(self.db, self.id, 0)
                self.log("Task {0} is not urgent !".format(id))
            else:
                urgentTask(self.db, self.id, 1)
                self.log("Task {0} is urgent !".format(id))
        self.reload(self.archives)


    def reload(self, archives=False):
        "Reload tasks/archives list"
        self.ui.lb.delete(0, END)
        self.tasks = dict()
        if archives:
            load(self, True)
        else:
            load(self, False)
        self.archives = archives
        self.ui.lb.focus_set()
        self.ui.lb.selection_set(END)
        return(True)


    def evtHel(self, evt):
        "Event display help"
        t = "{0} {1}".format(self.program, self.version)
        showinfo(t, self.dochelp)


    def log(self, msg):
        "Display log in status bar"
        self.ui.sb.log.configure(text="> {0}".format(msg))


if __name__ == '__main__':
    # start the program
    run = app(PROGRAM, VERSION, DOCHELP)
