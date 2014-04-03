#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# PARAM
#---------------------------------------------------------------------

# database file
BASE = "TestBase"
PATH = "~/"
SDBFILE = "{0}/2do_{1}.db".format(PATH, BASE)

# milestones
F1 = "-dev"
F2 = "-alfa"
F3 = "-beta"
F4 = "-rc"
F5 = "-next"

# teams
ANA = "ANA"
DEV = "DEV"
Q_R = "Q/R"
RE7 = "RE7"
ARB = "ARB"


#---------------------------------------------------------------------
# PROGRAM
#---------------------------------------------------------------------

PROGRAM = "2do {}".format(BASE)
VERSION = "v2.0-beta"
DOCHELP = """
{0} {1}
--
This software is a simple todo list manager.
It's written in Python using Tkinter and Sqlite.
--
Author: Julien Pecqueur
Home: http://github.com/jpec/2do
Email: jpec@julienpecqueur.net
License: GPL
--
Keyboard shortcuts on main window:
 <n> New task
 <c> Copy task
 <p> Paste task
 <e> Edit task
 <s> toggle Status flag
 <u> toggle Urgent flag
 <r> Delete task
 <t> view Trash
 <f> Filter box
 <h> Help
 <F5> Reload data (refresh)
 <F11> Open console
 

Keyboard shortcuts in trash:
 <t> view Tasks
 <d> restore task

Keyboard shortcuts in filter:
 <Escape> close filter
 <Return> apply filter

""".format(PROGRAM, VERSION)

#---------------------------------------------------------------------
# SOURCE CODE
#---------------------------------------------------------------------

from sqlite3 import connect
from sqlite3 import Error as SqlError
from os import name as uname
from os.path import isfile
from os.path import expanduser
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from tkinter.messagebox import showerror
from tkinter.messagebox import askyesno
from tkinter.ttk import Button, Frame, Entry


class console(object):
    
    "Class for console"
    
    def __init__(self, db, master):
        "Start the console"
        self.db = db
        self.master = master
        self.ui = self.draw_ui()
        self.ui.term.insert(END ,"Type your request and press <Enter>.\n")
        self.ui.mainloop()
    
    def execute(self, event=None):
        "Execute request"
        sql = self.ui.cmd.get()
        self.ui.cmd.configure(state = 'disabled')
        res = False
        if sql:
            try:
                sql = sql.strip()
                cur = self.db.execute(sql)
                self.ui.term.insert(END ,">>> {0}\n".format(sql))
                self.db.commit()
                if sql.lstrip().upper().startswith("SELECT"):
                    res = cur.fetchall()
            except SqlError as e:
                msg = "{0}".format(e.args[0])
                self.ui.term.insert(END ,"{0}\n".format(msg))
        self.ui.term.see(END)
        if res:
            for l in res:
                l=str(l)
                self.ui.term.insert(END ,l+"\n")
                self.ui.term.see(END)
        self.ui.cmd.configure(state = 'normal')
        self.ui.cmd.focus()
        

    def draw_ui(self):
        "Draw the UI"
        ui = Tk()
        ui.title("console")
        # Console
        ui.term = ScrolledText(ui)
        ui.term.pack(fill=BOTH, expand=1)
        # Barre commande
        ui.cmd = Entry(ui)
        ui.cmd.pack(side=LEFT, fill=BOTH, expand=1)
        ui.bind('<Return>', self.execute)
        ui.cmd.focus()
        return(ui)


