#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import gtk
import webkit
import gobject
import xml.dom.minidom
from xml.dom.minidom import Node
import time
import os
import sys
import crypt, random, string
import libcrypt
from sqlite3 import dbapi2 as sqlite

gobject.threads_init()

def responseToDialog(entry, dialog, response):
    dialog.response(response)

def dialog_info(info):
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_INFO,
        gtk.BUTTONS_OK,
        None)
    dialog.set_markup(info)
    dialog.show_all()
    dialog.run()
    dialog.destroy()

def dialog_get_password():
    dialog = gtk.MessageDialog(
        None,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_QUESTION,
        gtk.BUTTONS_OK,
        None)
    dialog.set_markup("""Please enter the <b>password</b>""")

    entry = gtk.Entry()
    entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
    hbox = gtk.HBox()
    hbox.pack_start(gtk.Label("Password:"), False, 5, 5)
    hbox.pack_end(entry)

    dialog.format_secondary_markup("This will be used for <i>identification</i> purposes")
    dialog.vbox.pack_end(hbox, True, True, 0)
    dialog.show_all()
    dialog.run()
    text = entry.get_text()
    dialog.destroy()
    return text

def accent2html(astring):
    values = {
        "à": "&agrave;",
        "è": "&egrave;",
        "ì": "&igrave;",
        "ò": "&ograve;",
        "ù": "&ugrave;",
        "À": "&Agrave;",
        "È": "&Egrave;",
        "Ì": "&Igrave;",
        "Ò": "&Ograve;",
        "Ù": "&Ugrave;",
        "!": "&#33;"
        }
    astring = astring.replace("&","&amp;")
    for lettera in values.keys():
        astring = astring.replace(lettera,values[lettera])
    return astring

def get_salt(chars = string.letters + string.digits):
    return random.choice(chars) + random.choice(chars)

def db2html(database="database.sql", password=None):
    if not os.path.exists("%s.dir/" % database):
        os.mkdir("%s.dir/" % database)
    adatabase = sqlite.connect(database)
    os.chdir("%s.dir/" % database)
    cursor =  adatabase.cursor()
    if not password:
        password = dialog_get_password()
        eget = cursor.execute("SELECT * FROM settings")
        for (key, value) in eget:
            if key == "salt":
                salt = value
            elif key == "password":
                check = value
        if not crypt.crypt(password,salt) == check:
            dialog_info("Your password is not correct!")
            sys.exit(1)
    eget = cursor.execute("SELECT * FROM pages")
    for (number, date, text ) in eget:
        xs = open("%s-%s.html" % (number, date), "w")
        xs.write("<html>\n%s</html>" % libcrypt.decrypt(text,password).decode("base64"))
        xs.close()
    dialog_info("diary converted in html pages")

class Page(object):
    def __init__(self):
        self.meta = dict()
        self.text = str()
        self.time = str()
        self.number = int()

    def set_page(self, text, date, number):
        self.text = text
        self.time = date
        self.number = number


class PagesManager(object):
    def __init__(self, database=None):
        self.pages = dict()
        self.settings = dict()
        self.__load_database(database)
        if self.settings["is_crypted"]:
            self.tmp_password = ""

    def __load_database(self, database=None):
        if not database:
            database = "./database.sql"
        self.database = sqlite.connect(database)
        self.cursor =  self.database.cursor()
        eget = self.cursor.execute("SELECT * FROM settings")
        for ( key, value ) in eget:
            if value == "True":
                self.settings[key] = True
            elif value == "False":
                self.settings[key] = False
            else:
                self.settings[key] = value
        
    def get_pages(self):
        eget = self.cursor.execute("SELECT * FROM pages")
        for (number, date, text ) in eget:
            self.pages[number] = Page()
            if self.settings["is_crypted"] and self.tmp_password:
                text = libcrypt.decrypt(text,self.tmp_password)
            try:
                self.pages[number].set_page(text.decode("base64"), date, number)
            except:
                self.pages[number].set_page(text, date, number)

    def make_page(self, text, date=None):
        if not date:
            date = time.strftime("%A %d %B %Y - %H:%M:%S")
        self.get_pages()
        num = len(self.pages.keys()) + 1
        if self.settings["is_crypted"] and self.tmp_password:
            text = libcrypt.crypt(text.encode("base64") ,self.tmp_password)
        self.cursor.execute( "INSERT INTO pages (number, date, text) VALUES ('%s', '%s', '%s')" % (num, date, text) )
        self.database.commit()
        self.get_pages()

    def check_passwd(self):
        if not crypt.crypt(self.tmp_password,self.settings["salt"]) == self.settings["password"]:
            return False
        return True

    def commit(self): self.database.commit()
    
    def close(self):
        self.database.commit()
        self.database.close()
    
