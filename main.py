import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from ttkbootstrap import Style
from ttkbootstrap.toast import ToastNotification
from tkextrafont import Font
import sqlite3
import time
import random


def main():
    #Tkinter
    global root
    root = tk.Tk()
    
    root.title("Quick Flashcards")
    root.geometry('700x500')
    root.resizable(False, False)
    root.iconphoto(False, tk.PhotoImage(file="img/icon.png"))

    #DataBase

    # database location
    database = "db/SetData.db"

    # queries to create our tables
    sql_create_sets_table = "CREATE TABLE IF NOT EXISTS sets(id INTEGER PRIMARY KEY, name TEXT UNIQUE, description TEXT, create_date TEXT);"
    sql_create_content_table = '''CREATE TABLE IF NOT EXISTS cards (
                                    set_name TEXT NOT NULL,
                                    word TEXT NOT NULL,
                                    answer TEXT NOT NULL,
                                    knowledge TEXT  DEFAULT "unknown" NOT NULL,
                                    PRIMARY KEY (set_name, word),
                                    FOREIGN KEY (set_name)
                                        REFERENCES sets (name)
                                        ON DELETE CASCADE
                                  );'''


    # creating the connection with database
    global cur
    conn, cur = create_connection(database)
    cur.execute("PRAGMA foreign_keys = ON;")


    # creating tables
    if conn is not None:
        create_table(conn, sql_create_sets_table)
        create_table(conn, sql_create_content_table)
    else:
        print("Error! Cannot create the database connection.")
        return

    # adding new fonts
    Font(file="font/Diphylleia-Regular.ttf", family="Diphylleia")
    Font(file="font/WorkSans-LightItalic.ttf", family="WorkSans")

    # applying style to the GUI elements
    style = Style(theme="darkly")
    style.configure('TLabel', font=('WorkSans', 16))
    style.configure('TButton', font=('WorkSans', 16), width=15)
    style.configure('TNotebook.Tab', font=('WorkSans', 14))


    # creating a notebook widget to manage tabs
    notebook = ttk.Notebook(root)

    # adding frames/tabs to notebook
    set_frame = sets_frame(ttk.Frame(notebook))
    learn_frame = learn(ttk.Frame(notebook))

    notebook.add(set_frame, text="Sets")
    notebook.add(learn_frame, text="Learn")

    notebook.pack(fill='both', expand=True, padx=5, pady=5)
    

    root.mainloop()

    # commiting the changes in database
    conn.commit()

    # outputting table names in my database
    res = cur.execute("SELECT name FROM sqlite_master")
    print(res.fetchall())

    # outputting data from sets table
    res = cur.execute("SELECT * FROM sets")
    print(res.fetchall())

    res = cur.execute("SELECT * FROM cards")
    print(res.fetchall())

    # closing database connection
    conn.close()