class app(object):

    "Class app for 2do"

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
        self.filter = False
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
            self.ui.lb.see(END)
            # loop
            self.ui.mainloop()
            # close database
            self.db.close()
        else:
            print("Database error !")


    def evtRef(self, event):
        "Event Refresh - Reload"
        self.log("Reloading data…")
        self.reload(self.archives)
        self.log("Data reloaded!")


    def evtCon(self, event):
        "Event - open console"
        console(self.db, self.ui)


    def evtVis(self, event):
        "Event toggle tasks/archive mode"
        self.vis()
        

    def vis(self):
        "Toggle tasks/archives mode"
        if not self.archives:
            # tasks mode
            self.reload(True)
            self.ui.tb.vis.configure(text="Tasks")
            self.ui.tb.arc.configure(text="Restore")
            self.ui.tb.new.configure(state=DISABLED)
            self.ui.tb.cop.configure(state=DISABLED)
            self.ui.tb.pas.configure(state=DISABLED)
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.don.configure(state=DISABLED)
            self.ui.tb.urg.configure(state=DISABLED)
            self.ui.tg.tf1.configure(state=DISABLED)
            self.ui.tg.tf2.configure(state=DISABLED)
            self.ui.tg.tf3.configure(state=DISABLED)
            self.ui.tg.tf4.configure(state=DISABLED)
            self.ui.tg.tf5.configure(state=DISABLED)
            self.ui.tg.tANA.configure(state=DISABLED)
            self.ui.tg.tDEV.configure(state=DISABLED)
            self.ui.tg.tQ_R.configure(state=DISABLED)
            self.ui.tg.tRE7.configure(state=DISABLED)
            self.ui.tg.tARB.configure(state=DISABLED)
            self.log("Displaying the archives bin…")
        else:
            # archives mode
            self.reload(False)
            self.ui.tb.vis.configure(text="Trash")
            self.ui.tb.arc.configure(text="Remove")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.cop.configure(state=NORMAL)
            self.ui.tb.pas.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.don.configure(state=NORMAL)
            self.ui.tb.urg.configure(state=NORMAL)
            self.ui.tg.tf1.configure(state=NORMAL)
            self.ui.tg.tf2.configure(state=NORMAL)
            self.ui.tg.tf3.configure(state=NORMAL)
            self.ui.tg.tf4.configure(state=NORMAL)
            self.ui.tg.tf5.configure(state=NORMAL)
            self.ui.tg.tANA.configure(state=NORMAL)
            self.ui.tg.tDEV.configure(state=NORMAL)
            self.ui.tg.tQ_R.configure(state=NORMAL)
            self.ui.tg.tRE7.configure(state=NORMAL)
            self.ui.tg.tARB.configure(state=NORMAL)
            self.log("Displaying the tasks…")


    def evtDis(self, event):
        "Event toggle display filter box"
        self.ui.fb.src.focus()
            

    def evtMas(self, event):
        "Event mask filter box"
        self.ui.lb.focus()
        
    
    def evtPas(self, event):
        "Event paste as new"
        if not self.archives:
            self.pas()

    
    def pas(self):
        "Paste as new task"
        task = ""
        task = self.ui.clipboard_get()
        if task != "":
            for elt in task.split("\n"):
                if len(elt) > 3:
                    self.new(elt)


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
            id = self.addTask(task, ANA)
            if id:
                self.log("Task {0} added !".format(id))
                self.reload(self.archives, task=id)
            else:
                self.log("Cannot save the task !")


    def evtCop(self, event):
        "Event copy task"
        self.cop()


    def cop(self):
        "Copy task"
        tasks = self.ui.lb.curselection()
        self.ui.clipboard_clear()
        for task in tasks:
            id = self.tasks[str(task)]
            old = self.getTaskInfos(id)
            self.ui.clipboard_append(old['task'])
            self.log("Tesk {0} copied.".format(id))


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
            new = askstring("Edit task ?", "Enter the new task :",
                            initialvalue=old)
            if new:
                self.editTask(id, new)
                self.log("Task {0} edited !".format(id))
        self.reload(self.archives, task=id)


    def evtF1(self, event):
        "Event tag milestone 1"
        if not self.archives:
            self.tag('milestone', F1)


    def evtF2(self, event):
        "Event tag milestone 2"
        if not self.archives:
            self.tag('milestone', F2)


    def evtF3(self, event):
        "Event tag milestone 3"
        if not self.archives:
            self.tag('milestone', F3)


    def evtF4(self, event):
        "Event tag milestone 4"
        if not self.archives:
            self.tag('milestone', F4)


    def evtF5(self, event):
        "Event tag milestone 5"
        if not self.archives:
            self.tag('milestone', F5)


    def evtANA(self, event):
        "Event tag team 1"
        if not self.archives:
            self.tag('team', ANA)


    def evtDEV(self, event):
        "Event tag team 2"
        if not self.archives:
            self.tag('team', DEV)


    def evtQ_R(self, event):
        "Event tag team 3"
        if not self.archives:
            self.tag('team', Q_R)


    def evtRE7(self, event):
        "Event tag team 4"
        if not self.archives:
            self.tag('team', RE7)


    def evtARB(self, event):
        "Event tag team 5"
        if not self.archives:
            self.tag('team', ARB)

        
    def tag(self, tag, value):
        "Tag milestone/team"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            if self.tagTask(id, tag, value):
                self.log("Task {0} tagged for {1} !".format(id, value))
            else:
                self.log("Cannot tag {0} for {1} !".format(id, value))
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
               askyesno("Archive ?",
                        "Do yo want to archive this task ?\n\"{0}\"".format(lb)):
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
        self.ui.lb.see(selection)
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
        self.reload(self.archives, END, None)
        self.log("Only tasks matching '{0}' are displayed !".format(mask))


    def evtHel(self, evt):
        "Event display help"
        t = "{0} {1}".format(self.program, self.version)
        showinfo(t, self.dochelp)


    def log(self, msg):
        "Display log in status bar"
        self.ui.sb.log.configure(text="{0}".format(msg))


    def isNewDb(self, dbfile):
        "Return True if the database doesn't exist"
        if isfile(dbfile):
            return(False)
        else:
            return(True)


    def openDb(self):
        "Open the database"
        path = expanduser(SDBFILE)
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
        sql = "CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        sql += "task TEXT, milestone TEXT, active INT, done INT, "
        sql += "urgent INT, team TEXT);"
        db.execute(sql)
        db.commit()
        self.db = db
        return(True)


    def addTask(self, task, team):
        "Add the task in the database"
        sql = "INSERT INTO tasks (task, milestone, team, active, done, urgent) "
        sql += "VALUES (?, '', ?, 1, 0, 0);"
        id = self.db.execute(sql, (task, team)).lastrowid
        self.db.commit()
        return(id)


    def tagTask(self, id, tag, value):
        "Set the milestone/team for the task"
        if tag == "milestone":
            sql = "UPDATE tasks SET milestone = ? WHERE id = ? ;"
        elif tag == "team":
            sql = "UPDATE tasks SET team = ? WHERE id = ? ;"
        else:
            return(False)
        self.db.execute(sql, (value, id))
        self.db.commit()
        return(True)
    

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
            sql = "SELECT id, task, milestone, active, done, urgent, team "
            sql += "FROM tasks "
            sql += "WHERE active = ? AND task LIKE ?;"
            r = self.db.execute(sql, (0, mask))
        else:
            sql = "SELECT id, task, milestone, active, done, urgent, team "
            sql += "FROM tasks "
            sql += "WHERE active = ? "
            sql += "AND ( task LIKE ? OR team LIKE ? OR milestone LIKE ? ) "
            sql += "ORDER BY milestone, task, id;"
            r = self.db.execute(sql, (1, mask, mask, mask))
        return(r.fetchall())


    def getTaskInfos(self, id):
        "Get task's infos"
        sql = "SELECT id, task, milestone, active, done, urgent "
        sql += "FROM tasks "
        sql += "WHERE id = ? ;"
        r = self.db.execute(sql, (id, ))
        t = dict()
        for id, task, milestone, active, done, urgent in r.fetchall():
            print(id, task, milestone, active,done, urgent)
            t['id'] = id
            t['task'] = task
            t['milestone'] = milestone
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
        for id, task, milestone, active, done, urgent, team in l:
            if archives:
                lbl = "[{0}] {1}".format(id, task)
            else:
                lbl = "[{0}] {1} ({2})".format(milestone, task, team)
            self.ui.lb.insert(i, lbl)
            if int(done) > 0:
                self.ui.lb.itemconfig(i, fg='grey', bg='white')
            elif int(urgent) > 0:
                self.ui.lb.itemconfig(i, fg='white', bg='red')
            elif team == ANA:
                self.ui.lb.itemconfig(i, fg='red', bg='white')
            elif team == RE7:
                self.ui.lb.itemconfig(i, fg='darkgreen', bg='white')
            elif team == DEV:
                self.ui.lb.itemconfig(i, fg='blue', bg='white')
            elif team == Q_R:
                self.ui.lb.itemconfig(i, fg='orange', bg='white')
            elif team == ARB:
                self.ui.lb.itemconfig(i, fg='black', bg='white')
            else:
                self.ui.lb.itemconfig(i, fg='black', bg='white')
            self.tasks[str(i)] = id
            self.sksat[id] = str(i)
            i = i+1
        return(True)

    
    def getButtonSize(self):
        "Return the button size"
        if 'nt' == uname:
            return(7)
        else:
            return(6)


    def drawUi(self):
        "Draw the UI"
        ui = Tk()
        ui.title("{0} {1}".format(self.program, self.version))
        # toolbar
        ui.tb = Frame(ui)
        ui.tb.pack(fill=X)
        # tools
        wb = self.getButtonSize()
        ui.tb.new = Button(ui.tb, text="New", width=wb, command=self.new)
        ui.tb.new.pack(side=LEFT, padx=2, pady=2)
        ui.tb.cop = Button(ui.tb, text="Copy", width=wb, command=self.cop)
        ui.tb.cop.pack(side=LEFT, padx=2, pady=2)
        ui.tb.pas = Button(ui.tb, text="Paste", width=wb, command=self.pas)
        ui.tb.pas.pack(side=LEFT, padx=2, pady=2)
        ui.tb.edi = Button(ui.tb, text="Edit", width=wb, command=self.edi)
        ui.tb.edi.pack(side=LEFT, padx=2, pady=2)
        ui.tb.don = Button(ui.tb, text="Status", width=wb, command=self.don)
        ui.tb.don.pack(side=LEFT, padx=2, pady=2)
        ui.tb.urg = Button(ui.tb, text="Urgent", width=wb, command=self.urg)
        ui.tb.urg.pack(side=LEFT, padx=2, pady=2)
        ui.tb.arc = Button(ui.tb, text="Remove", width=wb, command=self.arc)
        ui.tb.arc.pack(side=LEFT, padx=2, pady=2)
        ui.tb.ref = Button(ui.tb, text="Refresh", width=wb, command=lambda:self.evtRef(None))
        ui.tb.ref.pack(side=LEFT, padx=2, pady=2)
        ui.tb.vis = Button(ui.tb, text="Trash", width=wb, command=self.vis)
        ui.tb.vis.pack(side=RIGHT, padx=2, pady=2)
        ui.tb.cmd = Button(ui.tb, text="Console", width=wb, command=lambda:self.evtCon(None))
        ui.tb.cmd.pack(side=RIGHT, padx=2, pady=2)
        # tagbar
        ui.tg = Frame(ui)
        ui.tg.pack(fill=X)
        ui.tg.tf1 = Button(ui.tg, text=F1, width=wb, command=lambda:self.evtF1(None))
        ui.tg.tf1.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf2 = Button(ui.tg, text=F2, width=wb, command=lambda:self.evtF2(None))
        ui.tg.tf2.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf3 = Button(ui.tg, text=F3, width=wb, command=lambda:self.evtF3(None))
        ui.tg.tf3.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf4 = Button(ui.tg, text=F4, width=wb, command=lambda:self.evtF4(None))
        ui.tg.tf4.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf5 = Button(ui.tg, text=F5, width=wb, command=lambda:self.evtF5(None))
        ui.tg.tf5.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tANA = Button(ui.tg, text=ANA, width=wb, command=lambda:self.evtANA(None))
        ui.tg.tANA.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tDEV = Button(ui.tg, text=DEV, width=wb, command=lambda:self.evtDEV(None))
        ui.tg.tDEV.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tQ_R = Button(ui.tg, text=Q_R, width=wb, command=lambda:self.evtQ_R(None))
        ui.tg.tQ_R.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tRE7 = Button(ui.tg, text=RE7, width=wb, command=lambda:self.evtRE7(None))
        ui.tg.tRE7.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tARB = Button(ui.tg, text=ARB, width=wb, command=lambda:self.evtARB(None))
        ui.tg.tARB.pack(side=LEFT, padx=2, pady=2)
        # filterbar
        ui.fb = Frame(ui)
        ui.fb.pack(fill=X)
        self.mask = StringVar()
        self.mask.set("%")
        ui.fb.src = Entry(ui.fb, textvariable=self.mask)
        ui.fb.config(height=0)
        ui.fb.src.pack(side=LEFT,expand=True, fill=X, padx=2, pady=2)
        self.filter = True
        # listbox
        ui.cf = Frame(ui)
        ui.cf.pack(fill=BOTH, expand=True)
        ui.sl = Scrollbar(ui.cf, orient=VERTICAL)
        ui.lb = Listbox(ui.cf, selectmode=EXTENDED, yscrollcommand=ui.sl.set)
        ui.sl.config(command=ui.lb.yview)
        ui.sl.pack(side=RIGHT, fill=Y)
        ui.lb.pack(side=LEFT, expand=True, fill='both')
        # statusbar
        ui.sb = Frame(ui)
        ui.sb.pack(fill=X)
        ui.sb.log = Label(ui.sb)
        ui.sb.log.pack(expand=True, fill='both', padx=2, pady=2)
        ui.bind("<F5>", self.evtRef)
        ui.bind("<F11>", self.evtCon)
        ui.lb.bind("<n>", self.evtNew)
        ui.lb.bind("<c>", self.evtCop)
        ui.lb.bind("<p>", self.evtPas)
        ui.lb.bind("<e>", self.evtEdi)
        ui.lb.bind("<r>", self.evtArc)
        ui.lb.bind("<t>", self.evtVis)
        ui.lb.bind("<s>", self.evtDon)
        ui.lb.bind("<u>", self.evtUrg)
        ui.lb.bind("<h>", self.evtHel)
        ui.lb.bind("<f>", self.evtDis)
        ui.fb.src.bind("<Return>", self.evtSrc)
        ui.fb.src.bind("<Escape>", self.evtMas)
        ui.lb.bind("<Double-Button-1>", self.evtEdi)
        ui.lb.bind("<Button-2>", self.evtUrg)
        ui.lb.bind("<Double-Button-3>", self.evtDon)
        return(ui)


if __name__ == '__main__':
    # start the program
    run = app(PROGRAM, VERSION, DOCHELP)
