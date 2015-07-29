#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#---------------------------------------------------------------------
# PARAM
#---------------------------------------------------------------------

# database file
BASE = "test"
PATH = "."
SDBFILE = "{0}/2do_{1}.db".format(PATH, BASE)
 
# mode debug
DEBUG = False

#---------------------------------------------------------------------
# PROGRAM
#---------------------------------------------------------------------

PROGRAM = "2do {}".format(BASE)
VERSION = "v2.3"
DOCHELP = """
{0} {1}
--
This software is a simple todo list manager.
It's written in Python using Tkinter and Sqlite.
--
Author: Julien Pecqueur
Home: http://github.com/jpec/2do
Email: julien@peclu.net
License: GPL
--
Keyboard shortcuts on main window:
 <F1> New task
 <F2> Copy task
 <F3> Paste task
 <F4> Duplicate task
 <F5> Edit task
 <F6> Set date
 <F7> Toggle Status
 <F8> Toggle Urgent
 <F9> Delete task
 <F10> Reload data
 <F11> Open console
 <F12> View trash
 <ESC> Help

""".format(PROGRAM, VERSION)


#---------------------------------------------------------------------
# SOURCE CODE
#---------------------------------------------------------------------

from sqlite3 import connect
from sqlite3 import Error as SqlError
from os import name as uname
from os.path import isfile
from os.path import expanduser
from datetime import datetime
from tkinter import *
from tkinter.scrolledtext import ScrolledText
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from tkinter.messagebox import showerror
from tkinter.messagebox import askyesno
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askopenfilename


def debug(msgs):
    if DEBUG:
        print("[DEBUG]", msgs)

def start_to_do_app():
    return(to_do_app(PROGRAM, VERSION, DOCHELP))

def today():
    now = datetime.now()
    return(now.strftime("%d/%m/%Y"))

