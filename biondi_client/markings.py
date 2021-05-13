import tkinter as tk
from tkinter import ttk
from image_viewer import ImageViewer
from screenshot import LilSnippy
from file_management import FileManagement
from time import time
from math import floor
import config
class Marker(tk.Frame):
    """The popup prompt to create a marker.
    
    A popup prompt which collects a series of body information that is later
    entered in the database. This also starts the screenshot tool for further
    data collection.
    
    Attributes:
        master (tk.Frame): Mainframe of the application.
        x (int): X position of the mouse.
        y (int): Y position of the mouse.
        marker_canvas (tk.Canvas): The canvas holding all the markers.
        height (int): The height of the gridfile image.
        width (int): The width of the gridfile image.
        columns (int): The number of columns in the grid.
        rows (int): The number of rows in the grid.
        canvas_x (int): X position of the mouse relative to the canvas.
        canvas_y (int): Y position of the mouse relative to the canvas.
        folder_path (str): Directory of the folder where images are saved.
        annotator (str): The name of the annotator.
        body_type (str): The type of biondi body.
        var_GR (bool): True if the body has a green ring.
        var_MAF (bool): True if the body has multi-autoflouresence.
        var_MP (bool): True if the body has multi-prong.
        var_unsure (bool): True if the user is unsure.
        grid_id (char): The grid letter of the mouse click.
        notes (str): Any extra notes the user entered.
        
    Typical usage example:
        Marker(master, x, y, marker_canvas, height, width, columns, rows, folder_path)
    """
    def __init__(self, master, canvas_x, canvas_y, marker_canvas, height, width, columns, rows, folder_path):
        self.master = master
        self.marker_canvas = marker_canvas
        self.height = height
        self.width = width
        self.columns = columns
        self.rows = rows
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        self.folder_path = folder_path
        
        self.annotator = tk.StringVar(value = FileManagement(self.folder_path).get_annotator_name())
        self.body_type = tk.StringVar()
        self.body_type.set("drop")
        self.var_GR = tk.BooleanVar()
        self.var_MAF = tk.BooleanVar()
        self.var_MP = tk.BooleanVar()
        self.var_unsure = tk.BooleanVar()
        self.grid_id = self.get_grid(self.canvas_x, self.canvas_y)
        self.notes = tk.StringVar()
        
        marker = tk.Toplevel() #create window
        marker.title("popup")
        marker.grab_set()
        
        dropdown = ttk.Combobox(marker, values = config.all_bodies, textvariable = self.body_type)
        grC = tk.Checkbutton(marker, text = "GR", anchor ="w", variable = self.var_GR, onvalue = True, offvalue = False)
        mafC = tk.Checkbutton(marker, text = "MAF", anchor ="w", variable = self.var_MAF, onvalue = True, offvalue = False)
        mpC = tk.Checkbutton(marker, text = "MP", anchor ="w", variable = self.var_MP, onvalue = True, offvalue = False)
        unsure = tk.Checkbutton(marker, text = "UNSURE", variable = self.var_unsure, onvalue = True, offvalue = False)
        note_label = tk.Label(marker, text = "Notes:")
        note_entry = tk.Entry(marker, textvariable = self.notes)
        button_ok = tk.Button(marker, text = "OK", padx = 5, pady = 5, anchor = "se", command = lambda: self.draw(marker))
        annotator_entry = tk.Entry(marker, textvariable = self.annotator)
        
        dropdown.grid(row = 0, column = 0)
        grC.grid(row = 0, column = 1, sticky = 'w')
        mafC.grid(row = 1, column = 1, sticky = 'w')
        mpC.grid(row = 2, column = 1, sticky = 'w')
        unsure.grid(row = 0, column = 2)
        note_label.grid(row = 3, column = 0)
        note_entry.grid(row = 3, column = 1)
        button_ok.grid(row = 4, column = 2)
        annotator_entry.grid(row = 4, column = 0)
        

    def get_data(self):
        """Retrieves user inputs.
        
        Takes the user inputs from the popup and enters them into a data dictionary.
        This dictionary is later entered into the database.
        """
        time_added = int(time())
        body_file_name = str(self.body_type.get()) + "_" + str(time_added)
        annotation_file_name = body_file_name + "_ANNOTATION"
        fm = FileManagement(self.folder_path)
        
        data = {"time": time_added,
                "annotator_name": self.annotator.get(),
                "body_name": self.body_type.get(),
                "body_number": fm.count_bodies([self.body_type.get()], False, False, False, False) + 1,
                "x": self.canvas_x,
                "y": self.canvas_y,
                "grid_id": self.grid_id,
                "GR": self.var_GR.get(),
                "MAF": self.var_MAF.get(),
                "MP": self.var_MP.get(),
                "unsure": self.var_unsure.get(),
                "notes": self.notes.get(),
                "body_file_name": body_file_name + ".png",
                "annotation_file_name": annotation_file_name + ".png",
                "angle": None,
                "log": None,
                "dprong1": None,
                "lprong2": None
                }
        return data
        
    def get_grid(self, x, y):
        """Converts the mouse position into a grid id.
        
        Args:
            x (int): The canvas x of the mouse.
            y (int): The canvas y of the mouse.
        """
        row_num = floor(y / (self.height / self.rows))
        column_num = floor(x / (self.width / self.columns))
        key = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        return key[(row_num * self.columns) + column_num]

    
    def call_screenshot(self, data):
        """Calls LilSnippy to take a screenshot.
        
        Args:
            data (dict): The collection of data collected from the user entries.
        """
        app = LilSnippy(self.master, data, self.folder_path, self.marker_canvas)
        app.create_screen_canvas()
        
    def draw(self, marker):
        """Function called when the user presses ok to close the marker window.
        
        Args:
            marker (tk.Toplevel): The window of buttons and entries to collect data.
        """
        data = self.get_data()
        marker.destroy()
        self.call_screenshot(data)