class Gui(object):
    def __init__(self):
        self.manager = PagesManager()
        if self.manager.settings["is_crypted"]:
            self.manager.tmp_password = dialog_get_password()
            if not self.manager.check_passwd():
                dialog_info("Your password is not correct!")
                sys.exit(1)
        self.manager.get_pages()
        self.__number = len(self.manager.pages.keys()) + 1
        self.window = gtk.Window()
        self.window.set_title("Gread Diary")
        self.window.set_size_request(660,500)
        self.window.set_resizable(True)
        self.window.connect("destroy", self.destroy)
        self.__icon_new = self.window.render_icon(gtk.STOCK_NEW, gtk.ICON_SIZE_MENU)
        
        self.new_button = gtk.ToolButton(gtk.STOCK_NEW)
        self.new_button.connect("clicked", self.new)
        
        self.save_button = gtk.ToolButton(gtk.STOCK_SAVE)
        self.save_button.connect("clicked", self.save)

        self.convert_button = gtk.ToolButton(gtk.STOCK_CONVERT)
        self.convert_button.connect("clicked", self.__convert)


        self.back_button = gtk.ToolButton(gtk.STOCK_GO_BACK)
        self.back_button.connect("clicked", self.__go_back)
        self.forward_button = gtk.ToolButton(gtk.STOCK_GO_FORWARD)
        self.forward_button.connect("clicked", self.__go_forward)
        
        self.space_button_one = gtk.ToolItem()
        self.space_button_two = gtk.ToolItem()
        self.number_button = gtk.ToolItem()

        self.number_entry = gtk.Entry()
        self.number_entry.connect("activate", self.__change_page)
        
        self.number_button.add(self.number_entry)
        self.number_button.set_expand(False)
        self.space_button_one.set_expand(True)
        self.space_button_two.set_expand(True)

        self.panel_bar = gtk.Toolbar()
        self.panel_bar.add(self.back_button)
        self.panel_bar.add(self.space_button_one) 
        self.panel_bar.add(self.new_button)
        self.panel_bar.add(self.save_button)
        self.panel_bar.add(self.convert_button)
        self.panel_bar.add(self.space_button_two)
        self.panel_bar.add(self.number_button)
        self.panel_bar.add(self.forward_button)

        self.webkit = webkit.WebView()
        self.webkit.connect("populate-popup", self.__hide_menu)

        self.scroll_box = gtk.ScrolledWindow()
        self.scroll_box.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.scroll_box.add(self.webkit)

        self.__vbox = gtk.VBox(False, 0)
        self.__vbox.pack_start(self.scroll_box, True)
        self.__vbox.pack_start(self.panel_bar, False)
        self.window.add(self.__vbox)
        self.__disable_input()
        self.forward_button.set_sensitive(False)
        self.window.show_all()
        if len(self.manager.pages.keys()) >= 1:
            self.show_page(1)

    def __hide_menu(self, view, menu):
        if not self.webkit.get_editable():
            menu.destroy()

    def __change_page(self, view=None, menu=None): self.show_page(int(self.number_entry.get_text()))
        
    def __go_back(self, view=None, menu=None):
        self.show_page(self.__number - 1)

    def __convert(self, view=None, menu=None): db2html(password=self.manager.tmp_password)

    def __go_forward(self, view=None, menu=None):
        self.show_page(self.__number + 1)

    def new(self, widget=None, data=None):
        self.save_button.set_sensitive(True)
        self.webkit.load_string("", "text/html", "iso-8859-15", "new-page")
        self.webkit.set_editable(True)
        self.number_entry.set_editable(False)
        self.number_entry.set_text(str(len(self.manager.pages.keys())+1))
        self.__number = len(self.manager.pages.keys())+1
        self.back_button.set_sensitive(True)
        self.forward_button.set_sensitive(False)

    def save(self, widget=None, data=None):
        self.webkit.execute_script("document.title=document.documentElement.innerHTML;")
        text = accent2html(self.webkit.get_main_frame().get_title())
        self.manager.make_page(text)
        self.__number = len(self.manager.pages.keys())
        self.__disable_input()
        self.number_entry.set_editable(True)

    def __disable_input(self):
        self.webkit.set_editable(False)
        self.save_button.set_sensitive(False)

    def show_page(self, anumber):
        self.__disable_input()
        self.manager.get_pages()
        if int(anumber) >= len(self.manager.pages.keys()):
            anumber = len(self.manager.pages.keys())
            self.back_button.set_sensitive(True)
            self.forward_button.set_sensitive(False)
        elif int(anumber) <= 1:
            anumber = 1
            self.back_button.set_sensitive(False)
            self.forward_button.set_sensitive(True)
        else:
            self.back_button.set_sensitive(True)
            self.forward_button.set_sensitive(True)
        self.webkit.load_string("<html>\n%s</html>" % self.manager.pages[anumber].text, "text/html", "iso-8859-15", "new-page")
        self.__number = anumber
        self.number_entry.set_text(str(anumber))

    def quit(self, widget=None, data=None):
        self.destroy()

    def destroy(self, widget=None, data=None):
        self.manager.close()
        gtk.main_quit()

if __name__ == "__main__":
    if not os.path.isfile("database.sql"):
        print "Generating the database:",
        database = sqlite.connect("database.sql")
        cursor =  database.cursor()
        password = dialog_get_password()
        salt = get_salt()
        cursor.execute("CREATE TABLE pages (number INTEGER NOT NULL PRIMARY KEY, date TEXT NOT NULL, text TEXT NOT NULL)")
        cursor.execute("CREATE TABLE settings (key TEXT NOT NULL, value TEXT NOT NULL)")
        cursor.execute("INSERT INTO settings (key, value) VALUES ('is_crypted', 'True')")
        cursor.execute("INSERT INTO settings (key, value) VALUES ('salt', '%s')" % salt)
        cursor.execute("INSERT INTO settings (key, value) VALUES ('password', '%s')" % crypt.crypt(password,salt) )
        database.commit()
        database.close()
        print "done"
    c = Gui()
    gtk.main()