def is_urgent(date):
    if not (len(date) == 10 and date[2] == '/' and date[5] == '/'):
        return(False)
    try:
        d = int(date[0:2])
        m = int(date[3:5])
        y = int(date[6:10])
    except ValueError:
        return(False)
    else:
        t = today()
        dt = int(t[0:2])
        mt = int(t[3:5])
        yt = int(t[6:10])
        if y < yt or (y == yt and m < mt) or (y == yt and m == mt and d <= dt):
            return(True)
        else:
            return(False)
    

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
        sql = "CREATE TABLE tasks (task TEXT, milestone TEXT, active INT, done INT, urgent INT, team TEXT, date TEXT, updated TEXT);"
        debug([sql])
        db.execute(sql)
        db.commit()
        sql = "CREATE TABLE milestones (lb TEXT PRIMARY KEY NOT NULL, fg TEXT DEFAULT ('#000000'), bg TEXT DEFAULT ('#FFFFFF'), active BOOLEAN DEFAULT (1));"
        debug([sql])
        db.execute(sql)
        db.commit()
        sql = "INSERT INTO milestones(lb) VALUES('milestone');"
        debug([sql])
        db.execute(sql)
        db.commit()
        sql = "CREATE TABLE teams (lb TEXT PRIMARY KEY NOT NULL, fg TEXT DEFAULT ('#000000'), bg TEXT DEFAULT ('#FFFFFF'), active BOOLEAN DEFAULT (1));"
        debug([sql])
        db.execute(sql)
        db.commit()
        for team in [("ANA","#000000","#F68383"),("CHF","#000000","#81DAF5"),("Q/R","#DF731B","#FFFFFF"),
                  ("DEV","#000000","#D083F6"),("COR","#000000","#86F683"),("QAL","#000000","#F6B783"),
                  ("RE7","#088A08","#FFFFFF"),("ARB","#1B7ADF","#FFFFFF"),("VAL","#A4A4A4","#FFFFFF"),
                  ("N/A", "#000000","#FFFFFF")]:
            sql = "INSERT INTO teams(lb, fg, bg) VALUES(?, ?, ?);"
            db.execute(sql, team)
        db.commit()
        self.db = db
        return(True)

    def db_get_milestones(self):
        "Get milestones"
        sql = "SELECT lb, active FROM milestones WHERE active = 1 ORDER BY lb ;"
        r = self.db.execute(sql)
        return(r.fetchall())

    def db_get_teams(self):
        "Get teams"
        sql = "SELECT lb, fg, bg, active FROM teams WHERE active = 1 ORDER BY lb;"
        r = self.db.execute(sql)
        return(r.fetchall())
        
    def db_create_task(self, task, team):
        "Add the task in the database"
        sql = "INSERT INTO tasks (task, milestone, team, active, done, urgent, updated) VALUES (?, '', ?, 1, 0, 0, ?);"
        debug([sql, task, team, today()])
        id = self.db.execute(sql, (task, team, today())).lastrowid
        self.db.commit()
        return(id)

    def db_set_task_property(self, id, tag, value):
        "Set task property"
        update_date = False
        if tag == "milestone":
            sql = "UPDATE tasks SET milestone = ? WHERE rowid = ? ;"
        elif tag == "team":
            sql = "UPDATE tasks SET team = ? WHERE rowid = ? ;"
            update_date = True
        elif tag == "active":
            sql = "UPDATE tasks SET active = ? WHERE rowid = ? ;"
        elif tag == "done":
            sql = "UPDATE tasks SET done = ? WHERE rowid = ? ;"
            update_date = True
        elif tag == "urgent":
            sql = "UPDATE tasks SET urgent = ? WHERE rowid = ? ;"
        elif tag == "task":
            sql = "UPDATE tasks SET task = ? WHERE rowid = ? ;"
        elif tag == "date":
            sql = "UPDATE tasks SET date = ? WHERE rowid = ? ;"
        else:
            return(False)
        debug([sql, value, id])
        self.db.execute(sql, (value, id))
        if update_date:
            sql = "UPDATE tasks SET updated = ? WHERE rowid = ? ;"
            debug([sql, today(), id])
            self.db.execute(sql, (today(), id))
        self.db.commit()
        return(True)

    def db_get_tasks_list(self, archives, mask="%"):
        "Get the tasks list"
        sql = "SELECT rowid, task, milestone, active, done, urgent, team, date, updated FROM tasks WHERE active = ? AND (task LIKE ? OR team LIKE ? OR milestone LIKE ? OR date LIKE ?) ORDER BY milestone, task, rowid ;"
        if archives:
            debug([sql, 0, mask, mask, mask])
            r = self.db.execute(sql, (0, mask, mask, mask, mask))
        else:
            debug([sql, 1, mask, mask, mask])
            r = self.db.execute(sql, (1, mask, mask, mask, mask))
        return(r.fetchall())

    def task_create_task_from_task(self, id):
        "Create a task duplicating an existing task"
        task = self.task_get_task_details(id)
        sql = "INSERT INTO tasks (task, milestone, team, active, done, urgent, updated) VALUES (?, ?, ?, 1, 0, 0, ?);"
        debug([sql, task['task'], task['milestone'], task['team']])
        new = self.db.execute(sql, (task['task'], task['milestone'], task['team'], today())).lastrowid
        self.db.commit()
        return(new)

    def task_get_task_details(self, id):
        "Get task's details"
        sql = "SELECT rowid, task, milestone, active, done, urgent, team, date, updated FROM tasks WHERE rowid = ? ;"
        debug([sql, id])
        r = self.db.execute(sql, (id, ))
        t = dict()
        for id, task, milestone, active, done, urgent, team, date, updated in r.fetchall():
            debug([id, task, milestone, active, done, urgent, team, date, updated])
            t['id'] = id
            t['task'] = task
            t['milestone'] = milestone
            t['active'] = int(active)
            t['done'] = int(done)
            t['urgent'] = int(urgent)
            t['team'] = team
            t['date'] = date
            t['updated'] = updated
            return(t)


    ### CALLBACKS ###################################################

    def cb_refresh(self, event=None):
        "Event Refresh - Reload"
        self.ui_display_log("Reloading data…")
        total = self.ui_reload_tasks_list(self.archives)
        self.ui_display_log("{0} tasks displayed".format(total))

    def cb_open_console(self, event=None):
        "Event open console"
        console(self.db, self.ui)

    def cb_export_csv(self, event=None):
        "Event export as csv"
        self.ui_display_log("Exporting csv file…")
        total = self.export_tasks_list(self.archives)
        if total:
            self.ui_display_log("{0} tasks exported".format(total))
        else:
            self.ui_display_log("Cancelled.")

    def cb_import_csv(self, event=None):
        "Event export as csv"
        self.ui_display_log("Importing csv file…")
        total = self.import_tasks_list()
        self.ui_display_log("{0} task(s) imported".format(total))

    def cb_toggle_display(self, event=None):
        "Event toggle tasks/archive mode"
        if not self.archives:
            # tasks mode
            self.ui_reload_tasks_list(True)
            self.ui.tb.vis.configure(text="Tâches\nF12")
            self.ui.tb.arc.configure(text="Restaur.\nF9")
            self.ui.tb.new.configure(state=DISABLED)
            self.ui.tb.cop.configure(state=DISABLED)
            self.ui.tb.pas.configure(state=DISABLED)
            self.ui.tb.dup.configure(state=DISABLED)
            self.ui.tb.edi.configure(state=DISABLED)
            self.ui.tb.dat.configure(state=DISABLED)
            self.ui.tb.don.configure(state=DISABLED)
            self.ui.tb.urg.configure(state=DISABLED)
            self.ui_display_log("Displaying the archives bin…")
        else:
            # archives mode
            self.ui_reload_tasks_list(False)
            self.ui.tb.vis.configure(text="Poubelle\n12")
            self.ui.tb.arc.configure(text="Suppr.\nF9")
            self.ui.tb.new.configure(state=NORMAL)
            self.ui.tb.cop.configure(state=NORMAL)
            self.ui.tb.pas.configure(state=NORMAL)
            self.ui.tb.dup.configure(state=NORMAL)
            self.ui.tb.edi.configure(state=NORMAL)
            self.ui.tb.dat.configure(state=NORMAL)
            self.ui.tb.don.configure(state=NORMAL)
            self.ui.tb.urg.configure(state=NORMAL)
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
            old = self.task_get_task_details(id)
            self.ui.clipboard_append(old['task'])
            self.ui_display_log("Task {0} copied.".format(id))

    def cb_copy_notes(self, event=None):
        "Event copy task for notes"
        tasks = self.ui.lb.curselection()
        self.ui.clipboard_clear()
        for task in tasks:
            id = self.tasks[str(task)]
            old = self.task_get_task_details(id)
            if len(old['task']) > 5:
                self.ui.clipboard_append(old['task'][0:5]+", ")
            self.ui_display_log("Ctrl + v to paste in Notes…")
            
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

    def cb_set_date(self, event=None):
        "Event set date"
        if not self.archives:
            ids = self.ui.lb.curselection()
            for task in ids:
                id = self.tasks[str(task)]
                old = self.task_get_date(id)
                self.ui_display_log("Setting date for task {0}…".format(id))
                new = askstring("Editing task…", "Enter the new due date (DD/MM/YYYY) :",
                                initialvalue=old)
                if new or new == '':
                    self.db_set_task_property(id, "date", new)
                    self.ui_display_log("Task {0} edited !".format(id))
            self.ui_reload_tasks_list(self.archives, task=id)
            
    def cb_set_task_milestone(self, milestone=None):
        "Event tag milestone"
        if not self.archives:
            self.task_set_property('milestone', milestone)

    def cb_set_task_team(self, team=None):
        "Event tag team"
        if not self.archives:
            self.task_set_property('team', team, True)

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

    def cb_display_task(self, event=None):
        "Event display task details"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            t = self.task_get_task_details(id)
            text = t['task'] + "\n"
            if t['urgent']:
                text += "/!\\ URGENT /!\\ \n"
            text += "Date: " + t['date'] + "\n"
            text += "Updated: " + t['updated'] + "\n"
            text += "Team: " + t['team'] + "\n"
            text += "Milestone: " + t['milestone'] + "\n"
            if t['done']:
                text += "This task is finished.\n"
            if not t['active']:
                text += "This task is archived.\n"
            showinfo("Task n°{0}".format(id), text)

    def cb_restart(self, event=None):
        self.ui.destroy()
        start_to_do_app()

        
    ### FUNCTIONS ###################################################

    def task_get_task(self, id):
        "Get a task"
        t = self.task_get_task_details(id)
        return(t['task'])

    def task_get_date(self, id):
        "Get task's due date"
        t = self.task_get_task_details(id)
        return(t['date'])

    def task_get_updated(self, id):
        "Get task's update date"
        t = self.task_get_task_details(id)
        return(t['updated'])

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
            id = self.db_create_task(task, None)
            if id:
                self.ui_display_log("Task {0} added !".format(id))
                self.ui_reload_tasks_list(self.archives, task=id)
            else:
                self.ui_display_log("Cannot save the task !")

    def task_set_property(self, tag, value, update_date=False):
        "Tag milestone/team"
        ids = self.ui.lb.curselection()
        for task in ids:
            id = self.tasks[str(task)]
            if self.db_set_task_property(id, tag, value):
                self.ui_display_log("Task {0} tagged for {1} !".format(id, value))
            else:
                self.ui_display_log("Cannot tag {0} for {1} !".format(id, value))
        self.ui_reload_tasks_list(self.archives, task=id)

    def export_tasks_list(self, archives=False):
        "Reload tasks/archives list"
        fn = asksaveasfilename(title="Export as CSV…")
        if fn:
            f = open(fn, 'w')
            l = self.db_get_tasks_list(archives, self.mask.get())
            f.write("id;task;milestone;active;done;urgent;team;date;updated\n")
            for id, task, milestone, active, done, urgent, team, date, updated in l:
                c = "{};{};{};{};{};{};{};{};{}\n".format(id, task, milestone, active, done, urgent, team, date, updated)
                f.write(c)
            f.close()
            return(len(l))
        else:
            return(0)    

    def import_tasks_list(self):
        fn = askopenfilename(title="Import CSV…")
        c = 0
        if fn:
            f = open(fn, 'r')
            for l in f:
                l = l.replace('\n','')
                ls = l.split(";")
                if len(ls) != 8 or ls[0] == 'id':
                    continue
                id = self.db_create_task(ls[1], ls[6])
                self.db_set_task_property(id, 'done', ls[4])
                self.db_set_task_property(id, 'urgent', ls[5])
                self.db_set_task_property(id, 'milestone', ls[2])
                if ls[7] != 'None':
                    self.db_set_task_property(id, 'date', ls[7])
                c += 1
            f.close()
            if c:
                self.ui_reload_tasks_list(self.archives)
        return(c)

    def get_teams(self):
        "Get teams param"
        l = self.db_get_teams()
        t = {}
        for lb, fg, bg, act in l:
            t[lb] = (fg, bg)
        return(t)
        
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
        return(len(self.tasks))
    
    def ui_load_tasks_list(self, archives):
        "Load the tasks list"
        l = self.db_get_tasks_list(archives, self.mask.get())
        teams = self.get_teams()
        i = 0
        for id, task, milestone, active, done, urgent, team, date, updated in l:
            if not date:
                date = '----------'
            if archives:
                lbl = "{}|{}|{}|{}|{} (id={})".format(str(milestone).ljust(8),str(updated).ljust(10), str(date).ljust(10), team, task, id)
            elif int(done) > 0:
                lbl = "{}|{}|{}|{}".format(str(milestone).ljust(8), str(updated).ljust(10), str(date).ljust(10), task)
            elif team == "N/A":
                lbl = "{}|{}".format(str(milestone).ljust(8), task)
            else:
                lbl = "{}|{}|{}|{} ({})".format(str(milestone).ljust(8),str(updated).ljust(10), str(date).ljust(10), task, team)
            self.ui.lb.insert(i, lbl)
            if archives:
                self.ui.lb.itemconfig(i, fg="black", bg="white")
            elif int(done) > 0:
                self.ui.lb.itemconfig(i, fg='#A4A4A4', bg='white')
            elif int(urgent) > 0:
                self.ui.lb.itemconfig(i, fg='white', bg='red')
            elif team == 'N/A' and len(task) > 1 and task[0] == "*":
                self.ui.lb.itemconfig(i, fg='black', bg='#EEE')
            elif team != 'VAL' and is_urgent(date):
                self.ui.lb.itemconfig(i, fg='white', bg='red')
            elif team in teams:
                t_fg, t_bg = teams[team]
                self.ui.lb.itemconfig(i, fg=t_fg, bg=t_bg) 
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

    def ui_draw_team_buttons(self, ui):
        "Draw team toolbar"
        tg= Frame(ui)
        tg.pack(fill=X)
        l = self.db_get_teams()
        for team, fg, bg, active in l:
            tg.team = Button(tg, text=team, fg=fg, bg=bg)
            tg.team.configure(command=lambda k=str(team): self.cb_set_task_team(k))
            tg.team.pack(side=LEFT, padx=2, pady=2)
        return(tg)

    def ui_draw_milestone_buttons(self, ui):
        "Draw milestone toolbar"
        tg= Frame(ui)
        tg.pack(fill=X)
        l = self.db_get_milestones()
        for milestone, active in l:
            tg.milestone = Button(tg, text=milestone)
            tg.milestone.configure(command=lambda k=str(milestone): self.cb_set_task_milestone(k))
            tg.milestone.pack(side=LEFT, padx=2, pady=2)
        return(tg)

    def ui_draw_window(self):
        "Draw the UI"
        ui = Tk()
        ui.title("{0} {1}".format(self.program, self.version))
        # toolbar
        ui.tb = Frame(ui)
        ui.tb.pack(fill=X)
        # tools
        w = 6
        h = 2
        ui.tb.new = Button(ui.tb, text="Créer\nF1", width=w, height=h, command=self.cb_new_task)
        ui.tb.new.pack(side=LEFT, padx=2, pady=2)
        ui.tb.cop = Button(ui.tb, text="Copier\nF2", width=w, height=h, command=self.cb_copy_task)
        ui.tb.cop.pack(side=LEFT, padx=2, pady=2)
        ui.tb.pas = Button(ui.tb, text="Coller\nF3", width=w, height=h, command=self.cb_paste_task)
        ui.tb.pas.pack(side=LEFT, padx=2, pady=2)
        ui.tb.dup = Button(ui.tb, text="Cloner\nF4", width=w, height=h, command=self.cb_duplicate_task)
        ui.tb.dup.pack(side=LEFT, padx=2, pady=2)
        ui.tb.edi = Button(ui.tb, text="Editer\nF5", width=w, height=h, command=self.cb_edit_task)
        ui.tb.edi.pack(side=LEFT, padx=2, pady=2)
        ui.tb.dat = Button(ui.tb, text="Date\nF6", width=w, height=h, command=self.cb_set_date)
        ui.tb.dat.pack(side=LEFT, padx=2, pady=2)
        ui.tb.don = Button(ui.tb, text="Statut\nF7", width=w, height=h, command=self.cb_toggle_task_done)
        ui.tb.don.pack(side=LEFT, padx=2, pady=2)
        ui.tb.urg = Button(ui.tb, text="Urgent\nF8", width=w, height=h, command=self.cb_toggle_task_urgent)
        ui.tb.urg.pack(side=LEFT, padx=2, pady=2)
        ui.tb.arc = Button(ui.tb, text="Suppr.\nF9", width=w, height=h, command=self.cb_toggle_task_archive)
        ui.tb.arc.pack(side=LEFT, padx=2, pady=2)
        ui.tb.ref = Button(ui.tb, text="Actual.\nF10", width=w, height=h, command=self.cb_refresh)
        ui.tb.ref.pack(side=LEFT, padx=2, pady=2)
        ui.tb.hlp = Button(ui.tb, text="Aide\nESC", width=w, height=h, bg="grey", command=self.cb_display_help)
        ui.tb.hlp.pack(side=RIGHT, padx=2, pady=2)
        ui.tb.vis = Button(ui.tb, text="Poubelle\nF12", width=w, height=h, bg="grey",  command=self.cb_toggle_display)
        ui.tb.vis.pack(side=RIGHT, padx=2, pady=2)
        ui.tb.cmd = Button(ui.tb, text="Console\nF11", width=w, height=h, bg="grey", command=self.cb_open_console)
        ui.tb.cmd.pack(side=RIGHT, padx=2, pady=2)
        # tagbar 1
        ui.tg1 = self.ui_draw_team_buttons(ui)
        # tagbar 2
        ui.tg2 = self.ui_draw_milestone_buttons(ui)
        # filterbar
        ui.fb = Frame(ui)
        ui.fb.pack(fill=X)
        self.mask = StringVar()
        self.mask.set("%")
        ui.fb.src = Entry(ui.fb, textvariable=self.mask, width=30)
        ui.fb.config(height=0)
        ui.fb.src.pack(side=LEFT, padx=2, pady=2)
        ui.fb.but = Button(ui.fb, text="Filtrer", width=8, command=self.cb_filter)
        ui.fb.but.pack(side=LEFT, padx=2, pady=2)
        self.filter = True
        ui.fb.ex = Button(ui.fb, text="Importer", width=8, command=self.cb_import_csv)
        ui.fb.ex.pack(side=LEFT,  padx=2, pady=2)
        ui.fb.ex = Button(ui.fb, text="Exporter", width=8, command=self.cb_export_csv)
        ui.fb.ex.pack(side=LEFT, padx=2, pady=2)
        ui.fb.no = Button(ui.fb, text="Notes", width=8, command=self.cb_copy_notes)
        ui.fb.no.pack(side=LEFT, padx=2, pady=2)
        ui.fb.re = Button(ui.fb, text="Relancer", width=8, command=self.cb_restart)
        ui.fb.re.pack(side=LEFT, padx=2, pady=2)
        # listbox
        ui.cf = Frame(ui)
        ui.cf.pack(fill=BOTH, expand=True)
        ui.sl = Scrollbar(ui.cf, orient=VERTICAL)
        ui.lb = Listbox(ui.cf, selectmode=EXTENDED, yscrollcommand=ui.sl.set)
        ui.lb.config(font="fixed")
        ui.sl.config(command=ui.lb.yview)
        ui.sl.pack(side=RIGHT, fill=Y)
        ui.lb.pack(side=LEFT, expand=True, fill='both')
        # statusbar
        ui.sb = Frame(ui)
        ui.sb.pack(fill=X)
        ui.sb.ui_display_log = Label(ui.sb, anchor=W, justify=LEFT)
        ui.sb.ui_display_log.pack(side=LEFT, expand=True, fill='both', padx=2, pady=2)
        # Shorcut
        ui.bind("<F1>", self.cb_new_task)
        ui.lb.bind("<F2>", self.cb_copy_task)
        ui.bind("<F3>", self.cb_paste_task)
        ui.lb.bind("<F4>", self.cb_duplicate_task)
        ui.lb.bind("<F5>", self.cb_edit_task)
        ui.lb.bind("<F6>", self.cb_set_date)
        ui.lb.bind("<F7>", self.cb_toggle_task_done)
        ui.lb.bind("<F8>", self.cb_toggle_task_urgent)
        ui.lb.bind("<F9>", self.cb_toggle_task_archive)
        ui.bind("<F10>", self.cb_refresh)
        ui.bind("<F11>", self.cb_open_console)
        ui.bind("<F12>", self.cb_toggle_display)
        ui.bind("<Escape>", self.cb_display_help)
        ui.lb.bind("<space>", self.cb_display_task)
        ui.lb.bind("<n>", self.cb_copy_notes)
        ui.fb.src.bind("<Return>", self.cb_filter)
        ui.lb.bind("<Double-Button-1>", self.cb_edit_task)
        ui.lb.bind("<Button-3>", self.cb_display_task)
        ui.lb.bind("<Button-2>", self.cb_toggle_task_urgent)
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
    run = start_to_do_app()
