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

# If system is Window :
SDBFILE_NT = "Y:/todo.sqlite"
# If system is Unix :
SDBFILE_UX = "~/.todo.sqlite"


from sqlite3 import connect
import os
from os.path import isfile
from os.path import expanduser
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from tkinter.messagebox import askyesno
from tkinter.ttk import Button, Frame


def getCfg():
    # Strings
    cfg = dict()
    cfg['program'] = PROGRAM
    cfg['version'] = VERSION
    if 'nt' == os.name:
        cfg['file'] = SDBFILE_NT
    else:
        cfg['file'] = SDBFILE_UX
    cfg['help'] = DOCHELP
    cfg['taskdone'] = "{0} (terminée)"
    cfg['tasknotdone'] = "{0}"
    cfg['title'] = "{0} {1}"
    cfg['log'] = "> {0}"
    # SQL
    cfg['sqlCreate'] = "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, active INT, done INT, urgent INT);"
    cfg['sqlAdd'] = "INSERT INTO tasks (task, active, done, urgent) VALUES (?, 1, 0, 0);"
    cfg['sqlArchive'] = "UPDATE tasks SET active = 0 WHERE id = ? ;"
    cfg['sqlUnArchive'] = "UPDATE tasks SET active = 1 WHERE id = ? ;"
    cfg['sqlDone'] = "UPDATE tasks SET done = 1 WHERE id = ? ;"
    cfg['sqlUnDone'] = "UPDATE tasks SET done = 0 WHERE id = ? ;"
    cfg['sqlGet'] = "SELECT id, task, active, done, urgent FROM tasks WHERE active = 1 ;"
    cfg['sqlGet2'] = "SELECT id, task, active, done, urgent FROM tasks WHERE active = 0 ;"
    cfg['sqlGet1'] = "SELECT id, task, active, done, urgent FROM tasks WHERE id = ? ;"
    cfg['sqlEdit'] = "UPDATE tasks SET task = ? WHERE id = ? ;"
    cfg['sqlUrg'] = "UPDATE tasks SET urgent = 1 WHERE id = ? ;"
    cfg['sqlLow'] = "UPDATE tasks SET urgent = 0 WHERE id = ? ;"
    return(cfg)

def isNewDb(dbfile):
    if isfile(dbfile):
        return(False)
    else:
        return(True)


def openDb(cfg):
    path = expanduser(cfg['file'])
    print(path)
    new = isNewDb(path)
    db = connect(path)
    if not new:
        return(db)
    elif new and createTables(db, cfg):
        return(db)
    else:
        return(None)


def createTables(db, cfg):
    sql = cfg['sqlCreate']
    db.execute(sql)
    db.commit()
    return(True)


def addTask(db, cfg, task):
    sql = cfg['sqlAdd']
    id = db.execute(sql,(task, )).lastrowid
    db.commit()
    return(id)


def archiveTask(db, cfg, id):
    sql = cfg['sqlArchive']
    db.execute(sql,(id, ))
    db.commit()
    return(True)


def unarchiveTask(db, cfg, id):
    sql = cfg['sqlUnArchive']
    db.execute(sql,(id, ))
    db.commit()
    return(True)


def doneTask(db, cfg, id):
    sql = cfg['sqlDone']
    db.execute(sql,(id, ))
    db.commit()
    return(True)


def undoneTask(db, cfg, id):
    sql = cfg['sqlUnDone']
    db.execute(sql,(id, ))
    db.commit()
    return(True)


def urgentTask(db, cfg, id):
    sql = cfg['sqlUrg']
    db.execute(sql,(id, ))
    db.commit()
    return(True)


def lowTask(db, cfg, id):
    sql = cfg['sqlLow']
    db.execute(sql,(id, ))
    db.commit()
    return(True)


def editTask(db, cfg, id, new):
    sql = cfg['sqlEdit']
    id = db.execute(sql,(new, id))
    db.commit()
    return(True)


def getTasks(db, cfg, archives):
    if archives:
        sql = cfg['sqlGet2']
    else:
        sql = cfg['sqlGet']
    r = db.execute(sql)
    return(r.fetchall())


def getTask(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql,(id, ))
    for id, task, active, done, urgent in r.fetchall():
        return(task)


def isUrgent(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql,(id, ))
    for id, task, active, done, urgent in r.fetchall():
        return(int(urgent))

        
