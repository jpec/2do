#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# PARAM
#---------------------------------------------------------------------

# database file
BASE = "test"
PATH = "~"
SDBFILE = "{0}/2do_{1}.db".format(PATH, BASE)

# milestones
M1 = {'lb' : "Project1", 'fg' : "black", 'bg' : "white"}
M2 = {'lb' : "Project2", 'fg' : "black", 'bg' : "white"}
M3 = {'lb' : "Project3", 'fg' : "black", 'bg' : "white"}
M4 = {'lb' : "Project4", 'fg' : "black", 'bg' : "white"}
M5 = {'lb' : "Project5", 'fg' : "black", 'bg' : "white"}
M6 = {'lb' : "Project6", 'fg' : "black", 'bg' : "white"}
M7 = {'lb' : "Project7", 'fg' : "black", 'bg' : "white"}
M8 = {'lb' : "Project8", 'fg' : "black", 'bg' : "white"}
M9 = {'lb' : "Project9", 'fg' : "black", 'bg' : "white"}
M0 = {'lb' : "Project0", 'fg' : "black", 'bg' : "white"}

# teams
T1 = {'lb' : "ANA", 'fg' : "red", 'bg' : "white"}
T2 = {'lb' : "CHF", 'fg' : "darkblue", 'bg' : "white"}
T3 = {'lb' : "Q/A", 'fg' : "orange", 'bg' : "white"}
T4 = {'lb' : "DEV", 'fg' : "black", 'bg' : "#FF9999"}
T5 = {'lb' : "COR", 'fg' : "black", 'bg' : "#7ACCA3"}
T6 = {'lb' : "QAL", 'fg' : "black", 'bg' : "orange"}
T7 = {'lb' : "RE7", 'fg' : "darkgreen", 'bg' : "white"}
T8 = {'lb' : "ARB", 'fg' : "black", 'bg' : "yellow"}
T9 = {'lb' : "VAL", 'fg' : "black", 'bg' : "grey"}
T0 = {'lb' : "N/A", 'fg' : "black", 'bg' : "white"}
 
# mode debug
DEBUG = False


#---------------------------------------------------------------------
# PROGRAM
#---------------------------------------------------------------------

PROGRAM = "2do {}".format(BASE)
VERSION = "v2.0"
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
 <F1> New task
 <F2> Copy task
 <F3> Paste task
 <F4> Duplicate task
 <F5> Edit task
 <F6> Toggle Status
 <F7> Toggle Urgent
 <F8> Delete task
 <F9> Reload data
 <F10> Open console
 <F11> View trash
 <F12> Help

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


