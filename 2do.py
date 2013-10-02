#!/usr/bin/env python3
# -*- coding: utf-8 -*-
PROGRAM = "2do"
VERSION = "v0.1"
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
""".format(PROGRAM, VERSION)

# If system is Window :
SDBFILE = "Y:/todo.sqlite"
# If system is Unix :
#SDBFILE = "~/.todo.sqlite"

# Strings
cfg = dict()
cfg['program'] = PROGRAM
cfg['version'] = VERSION
cfg['file'] = SDBFILE
cfg['help'] = DOCHELP
cfg['new'] = "Nouvelle (n)"
cfg['edi'] = "Editer (e)"
cfg['del'] = "Archiver (A)"
cfg['done'] = "Statut (s)"
cfg['urgent'] = "Urgence (u)"
cfg['newtask'] = "Nouvelle tache…"
cfg['newtask2'] = "Entrez le nom de la nouvelle tache :"
cfg['taskdone'] = "{0} (terminée)"
cfg['tasknotdone'] = "{0}"
cfg['title'] = "{0} {1}"
cfg['loading'] = "Chargement taches…"
cfg['errordb'] = "Cannot open DB."
cfg['ready'] = "Application chargée…"
cfg['newtask'] = "Ajout nouvelle tache…"
cfg['newtaskok'] = "Tache {0} ajoutée."
cfg['errorsaving'] = "Erreur survenue lors de l'enregistrement."
cfg['taskdel'] = "Tache {0} archivée…"
cfg['taskdon'] = "Tache {0} : bascule statut…"
cfg['taskurgent'] = "Tache {0} : bascule urgence…"
cfg['log'] = "> {0}"
cfg['taskedit'] = "Tache {0} modifiée…"
cfg['editask'] = "Modifier la tache…"
cfg['editask2'] = "Nouveau nom pour la tache :"
# SQL
cfg['sqlCreate'] = "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, active INT, done INT, urgent INT);"
cfg['sqlAdd'] = "INSERT INTO tasks (task, active, done, urgent) VALUES (\"{0}\", 1, 0, 0);"
cfg['sqlArchive'] = "UPDATE tasks SET active = 0 WHERE id = {0};"
cfg['sqlDone'] = "UPDATE tasks SET done = 1 WHERE id = {0};"
cfg['sqlUnDone'] = "UPDATE tasks SET done = 0 WHERE id = {0};"
cfg['sqlGet'] = "SELECT id, task, active, done, urgent FROM tasks WHERE active = 1 ;"
cfg['sqlGet1'] = "SELECT id, task, active, done, urgent FROM tasks WHERE id = {0} ;"
cfg['sqlEdit'] = "UPDATE tasks SET task = \"{0}\" WHERE id = {1} ;"
cfg['sqlUrg'] = "UPDATE tasks SET urgent = 1 WHERE id = {0};"
cfg['sqlLow'] = "UPDATE tasks SET urgent = 0 WHERE id = {0};"


from sqlite3 import connect
from os.path import isfile
from os.path import expanduser
from tkinter import *
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
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
    id = db.execute(sql.format(task.replace("\"", "'"))).lastrowid
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


def urgentTask(db, cfg, id):
    sql = cfg['sqlUrg']
    db.execute(sql.format(id))
    db.commit()
    return(True)


def lowTask(db, cfg, id):
    sql = cfg['sqlLow']
    db.execute(sql.format(id))
    db.commit()
    return(True)


def editTask(db, cfg, id, new):
    sql = cfg['sqlEdit']
    id = db.execute(sql.format(new.replace("\"", "'"), id))
    db.commit()
    return(True)


def getTasks(db, cfg, archives = False):
    sql = cfg['sqlGet']
    r = db.execute(sql)
    return(r.fetchall())


def getTask(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql.format(id))
    for id, task, active, done, urgent in r.fetchall():
        return(task)


def isUrgent(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql.format(id))
    for id, task, active, done, urgent in r.fetchall():
        return(int(urgent))

        
def isDone(db, cfg, id):
    sql = cfg['sqlGet1']
    r = db.execute(sql.format(id))
    for id, task, active, done, urgent in r.fetchall():
        return(int(done))

        
def load(app):
    l = getTasks(app.db, app.cfg)
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
    ui.tb.new = Button(ui.tb, text=cfg['new'], command=app.new)
    ui.tb.new.grid(row=1, column=0, padx=2, pady=2)
    ui.tb.edi = Button(ui.tb, text=cfg['edi'], command=app.edi)
    ui.tb.edi.grid(row=1, column=1, padx=2, pady=2)
    ui.tb.arc = Button(ui.tb, text=cfg['del'], command=app.arc)
    ui.tb.arc.grid(row=1, column=5, padx=2, pady=2)
    ui.tb.don = Button(ui.tb, text=cfg['done'], command=app.don)
    ui.tb.don.grid(row=1, column=2, padx=2, pady=2)
    ui.tb.urg = Button(ui.tb, text=cfg['urgent'], command=app.urg)
    ui.tb.urg.grid(row=1, column=3, padx=2, pady=2)
    # listbox
    ui.lb = Listbox(ui, font=('Consolas', 10))
    ui.lb.pack(expand=True, fill='both')
    # statusbar
    ui.sb = Frame(ui)
    ui.sb.pack(anchor='sw')
    ui.sb.log = Label(ui.sb)
    ui.sb.log.pack(expand=True, fill='both')
    ui.bind("<n>", app.evtNew)
    ui.bind("<e>", app.evtEdi)
    ui.bind("<A>", app.evtArc)
    ui.bind("<s>", app.evtDon)
    ui.bind("<u>", app.evtUrg)
    ui.bind("<h>", app.evtHel)
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
            self.ui.lb.selection_set(END)
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
            if isDone(self.db, self.cfg, id):
                undoneTask(self.db, self.cfg, id)
            else:
                doneTask(self.db, self.cfg, id)
            self.log(cfg['taskdon'].format(id))
        self.reload()
            
    
    def evtUrg(self, event):
        self.urg()


    def urg(self):
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[task]
            if isUrgent(self.db, self.cfg, id):
                lowTask(self.db, self.cfg, id)
            else:
                urgentTask(self.db, self.cfg, id)
            self.log(cfg['taskurgent'].format(id))
        self.reload()
            

    def reload(self):
        self.ui.lb.delete(0, END)
        self.tasks = dict()
        load(self)
        self.ui.lb.focus_set()
        self.ui.lb.selection_set(END)
        return(True)

    def evtHel(self, evt):
        cfg = self.cfg
        showinfo(cfg['program'], cfg['help'])

    def log(self, msg):
        self.ui.sb.log.configure(text=cfg['log'].format(msg))


run = app(cfg)