def isDone(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql,(id, ))
    for id, task, active, done, urgent in r.fetchall():
        return(int(done))


def isNotArchive(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql,(id, ))
    for id, task, active, done, urgent in r.fetchall():
        return(int(active))
    
        
def load(app, archives):
    l = getTasks(app.db, app.cfg, archives)
    i = 0
    for id, task, active, done, urgent in l:
        if int(done) > 0:
            lbl = cfg['taskdone'].format(task)
        else:
            lbl = cfg['tasknotdone'].format(task)
        app.ui.lb.insert(id, lbl)
        if int(done) > 0:
            app.ui.lb.itemconfig(i, fg='grey')
        elif int(urgent) > 0:
            app.ui.lb.itemconfig(i, fg='red')
        else:
            app.ui.lb.itemconfig(i, fg='black')
        app.tasks[i] = id
        i = i+1
    return(True)


def drawUi(app, cfg):
    ui = Tk()
    ui.title(cfg['title'].format(cfg['program'], cfg['version']))
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

    def __init__(self, cfg):
        # open / create db
        self.cfg = cfg
        self.db = openDb(cfg)
        self.task = None
        self.tasks = dict()
        self.archives = None
        if self.db:
            # launch app
            self.ui = drawUi(self, cfg)
            self.log("Loading data…")
            load(self, self.archives)
            self.log("Data loaded !")
            self.ui.lb.focus_set()
            self.log("Press <h> to display help…")
            self.ui.lb.selection_set(END)
            self.ui.mainloop()
            self.db.close()
        else:
            print("Database error !")


    def evtVis(self, event):
        self.vis()


    def vis(self):
        if not self.archives:
            self.reload(True)
            self.ui.tb.vis.configure(text="View tasks")
            self.ui.tb.new.configure(state=DISABLED)
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.don.configure(state=DISABLED)
            self.ui.tb.urg.configure(state=DISABLED)
            self.log("Displaying the archives bin…")
        else:
            self.reload(False)
            self.ui.tb.vis.configure(text="View bin")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.don.configure(state=NORMAL)
            self.ui.tb.urg.configure(state=NORMAL)
            self.log("Displaying the tasks…")


    def evtNew(self, event):
        if not self.archives:
            self.new()


    def new(self):
        self.log("Appending new task…")
        task = askstring("New task ?", "Enter the new task :")
        if task:
            id = addTask(self.db, self.cfg, task)
            if id:
                self.log("Task {0} added !".format(id))
                self.reload(self.archives)
            else:
                self.log("Cannot save the task !")

                
    def evtEdi(self, event):
        if not self.archives:
            self.edi()

        
    def edi(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            old = getTask(self.db, self.cfg, id)
            self.log("Editing task {0}…".format(id))
            new = askstring("Edit task ?", "Enter the new task :", initialvalue=old)
            if new:
                editTask(self.db, self.cfg, id, new)
                self.log("Task {0} edited !".format(id))
                self.reload(self.archives)


    def evtArc(self, event):
        self.arc()


    def arc(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            if isNotArchive(self.db, self.cfg, id) and \
               askyesno("Archive ?", "Do yo want to archive task {0} ?".format(id)):
                archiveTask(self.db, self.cfg, id)
                self.log("Task {0} archived !".format(id))
            else:
                unarchiveTask(self.db, self.cfg, id)
                self.log("Task {0} un-archived !".format(id))
            self.reload(self.archives)


    def evtDon(self, event):
        if not self.archives:
            self.don()


    def don(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            if isDone(self.db, self.cfg, id):
                undoneTask(self.db, self.cfg, id)
                self.log("Task {0} un-done !".format(id))
            else:
                doneTask(self.db, self.cfg, id)
                self.log("Task {0} done !".format(id))
        self.reload(self.archives)
            
    
    def evtUrg(self, event):
        if not self.archives:
            self.urg()


    def urg(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            if isUrgent(self.db, self.cfg, id):
                lowTask(self.db, self.cfg, id)
                self.log("Task {0} is not urgent !".format(id))
            else:
                urgentTask(self.db, self.cfg, id)
                self.log("Task {0} is urgent !".format(id))
        self.reload(self.archives)
            

    def reload(self, archives=False):
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
        cfg = self.cfg
        showinfo(cfg['program'], cfg['help'])


    def log(self, msg):
        self.ui.sb.log.configure(text=cfg['log'].format(msg))

cfg = getCfg()
run = app(cfg)