def debug(msgs):
    if DEBUG:
        print("[DEBUG]", msgs)


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
            self.ui_display_log(SDBFILE)
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
        debug([path])
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
        sql = "CREATE TABLE tasks (task TEXT, milestone TEXT, active INT, done INT, urgent INT, team TEXT);"
        debug([sql])
        db.execute(sql)
        db.commit()
        self.db = db
        return(True)

    def db_create_task(self, task, team):
        "Add the task in the database"
        sql = "INSERT INTO tasks (task, milestone, team, active, done, urgent) VALUES (?, '', ?, 1, 0, 0);"
        debug([sql, task, team])
        id = self.db.execute(sql, (task, team)).lastrowid
        self.db.commit()
        return(id)

    def db_set_task_property(self, id, tag, value):
        "Set task property"
        if tag == "milestone":
            sql = "UPDATE tasks SET milestone = ? WHERE rowid = ? ;"
        elif tag == "team":
            sql = "UPDATE tasks SET team = ? WHERE rowid = ? ;"
        elif tag == "active":
            sql = "UPDATE tasks SET active = ? WHERE rowid = ? ;"
        elif tag == "done":
            sql = "UPDATE tasks SET done = ? WHERE rowid = ? ;"
        elif tag == "urgent":
            sql = "UPDATE tasks SET urgent = ? WHERE rowid = ? ;"
        elif tag == "task":
            sql = "UPDATE tasks SET task = ? WHERE rowid = ? ;"
        else:
            return(False)
        debug([sql, value, id])
        self.db.execute(sql, (value, id))
        self.db.commit()
        return(True)

    def db_get_tasks_list(self, archives, mask="%"):
        "Get the tasks list"
        sql = "SELECT rowid, task, milestone, active, done, urgent, team FROM tasks WHERE active = ? AND (task LIKE ? OR team LIKE ? OR milestone LIKE ?) ORDER BY milestone, task, rowid ;"
        if archives:
            debug([sql, 0, mask, mask, mask])
            r = self.db.execute(sql, (0, mask, mask, mask))
        else:
            debug([sql, 1, mask, mask, mask])
            r = self.db.execute(sql, (1, mask, mask, mask))
        return(r.fetchall())

    def task_create_task_from_task(self, id):
        "Create a task duplicating an existing task"
        task = self.task_get_task_details(id)
        sql = "INSERT INTO tasks (task, milestone, team, active, done, urgent) VALUES (?, ?, ?, 1, 0, 0);"
        debug([sql, task['task'], task['milestone'], task['team']])
        new = self.db.execute(sql, (task['task'], task['milestone'], task['team'])).lastrowid
        self.db.commit()
        return(new)

    def task_get_task_details(self, id):
        "Get task's details"
        sql = "SELECT rowid, task, milestone, active, done, urgent, team FROM tasks WHERE rowid = ? ;"
        debug([sql, id])
        r = self.db.execute(sql, (id, ))
        t = dict()
        for id, task, milestone, active, done, urgent, team in r.fetchall():
            debug([id, task, milestone, active, done, urgent, team])
            t['id'] = id
            t['task'] = task
            t['milestone'] = milestone
            t['active'] = int(active)
            t['done'] = int(done)
            t['urgent'] = int(urgent)
            t['team'] = team
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
            self.ui.tb.vis.configure(text="Tasks\nF11")
            self.ui.tb.arc.configure(text="Restore\nF8")
            self.ui.tb.new.configure(state=DISABLED)
            self.ui.tb.cop.configure(state=DISABLED)
            self.ui.tb.pas.configure(state=DISABLED)
            self.ui.tb.dup.configure(state=DISABLED)
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.don.configure(state=DISABLED)
            self.ui.tb.urg.configure(state=DISABLED)
            self.ui.tg1.tm1.configure(state=DISABLED)
            self.ui.tg1.tm2.configure(state=DISABLED)
            self.ui.tg1.tm3.configure(state=DISABLED)
            self.ui.tg1.tm4.configure(state=DISABLED)
            self.ui.tg1.tm5.configure(state=DISABLED)
            self.ui.tg1.tm6.configure(state=DISABLED)
            self.ui.tg1.tm7.configure(state=DISABLED)
            self.ui.tg1.tm8.configure(state=DISABLED)
            self.ui.tg1.tm9.configure(state=DISABLED)
            self.ui.tg1.tm0.configure(state=DISABLED)
            self.ui.tg2.tt1.configure(state=DISABLED)
            self.ui.tg2.tt2.configure(state=DISABLED)
            self.ui.tg2.tt3.configure(state=DISABLED)
            self.ui.tg2.tt4.configure(state=DISABLED)
            self.ui.tg2.tt5.configure(state=DISABLED)
            self.ui.tg2.tt6.configure(state=DISABLED)
            self.ui.tg2.tt7.configure(state=DISABLED)
            self.ui.tg2.tt8.configure(state=DISABLED)
            self.ui.tg2.tt9.configure(state=DISABLED)
            self.ui.tg2.tt0.configure(state=DISABLED)
            self.ui_display_log("Displaying the archives bin…")
        else:
            # archives mode
            self.ui_reload_tasks_list(False)
            self.ui.tb.vis.configure(text="Trash\nF11")
            self.ui.tb.arc.configure(text="Remove\nF8")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.cop.configure(state=NORMAL)
            self.ui.tb.pas.configure(state=NORMAL)
            self.ui.tb.dup.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.don.configure(state=NORMAL)
            self.ui.tb.urg.configure(state=NORMAL)
            self.ui.tg1.tm1.configure(state=NORMAL)
            self.ui.tg1.tm2.configure(state=NORMAL)
            self.ui.tg1.tm3.configure(state=NORMAL)
            self.ui.tg1.tm4.configure(state=NORMAL)
            self.ui.tg1.tm5.configure(state=NORMAL)
            self.ui.tg1.tm6.configure(state=NORMAL)
            self.ui.tg1.tm7.configure(state=NORMAL)
            self.ui.tg1.tm8.configure(state=NORMAL)
            self.ui.tg1.tm9.configure(state=NORMAL)
            self.ui.tg1.tm0.configure(state=NORMAL)
            self.ui.tg2.tt1.configure(state=NORMAL)
            self.ui.tg2.tt2.configure(state=NORMAL)
            self.ui.tg2.tt3.configure(state=NORMAL)
            self.ui.tg2.tt4.configure(state=NORMAL)
            self.ui.tg2.tt5.configure(state=NORMAL)
            self.ui.tg2.tt6.configure(state=NORMAL)
            self.ui.tg2.tt7.configure(state=NORMAL)
            self.ui.tg2.tt8.configure(state=NORMAL)
            self.ui.tg2.tt9.configure(state=NORMAL)
            self.ui.tg2.tt0.configure(state=NORMAL)
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

    def cb_duplicate_task(self, event=None):
        "Event duplicate task"
        tasks = self.ui.lb.curselection()
        self.ui.clipboard_clear()
        for task in tasks:
            id = self.tasks[str(task)]
            new = self.task_create_task_from_task(id)
            self.ui_display_log("Task {0} duplicated in {1}.".format(id, new))
        self.ui_reload_tasks_list(self.archives)

    def cb_copy_task(self, event=None):
        "Event copy task"
        tasks = self.ui.lb.curselection()
        self.ui.clipboard_clear()
        for task in tasks:
            id = self.tasks[str(task)]
            # DEPRECATED :
            old = self.task_get_task_details(id)
            self.ui.clipboard_append(old['task'])
            self.ui_display_log("Task {0} copied.".format(id))

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
                    self.db_set_task_property(id, "task", new)
                    self.ui_display_log("Task {0} edited !".format(id))
            self.ui_reload_tasks_list(self.archives, task=id)

    def cb_set_task_milestone1(self, event=None):
        "Event tag milestone 1"
        if not self.archives:
            self.task_set_property('milestone', M1['lb'])

    def cb_set_task_milestone2(self, event=None):
        "Event tag milestone 2"
        if not self.archives:
            self.task_set_property('milestone', M2['lb'])

    def cb_set_task_milestone3(self, event=None):
        "Event tag milestone 3"
        if not self.archives:
            self.task_set_property('milestone', M3['lb'])

    def cb_set_task_milestone4(self, event=None):
        "Event tag milestone 4"
        if not self.archives:
            self.task_set_property('milestone', M4['lb'])

    def cb_set_task_milestone5(self, event=None):
        "Event tag milestone 5"
        if not self.archives:
            self.task_set_property('milestone', M5['lb'])

    def cb_set_task_milestone6(self, event=None):
        "Event tag milestone 6"
        if not self.archives:
            self.task_set_property('milestone', M6['lb'])

    def cb_set_task_milestone7(self, event=None):
        "Event tag milestone 7"
        if not self.archives:
            self.task_set_property('milestone', M7['lb'])

    def cb_set_task_milestone8(self, event=None):
        "Event tag milestone 8"
        if not self.archives:
            self.task_set_property('milestone', M8['lb'])

    def cb_set_task_milestone9(self, event=None):
        "Event tag milestone 9"
        if not self.archives:
            self.task_set_property('milestone', M9['lb'])

    def cb_set_task_milestone0(self, event=None):
        "Event tag milestone 0"
        if not self.archives:
            self.task_set_property('milestone', M0['lb'])

    def cb_set_task_team1(self, event=None):
        "Event tag team 1"
        if not self.archives:
            self.task_set_property('team', T1['lb'])

    def cb_set_task_team2(self, event=None):
        "Event tag team 2"
        if not self.archives:
            self.task_set_property('team', T2['lb'])

    def cb_set_task_team3(self, event=None):
        "Event tag team 3"
        if not self.archives:
            self.task_set_property('team', T3['lb'])

    def cb_set_task_team4(self, event=None):
        "Event tag team 4"
        if not self.archives:
            self.task_set_property('team', T4['lb'])

    def cb_set_task_team5(self, event=None):
        "Event tag team 5"
        if not self.archives:
            self.task_set_property('team', T5['lb'])

    def cb_set_task_team6(self, event=None):
        "Event tag team 6"
        if not self.archives:
            self.task_set_property('team', T6['lb'])

    def cb_set_task_team7(self, event=None):
        "Event tag team 7"
        if not self.archives:
            self.task_set_property('team', T7['lb'])

    def cb_set_task_team8(self, event=None):
        "Event tag team 8"
        if not self.archives:
            self.task_set_property('team', T8['lb'])

    def cb_set_task_team9(self, event=None):
        "Event tag team 9"
        if not self.archives:
            self.task_set_property('team', T9['lb'])

    def cb_set_task_team0(self, event=None):
        "Event tag team 0"
        if not self.archives:
            self.task_set_property('team', T0['lb'])

    def cb_toggle_task_archive(self, event=None):
        "Event toggle archive flag"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            lb = self.task_get_task(id)
            if self.task_is_archived(id) and \
               askyesno("Archive ?", "Do yo want to archive this task ?\n\"{0}\"".format(lb)):
                self.db_set_task_property(id, "active", 0)
                self.ui_display_log("Task {0} archived !".format(id))
            else:
                self.db_set_task_property(id, "active", 1)
                self.ui_display_log("Task {0} un-archived !".format(id))
        self.ui_reload_tasks_list(self.archives)

    def cb_toggle_task_done(self, event=None):
        "Event toggle done flag"
        if not self.archives:
            ids = self.ui.lb.curselection()
            for task in ids:
                id = self.tasks[str(task)]
                if self.task_is_done(id):
                    self.db_set_task_property(id, "done", 0)
                    self.ui_display_log("Task {0} un-done !".format(id))
                else:
                    self.db_set_task_property(id, "done", 1)
                    self.ui_display_log("Task {0} done !".format(id))
            self.ui_reload_tasks_list(self.archives, task=id)

    def cb_toggle_task_urgent(self, event=None):
        "Event toggle urgent flag"
        if not self.archives:
            ids = self.ui.lb.curselection()
            for task in ids:
                id = self.tasks[str(task)]
                if self.task_is_urgent(id):
                    self.db_set_task_property(id, "urgent", 0)
                    self.ui_display_log("Task {0} is not urgent !".format(id))
                else:
                    self.db_set_task_property(id, "urgent", 1)
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

    def task_create(self, task=None):
        "Create a new task"
        self.ui_display_log("Appending new task…")
        if not task:
            task = askstring("New task ?", "Enter the new task :\nPlease use the following format :\n 'N° - Details for the task'")
        if task:
            id = self.db_create_task(task, T1['lb'])
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
        for id, task, milestone, active, done, urgent, team in l:
            if archives:
                lbl = "[{0}] {1} ({2}) | id={3}".format(milestone, task, team, id)
            elif int(done) > 0:
                lbl = "[{0}] {1}".format(milestone, task)
            else:
                lbl = "[{0}] {1} ({2})".format(milestone, task, team)
            self.ui.lb.insert(i, lbl)
            if int(done) > 0:
                self.ui.lb.itemconfig(i, fg='grey', bg='white')
            elif int(urgent) > 0:
                self.ui.lb.itemconfig(i, fg='white', bg='red')
            elif team == T1['lb']:
                self.ui.lb.itemconfig(i, fg=T1['fg'], bg=T1['bg'])
            elif team == T2['lb']:
                self.ui.lb.itemconfig(i, fg=T2['fg'], bg=T2['bg'])
            elif team == T3['lb']:
                self.ui.lb.itemconfig(i, fg=T3['fg'], bg=T3['bg'])
            elif team == T4['lb']:
                self.ui.lb.itemconfig(i, fg=T4['fg'], bg=T4['bg'])
            elif team == T5['lb']:
                self.ui.lb.itemconfig(i, fg=T5['fg'], bg=T5['bg'])
            elif team == T6['lb']:
                self.ui.lb.itemconfig(i, fg=T6['fg'], bg=T6['bg'])
            elif team == T7['lb']:
                self.ui.lb.itemconfig(i, fg=T7['fg'], bg=T7['bg'])
            elif team == T8['lb']:
                self.ui.lb.itemconfig(i, fg=T8['fg'], bg=T8['bg'])
            elif team == T9['lb']:
                self.ui.lb.itemconfig(i, fg=T9['fg'], bg=T9['bg'])
            elif team == T0['lb']:
                self.ui.lb.itemconfig(i, fg=T0['fg'], bg=T0['bg']) 
            else:
                self.ui.lb.itemconfig(i, fg="black", bg="white")
            self.tasks[str(i)] = id
            self.sksat[id] = str(i)
            i = i+1
        return(True)

    def ui_display_log(self, msg):
        "Display ui_display_log in status bar"
        debug([msg])
        self.ui.sb.ui_display_log.configure(text="{0}".format(msg))

    def ui_draw_window(self):
        "Draw the UI"
        ui = Tk()
        ui.title("{0} {1}".format(self.program, self.version))
        # toolbar
        ui.tb = Frame(ui)
        ui.tb.pack(fill=X)
        # tools
        ui.tb.new = Button(ui.tb, text="New\nF1", width=6, command=self.cb_new_task)
        ui.tb.new.pack(side=LEFT, padx=2, pady=2)
        ui.tb.cop = Button(ui.tb, text="Copy\nF2", width=6, command=self.cb_copy_task)
        ui.tb.cop.pack(side=LEFT, padx=2, pady=2)
        ui.tb.pas = Button(ui.tb, text="Paste\nF3", width=6, command=self.cb_paste_task)
        ui.tb.pas.pack(side=LEFT, padx=2, pady=2)
        ui.tb.dup = Button(ui.tb, text="Duplica\nF4", width=6, command=self.cb_duplicate_task)
        ui.tb.dup.pack(side=LEFT, padx=2, pady=2)
        ui.tb.edi = Button(ui.tb, text="Edit\nF5", width=6, command=self.cb_edit_task)
        ui.tb.edi.pack(side=LEFT, padx=2, pady=2)
        ui.tb.don = Button(ui.tb, text="Status\nF6", width=6, command=self.cb_toggle_task_done)
        ui.tb.don.pack(side=LEFT, padx=2, pady=2)
        ui.tb.urg = Button(ui.tb, text="Urgent\nF7", width=6, command=self.cb_toggle_task_urgent)
        ui.tb.urg.pack(side=LEFT, padx=2, pady=2)
        ui.tb.arc = Button(ui.tb, text="Remove\nF8", width=6, command=self.cb_toggle_task_archive)
        ui.tb.arc.pack(side=LEFT, padx=2, pady=2)
        ui.tb.ref = Button(ui.tb, text="Refresh\nF9", width=6, command=self.cb_refresh)
        ui.tb.ref.pack(side=LEFT, padx=2, pady=2)
        ui.tb.hlp = Button(ui.tb, text="Help\nF12", width=6, command=self.cb_display_help)
        ui.tb.hlp.pack(side=RIGHT, padx=2, pady=2)
        ui.tb.vis = Button(ui.tb, text="Trash\nF11", width=6, command=self.cb_toggle_display)
        ui.tb.vis.pack(side=RIGHT, padx=2, pady=2)
        ui.tb.cmd = Button(ui.tb, text="Console\nF10", width=6, command=self.cb_open_console)
        ui.tb.cmd.pack(side=RIGHT, padx=2, pady=2)
        # tagbar 1
        ui.tg1= Frame(ui)
        ui.tg1.pack(fill=X)
        ui.tg1.tm1 = Button(ui.tg1, text=M1['lb'], fg=M1['fg'], bg=M1['bg'], command=self.cb_set_task_milestone1)
        ui.tg1.tm1.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm2 = Button(ui.tg1, text=M2['lb'], fg=M2['fg'], bg=M2['bg'], command=self.cb_set_task_milestone2)
        ui.tg1.tm2.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm3 = Button(ui.tg1, text=M3['lb'], fg=M3['fg'], bg=M3['bg'], command=self.cb_set_task_milestone3)
        ui.tg1.tm3.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm4 = Button(ui.tg1, text=M4['lb'], fg=M4['fg'], bg=M4['bg'], command=self.cb_set_task_milestone4)
        ui.tg1.tm4.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm5 = Button(ui.tg1, text=M5['lb'], fg=M5['fg'], bg=M5['bg'], command=self.cb_set_task_milestone5)
        ui.tg1.tm5.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm6 = Button(ui.tg1, text=M6['lb'], fg=M6['fg'], bg=M6['bg'], command=self.cb_set_task_milestone6)
        ui.tg1.tm6.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm7 = Button(ui.tg1, text=M7['lb'], fg=M7['fg'], bg=M7['bg'], command=self.cb_set_task_milestone7)
        ui.tg1.tm7.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm8 = Button(ui.tg1, text=M8['lb'], fg=M8['fg'], bg=M8['bg'], command=self.cb_set_task_milestone8)
        ui.tg1.tm8.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm9 = Button(ui.tg1, text=M9['lb'], fg=M9['fg'], bg=M9['bg'], command=self.cb_set_task_milestone9)
        ui.tg1.tm9.pack(side=LEFT, padx=2, pady=2)
        ui.tg1.tm0 = Button(ui.tg1, text=M0['lb'], fg=M0['fg'], bg=M0['bg'], command=self.cb_set_task_milestone0)
        ui.tg1.tm0.pack(side=LEFT, padx=2, pady=2)
        # tagbar 2
        ui.tg2 = Frame(ui)
        ui.tg2.pack(fill=X)
        ui.tg2.tt1 = Button(ui.tg2, text=T1['lb'], fg=T1['fg'], bg=T1['bg'], command=self.cb_set_task_team1)
        ui.tg2.tt1.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt2 = Button(ui.tg2, text=T2['lb'], fg=T2['fg'], bg=T2['bg'], command=self.cb_set_task_team2)
        ui.tg2.tt2.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt3 = Button(ui.tg2, text=T3['lb'], fg=T3['fg'], bg=T3['bg'], command=self.cb_set_task_team3)
        ui.tg2.tt3.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt4 = Button(ui.tg2, text=T4['lb'], fg=T4['fg'], bg=T4['bg'], command=self.cb_set_task_team4)
        ui.tg2.tt4.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt5 = Button(ui.tg2, text=T5['lb'], fg=T5['fg'], bg=T5['bg'], command=self.cb_set_task_team5)
        ui.tg2.tt5.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt6 = Button(ui.tg2, text=T6['lb'], fg=T6['fg'], bg=T6['bg'], command=self.cb_set_task_team6)
        ui.tg2.tt6.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt7 = Button(ui.tg2, text=T7['lb'], fg=T7['fg'], bg=T7['bg'], command=self.cb_set_task_team7)
        ui.tg2.tt7.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt8 = Button(ui.tg2, text=T8['lb'], fg=T8['fg'], bg=T8['bg'], command=self.cb_set_task_team8)
        ui.tg2.tt8.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt9 = Button(ui.tg2, text=T9['lb'], fg=T9['fg'], bg=T9['bg'], command=self.cb_set_task_team9)
        ui.tg2.tt9.pack(side=LEFT, padx=2, pady=2)
        ui.tg2.tt0 = Button(ui.tg2, text=T0['lb'], fg=T0['fg'], bg=T0['bg'], command=self.cb_set_task_team0)
        ui.tg2.tt0.pack(side=LEFT, padx=2, pady=2)
        # filterbar
        ui.fb = Frame(ui)
        ui.fb.pack(fill=X)
        self.mask = StringVar()
        self.mask.set("%")
        ui.fb.src = Entry(ui.fb, textvariable=self.mask)
        ui.fb.config(height=0)
        ui.fb.src.pack(side=LEFT, expand=True, fill=X, padx=2, pady=2)
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
        # Shorcuc
        ui.bind("<F1>", self.cb_new_task)
        ui.lb.bind("<F2>", self.cb_copy_task)
        ui.bind("<F3>", self.cb_paste_task)
        ui.lb.bind("<F4>", self.cb_duplicate_task)
        ui.lb.bind("<F5>", self.cb_edit_task)
        ui.lb.bind("<F6>", self.cb_toggle_task_done)
        ui.lb.bind("<F7>", self.cb_toggle_task_urgent)
        ui.lb.bind("<F8>", self.cb_toggle_task_archive)
        ui.bind("<F9>", self.cb_refresh)
        ui.bind("<F10>", self.cb_open_console)
        ui.bind("<F11>", self.cb_toggle_display)
        ui.bind("<F12>", self.cb_display_help)
        ui.fb.src.bind("<Return>", self.cb_filter)
        ui.lb.bind("<Double-Button-1>", self.cb_edit_task)
        ui.lb.bind("<Double-Button-3>", self.cb_toggle_task_urgent)
        return(ui)


class console(object):
    
    "Class for console"
    
    def __init__(self, db, master):
        "Start the console"
        self.db = db
        self.master = master
        self.ui = self.console_draw_ui()
        self.ui.term.insert(END ,"  _____ ___  _   _  ____  ___  _      ____  \n")
        self.ui.term.insert(END ," / ____/ _ \| \ | |/ ___|/ _ \| |    |___ \ \n")
        self.ui.term.insert(END ,"| |   | | | |  \| | (__ | | | | |      __) |\n")
        self.ui.term.insert(END ,"| |   | | | | . ` |\__ \| | | | |     |__ < \n")
        self.ui.term.insert(END ,"| |___| |_| | |\  |___) | |_| | |____ ___) |\n")
        self.ui.term.insert(END ," \_____\___/|_| \_|____/ \___/|______|____/ \n")
        self.ui.term.insert(END ,"                                            \n")
        self.ui.term.insert(END ,"\n")
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
        ui.title("C0NS0LE")
        # Console
        ui.term = ScrolledText(ui, bg='black', fg='green')
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