class GridMark():
    """Creates a clickable marking on the gridfile.
    
    When called, this creates a marker on the mouse position which can be clicked
    to open the imageviewer and show the correlating image.
    
    Attributes:
        marker_canvas (tk.Canvas): Canvas where markers are stored.
        folder_path (str): Path to the folder where images are saved.
        time (int): Unix time of the selected body.
        
    Typical Usage Example:
        GridMark(marker_canvas, folder_path, body_info)
    """
    def __init__(self, marker_canvas, folder_path, body_info):
        self.marker_canvas = marker_canvas
        self.folder_path = folder_path
        body_name = body_info["body_name"]
        x = body_info["x"]
        y = body_info["y"]
        self.time = body_info["time"]
        tag = "m{0}".format(self.time)
        self.marker_canvas.create_text(x, y, font = ("Calibri", 18, "bold"), fill = 'WHITE', activefill = "red",
                                       text = config.body_index[body_name], tag = tag)
        
        self.marker_canvas.tag_bind(tag, '<ButtonPress-1>', self._on_click)
        self.marker_canvas.update 
        
    def _on_click(self, event):
        ImageViewer(self.folder_path, self.marker_canvas).open_file(self.time)
        
class GridIgnored():
    """Creates a clickable ignored marker.
    
    Generates a marker_canvas marker that shows if something is being 
    ignored for the time being.
    
    Attributes:
        marker_canvas (tk.Canvas): Canvas where markers are stored.
        folder_path (str): Path to the folder where images are saved.
        canvas_x (int) Canvas x coordinate where the user clicked
        canvas_y (int): Canvas y coordinate where the user clicked
    
    Typical Usage Example:
    GridIgnored(marker_canvas, folder_path, canvas_x, canvas_y)
    """
    def __init__(self, marker_canvas, folder_path, canvas_x, canvas_y):
        self.marker_canvas = marker_canvas
        self.folder_path = folder_path
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y
        
        self.tag = "i{0}{1}".format(canvas_x, canvas_y)
        self.marker_canvas.create_text(canvas_x, canvas_y, font = ("Calibri", 24, "bold"), fill = 'magenta', activefill = "red",
                                       text = "X", tag = self.tag)
        
        self.marker_canvas.tag_bind(self.tag, '<ButtonPress-1>', self._on_click)
        self.marker_canvas.update 
        
    def _on_click(self, event):
        self.marker_canvas.delete(self.tag)
        coords = (self.canvas_x, self.canvas_y)
        FileManagement(self.folder_path).delete_ignored(coords)