# this function is for the first tab "Sets" in my app
def sets_frame(frame):

    # destroying everything in the frame
    clear_frame(frame)


    # this function is for creating new set and importing it to database
    def create_set_frame(frame):

        clear_frame(frame)

        # variables for holding the input from user
        set_name = tk.StringVar(None)
        set_description = tk.StringVar()

        #GUI
        ttk.Label(frame, text="").pack()
        ttk.Label(frame, text="Set Name:").pack(fill='x',padx=150, pady=10)

        name = ttk.Entry(frame, font=('WorkSans', 16), textvariable=set_name)
        # focus on the first entry
        name.focus()
        name.pack(fill='x',padx=150, pady=5)

        ttk.Label(frame, text="").pack()

        ttk.Label(frame, text="Description:").pack(fill='x',padx=150, pady=10)
        ttk.Entry(frame, font=('WorkSans', 16), textvariable=set_description).pack(fill='x',padx=150, pady=5)
        ttk.Label(frame, text="").pack()
        
        ttk.Button(frame, text="Create", cursor="hand2", command=lambda: success_text(set_name.get(), set_description.get(), name)).pack(pady=10)
        ttk.Button(frame, text="Return", cursor="hand2", bootstyle="outline", command=lambda: sets_frame(frame)).pack(pady=10)


        # this function is for adding set to DB and informing user if it was successful or not
        def success_text(set_name, set_description, name):

            # if user click's 'create' without giving a name to set
            if(len(set_name) == 0):

                # changing the look of the 'name' entry on wrong user input and poping up a notification about it
                name.configure(bootstyle="danger")
                notification = ttk.Label(frame, text="Please provide set name!", bootstyle="inverse-danger", width=25, anchor="center")
                notification.place(x=350, y=30)
                # here I'm making the notification disappear after 1,5 seconds (1500 ms)
                root.after(1500, notification.destroy)
            

            # trying to insert our data that we collected from user to database
            else:

                # parameters for database
                params = (set_name, set_description, time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()))

                try:

                    # inserting parameters to 'sets' table in DataBase
                    cur.execute("INSERT INTO sets (name, description, create_date) VALUES(?,?,?)", params)
                    clear_frame(frame)
                    ttk.Label(frame, text="Set was created succesfully!\nTo add new cards to set, click \"Return\" and choose \"Edit Set\"", anchor="center", justify=tk.CENTER).pack(expand=True)
                    ttk.Button(frame, text="Return", cursor="hand2", command=lambda: sets_frame(frame)).pack(pady=50)

                except Exception as e:
                    
                    clear_frame(frame)
                    ttk.Label(frame, text="Ups! Something went wrong!\nI was not able to create your set:(\nCheck out if the set does not already exist", justify=tk.CENTER).pack(expand=True)
                    ttk.Button(frame, text="Return", cursor="hand2", command=lambda: sets_frame(frame)).pack(pady=50)


    # this function is for making changes in already created set (add word, delete word, delete whole set)
    def edit_set(frame):

        clear_frame(frame)
        
        # getting information about our sets from DB, and importing it to combobox
        set_names = cur.execute("SELECT name FROM sets")
        set_names = set_names.fetchall()
        """ the reason for code below is because DB returns values in set, when a value is separated by space
        for example set name "French A2" then combobox is showing it like "{Frenchh A2}". Which makes harder other
        functions, like deleting set from DB, because the DB does not recognize set name such as {Frenchh A2}.
        Code below resolves this problem """
        set_names = [item for result in set_names for item in result if item]

        # combobox with set names in it
        combobox = ttk.Combobox(frame, state="readonly", cursor="hand2", font=('WorkSans', 16), width= 15, values=set_names)
        combobox.set("Choose Set")
        combobox.pack(pady=50)
        
        ttk.Button(frame, text="Add Card", cursor="hand2", command=lambda:add_card(combobox, frame)).pack(pady=10)
        ttk.Button(frame, text="Delete Card", cursor="hand2", command=lambda:delete_card(combobox, frame)).pack(pady=10)
        ttk.Button(frame, text="Return", cursor="hand2", bootstyle="outline", command=lambda: sets_frame(frame)).pack(pady=10)
        ttk.Label(frame).pack()
        ttk.Button(frame, text="Destroy Set", cursor="hand2", bootstyle="danger", command=lambda:destroy_set(frame, combobox, set_names)).pack(expand=True)

        # here we are checking out if the user choose set from combobox
        def no_set_name(name):

            if name == "Choose Set":
                combobox.configure(bootstyle="danger")
                combobox.bind("<Button-1>", lambda x:combobox.configure(bootstyle="default"))
                return True
            
            else:
                return False
            
        # this function is for inserting new cards to our set
        def add_card(combobox, frame):
            # get the selected value from combobox
            selected_set = combobox.get()

            global root

            # here we are checking if user choose a value or left the default "Choose Set" value
            if no_set_name(selected_set) == False:
                clear_frame(frame)
                
                ttk.Label(frame, text="").pack(pady=20)
                ttk.Label(frame, text="Question:").pack(fill='x',padx=150, pady=10)

                word = tk.Entry(frame, font=('WorkSans', 16), width=10)
                word.focus()
                word.pack(fill='x',padx=150, pady=5)
                ttk.Label(frame, text="").pack()
                ttk.Label(frame, text="Answer:").pack(fill='x',padx=150, pady=10)
                answer = tk.Entry(frame, font=('WorkSans', 16), width=10)
                answer.pack(fill='x',padx=150, pady=5)

                ttk.Label(frame, text="").pack()
                ttk.Button(frame, text="Add", cursor="hand2", command=lambda:import_to_database(selected_set, word.get(), answer.get(), frame)).pack(pady=10)
                ttk.Button(frame, text="Return", cursor="hand2", bootstyle="outline", command=lambda: edit_set(frame)).pack(pady=10)

            # importing card to our database
            def import_to_database(selected_set, word, answer, frame):

                global root
                params = (selected_set, word, answer)

                # checking if user left entry areas empty, if so, then pop up error message
                if len(word) == 0 or len(answer) == 0:
                    notification = ttk.Label(frame, text="Please provide full card details!", bootstyle="inverse-danger", width=25, anchor="center")
                    notification.place(x=350, y=30)
                    root.after(1500, notification.destroy)
                    
                else:
                    try:
                        cur.execute("INSERT INTO cards (set_name, word, answer) VALUES(?,?,?)", params)
                        notification = ttk.Label(frame, text="Success!", bootstyle="inverse-success", width=10, anchor="center")
                        notification.place(x=550, y=30)
                        root.after(1500, notification.destroy)
                        clear_inputs()

                    except Exception as e:
                        notification = ttk.Label(frame, text="Card already exists!", bootstyle="inverse-warning", width=20, anchor="center")
                        notification.place(x=410, y=30)
                        root.after(1500, notification.destroy)
            
            # clearing entry areas
            def clear_inputs():
                word.delete(0, tk.END)
                answer.delete(0, tk.END)

        # this function enables deleting card from set
        def delete_card(combobox, frame):

            # get the chosen set name from combobox
            selected_set = combobox.get()

            if no_set_name(selected_set) == False:

                clear_frame(frame)

                # get all cards in chosen set from database
                set_cards = cur.execute("SELECT word FROM cards WHERE set_name = ?", (selected_set,))
                set_cards = set_cards.fetchall()
                set_cards = [item for result in set_cards for item in result if item]

                ttk.Label(frame).pack()
                ttk.Label(frame, text=("Set: "+selected_set), bootstyle="inverse-dark").pack(pady=10)
                
                # this combobox lets the user to choose or write the card they want to delete
                del_combo = ttk.Combobox(frame, cursor="hand2", font=('WorkSans', 16), width= 15, values=set_cards)
                del_combo.pack(pady=20)
                # set the default value in combobox
                del_combo.set("Choose Card")
                # on click in combobox with left button of the mouse, any value in combobox will disappear
                del_combo.bind("<Button-1>", lambda x:del_combo.set(""))

                ttk.Button(frame, text="Delete Card", cursor="hand2", bootstyle="danger", command=lambda:update_db(selected_set, del_combo, set_cards)).pack(pady=30)
                ttk.Label(frame, text="").pack()
                ttk.Button(frame, text="Return", cursor="hand2", bootstyle="outline", command=lambda: edit_set(frame)).pack(side=tk.BOTTOM, pady=40)



            def update_db(set, combobox, cards):
                # get the card name from combobox
                word = combobox.get()

                # check if the name, that user provided is valid
                if word in cards:

                    try:
                        # delete the card from card table in DB
                        query = "DELETE FROM cards WHERE set_name=? AND word=?"
                        cur.execute(query, (set, word))
                        notification = ttk.Label(frame, text="Deleted!", bootstyle="inverse-success", width=10, anchor="center")
                        notification.place(x=550, y=30)
                        root.after(1500, notification.destroy)
                    
                    except:
                        print("I was not able to delete the chosen card")

                    # delete the value in combobox entry and remove the card name from combobox value list
                    combobox.set("")
                    cards.remove(word)
                    combobox.configure(values=cards)
                    

                else:
                    combobox.configure(bootstyle = "danger")
                    notification = ttk.Label(frame, text="Choose a card!", bootstyle="inverse-warning", anchor="center", width=15)
                    notification.place(x=490, y=30)
                    root.after(1500, notification.destroy)

        # delete the whole set, with all it's cards
        def destroy_set(frame, combobox, set_names):
            
            # pop up a window to confirm destroying the set
            def proceed_window(set_name):
                return messagebox.askokcancel(f"Destroy Set", "Are you sure?\nYou will lose all cards in this set!")

            set_name = combobox.get()

            if no_set_name(set_name) == False:
                if proceed_window(set_name) == True:

                    query = "DELETE FROM sets WHERE name=?"
                    
                    cur.execute(query, (set_name,))

                    set_names.remove(set_name)
                    combobox.configure(values=set_names)
                    combobox.set("Choose Set")


    ttk.Button(frame, text="Create New Set", cursor="hand2", command=lambda: create_set_frame(frame)).place(relx=0.5, rely=0.4, anchor="center")
    ttk.Button(frame, text="Edit Set", cursor="hand2",command=lambda: edit_set(frame)).place(relx=0.5, rely=0.6, anchor="center")

    return frame


