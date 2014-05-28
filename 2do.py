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
 <h> Help
 <F5> Reload data (refresh)
 <F11> Open console
 

Keyboard shortcuts in trash:
 <t> view Tasks
 <d> restore task

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


class to_do_app(object):

    "Class for 2do application"

    def __init__(self, program, version, dochelp):
        "Initialize the class"
        # open/create the database
        self.db = self.db_open_connection()
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
            self.ui = self.ui_draw_window()
            self.ui_display_log("Loading data…")
            # load tasks
            try:
                self.ui_load_tasks_list(self.archives)
                self.ui_display_log("Data loaded !")
            except ValueError:
                self.ui_display_log("Cannot load data !")
                self.cb_open_console(None)
            self.ui.lb.focus_set()
            self.ui_display_log("Press <h> to display help…")
            self.ui.lb.selection_set(END)
            self.ui.lb.see(END)
            # loop
            self.ui.mainloop()
            # close database
            self.db.close()
        else:
            print("Database error !")


    ### DATABASE MANAGEMENT FUNCTIONS ###############################

    def db_is_new(self, dbfile):
        "Return True if the database doesn't exist"
        if isfile(dbfile):
            return(False)
        else:
            return(True)


    def db_open_connection(self):
        "Open the database if exists, else create a new database"
        path = expanduser(SDBFILE)
        print(path)
        new = self.db_is_new(path)
        db = connect(path)
        if not new:
            return(db)
        elif new and self.db_create_tables(db):
            return(db)
        else:
            return(None)


    def db_create_tables(self, db):
        "Create the database's tables"
        sql = "CREATE TABLE tasks "
        sql += "( "
        sql += "    id INTEGER PRIMARY KEY AUTOINCREMENT, "
        sql += "    task TEXT, "
        sql += "    milestone TEXT, "
        sql += "    active INT, "
        sql += "    done INT, "
        sql += "    urgent INT, "
        sql += "    team TEXT, "
        sql += "    project TEXT "
        sql += ");"
        db.execute(sql)
        sql = "CREATE TABLE projects "
        sql += "( "
        sql += "    id INTEGER PRIMARY KEY AUTOINCREMENT, "
        sql += "    project TEXT "
        sql += ") ;"
        db.execute(sql)
        db.commit()
        self.db = db
        return(True)


    def db_get_projects_UNUSED(self, mask="%"):
        "Get the list of projects"
        sql = "SELECT project FROM projects WHERE project LIKE ? ;"
        r = self.db.execute(sql, (mask, ))
        return(r.fetchall())


    def db_set_project(self, id, project):
        "Set the project value for a task"
        sql = "UPDATE tasks SET project = ? where id = ? ;"
        self.db.execute(sql, (project, id))
        self.db.commit()
        return(project)


    def db_create_task(self, task, team):
        "Add the task in the database"
        sql = "INSERT INTO tasks (task, milestone, team, active, done, urgent) "
        sql += "VALUES (?, '', ?, 1, 0, 0);"
        id = self.db.execute(sql, (task, team)).lastrowid
        self.db.commit()
        return(id)


    def db_set_task_property(self, id, tag, value):
        "Set task property"
        if tag == "milestone":
            sql = "UPDATE tasks SET milestone = ? WHERE id = ? ;"
        elif tag == "team":
            sql = "UPDATE tasks SET team = ? WHERE id = ? ;"
        elif tag == "active":
            sql = "UPDATE tasks SET active = ? WHERE id = ? ;"
        elif tag == "done":
            sql = "UPDATE tasks SET done = ? WHERE id = ? ;"
        elif tag == "urgent":
            sql = "UPDATE tasks SET urgent = ? WHERE id = ? ;"
        elif tag == "task":
            sql = "UPDATE tasks SET task = ? WHERE id = ? ;"
        elif tag == "project":
            sql = "UPDATE tasks SET project = ? WHERE id = ? ;"
        else:
            return(False)
        self.db.execute(sql, (value, id))
        self.db.commit()
        return(True)
    

    def db_set_task_active_DEPRECATED(self, id, value):
        return(self.db_set_task_property(id, "active", value))


    def db_set_task_done_DEPRECATED(self, id, value):
        return(self.db_set_task_property(id, "done", value))


    def db_set_task_urgent_DEPRECATED(self, id, value):
        return(self.db_set_task_property(id, "urgent", value))


    def db_set_task_DEPRECATED(self, id, value):
        return(self.db_set_task_property(id, "task", value))


    def db_get_tasks_list(self, archives, mask="%"):
        "Get the tasks list"
        sql = "SELECT "
        sql += "    id, "
        sql += "    task, "
        sql += "    milestone, "
        sql += "    active, "
        sql += "    done, "
        sql += "    urgent, "
        sql += "    team, "
        sql += "    project "
        sql += "FROM tasks "
        sql += "WHERE "
        sql += "    active = ? "
        sql += "AND ( "
        sql += "    task LIKE ? "
        sql += "    OR team LIKE ? "
        sql += "    OR milestone LIKE ? "
        sql += "    OR project LIKE ? "
        sql += ") "
        sql += "ORDER BY milestone, task, id "
        sql += ";"
        if archives:
            r = self.db.execute(sql, (0, mask, mask, mask, mask))
        else:
            r = self.db.execute(sql, (1, mask, mask, mask, mask))
        return(r.fetchall())


    def task_get_task_details(self, id):
        "Get task's details"
        sql = "SELECT "
        sql += "    id, "
        sql += "    task, "
        sql += "    milestone, "
        sql += "    active, "
        sql += "    done, "
        sql += "    urgent, "
        sql += "    project "
        sql += "FROM tasks "
        sql += "WHERE "
        sql += "    id = ? "
        sql += ";"
        r = self.db.execute(sql, (id, ))
        t = dict()
        for id, task, milestone, active, done, urgent, project in r.fetchall():
            print(id, task, milestone, active,done, urgent, project)
            t['id'] = id
            t['task'] = task
            t['milestone'] = milestone
            t['active'] = int(active)
            t['done'] = int(done)
            t['urgent'] = int(urgent)
            t['project'] = project
            return(t)


    ### CALLBACKS ###################################################

    def cb_refresh(self, event=None):
        "Event Refresh - Reload"
        self.ui_display_log("Reloading data…")
        self.ui_reload_tasks_list(self.archives)
        self.ui_display_log("Data reloaded!")


    def cb_open_console(self, event=None):
        "Event open console"
        console(self.db, self.ui)


    def cb_toggle_display(self, event=None):
        "Event toggle tasks/archive mode"
        if not self.archives:
            # tasks mode
            self.ui_reload_tasks_list(True)
            self.ui.tb.vis.configure(text="Tasks")
            self.ui.tb.arc.configure(text="Restore")
            self.ui.tb.new.configure(state=DISABLED)
            self.ui.tb.cop.configure(state=DISABLED)
            self.ui.tb.pas.configure(state=DISABLED)
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.pro.configure(state=DISABLED)
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
            self.ui_display_log("Displaying the archives bin…")
        else:
            # archives mode
            self.ui_reload_tasks_list(False)
            self.ui.tb.vis.configure(text="Trash")
            self.ui.tb.arc.configure(text="Remove")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.cop.configure(state=NORMAL)
            self.ui.tb.pas.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.pro.configure(state=NORMAL)
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
            self.ui_display_log("Displaying the tasks…")


    def cb_paste_task(self, event=None):
        "Event paste as new task"
        if not self.archives:
            task = ""
            task = self.ui.clipboard_get()
            if task != "":
                for elt in task.split("\n"):
                    if len(elt) > 3:
                        self.task_create(elt)


    def cb_new_task(self, event=None):
        "Event create new task"
        if not self.archives:
            self.task_create()


    def cb_copy_task(self, event=None):
        "Event copy task"
        tasks = self.ui.lb.curselection()
        self.ui.clipboard_clear()
        for task in tasks:
            id = self.tasks[str(task)]
            # DEPRECATED :
            old = self.task_get_task_details(id)
            self.ui.clipboard_append(old['task'])
            self.ui_display_log("Tesk {0} copied.".format(id))


    def cb_edit_task(self, event=None):
        "Event edit task(s)"
        if not self.archives:
            ids = self.ui.lb.curselection()
            for task in ids:
                id = self.tasks[str(task)]
                old = self.task_get_task(id)
                self.ui_display_log("Editing task {0}…".format(id))
                new = askstring("Editing task…", "Enter the new task :\nPlease use the following format :\n 'N° - Details for the task'",
                                initialvalue=old)
                if new:
                    self.db_set_task_DEPRECATED(id, new)
                    self.ui_display_log("Task {0} edited !".format(id))
            self.ui_reload_tasks_list(self.archives, task=id)


    def cb_set_task_milestone1(self, event=None):
        "Event tag milestone 1"
        if not self.archives:
            self.task_set_property('milestone', F1)


    def cb_set_task_milestone2(self, event=None):
        "Event tag milestone 2"
        if not self.archives:
            self.task_set_property('milestone', F2)


    def cb_set_task_milestone3(self, event=None):
        "Event tag milestone 3"
        if not self.archives:
            self.task_set_property('milestone', F3)


    def cb_set_task_milestone4(self, event=None):
        "Event tag milestone 4"
        if not self.archives:
            self.task_set_property('milestone', F4)


    def cb_set_task_milestone5(self, event=None):
        "Event tag milestone 5"
        if not self.archives:
            self.task_set_property('milestone', F5)


    def cb_set_task_team1(self, event=None):
        "Event tag team 1"
        if not self.archives:
            self.task_set_property('team', ANA)


    def cb_set_task_team2(self, event=None):
        "Event tag team 2"
        if not self.archives:
            self.task_set_property('team', DEV)


    def cb_set_task_team3(self, event=None):
        "Event tag team 3"
        if not self.archives:
            self.task_set_property('team', Q_R)


    def cb_set_task_team4(self, event=None):
        "Event tag team 4"
        if not self.archives:
            self.task_set_property('team', RE7)


    def cb_set_task_team5(self, event=None):
        "Event tag team 5"
        if not self.archives:
            self.task_set_property('team', ARB)


    def cb_set_task_project(self, event=None):
        "Event set project"
        ids = self.ui.lb.curselection()
        first = None
        for task in ids:
            id = self.tasks[str(task)]
            if not first:
                first = id
            self.ui_display_log("Setting project for task {0}…".format(id))
            old = self.task_get_project(id)
            new = None
            while not new:
                new = askstring("Editing task {0}".format(id), "Enter the new project :", initialvalue=old)
            if new and self.db_set_project(id, new):
                self.ui_display_log("Task {0} is attached to the {1} project !".format(id, new))
            else:
                self.ui_display_log("Cannot attach task {0} to the {1} project !".format(id, new))
        self.ui_reload_tasks_list(self.archives, task=first)

        
    def cb_toggle_task_archive(self, event=None):
        "Event toggle archive flag"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            lb = self.task_get_task(id)
            if self.task_is_archived(id) and \
               askyesno("Archive ?", "Do yo want to archive this task ?\n\"{0}\"".format(lb)):
                self.db_set_task_active_DEPRECATED(id, 0)
                self.ui_display_log("Task {0} archived !".format(id))
            else:
                self.db_set_task_active_DEPRECATED(id, 1)
                self.ui_display_log("Task {0} un-archived !".format(id))
        self.ui_reload_tasks_list(self.archives)


    def cb_toggle_task_done(self, event=None):
        "Event toggle done flag"
        if not self.archives:
            ids = self.ui.lb.curselection()
            for task in ids:
                id = self.tasks[str(task)]
                if self.task_is_done(id):
                    self.db_set_task_done_DEPRECATED(id, 0)
                    self.ui_display_log("Task {0} un-done !".format(id))
                else:
                    self.db_set_task_done_DEPRECATED(id, 1)
                    self.ui_display_log("Task {0} done !".format(id))
            self.ui_reload_tasks_list(self.archives, task=id)


    def cb_toggle_task_urgent(self, event=None):
        "Event toggle urgent flag"
        if not self.archives:
            ids = self.ui.lb.curselection()
            for task in ids:
                id = self.tasks[str(task)]
                if self.task_is_urgent(id):
                    self.db_set_task_urgent_DEPRECATED(id, 0)
                    self.ui_display_log("Task {0} is not urgent !".format(id))
                else:
                    self.db_set_task_urgent_DEPRECATED(id, 1)
                    self.ui_display_log("Task {0} is urgent !".format(id))
            self.ui_reload_tasks_list(self.archives, task=id)


    def cb_filter(self, event=None):
        "Event search"
        mask = self.mask.get()
        if mask == "":
            mask = "%"
            self.mask.set(mask)
        self.ui_reload_tasks_list(self.archives, END, None)
        self.ui_display_log("Only tasks matching '{0}' are displayed !".format(mask))


    def cb_display_help(self, event=None):
        "Event display help"
        t = "{0} {1}".format(self.program, self.version)
        showinfo(t, self.dochelp)

        
    ### FUNCTIONS ###################################################

    def task_get_task(self, id):
        "Get a task"
        t = self.task_get_task_details(id)
        return(t['task'])


    def task_is_urgent(self, id):
        "Get urgent flag for the task"
        t = self.task_get_task_details(id)
        return(t['urgent'])


    def task_is_done(self, id):
        "Get done flag for the task"
        t = self.task_get_task_details(id)
        return(t['done'])


    def task_is_archived(self, id):
        "Get the *active* flag for the task"
        t = self.task_get_task_details(id)
        return(t['active'])


    def task_get_project(self, id):
        "Get the project of the task"
        t = self.task_get_task_details(id)
        return(t['project'])


    def task_create(self, task=None):
        "Create a new task"
        self.ui_display_log("Appending new task…")
        if not task:
            task = askstring("New task ?", "Enter the new task :\nPlease use the following format :\n 'N° - Details for the task'")
        if task:
            id = self.db_create_task(task, ANA)
            if id:
                self.ui_display_log("Task {0} added !".format(id))
                self.ui_reload_tasks_list(self.archives, task=id)
            else:
                self.ui_display_log("Cannot save the task !")


    def task_set_property(self, tag, value):
        "Tag milestone/team"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            if self.db_set_task_property(id, tag, value):
                self.ui_display_log("Task {0} tagged for {1} !".format(id, value))
            else:
                self.ui_display_log("Cannot tag {0} for {1} !".format(id, value))
        self.ui_reload_tasks_list(self.archives, task=id)


    def ui_reload_tasks_list(self, archives=False, selection=END, task=None):
        "Reload tasks/archives list"
        self.ui.lb.delete(0, END)
        self.tasks = dict()
        self.sksat = dict()
        if archives:
            self.ui_load_tasks_list(True)
        else:
            self.ui_load_tasks_list(False)
        self.archives = archives
        self.ui.lb.focus_set()
        if task:
            selection = self.sksat[task] 
        elif len(selection) > 1 and selection != END:
            selection = selection[-1:]
        self.ui.lb.selection_set(selection)
        self.ui.lb.see(selection)
        return(True)
    

    def ui_load_tasks_list(self, archives):
        "Load the tasks list"
        l = self.db_get_tasks_list(archives, self.mask.get())
        i = 0
        for id, task, milestone, active, done, urgent, team, project in l:
            if archives:
                lbl = "[{0}] {1} - {2} ({3}) | id={4}".format(milestone, project, task, team, id)
            else:
                lbl = "[{0}] {1} - {2} ({3})".format(milestone, project, task, team)
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


    def ui_display_log(self, msg):
        "Display ui_display_log in status bar"
        self.ui.sb.ui_display_log.configure(text="{0}".format(msg))


    def ui_get_button_size(self):
        "Return the button size"
        if 'nt' == uname:
            return(7)
        else:
            return(6)
        

    def ui_draw_window(self):
        "Draw the UI"
        ui = Tk()
        ui.title("{0} {1}".format(self.program, self.version))
        # toolbar
        ui.tb = Frame(ui)
        ui.tb.pack(fill=X)
        # tools
        wb = self.ui_get_button_size()
        ui.tb.new = Button(ui.tb, text="New", width=wb, command=self.cb_new_task)
        ui.tb.new.pack(side=LEFT, padx=2, pady=2)
        ui.tb.cop = Button(ui.tb, text="Copy", width=wb, command=self.cb_copy_task)
        ui.tb.cop.pack(side=LEFT, padx=2, pady=2)
        ui.tb.pas = Button(ui.tb, text="Paste", width=wb, command=self.cb_paste_task)
        ui.tb.pas.pack(side=LEFT, padx=2, pady=2)
        ui.tb.edi = Button(ui.tb, text="Edit", width=wb, command=self.cb_edit_task)
        ui.tb.edi.pack(side=LEFT, padx=2, pady=2)
        ui.tb.pro = Button(ui.tb, text="Project", width=wb, command=self.cb_set_task_project)
        ui.tb.pro.pack(side=LEFT, padx=2, pady=2)
        ui.tb.don = Button(ui.tb, text="Status", width=wb, command=self.cb_toggle_task_done)
        ui.tb.don.pack(side=LEFT, padx=2, pady=2)
        ui.tb.urg = Button(ui.tb, text="Urgent", width=wb, command=self.cb_toggle_task_urgent)
        ui.tb.urg.pack(side=LEFT, padx=2, pady=2)
        ui.tb.arc = Button(ui.tb, text="Remove", width=wb, command=self.cb_toggle_task_archive)
        ui.tb.arc.pack(side=LEFT, padx=2, pady=2)
        ui.tb.ref = Button(ui.tb, text="Refresh", width=wb, command=self.cb_refresh)
        ui.tb.ref.pack(side=LEFT, padx=2, pady=2)
        ui.tb.vis = Button(ui.tb, text="Trash", width=wb, command=self.cb_toggle_display)
        ui.tb.vis.pack(side=RIGHT, padx=2, pady=2)
        ui.tb.cmd = Button(ui.tb, text="Console", width=wb, command=self.cb_open_console)
        ui.tb.cmd.pack(side=RIGHT, padx=2, pady=2)
        # tagbar
        ui.tg = Frame(ui)
        ui.tg.pack(fill=X)
        ui.tg.tf1 = Button(ui.tg, text=F1, width=wb, command=self.cb_set_task_milestone1)
        ui.tg.tf1.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf2 = Button(ui.tg, text=F2, width=wb, command=self.cb_set_task_milestone2)
        ui.tg.tf2.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf3 = Button(ui.tg, text=F3, width=wb, command=self.cb_set_task_milestone3)
        ui.tg.tf3.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf4 = Button(ui.tg, text=F4, width=wb, command=self.cb_set_task_milestone4)
        ui.tg.tf4.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tf5 = Button(ui.tg, text=F5, width=wb, command=self.cb_set_task_milestone5)
        ui.tg.tf5.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tANA = Button(ui.tg, text=ANA, width=wb, command=self.cb_set_task_team1)
        ui.tg.tANA.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tDEV = Button(ui.tg, text=DEV, width=wb, command=self.cb_set_task_team2)
        ui.tg.tDEV.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tQ_R = Button(ui.tg, text=Q_R, width=wb, command=self.cb_set_task_team3)
        ui.tg.tQ_R.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tRE7 = Button(ui.tg, text=RE7, width=wb, command=self.cb_set_task_team4)
        ui.tg.tRE7.pack(side=LEFT, padx=2, pady=2)
        ui.tg.tARB = Button(ui.tg, text=ARB, width=wb, command=self.cb_set_task_team5)
        ui.tg.tARB.pack(side=LEFT, padx=2, pady=2)
        # filterbar
        ui.fb = Frame(ui)
        ui.fb.pack(fill=X)
        self.mask = StringVar()
        self.mask.set("%")
        ui.fb.lbl = Label(ui.fb, text="Tasks filter: ")
        ui.fb.lbl.pack(side=LEFT, padx=2, pady=2)
        ui.fb.src = Entry(ui.fb, textvariable=self.mask)
        ui.fb.config(height=0)
        ui.fb.src.pack(side=LEFT,expand=True, fill=X, padx=2, pady=2)
        self.filter = True
        ui.fb.but = Button(ui.fb, text="Apply", command=self.cb_filter)
        ui.fb.but.pack(side=LEFT, padx=2, pady=2)
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
        ui.sb.ui_display_log = Label(ui.sb)
        ui.sb.ui_display_log.pack(expand=True, fill='both', padx=2, pady=2)
        ui.bind("<F5>", self.cb_refresh)
        ui.bind("<F11>", self.cb_open_console)
        ui.lb.bind("<n>", self.cb_new_task)
        ui.lb.bind("<c>", self.cb_copy_task)
        ui.lb.bind("<p>", self.cb_paste_task)
        ui.lb.bind("<e>", self.cb_edit_task)
        ui.lb.bind("<r>", self.cb_toggle_task_archive)
        ui.lb.bind("<t>", self.cb_toggle_display)
        ui.lb.bind("<s>", self.cb_toggle_task_done)
        ui.lb.bind("<u>", self.cb_toggle_task_urgent)
        ui.lb.bind("<h>", self.cb_display_help)
        ui.fb.src.bind("<Return>", self.cb_filter)
        ui.lb.bind("<Double-Button-1>", self.cb_edit_task)
        ui.lb.bind("<Button-2>", self.cb_set_task_project)
        ui.lb.bind("<Double-Button-3>", self.cb_toggle_task_urgent)
        return(ui)



class console(object):
    
    "Class for console"
    
    def __init__(self, db, master):
        "Start the console"
        self.db = db
        self.master = master
        self.ui = self.console_draw_ui()
        self.ui.term.insert(END ,"Type your request and press <Enter>.\n")
        self.ui.mainloop()
    

    def console_execute_sql(self, event=None):
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
        

    def console_draw_ui(self):
        "Draw the UI"
        ui = Tk()
        ui.title("console")
        # Console
        ui.term = ScrolledText(ui)
        ui.term.pack(fill=BOTH, expand=1)
        # Barre commande
        ui.cmd = Entry(ui)
        ui.cmd.pack(side=LEFT, fill=BOTH, expand=1)
        ui.bind('<Return>', self.console_execute_sql)
        ui.cmd.focus()
        return(ui)



if __name__ == '__main__':
    # start the program
    run = to_do_app(PROGRAM, VERSION, DOCHELP)
