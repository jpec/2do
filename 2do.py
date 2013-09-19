#!/usr/bin/env python3
# -*- coding: utf-8 -*-
PROGRAM = "2do"
VERSION = "v0.1"

# Strings
cfg = dict()
cfg['program'] = PROGRAM
cfg['version'] = VERSION
cfg['file'] = "~/todo.sqlite"
cfg['new'] = "New (n)"
cfg['edi'] = "Edit (e)"
cfg['del'] = "Archive (A)"
cfg['done'] = "Done (d)"
cfg['undone'] = "Undone (u)"
cfg['urgent'] = "Urgente"
cfg['newtask'] = "New task…"
cfg['newtask2'] = "Enter the name of the new task :"
cfg['taskdone'] = "{0} (DONE)"
cfg['tasknotdone'] = "{0}"
cfg['title'] = "{0} {1}"
cfg['loading'] = "Loading task…"
cfg['errordb'] = "Cannot open DB."
cfg['ready'] = "Loaded…"
cfg['newtask'] = "Adding new task…"
cfg['newtaskok'] = "Task {0} added."
cfg['errorsaving'] = "Saving return error."
cfg['taskdel'] = "Task {0} archived."
cfg['taskdon'] = "Tache {0} done."
cfg['taskund'] = "Tache {0} undone."
cfg['log'] = "> {0}"
cfg['taskedit'] = "Task {0} edited."
cfg['editask'] = "Editing task…"
cfg['editask2'] = "Enter the new name of the task :"
# SQL
cfg['sqlCreate'] = "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, active INT, done INT);"
cfg['sqlAdd'] = "INSERT INTO tasks (task, active, done) VALUES ('{0}', 1, 0);"
cfg['sqlArchive'] = "UPDATE tasks SET active = 0 WHERE id = {0};"
cfg['sqlDone'] = "UPDATE tasks SET done = 1 WHERE id = {0};"
cfg['sqlUnDone'] = "UPDATE tasks SET done = 0 WHERE id = {0};"
cfg['sqlGet'] = "SELECT id, task, active, done FROM tasks WHERE active = 1 ;"
cfg['sqlGet1'] = "SELECT id, task, active, done FROM tasks WHERE id = {0} ;"
cfg['sqlEdit'] = "UPDATE tasks SET task = '{0}' WHERE id = {1} ;"

from sqlite3 import connect
from os.path import isfile
from os.path import expanduser
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.ttk import Button, Frame


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
    id = db.execute(sql.format(task)).lastrowid
    db.commit()
    return(id)

def archiveTask(db, cfg, id):
    sql = cfg['sqlArchive']
    db.execute(sql.format(id))
    db.commit()
    return(True)

def doneTask(db, cfg, id):
    sql = cfg['sqlDone']
    db.execute(sql.format(id))
    db.commit()
    return(True)

def undoneTask(db, cfg, id):
    sql = cfg['sqlUnDone']
    db.execute(sql.format(id))
    db.commit()
    return(True)

def editTask(db, cfg, id, new):
    sql = cfg['sqlEdit']
    db.execute(sql.format(new, id))
    db.commit()
    return(True)

def getTasks(db, cfg, archives = False):
    sql = cfg['sqlGet']
    r = db.execute(sql)
    return(r.fetchall())

def getTask(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql.format(id))
    for id, task, active, done in r.fetchall():
        return(task)

def load(app):
    l = getTasks(app.db, app.cfg)
    i = 0
    for id, task, active, done in l:
        if int(done) > 0:
            lbl = cfg['taskdone'].format(task)
        else:
            lbl = cfg['tasknotdone'].format(task)
        app.ui.lb.insert(id, lbl)
        app.tasks[str(i)] = id
        i = i+1
    return(True)

def drawUi(app, cfg):
    ui = Tk()
    ui.title(cfg['title'].format(cfg['program'], cfg['version']))
    # toolbar
    ui.tb = Frame(ui)
    ui.tb.pack(anchor='nw')
    # tools
    ui.tb.new = Button(ui.tb, text=cfg['new'], width=12, command=app.new)
    ui.tb.new.grid(row=1, column=0, padx=2, pady=2)
    ui.tb.edi = Button(ui.tb, text=cfg['edi'], width=12, command=app.edi)
    ui.tb.edi.grid(row=1, column=1, padx=2, pady=2)
    ui.tb.arc = Button(ui.tb, text=cfg['del'], width=12, command=app.arc)
    ui.tb.arc.grid(row=1, column=4, padx=2, pady=2)
    ui.tb.don = Button(ui.tb, text=cfg['done'], width=12, command=app.don)
    ui.tb.don.grid(row=1, column=2, padx=2, pady=2)
    ui.tb.und = Button(ui.tb, text=cfg['undone'], width=12, command=app.und)
    ui.tb.und.grid(row=1, column=3, padx=2, pady=2)
    # listbox)
    ui.lb = Listbox(ui)
    ui.lb.pack(expand=True, fill='both')
    # statusbar
    ui.sb = Frame(ui)
    ui.sb.pack(anchor='sw')
    ui.sb.log = Label(ui.sb)
    ui.sb.log.pack(expand=True, fill='both')
    ui.bind("<n>", app.evtNew)
    ui.bind("<e>", app.evtEdi)
    ui.bind("<A>", app.evtArc)
    ui.bind("<d>", app.evtDon)
    ui.bind("<u>", app.evtUnd)
    return(ui)

class app(object):

    def __init__(self, cfg):
        # open / create db
        self.cfg = cfg
        self.db = openDb(cfg)
        self.task = None
        self.tasks = dict()
        if self.db:
            # launch app
            self.ui = drawUi(self, cfg)
            self.log(cfg['loading'])
            load(self)
            self.log(cfg['ready'])
            self.ui.lb.focus_set()
            self.ui.mainloop()
            self.db.close()
        else:
            print(cfg['errordb'])

    def evtNew(self, event):
        self.new()

    def new(self):
        self.log(cfg['newtask'])
        task = askstring(cfg['newtask'], cfg['newtask2'])
        if task:
            id = addTask(self.db, self.cfg, task)
            if id:
                self.log(cfg['newtaskok'].format(id))
                self.reload()
            else:
                self.log(cfg['errorsaving'])
                
    def evtEdi(self, event):
        self.edi()
        
    def edi(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            old = getTask(self.db, self.cfg, id)
            self.log(cfg['editask'])
            new = askstring(cfg['editask'], cfg['editask2'], initialvalue=old)
            if new:
                editTask(self.db, self.cfg, id, new)
                self.log(cfg['taskedit'].format(id))
                self.reload()

    def evtArc(self, event):
        self.arc()

    def arc(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            archiveTask(self.db, self.cfg, id)
            self.log(cfg['taskdel'].format(id))
            self.reload()

    def evtDon(self, event):
        self.don()

    def don(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            doneTask(self.db, self.cfg, id)
            self.log(cfg['taskdon'].format(id))
            self.reload()

    def evtUnd(self, event):
        self.und()

    def und(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            undoneTask(self.db, self.cfg, id)
            self.log(cfg['taskund'].format(id))
            self.reload()
        
    def reload(self):
        self.ui.lb.delete(0, END)
        self.tasks = dict()
        load(self)
        self.ui.lb.focus_set()
        return(True)

    def log(self, msg):
        self.ui.sb.log.configure(text=cfg['log'].format(msg))


run = app(cfg)