# this function is for the second tab "Learn" in my app
def learn(frame):

    """ 
        origin: after getting the information about set names from DB and importing to learn combobox,
        I found out, that after creating a new set, it will not show up in that combobox.
        So my solution was to get data from DB, every time, a user clicks the learn combobox with the left mouse button.
        That's why "learn_combobox_update()" function exists.
    """
    def learn_combobox_update(combobox):

        # getting information about our sets from DB, and importing it to combobox
        set_names = cur.execute("SELECT name FROM sets")
        set_names = set_names.fetchall()
        set_names = [item for result in set_names for item in result if item]

        #updating combobox values parameter
        combobox.configure(values=set_names)


    # this function gets data from "cards" set depending on the set_name and knowledge level
    def get_values(name, knowledge):
        cards = cur.execute("SELECT word FROM cards WHERE set_name=? AND knowledge=?", (name, knowledge))
        cards = cards.fetchall()
        cards = [item for result in cards for item in result if item]

        return cards
    

    """ 
        here I am separating data in to three lists depending on the knowledge level. Each list has different
        occurebce change. Less known cards will appear more often than known cards.
    """
    def learning_phase(combobox, frame):

        set_name = combobox.get()

        clear_frame(frame)

        known_cards = list(get_values(set_name, "known"))
        medium_cards = get_values(set_name, "medium")
        unknown_cards = list(get_values(set_name, "UNKOWN"))

        seqs = [known_cards, medium_cards, unknown_cards]
        """ 
            here we are choosing one random card, from weighted lists. 
            First it was returning all cards from list,
            thats why I am using asterisk(*)
        """

        card = random.choice(*random.choices(seqs, weights=(0, 0, 100), k=1))

        card_area = tk.Canvas(frame, width=650, height=350, border=4, cursor="hand2")
        card_area.config(bg='gray')
        card_area.pack(pady=20)
        text_item = card_area.create_text(650/2,350/2, width=600, text=card, fill="black", font="Worksans 24", anchor="center", justify="center")

        button_bad = ttk.Button(frame, text="Bad", state="disabled")
        button_bad.pack(side="left", padx=20)

        button_not_bad = ttk.Button(frame, text="Not bad", state="disabled")
        button_not_bad.pack(side="left")

        button_good = ttk.Button(frame, text="Good", state="disabled")
        button_good.pack(side="left", padx=20)

        buttons = [button_bad, button_not_bad, button_good]

        card_area.bind("<Button-1>", lambda x:reveal_answer(set_name, card, card_area, text_item, buttons))



    def reveal_answer(set:str, name: str, canvas:tk.Canvas, text_item, buttons):
        query = "SELECT answer FROM cards WHERE set_name=? AND word=?"

        answer = cur.execute(query, (set, name)).fetchone()

        canvas.configure(cursor="")

        canvas.itemconfig(text_item, text=answer)
        for button in buttons:
            button.configure(state="enabled", cursor="hand2")

    clear_frame(frame)
    
    ttk.Label(frame).pack(pady=67)

    # combobox for letting the user select learning set
    combobox = ttk.Combobox(frame, cursor="hand2", font=('WorkSans', 16), width= 15, state="readonly")
    combobox.pack()
    combobox.set("Choose Set")
    # on left mouse button click, call the "learn_combobox_update" function
    combobox.bind("<Button-1>", lambda x:learn_combobox_update(combobox))
    
    ttk.Button(frame, text="START", cursor="hand2", command=lambda: learning_phase(combobox, frame)).pack(pady=50)

    return frame



# clearing all frame by destroying its children
def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()
    

# find the center of the Canvas
def findXCenter(canvas, item):
      coords = canvas.bbox(item)
      xOffset = (700 / 2) - ((coords[2] - coords[0]) / 2)
      return xOffset


# connect (create if does not exists) with DB
def create_connection(db_file):

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(e)

    return conn


# creating table
def create_table(conn, create_table_sql):
    try:
        cur.execute(create_table_sql)
    except Exception as e:
        print(e)



if __name__ == "__main__":
    main()

    

    