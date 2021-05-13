import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from math import floor
import sys
from image_viewer import ImageViewer
from file_management import FileManagement
from markings import GridMark, Marker, GridIgnored
import config

class Application(tk.Frame):
    """The main hub window for viewing and editing the gridfile.
    
    The Main Application consists of three main aspects: A scrollable canvas to view the image, 
    a top toolbar, and a bottom tool to track and jump to whatever grid square you are on. This window has all the main
    functionalities such as creating clickable markers, opening new folders, jumping and tracking grid squares, and opening the
    biondi body image viewer.
    
    Attributes:
        master (tk.Tk): This is a copy of the root and used as the main window.
        mousex (tk.IntVar): Used to store the x mouse position on the image.
        mousey (tk.IntVar): Used to store the y mouse position on the image.
        coord_label (tk.Label): Displays the current x and y position of the mouse on the image using the 
            mousex and mouse y vars.
        body_count (tk.IntVar): Number of biondi bodies saved.
        body_count_label (tk.Label): Displays the number of biondi bodies saved.
        canvas (tk.Canvas): Used to hold and display the image.
        marker_canvas (tk.Canvas): A copy of canvas; used to store and display the clickable grid markings.
        grid_canvas (tk.Canvas): A copy of canvas; used to store and display the 7x7 grid overlay.
        vbar (tk.Scrollbar): The vertical scrollbar used to scroll canvas.
        hbar (tk.Scrollbar): The horizontal scrollbar used to scroll canvas.
        path (str: The inputed used folder path directory).
        folder_path (str): Path with a slash added. This is so we can access different components in the folder easier
            (don't have to re add slash every time).
        image (PIL Image): The image object to which the gridfile image is assigned to.
        width (int): The width of the image.
        height (int): The height of the image.
        container (tkinter rectangle): Used to enclose the image; allows scrolling on the canvas.
        rows (int): 7 rows; used as a var to create the grid overlay.
        columns (int): 7 columns; used as a var to create the grid overlay.
        toolbar (tk.Frame): object that is attributed to storing and displaying the top toolbar.
        grid_window (tk.Frame): object that is attributed to storing and displaying the bottom grid square tracker.
        all_bodies (list): List of all possible biondi bodies.


    Typical usage example:
        i = Application(root, path=path)
    """
    def __init__(self, mainframe, path):
        self.master = mainframe

        #initializes the main frame
        tk.Frame.__init__(self, master=mainframe)
        self.master.title('Imaris Screenshot Tool')

        self.folder_path = path + "/"
        
        #coord bar
        self.mousex = tk.IntVar(value = 0)
        self.mousey = tk.IntVar(value = 0)
        self.coord_label = tk.Label(self.master, text = "X: {0}  Y: {1}".format(self.mousex.get(), self.mousey.get()))
        self.coord_label.grid(row = 3, column = 0, sticky = "sw")

        # body count
        try:
            self.body_count = tk.IntVar(value = FileManagement(self.folder_path).count_bodies(config.all_bodies, False, False, False, False))
        except: # incase the case is not initiated
            error_screen = tk.Toplevel()
            error_screen.focus_get()
            error_label1 = tk.Label(error_screen, text = "Unable to open file. May not be initialized.")
            error_label2 = tk.Label(error_screen, text = "Press okay to exit the system.")
            error_label1.grid(row = 0, column = 0, sticky = 'nswe')
            error_label2.grid(row = 2, column = 0, sticky = 'nswe')

            close_button = tk.Button(error_screen, text = "OK", command = lambda: sys.exit())
            close_button.grid(row = 3, column = 0, sticky = 's')
        self.body_count_label = tk.Label(self.master, text = "{0} Bodies Annotated".format(self.body_count.get()))
        self.body_count_label.grid(row = 3, column = 0 , sticky = "se")
        self.update_count()
        
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self.master, highlightthickness=0)
        self.marker_canvas = self.canvas
        self.grid_canvas = self.canvas
        
        self.canvas.grid(row = 1, column = 0, sticky = 'nswe')
        self.grid_canvas.grid(row = 1, column = 0, sticky = 'nswe')
        self.marker_canvas.grid(row=1, column = 0, sticky = 'nswe')
        
        self.canvas.update()  # wait till canvas is created

        vbar = tk.Scrollbar(self.master, orient='vertical', command = self.canvas.yview)
        hbar = tk.Scrollbar(self.master, orient='horizontal', command = self.canvas.xview)
        vbar.grid(row=1, column=1, sticky='ns')
        hbar.grid(row=2, column=0, sticky='we')
        self.canvas.configure(xscrollcommand = hbar.set, yscrollcommand = vbar.set, xscrollincrement = '2', yscrollincrement = '2')
        self.canvas.update()

        
        # Make the canvas expandable
        self.master.rowconfigure(1, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Bind events to the Canvas
        self.canvas.bind('<MouseWheel>', self.verti_wheel)
        self.canvas.bind('<Shift-MouseWheel>', self.hori_wheel)  
        self.canvas.bind('<Button-3>', self.open_popup)
        self.canvas.bind('<Motion>', self.update_coords)


        self.image = Image.open(self.folder_path + "gridfile.jpg")  # open image
        self.width, self.height = self.image.size

        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)

        self.show_image()

        #self.master.geometry(str(600) + "x" + str(600))
        
        self.rows = 7
        self.columns = 7
        self.create_grid()
        
        self.initiate_markers()
        
        #option bar
        self.option_bar = OptionBar(self.master, self.folder_path, self.marker_canvas, self.grid_canvas)
        self.option_bar.grid(row = 0, column = 0, sticky = 'nswe')
        
        #grid window
        grid_window = GridWindow(self.master, self.canvas, self.folder_path, self.width, self.height)
        grid_window.grid(row = 4, column = 0)
        
    def create_grid(self):
        """Creates the grid overlay.
        
        Creates a 7x7 white grid overlay that is placed on top of canvas. 
        The grid overlay is stored in grid_canvas. size of the grid overlay scales
        with the image size using box_height and box_width.
        """
        box_width =  round(self.width / self.columns)
        box_height = round(self.height / self.rows)
        num_v_lines = self.rows - 1
        num_h_lines = self.rows - 1
        
        #for loops go through 7 times each creating equally spaced lines
        for i in range(0, num_v_lines): 
            self.grid_canvas.create_line(box_width * (i+1), 0, box_width * (i+1), self.height,
                                        fill = "cyan", width = 2, tag = "line")
        for i in range(0, num_h_lines):
            self.grid_canvas.create_line(0, box_height * (i+1), self.width, box_height * (i+1),
                                        fill = "cyan", width = 2, tag = "line")
            
        num_squares = self.rows * self.columns
        
        if round(box_width / 5) > round(box_height / 5):
            padding = round(box_height / 5)
        else:
            padding = round(box_width / 5)
            
        key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        n = 0
        for i in range(0, self.rows): #for loop that runs 49 times to create appropriatly scaled grid letters
            for j in range(0, self.columns):
                self.grid_canvas.create_text((j + 1) * box_height - padding, (i + 1) * box_width - padding,
                                            font = ("Calibri", 24, "bold"), fill = 'cyan', text = key[n], tag = "letter")
                n += 1
                if n > num_squares:
                    break

    def initiate_markers(self):
        """Initializes marker info in FileManagment.
    
        Creates a marker for every body on the application's startup. Iterates
        through the bodies in the database to do so. Also creates a marker for
        every ignored marker
        """
        data = FileManagement(self.folder_path).query_images(config.all_bodies, False, False, False, False)
        for i in data:
            body_info = {}
            x = 0
            for choice in ("time", "body_name", "body_number", "x", "y"):
                body_info[choice] = i[x]
                x += 1
            GridMark(self.marker_canvas, self.folder_path, body_info)
        
        # generates ignored markers
        ignored = FileManagement(self.folder_path).query_all_ignored()
        for coord in ignored:
            GridIgnored(self.marker_canvas, self.folder_path, coord[0], coord[1])
            
    def open_new_folder(self):
        """Opens a new folder with its respective image and Markings."""
        path = filedialog.askdirectory()
        i = Application(root, path=path)

    def update_count(self):
        self.body_count.set(FileManagement(self.folder_path).count_bodies(config.all_bodies, False, False, False, False))
        self.body_count_label.configure(text = "{0} Bodies Annotated".format(self.body_count.get()))
        self.master.after(2000, self.update_count)
        
    def update_coords(self, event):
        """ Event method that updates mouse position on the image

        Activates on mouse movement. Gets current x y canvas position of the mouse. 
        Sets those values on the coord_label.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.mousex.set(x)
        self.mousey.set(y)

        self.coord_label.configure(text = "X: {0}  Y: {1}".format(self.mousex.get(), self.mousey.get()))
        self.coord_label.update()

    def open_popup(self, event):
        """Event method that opens up the Marker popup.

        x and y are the coords of where the mouse clicked. Then converted to canvas coordinates
        which is used to add a marker.
        """
        x = event.x
        y = event.y
        canvas_x = self.marker_canvas.canvasx(x)
        canvas_y = self.marker_canvas.canvasy(y)
        
        Marker(self.master, canvas_x, canvas_y, self.marker_canvas, self.height, self.width, self.columns, self.rows, self.folder_path)

    def verti_wheel(self, event):
        """Event method that scrolls the image vertically using the mousewheel.

        Scrolls the image 20 units up or down depending on the direction of the mousewheel input.
        """
        if event.num == 5 or event.delta == -120:  # scroll down
            self.canvas.yview('scroll', 20, 'units')
        if event.num == 4 or event.delta == 120:
            self.canvas.yview('scroll', -20, 'units')

    def hori_wheel(self, event):
        """Event method that scrolls the image horizontally using shift + mousewheel.

        Scrolls the image 20 units left or right depending on the direction of the mousewheel.
        """
        if event.num == 5 or event.delta == -120:  # scroll down
            self.canvas.xview('scroll', 20, 'units')
        if event.num == 4 or event.delta == 120:
            self.canvas.xview('scroll', -20, 'units')

    def show_image(self):
        """Displays the image on canvas

        Configures a scroll region on canvas (allows it to be scrollable) and sets the dimensions to
        self.container (has the witdh and height of the image). ImageTk.PhotoImage allows pngs and jpgs to be
        displayed. 
        """
        self.canvas.configure(scrollregion=self.canvas.bbox(self.container))  # set scroll region
        image = self.image
        imagetk = ImageTk.PhotoImage(image)
        imageid = self.canvas.create_image(0,0,anchor= 'nw', image=imagetk) #glues the image to the topleft of the place where the image is stored.
        self.canvas.lower(imageid)  # set image into background
        self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

class GridWindow(tk.Frame):
    """The grid square tool located at the bottom of Application
    
    Used to scroll between grid squares based on the file's unique randomized grid order. 
    You can mark grids as complete and jump to grid squares on the image without having to scroll.
    
    Attributes:
        master (tk.Tk): The current instance of Application's master is stored here.
        main_canvas (tk.Canvas): The current instance of Application's canvas is stored here.
        folder_path (str): The path directory of the current opened folder.
        final_order (list): The randomized grid order unique to the folder.
        width (int): The width of the image in Application.
        height (int): The height of the image in Application.
        rows (int): Seven rows of grid squares.
        columns (int): Seven columns of grid squares.
        i (int): The current index of the final_order list.
        v (tk.StringVar): The variable used to store the current grid square in the current_grid label.
        text (tk.Label): The label which displays the text "current grid square:".
        current_grid (tk.Label): The label which displays v, the current grid square.
        forward_button (tk.Button): Calls the forward method.
        backward_button (tk.Button): Calls the backward method.
        jumpto_button (tk.Button): Calls the move_canvas method.

    Typical usage example:
        grid_window = GridWindow(root, canvas, folder_path, width, height)
    """
    def __init__(self, master, main_canvas, folder_path, width, height):
        tk.Frame.__init__(self)
        self.master = master
        self.main_canvas = main_canvas
        self.folder_path = folder_path
        self.final_order = FileManagement(self.folder_path).get_grid()
        self.width = width
        self.height = height
        self.rows = 7
        self.columns = 7
        
        bools = [i[1] for i in self.final_order] # creates a list of just the booleans of whether grid is finished
        self.i = next((i for i, j in enumerate(bools) if j == False), 0) # finds the first instance of false and jumps to that
        
        self.v = tk.StringVar()
        self.v.set(str(self.final_order[self.i][0]))
        self.text = tk.Label(self, text = "Current Grid Square:")
        self.text.grid(row = 0, column = 1)
        self.current_grid = tk.Label(self, text = self.v.get())
        self.current_grid.grid(row = 1, column = 1)

        self.forward_button = tk.Button(self, text = ">", command = self.forward)
        self.forward_button.grid(row=2, column = 2)
        

        self.backward_button = tk.Button(self, text = "<", command = self.backward)
        self.backward_button.grid(row=2, column = 0)

        self.jumpto_button = tk.Button(self, text = "Jump to", command = self.move_canvas)
        self.jumpto_button.grid(row = 2, column  = 1)
        
        self.make_check_button()

    def make_check_button(self):
        """Checkbox that marks a grid square as complete.

        stores if the grid is finished in var_fin. On mark, the method update_finished is called.
        """
        self.var_fin = tk.IntVar()
        self.var_fin.set(self.final_order[self.i][1])
        self.finished = tk.Checkbutton(self, text = "Finished", variable = self.var_fin,
                                        onvalue = 1, offvalue = 0, command = lambda y = self.final_order[self.i][0]: self.update_finished(y))
        self.finished.grid(row = 3, column = 1)
        
    def update_finished(self, grid_id):
        """Updates the database of a finished grid square.

            Sends the grid square over to the database to be marked as complete and be remembered for future 
            use of the folder

            Args:
                grid_id (str): The grid square letter marked as complete

        """
        fin = self.var_fin.get()
        FileManagement(self.folder_path).finish_grid(grid_id, fin)
        self.final_order = FileManagement(self.folder_path).get_grid()

    def get_scrollx(self):
        """Figures out the amount of x units that need to be scrolled to a grid square.

        w is the base amount of scrolling per one grid tile. The return statment calculates how far the grid is
        on the x axis and scales it with w.
        """
        total_squares = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvw"
        index = total_squares.find(self.final_order[self.i][0])
        self.w = self.width / self.columns
        return (index % self.columns) * self.w

    def get_scrolly(self): #look at later
        """Figures out the amount of y units that need to be scrolled to a grid square

        Uses the ASCII number of a character to calculate where in the grid it is to get the
        amount to scroll on y. 
        """
        c = self.final_order[self.i][0]
        self.h = self.height / self.rows
        if c.islower():
            index = ord(c) - 96 + 26
        else:
            index = ord(c) - 64
        
        if index % 7 == 0: # rows - 1 to ensure the right edge does not drop down a row
            scrolly = (index / 7 - 1) * self.h
        else:
            scrolly = floor(index / (self.rows)) * self.h 
        return scrolly    

    def move_canvas(self):
        """Scrolls the canvas to the current grid square.

        Moves the canvas view based on the amounts of scrollx and scrolly.
        """
        scrollx = self.get_scrollx()
        scrolly = self.get_scrolly()

        offsetx = +1 if scrollx >= 0 else 0
        offsety = +1 if scrolly >= 0 else 0
        self.main_canvas.xview_moveto(float(scrollx + offsetx)/self.width)
        self.main_canvas.yview_moveto(float(scrolly + offsety)/self.height)
        # self.master.geometry("600x600")
        
    def forward(self):
        """Moves forward to the next grid square in final_order.

        Increases i by 1 and updates the Label text and checkbuttons.
        """
        if self.i < len(self.final_order) -1:
            self.i += 1 
        self.v.set(str(self.final_order[self.i][0]))
        
        self.current_grid.configure(text = self.v.get())
        self.current_grid.update()
        
        self.finished.destroy()
        self.make_check_button()

    def backward(self): 
        """Moves backward to the previous grid square in final_order

        Decreases i by 1 and updates the Label text and checkbuttons
        """
        if self.i > 0:
            self.i -= 1 
        self.v.set((self.final_order[self.i][0]))
        self.current_grid.configure(text = self.v.get())
        self.current_grid.update()
        
        self.finished.destroy()
        self.make_check_button()

class OptionBar(tk.Frame):
    """The toolbar located at the top of Application
    
    Has two main functions: File and View. The File dropdown can open a new folder, export biondi body images, 
    and close the application. The View dropdown menu can open the biondi body image viewer, reset the window size, 
    toggle the grid lines on and off, toggle the grid letters on and off, sort marker buttons based on body type, and 
    sort marker buttons based on secondary body type (GR, MAF, MP).
    
    Attributes:
        master (tk.Tk): The current instance of Application's master is stored here.
        folder_path (str): the path directory of the current opened folder.
        marker_canvas (tk.Canvas): Application's marker_canvas is stored here.
        grid_canvas (tk.Canvas): Application's grid_canvas is stored here.
        new_folder_path (tk.StringVar): Where a folder path would be stored if user opens a new folder.
        case_name (tk.StringVar): Case name user would input if they export images.
        grid_var (tk.BooleanVar): Stores whether grid lines should be hidden or not.
        letter_var (tk.BooleanVar): Stores whether grid letters should be hidden or not.
        file_b (tk.MenuButton): The object to which the File dropdown button is assigned to.
        file_menu (tk.Menu): The object to which the File dropdown options are assigned to.
        view_b (tk.MenuButton): The object to which the View dropdown button is assigned to.
        view_menu (tk.Menu): The object to which the View dropwdown options are assigned to.
        body_menu (tk.Menu): The object to which the primary body options are assigned to 
            (sublist of view_menu).
        choices (dict): Stores the options in all_bodies as checkbuttons.
        secondary_menu (tk.Menu): The object to which the secondary body name options are assigned to
            (sublist of view_menu).
        secondary (list): The options for secondary_menu.
        secondary_choices (dict): Stores the options in secondary as checkbuttons.

    Typical usage example:
        OptionBar = OptionBar(root, folder_path, marker_canvas, grid_canvas)
    """
    def __init__(self, master, folder_path, marker_canvas, grid_canvas):
        tk.Frame.__init__(self)
        self.master = master
        self.folder_path = folder_path
        self.marker_canvas = marker_canvas
        self.grid_canvas = grid_canvas
        
        self.new_folder_path = tk.StringVar(value = "")
        self.case_name = tk.StringVar(value = "")
        self.grid_var = tk.BooleanVar(value = True)
        self.letter_var = tk.BooleanVar(value = True)
        self.ignored_var = tk.BooleanVar(value = True)
        
        # file menu
        file_b = tk.Menubutton(self, text = "File", relief = "raised")
        file_menu = tk.Menu(file_b, tearoff = False)
        file_b.configure(menu = file_menu)
        file_b.pack(side = "left")
        
        file_menu.add_command (label = "Open New Folder", command = self.open_new_folder)
        file_menu.add_command(label = "Export Images", command = self.export_images)
        file_menu.add_command(label = "Exit", command = root.quit)
        
        # edit menu
        edit_b = tk.Menubutton(self, text = "Edit", relief = "raised")
        edit_menu = tk.Menu(edit_b, tearoff = False)
        edit_b.configure(menu = edit_menu)
        edit_b.pack(side = "left")
        
        edit_menu.add_command(label = "Add Ignored Marker", command = self.add_ignored)
        
        # view menu
        view_b = tk.Menubutton(self, text = "View", relief = "raised")
        view_menu = tk.Menu(view_b, tearoff = False)
        view_b.configure(menu = view_menu)
        view_b.pack(side = "left")
        
        view_menu.add_command(label = "Open Image Viewer", command = self.open_image_viewer)
        view_menu.add_command(label = "Set Window to Original Size", command = self.original_size)
        view_menu.add_checkbutton(label = "Show Grid", variable = self.grid_var, onvalue = True,
                                  offvalue = False, command = self.show_grid)
        view_menu.add_checkbutton(label = "Show Letters", variable = self.letter_var, onvalue = True,
                                  offvalue = False, command = self.show_letter)
        view_menu.add_checkbutton(label = "Show Ignored", variable = self.ignored_var, onvalue = True,
                                  offvalue = False, command = self.show_ignored)
        
        body_menu = tk.Menu(view_menu, tearoff = False)
        self.choices = {}
        for choice in config.all_bodies:
            self.choices[choice] = tk.BooleanVar(value = True)
            body_menu.add_checkbutton(label=choice, variable=self.choices[choice], 
                                onvalue = True, offvalue = False, command = self.show_select_markers)
        view_menu.add_cascade(label = "Show Bodies", menu = body_menu)
        
        secondary_menu = tk.Menu(view_menu, tearoff = False)
        self.secondary = ["GR", "MAF", "MP", "unsure"]
        self.secondary_choices = {}
        for choice in self.secondary:
            self.secondary_choices[choice] = tk.BooleanVar(value = False)
            secondary_menu.add_checkbutton(label=choice, variable=self.secondary_choices[choice], 
                                onvalue = False, offvalue = True, command = self.show_select_markers)
        view_menu.add_cascade(label = "Show Secondary", menu = secondary_menu)
        
        
    def open_new_folder(self):
        """Opens a new instance of Application.

            Opens a new instance of Application using a folder from file explorer.
        """
        path = filedialog.askdirectory()
        i = Application(root, path=path)
        
    def export_images(self):
        """Exports biondi body images.

            Exports current biondi body images (combines markings with screenshots), takes in the Case Name 
            from the user, and allows the user to select where the images can be exported through a browse folder path
            button.
        """
        export = tk.Toplevel()
        export.transient(root)
        export.title("Export")
        # export.geometry("300x130")
        export.columnconfigure(2, weight = 1)
        
        name = tk.Label(export, text = "Case Name:")
        name.grid(row = 1, column = 0, padx =10, pady = 10, sticky = "nsew")
        
        name_entry = tk.Entry(export, textvariable = self.case_name)
        name_entry.grid(row = 1, column = 1, padx =10, pady = 10, sticky = "nsew")
        
        folder_entry = tk.Entry(export, textvariable = self.new_folder_path)
        folder_entry.grid(row = 2, column = 0, padx =10, pady = 10, sticky = "nsew")
        
        def select_folder():
            """Selects folder where exported images should go.

                Gets the image path from file explorer on click of the browse button.
            """
            path = filedialog.askdirectory()
            if path == "":
                return
            else:
                self.new_folder_path.set(path + "/")
                folder_entry.update()
            
        folder_button = tk.Button(export, text = "Browse", command = select_folder)
        folder_button.grid(row = 2, column = 1, padx = 10, pady = 10, sticky = "w")
        
        def confirm():
            """Exports images to folder_path.

            Takes case name and folder path and exports biondi images to the designated folder.
            """
            if self.case_name.get() == "" or self.new_folder_path.get() == "/":
                return
            else:
                FileManagement(self.folder_path).export_case(self.new_folder_path.get(), self.case_name.get())
                export.destroy()
        
        ok_button = tk.Button(export, text = "Okay", command = confirm)
        ok_button.grid(row = 3, column = 1, padx = 10, pady = 10, sticky = "e")
        
    def add_ignored(self):
        def create_ignored_marker(event):
            """Event method that adds an ignored marker.

            x and y are the coords of where the mouse clicked. Then converted to canvas coordinates
            which is used to add a marker.
            """
            x = event.x
            y = event.y
            canvas_x = self.marker_canvas.canvasx(x)
            canvas_y = self.marker_canvas.canvasy(y)
            coords = (canvas_x, canvas_y)
            
            GridIgnored(self.marker_canvas,self.folder_path, canvas_x, canvas_y)
            FileManagement(self.folder_path).add_ignored(coords)
            
        def reset(event):
            self.marker_canvas.configure(cursor = "")
            self.marker_canvas.unbind("<Button-1>")
            self.marker_canvas.unbind("<ButtonRelease-1>")
        
        self.marker_canvas.configure(cursor = "cross")
        self.marker_canvas.bind('<Button-1>', create_ignored_marker)
        self.marker_canvas.bind('<ButtonRelease-1>', reset)
    
    def open_image_viewer(self):
        """Opens the biondi body image viewer.

        Calls the ImageViewer class in image_viewer.py.
        """
        ImageViewer(self.folder_path, self.marker_canvas) #TEST CLASS
    
    def original_size(self):
        """Resets the Application window to the original size.

        Changes the Application window to the original 600 by 600 size using
        master.
        """
        self.master.geometry("600x600")
        
    def show_grid(self):
        """Toggles grid lines on and off."""
        if self.grid_var.get() == False: 
            self.grid_canvas.itemconfigure("line", state = "hidden")
        else:
            self.grid_canvas.itemconfigure("line", state = "normal")
            
    def show_letter(self):
        """Toggles grid letters on and off."""
        if self.letter_var.get() == False:
            self.grid_canvas.itemconfigure("letter", state = "hidden")
        else:
            self.grid_canvas.itemconfigure("letter", state = "normal")
            
    def _get_body_selection(self):
        """Gets what options in body_selection are markes as True.

        Used with show_select_markers. Goes thru list and appends which ever options are 
        True to choices.
        """
        body_selection = []
        for name, var in self.choices.items():
            if var.get() == True:
                body_selection.append(name)
        return body_selection
    
    def _get_secondary_selection(self):
        """Gets what options in secondary are markes as True.

        Used with show_select_markers. Goes thru list and appends which ever options are 
        True to secondary_choices.
        """
        secondary_selection = []
        for name, var in self.secondary_choices.items():
            x = var.get()
            secondary_selection.append(x)
        return secondary_selection
            
    def show_select_markers(self):
        """Toggles which markers get shown based on the filter

        Takes seconday_selection and body_selection and shows the markers based on those requirements
        from FileManagement.
        """
        all_data = FileManagement(self.folder_path).query_images(config.all_bodies, False, False, False, False)
        for i in all_data:
            self.grid_canvas.delete("m" + str(i[0]))
        
        bodies = self._get_body_selection()
        secondary_selection = self._get_secondary_selection()
        
        data = FileManagement(self.folder_path).query_images(bodies, secondary_selection[0], secondary_selection[1], 
                               secondary_selection[2], secondary_selection[3])
        for i in data:
            body_info = {}
            x = 0
            for choice in ("time", "body_name", "body_number", "x", "y"):
                body_info[choice] = i[x]
                x += 1
            GridMark(self.marker_canvas, self.folder_path, body_info)
            
    def show_ignored(self):
        ignored = FileManagement(self.folder_path).query_all_ignored()
        if self.ignored_var.get() == False:
            for coords in ignored:
                tag = "i{0}{1}".format(coords[0], coords[1])
                self.marker_canvas.delete(tag)
        else:
            for coords in ignored:
                GridIgnored(self.marker_canvas,self.folder_path, coords[0], coords[1])
            

class OpeningWindow:
    def __init__(self, master):
        self.master = master
        # self.master.geometry("580x100")
        self.master.title("Imaris Screenshot Tool")

        w1 = "Welcome to the Imaris Screenshot Tool!"
        w2 = "If you are returning to a previous session, please click on the \"Open Previous Folder\" button."
        w3 = "If you are starting a new session, please create an empty folder and select it using the \"Initiate Folder\" button."

        self.welcome_label1 = tk.Label(self.master, text = w1)
        self.welcome_label1.grid(row = 0, column = 2, sticky = 'nswe')
        
        self.welcome_label2 = tk.Label(self.master, text = w2)
        self.welcome_label2.grid(row = 2, column = 2, sticky = 'nswe')
        
        self.welcome_label3 = tk.Label(self.master, text = w3)
        self.welcome_label3.grid(row = 3, column = 2, sticky = 'nswe')
        
        self.button_frame = tk.Frame(self.master)
        self.button_frame.grid(row = 4, column = 2, sticky = 'ns')

        self.find_image_button = tk.Button(self.button_frame, text="Open Previous Folder", command = lambda: self.open_image())
        self.find_image_button.pack(side = "left", padx = 2 , pady = 2)
        
        self.initiate_folder_button = tk.Button(self.button_frame, text = "Initiate Folder", command = self.initiate_folder)
        self.initiate_folder_button.pack(side = "left", padx = 2 , pady = 2)
    
    def open_image(self):
        """Opens initial Application and destroys initial window assess

        Creates Application and destroys initial assets so they do not interfere with
        the Application class.
        
        Args:
            welcome_label1 (tk.Label): Label of text used to welcome user into the program.
            welcome_label2 (tk.Label): Label of text used to welcome user into the program.
            welcome_label3 (tk.Label): Label of text used to welcome user into the program.
            welcome_label4 (tk.Label): Label of text used to welcome user into the program.
            button_frame (tk.Frame): Frame containing buttons in the opening window.
        """
        path = filedialog.askdirectory()
        if path == "":
            return
        self.welcome_label1.destroy()
        self.welcome_label2.destroy()
        self.welcome_label3.destroy()
        self.button_frame.destroy()
        i = Application(root, path=path)

    def confirm_function(self, name, folder_path, file_path, nf):
        """Initializes a new folder and creates a success label

        Calls FileManagement to initate a folder with a grid image file 
        and annotator initials. Creates a success window on completion.
        
        Args:
            folder_path (str): Path to folder where images will be saved selected from the askdirectory.
            file_path (str): Path to the gridfile image to be copied into the saving folder.
            nf (tk.Toplevel): Toplevel window to select the folder path and file path.
        """
        if folder_path == "" or file_path == "" or name == "":
            return
        
        nf.destroy()

        FileManagement(folder_path + "/").initiate_folder(file_path, name)
        
        done_screen = tk.Toplevel()

        success_label1 = tk.Label(done_screen, text = "Folder sucessfully initialized!")
        success_label1.grid(row = 0, column = 0, sticky = 'nswe')

        def init_confirm():
            done_screen.destroy()
            self.welcome_label1.destroy()
            self.welcome_label2.destroy()
            self.welcome_label3.destroy()
            self.button_frame.destroy()
            i = Application(root, path = folder_path)
            
        close_button = tk.Button(done_screen, text = "OK", command = lambda: init_confirm())
        close_button.grid(row = 3, column = 0, sticky = 's')

    def initiate_folder(self):
        """Creates a Window for inputting args to initialize folder

        Creates a window and corresponding buttons and entry fields for users
        to enter in data to initialize a folder for biondi body analysis.
        """
        nf = tk.Toplevel()
        # nf.geometry("365x165")
        nf.transient(root)

        folder_path = tk.StringVar()
        folder_ebox = tk.Entry(nf, textvariable = folder_path, width = 50)
        folder_ebox.grid(row = 1, column = 0)
        
        folder_button = tk.Button(nf, text = "Browse...", command = lambda: folder_path.set(filedialog.askdirectory()))
        folder_button.grid(row = 1, column = 1)

        file_name = tk.StringVar()
        file_ebox = tk.Entry(nf, textvariable = file_name, width = 50)
        file_ebox.grid(row = 4, column = 0)

        file_button = tk.Button(nf, text = "Browse...", command = lambda: file_name.set(filedialog.askopenfilename()))
        file_button.grid(row = 4, column = 1)

        name = tk.StringVar()
        name_ebox = tk.Entry(nf, textvariable = name, width = 50)
        name_ebox.grid(row = 6, column = 0)

        confirm_button = tk.Button(nf, text = "Confirm", command = lambda: self.confirm_function(name.get(), folder_path.get(), file_name.get(), nf))
        confirm_button.grid(row = 8, column = 1)

        folder_label = tk.Label(nf, text = "Enter an empty folder directory:")
        folder_label.grid(row = 0, column = 0, sticky = 'w')

        file_label = tk.Label(nf, text = "Enter the grid file directory:")
        file_label.grid(row = 3, column = 0, sticky = 'w')

        name_label = tk.Label(nf, text = "Enter your initials (eg. BJ):")
        name_label.grid(row = 5, column = 0, sticky = 'w')
    
if __name__ == "__main__":
    root = tk.Tk()
    app = OpeningWindow(root)
    root.mainloop()