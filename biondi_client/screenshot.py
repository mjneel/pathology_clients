import tkinter as tk
import pyautogui
from PIL import ImageTk, Image, ImageDraw, ImageFont
from tkinter.colorchooser import askcolor
from file_management import FileManagement
import config
import math
import time
class ScreenshotEditor(tk.Toplevel):
    """A basic image editor for image markups.
    
    This class is used to initialize a new window with options to annotate
    the taken screenshot from LilSnippy/Image Viewer. Tools include paint brush,
    select color, move location text, undo, redo, and save
    
    Attributes:
        body_info (dict): A collection of all relevant body information for use
            in different functions.
        folder_path (str): The string directory to the selected folder for saving.
        marker_canvas (tk.Canvas): Canvas where markers are saved on the gridfile.
        im (PIL image): An image file of the screenshot.
        img (tk PhotoImage): An image file of the screenshot.
        width (int): The width of the screenshot.
        height (int): The height of the screenshot.
        new (Bool): True if the image inputted is new and False if the image inputted
        is from the Image Viewer.
        annotation (PIL image): Empty image where the annotations are saved for a separate
            file.
        draw (PIL drawing): Pillow drawing for creating markups on annotation.
        screenshot_frame (tk.Frame): Frame where the screenshot canvas is stored.
        screenshot_canvas (tk.Canvas): The canvas where the image is created and shown.
        toolbar_frame (tk.Frame): The frame where tool buttons are stored.
        old_x (int): The x position of the mouse prior. Used in drawing lines.
        old_y (int): The y position of the mouse prior. Used in drawing lines.
        line_width (int): Line width of the markup lines
        color (str): The color of the markup lines.
        text_annotation (str): The string placed on the image.
        margin (int): The distance from the end to the text position
        
    Typical usage example:
        ScreenshotEditor(body_info, folder_path, marker_canvas, im, new)   
    """
    def __init__(self, body_info, folder_path, marker_canvas, im, new):
        tk.Toplevel.__init__(self)
        self.title("Screenshot Editor")
        self.body_info = body_info
        self.folder_path = folder_path
        self.marker_canvas = marker_canvas
        self.im = im
        self.img = ImageTk.PhotoImage(im)
        self.width = self.img.width()
        self.height = self.img.height()
        self.new = new
        
        self.annotation = Image.new("RGBA", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.annotation) #initialize a pillow drawing that runs in the background for saving annotations
        
        self.focus_set()
        self.grab_set()
        
        self.screenshot_frame = tk.Frame(self)
        self.screenshot_frame.grid(row = 1, column = 0)
        
        self.create_screenshot_canvas()

        self.toolbar_frame = tk.Frame(self)
        self.toolbar_frame.grid(row=0, column = 0, sticky = "nsew")
        
        self.create_toolbar()
        
        self.setup()

    def setup(self):
        """Initializes a series of attributes and binds.
        
        Different variables used for annotations are initialized in here. Button clicks
        are bound for drawing lines to markup the image.
        """
        self.old_x = None
        self.old_y = None
        self.line_width = 3
        self.color = 'white'
        self.active_button = self.brush_button # remembers the previously activated button
        self.screenshot_canvas.bind('<B1-Motion>', self.paint)
        self.screenshot_canvas.bind('<ButtonRelease-1>', self.reset)

        self.text_annotation = "{0} {1}, {2}".format(self.body_info["grid_id"], self.body_info["x"], self.body_info["y"])
        
        # find the appropriate margin for the text
        if self.width > self.height: 
            self.margin = .05 * self.height
        else:
            self.margin = .05 * self.width
        
        # creates first text location
        self.screenshot_canvas.create_text(self.margin, self.margin, text = self.text_annotation, 
                                font =("Calibri", 14), anchor = "nw", fill = 'white', tag ="text") 
        
    def create_screenshot_canvas(self):
        """Creates the screenshot canvas.
        
        Creates a canvas where the image is stored. All lines drawn that the user 
        can see are also stored on this canvas.
        """
        self.screenshot_canvas = tk.Canvas(self.screenshot_frame, width = self.width, height = self.height,
                                    borderwidth = 0, highlightthickness = 0)
        self.screenshot_canvas.pack(expand = True)
        self.screenshot_canvas.create_image(0, 0, image = self.img, anchor = "nw")
        self.screenshot_canvas.img = self.img
        self.screenshot_canvas.focus_set()
        
    def create_toolbar(self):
        """Creates the buttons on the toolbar.
        
        Initializes and places a series of buttons which end up as the tool
        selection on the top toolbar.
        """
        self.brush_button = tk.Button(self.toolbar_frame, text = "brush", command = self.use_brush)
        self.brush_button.grid(row = 0, column = 0)
        
        self.color_button = tk.Button(self.toolbar_frame, text = 'color', command = self.choose_color)
        self.color_button.grid(row = 0, column = 1)
        
        self.undo_button = tk.Button(self.toolbar_frame, text = 'clear canvas', command = self.clear)
        self.undo_button.grid(row = 0, column = 2)
        
        self.text_button = tk.Button(self.toolbar_frame, text = "top-left", command = self.text)
        self.text_button.grid(row = 0, column = 3)

        self.save_button = tk.Button(self.toolbar_frame, text = 'save', command = self.save)
        self.save_button.grid(row = 0, column = 4)
        
    def use_brush(self):
        """Function used the activate the brush from the button"""
        self.activate_button(self.brush_button)
        
        self.screenshot_canvas.unbind("<B1-Motion>")
        self.screenshot_canvas.unbind("<ButtonRelease-1>")
        
        self.screenshot_canvas.bind('<B1-Motion>', self.paint)
        self.screenshot_canvas.bind('<ButtonRelease-1>', self.reset)
        
    def activate_button(self, some_button):
        """Keeps brush button sunken as it is used.
        
        Configures the button to maintain being sunken/raised as its used.
        
        """
        self.active_button.config(relief = "raised")
        some_button.config(relief = "sunken")
        self.active_button = some_button
        
    def choose_color(self):
        """Allows user to choose a color for lines.
        
        Initaites a color chooser for users to select a color for the annotations.
        """
        self.color = askcolor(color = self.color, parent = self.toolbar_frame)[1]

    def paint(self, event):
        """Create paint lines.
        
        Creates an annotation line for marking around where the biondi body is. used
        as a callback function when the paint tool is selected.
        """
        if self.old_x and self.old_y: # if the mouse has already been clicked
            self.screenshot_canvas.create_line(self.old_x, self.old_y, event.x, event.y, 
                                    width = self.line_width, fill = self.color, 
                                    capstyle = "round", smooth = True, splinesteps = 36, 
                                    tag='line') 
            # draws on the pillow annotation image for saving later
            self.draw.line((self.old_x, self.old_y, event.x, event.y), fill = self.color, 
                            width = self.line_width, joint = "curve")
        self.old_x = event.x
        self.old_y = event.y
        
    def reset(self, event):
        """Resets coordinates to create a new line.
        
        Callback function used to reset the coordinates so that paint will 
        create a new line instead of connecting back up to the old.
        """
        self.old_x, self.old_y = None, None
        
    def text(self): # moves text around
        """Move text around the four corners
        
        Function used with the location button to move the text around the corners
        to avoid covering up bodies. Rewrites the text on the button to reflect
        the location the text is currently in.
        """
        if self.text_button['text'] == 'top-left':
            self.text_position(self.width - self.margin, self.margin, "ne")
            self.text_button.configure(text='top-right')
        elif self.text_button['text'] == 'top-right':
            self.text_position(self.margin, self.height - self.margin, "sw")
            self.text_button.configure(text='bottom-left')
        elif self.text_button['text'] == 'bottom-left':
            self.text_position(self.width - self.margin, self.height - self.margin, "se")
            self.text_button.configure(text='bottom-right')
        elif self.text_button['text'] == 'bottom-right':
            self.text_position(self.margin, self.margin, "nw")
            self.text_button.configure(text='top-left')
        
    def text_position(self, x, y, position):
        self.screenshot_canvas.delete('text')
        self.screenshot_canvas.create_text(x, y, text = self.text_annotation, 
                                font =("Calibri", 14), anchor = position, 
                                fill = 'white', tag ="text")
    def clear(self): 
        """Removes all line drawn.
        
        Used to clear the canvas to redo annotations if the user has messed up.
        """
        self.annotation = Image.new("RGBA", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.annotation)
        
        self.screenshot_canvas.delete('line') # deletes line all lines

    def save(self):
        """Commits the image and annotation to new files.
        
        Saves the image and annotation as png files with an alpha channel for merging
        later. If the image is new, it also adds it to the database.
        """
        # parameters for the PIL annotations done in tandem with the seen tkinter annotations
        self.font = ImageFont.truetype("calibrib.ttf", 20) 
        bounds = self.screenshot_canvas.bbox("text")
        self.draw.text((bounds[0], bounds[1]), fill = 'white', 
                        font = self.font, text = self.text_annotation) 
                        #takes the bottom left coordinate of text and places the text on the pillow drawing
        
        if self.new == True: # if the image is being saved from LilSnippy
            FileManagement(self.folder_path).save_image(self.body_info, self.im, self.annotation)
            from markings import GridMark
            GridMark(self.marker_canvas, self.folder_path, self.body_info)
        else: # if the annotations are being edited from Image Viewer
            self.annotation.save(self.folder_path + self.body_info["annotation_file_name"])
        
        self.destroy()
        
        number = FileManagement(self.folder_path).count_bodies(config.all_bodies, False, False, False, False)
        if number == 300: # opens a popup at 300 biondi bodies done
            done_screen = tk.Toplevel()
            done_screen.grab_set()
            success_label = tk.Label(done_screen, text = "You have finished annotating 300 bodies.")
            success_label.pack(side = 'top')

            close_button = tk.Button(done_screen, text = "OK", command = lambda: done_screen.destroy())
            close_button.pack(side = "bottom")
            
            
class Ringer(tk.Toplevel):
    def __init__(self, body_info, folder_path, marker_canvas, im, new):
        tk.Toplevel.__init__(self)
        self.title("Ringbell Tool")
        self.body_info = body_info
        self.folder_path = folder_path
        self.marker_canvas = marker_canvas
        self.im = im
        self.img = ImageTk.PhotoImage(im)
        self.width = self.img.width()
        self.height = self.img.height()
        self.new = new
        
        self.focus_set()
        self.grab_set()
        
        self.screenshot_frame = tk.Frame(self)
        self.screenshot_frame.grid(row = 1, column = 0)
        
        self.create_screenshot_canvas()

        self.toolbar_frame = tk.Frame(self)
        self.toolbar_frame.grid(row=0, column = 0, sticky = "nsew")
        
        self.create_toolbar()
        self.setup()
        
    def setup(self):
        """Initializes a series of attributes and binds.
        
        Different variables used for annotations are initialized in here. Button clicks
        are bound for drawing lines to markup the image.
        """
        self.old_x = None
        self.old_y = None
        
        self.d = None
        self.l = []
        self.line_width = 2
        self.color = 'white'
        self.active_button = self.d_button # remembers the previously activated button
        self.use_distance()
        
    def activate_button(self, some_button):
        """Keeps brush button sunken as it is used.
        
        Configures the button to maintain being sunken/raised as its used.
        
        """
        self.active_button.config(relief = "raised")
        some_button.config(relief = "sunken")
        self.active_button = some_button
        
    def create_toolbar(self):
        self.d_button = tk.Button(self.toolbar_frame, text = "distance", command = self.use_distance)
        self.d_button.grid(row = 0, column = 0)
        
        self.l_button = tk.Button(self.toolbar_frame, text = "length", command = self.use_length)
        self.l_button.grid(row = 0, column = 1)
        
        self.clear_button = tk.Button(self.toolbar_frame, text = "clear all", command = self.clear_all)
        self.clear_button.grid(row = 0, column = 2)
        
        self.ok_button = tk.Button(self.toolbar_frame, text = "ok", command = self.ok)
        self.ok_button.grid(row = 0, column = 3)
        
    def ok(self):
        if (self.l == []) | (self.d == None):
            return
        
        self.body_info["log"], self.body_info["dprong1"], self.body_info["lprong2"] = self.calc_log()
        if self.new:
            ScreenshotEditor(self.body_info, self.folder_path, self.marker_canvas, self.im, True)
        else:
            info = (self.body_info["body_name"], self.body_info["GR"], 
                    self.body_info["MAF"], self.body_info["MP"], 
                    self.body_info["unsure"], self.body_info["notes"], 
                    self.body_info["angle"], self.body_info["log"], 
                    self.body_info["dprong1"], self.body_info["lprong2"],
                    self.body_info["time"])
            FileManagement(self.folder_path).edit_info(info)
            
        self.destroy()
        
    def create_screenshot_canvas(self):
        """Creates the screenshot canvas.
        
        Creates a canvas where the image is stored. All lines drawn that the user 
        can see are also stored on this canvas.
        """
        self.screenshot_canvas = tk.Canvas(self.screenshot_frame, width = self.width, height = self.height,
                                    borderwidth = 0, highlightthickness = 0, cursor = "cross")
        self.screenshot_canvas.pack(expand = True)
        self.screenshot_canvas.create_image(0, 0, image = self.img, anchor = "nw")
        self.screenshot_canvas.img = self.img
        self.screenshot_canvas.focus_set()
    
    def use_distance(self):
        self.activate_button(self.d_button)
        
        self.screenshot_canvas.bind("<Button-1>", self.distance)
        self.screenshot_canvas.bind("<Button-3>", self.distance_reset)
        self.screenshot_canvas.bind("<Motion>", self.d_ghost_line)
        
        self.screenshot_canvas.delete("distance_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("d_text")
        
        self.old_x = None
        self.old_y = None
        
    def distance(self, event):
        coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasx(event.y))
        if self.old_x and self.old_y:
            
            self.screenshot_canvas.create_line(self.old_x, self.old_y, coords, width = self.line_width, fill = "purple",
                                               capstyle = "round", smooth = True, splinesteps = 36, tag = "distance_line")
            self.d = (self.old_x, self.old_y, coords[0], coords[1])
            
            self.screenshot_canvas.unbind("<Motion>")
            self.screenshot_canvas.unbind("<Button-3>")
            self.screenshot_canvas.unbind("<Button-1>")
            
            self.screenshot_canvas.bind("<Button-1>", self.distance_reset)
        self.old_x, self.old_y = coords
        
    def distance_reset(self, event):
        self.screenshot_canvas.delete("distance_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("d_text")
        
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.bind("<Button-1>", self.distance)
        self.screenshot_canvas.bind("<Button-3>", self.distance_reset)
        self.screenshot_canvas.bind("<Motion>", self.d_ghost_line)
        
        self.d = None
        self.old_x = None
        self.old_y = None
        
    def d_ghost_line(self, event):
        old_coords = (self.old_x, self.old_y)
        ghost_coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasy(event.y))
        if self.old_x and self.old_y: 
            self.screenshot_canvas.delete("ghost")
            self.screenshot_canvas.create_line(old_coords, ghost_coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "gray", width = self.line_width, tag = "ghost")
            distance = self.distance_form((old_coords[0], old_coords[1], ghost_coords[0], ghost_coords[1]))
            self.screenshot_canvas.delete("d_text")
            self.screenshot_canvas.create_text(ghost_coords[0] + 10, ghost_coords[1] + 10, fill = "white", font = "Calibri 12",
                                text = str(distance), tag = "d_text", anchor = "nw")
            
    def use_length(self):
        self.activate_button(self.l_button)
        
        self.screenshot_canvas.unbind("<Motion>")
        self.screenshot_canvas.unbind("<Button-3>")
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.delete("length_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("l_text")
        
        self.screenshot_canvas.bind("<Button-1>", self.length)
        self.screenshot_canvas.bind("<Button-3>", self.length_confirm)
        self.screenshot_canvas.bind("<Motion>", self.l_ghost_line)
        
        self.old_x = None
        self.old_y = None
        
    def length(self, event):
        coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasx(event.y))
        if self.old_x and self.old_y:
            self.screenshot_canvas.create_line(self.old_x, self.old_y, coords, width = self.line_width, fill = "cyan",
                                               capstyle = "round", smooth = True, splinesteps = 36, tag = "length_line")
            self.l.append((self.old_x, self.old_y, coords[0], coords[1]))
        self.old_x, self.old_y = coords
        
    def length_confirm(self, event):
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.unbind("<Motion>")
        self.screenshot_canvas.unbind("<Button-3>")
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.bind("<Button-1>", self.length_reset)
        
    def length_reset(self, event):
        self.screenshot_canvas.delete("length_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("l_text")
        
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.bind("<Button-1>", self.length)
        self.screenshot_canvas.bind("<Button-3>", self.length_confirm)
        self.screenshot_canvas.bind("<Motion>", self.l_ghost_line)
        
        self.l = []
        self.old_x = None
        self.old_y = None
            
    def l_ghost_line(self, event):
        old_coords = (self.old_x, self.old_y)
        ghost_coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasy(event.y))
        if self.old_x and self.old_y: 
            self.screenshot_canvas.delete("ghost")
            self.screenshot_canvas.create_line(old_coords, ghost_coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "gray", width = self.line_width, tag = "ghost")
            length = 0
            for x in self.l:
                length += self.distance_form(x)
            self.screenshot_canvas.delete("l_text")
            self.screenshot_canvas.create_text(ghost_coords[0] + 10, ghost_coords[1] + 10, fill = "cyan", font = "Calibri 12",
                                text = str(length), tag = "l_text", anchor = "nw")
            
    def distance_form(self, coords):
        distance = math.sqrt((coords[0] - coords[2])**2 + (coords[1] - coords[3])**2)
        
        return distance
        
    def calc_log(self):
        distance = self.distance_form(self.d)
        length = 0
        for x in self.l:
            length += self.distance_form(x)
            
        return round(math.log10(length / distance), 4), distance, length
    
    def clear_all(self):
        self.d = None
        self.l = []
        self.old_x = None
        self.old_y = None
        
        self.screenshot_canvas.delete("distance_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("d_text")
        self.screenshot_canvas.delete("length_line")
        self.screenshot_canvas.delete("l_text")
        
        if self.active_button == self.d_button:
            self.use_distance()
        else:
            self.use_length()
class Angler(tk.Toplevel):
    def __init__(self, body_info, folder_path, marker_canvas, im, new):
        tk.Toplevel.__init__(self)
        self.title("Angle Tool")
        self.body_info = body_info
        self.folder_path = folder_path
        self.marker_canvas = marker_canvas
        self.im = im
        self.img = ImageTk.PhotoImage(im)
        self.width = self.img.width()
        self.height = self.img.height()
        self.new = new
        
        self.curr_angle = None
        
        self.focus_set()
        self.grab_set()
        
        self.screenshot_frame = tk.Frame(self)
        self.screenshot_frame.grid(row = 1, column = 0)
        
        self.create_screenshot_canvas()

        self.toolbar_frame = tk.Frame(self)
        self.toolbar_frame.grid(row=0, column = 0, sticky = "nsew")
        
        self.create_toolbar()
        self.setup()
        
    def create_toolbar(self):
        self.a_button = tk.Button(self.toolbar_frame, text = "angle", command = self.use_angle)
        self.a_button.grid(row = 0, column = 0)
        
        self.p1_button = tk.Button(self.toolbar_frame, text = "prong 1", command = self.use_p1)
        self.p1_button.grid(row = 0, column = 1)
        
        self.p2_button = tk.Button(self.toolbar_frame, text = "prong 2", command = self.use_p2)
        self.p2_button.grid(row = 0, column = 2)
        
        self.clear_button = tk.Button(self.toolbar_frame, text = "clear all", command = self.clear_all)
        self.clear_button.grid(row = 0, column = 3)
        
        self.ok_button = tk.Button(self.toolbar_frame, text = "ok", command = self.ok)
        self.ok_button.grid(row = 0, column = 4)
        
    def ok(self):
        if (self.curr_angle == None) | (self.p1 == []) | (self.p2 == []):
            return
        else:
            self.body_info["angle"] = self.curr_angle
            self.body_info["dprong1"] = self.calc_dist(self.p1)
            self.body_info["lprong2"] = self.calc_dist(self.p2)
        
        if self.new:
            ScreenshotEditor(self.body_info, self.folder_path, self.marker_canvas, self.im, True)
        else:
            info = (self.body_info["body_name"], self.body_info["GR"], 
                    self.body_info["MAF"], self.body_info["MP"], 
                    self.body_info["unsure"], self.body_info["notes"], 
                    self.body_info["angle"], self.body_info["log"], 
                    self.body_info["dprong1"], self.body_info["lprong2"], self.body_info["time"])
            FileManagement(self.folder_path).edit_info(info)
            
        self.destroy()
        
    def create_screenshot_canvas(self):
        """Creates the screenshot canvas.
        
        Creates a canvas where the image is stored. All lines drawn that the user 
        can see are also stored on this canvas.
        """
        self.screenshot_canvas = tk.Canvas(self.screenshot_frame, width = self.width, height = self.height,
                                    borderwidth = 0, highlightthickness = 0, cursor = "cross")
        self.screenshot_canvas.pack(expand = True)
        self.screenshot_canvas.create_image(0, 0, image = self.img, anchor = "nw")
        self.screenshot_canvas.img = self.img
        self.screenshot_canvas.focus_set()
        
    def setup(self):
        self.prev_axis_angle = 0
        self.prev_angle = 0
        self.passed = False
        self.rotation = False
        
        self.points = []
        self.old_x = None
        self.old_y = None
        
        self.p1 = []
        self.p2 = []
        
        self.prong1 = None
        self.prong2 = None
        
        self.line_width = 2
        self.length_color = "cyan"
        self.active_button = self.a_button
        self.use_angle()
        
    def activate_button(self, some_button):
        """Keeps brush button sunken as it is used.
        
        Configures the button to maintain being sunken/raised as its used.
        
        """
        self.active_button.config(relief = "raised")
        some_button.config(relief = "sunken")
        self.active_button = some_button
        
    def use_angle(self):
        self.activate_button(self.a_button)
        
        self.screenshot_canvas.bind("<Button-1>", self.angle_tool)
        self.screenshot_canvas.bind("<Motion>", self.a_ghost_line)
        
        self.screenshot_canvas.delete("angle_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("angle_text")
        
        self.old_x = None
        self.old_y = None
        self.prev_axis_angle = 0
        self.prev_angle = 0
        self.passed = False
        self.rotation = False
        self.points = []
        
    def angle_tool(self, event):
        # first point selected
        coords= (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasy(event.y))
        old_coords = (self.old_x, self.old_y)
        
        if self.old_x and self.old_y:
            self.screenshot_canvas.create_line(old_coords, coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "white", width = 5, tag = "angle_line")
        self.old_x, self.old_y = coords
        self.points.append(coords)
        
        if len(self.points) == 2: # if only one line is drawn
            time.sleep(.1)
            self.screenshot_canvas.bind("<Motion>", self.calc_angle)
        elif len(self.points) == 3:
            self.screenshot_canvas.unbind("<Button-1>")
            self.screenshot_canvas.unbind("<Motion>")
            
            self.screenshot_canvas.bind("<Button-1>", self.angle_reset)
        
    def a_ghost_line(self, event):
        # gray line indicating where angle is
        old_coords = (self.old_x, self.old_y)
        ghost_coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasy(event.y))
        if self.old_x and self.old_y: 
            self.screenshot_canvas.delete("ghost")
            self.screenshot_canvas.create_line(old_coords, ghost_coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "gray", width = 5, tag = "ghost")
        
    def angle_reset(self, event):
        self.screenshot_canvas.delete("angle_line")
        self.screenshot_canvas.delete("angle")
        self.screenshot_canvas.delete("ghost")
        
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.use_angle()
        
    def angle(self, cur_coords):
        # gets atan where origin is placed at mid point
        def atan_angle(a, x_sign, y_sign):
            degree = math.degrees(math.atan2(x_sign*(a[1] - self.points[1][1]), y_sign*(a[0] - self.points[1][0])))
            return degree
        
        first_angle = atan_angle(self.points[0], -1, 1)
        
        # rotates the axises according to where the first angle is
        if (first_angle > 0) & (first_angle <= 90):
            axis_angle = atan_angle(cur_coords, -1, 1)
        elif (first_angle > 90) & (first_angle <= 180):
            axis_angle = atan_angle(cur_coords, 1, -1)
        elif (first_angle < 0) & (first_angle >= -90):
            axis_angle = atan_angle(cur_coords, -1, 1)
        else:
            axis_angle = atan_angle(cur_coords, 1, -1)
            
        if first_angle > 90:
            first_angle = -(180 - first_angle)
        elif first_angle < -90:
            first_angle = -(-180 - first_angle)
            
        # checks if the mouse has passed 180 degrees
        if ((175 < self.prev_axis_angle <= 180) & (-180 <= axis_angle < -175)) or ((175 < axis_angle <= 180) & (-180 <= self.prev_axis_angle < -175)):
            if self.passed == False:
                self.passed = True
            else:
                self.passed = False
                
        # adds 360 if the angle passes 180
        if (self.passed == True) & (axis_angle - first_angle <= 0):
            a = 360
        elif (self.passed == True) & (axis_angle - first_angle > 0):
            a = -360
        else: 
            a = 0 
        curr_angle = axis_angle + a - first_angle
        
        def sign_change(curr_angle):
            if (((self.prev_angle > 0) & (curr_angle < 0)) | ((curr_angle > 0) & (self.prev_angle < 0))):
                return True
            else:
                return False
            
        if (self.rotation == False) & (self.prev_angle != 0) & sign_change(curr_angle): # if the cursor has made one full pass for angles about 360
            self.rotation = True
            self.prev_angle = 0 # sets prev angle to zero to prevent the angle from going back down
            
        if self.rotation: # angles above 360
            final_angle = 360 + (360 - abs(curr_angle))
            if (final_angle <= 700) & (self.prev_angle != 0) & sign_change(curr_angle): # if the angle above 360 is going down under 360
                final_angle = abs(curr_angle)
                self.rotation = False
            elif final_angle >= 718.00: # if two rotations are completed
                self.rotation = False
                self.passed = False
                a = 0
                final_angle = abs(curr_angle)
        else:
            final_angle = abs(curr_angle)
            
            
        self.prev_axis_angle = axis_angle
        self.prev_angle = curr_angle
        return round(final_angle, 4)
    
    def calc_angle(self, event):
        old_coords = (self.old_x, self.old_y)
        coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasy(event.y))
        self.curr_angle = self.angle(coords)

        self.screenshot_canvas.delete("ghost") 
        self.screenshot_canvas.delete("angle_text")
        self.screenshot_canvas.create_line(old_coords, coords,
                                fill = "gray", width = 5, tag = "ghost")
        self.screenshot_canvas.create_text(coords[0] + 10, coords[1] + 10, fill = "white", font = "Calibri 12",
                                text = str(self.curr_angle), tag = "angle_text", anchor = "nw")
        
    def get_angle(self):
        return self.curr_angle
    
    def use_p1(self):
        self.activate_button(self.p1_button)
        self.screenshot_canvas.unbind("<Motion>")
        self.screenshot_canvas.unbind("<Button-3>")
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.delete("p1_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("p1_text")
        
        self.screenshot_canvas.bind("<Button-1>", lambda event, name = "p1": self.l_line(event, name))
        self.screenshot_canvas.bind("<Button-3>", lambda event, name = "p1": self.l_confirm(event, name))
        self.screenshot_canvas.bind("<Motion>", lambda event, name = "p1": self.l_ghost_line(event, name))
        
        self.old_x, self.old_y = None, None
        
    def use_p2(self):
        self.activate_button(self.p2_button)
        self.screenshot_canvas.unbind("<Motion>")
        self.screenshot_canvas.unbind("<Button-3>")
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.delete("p2_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("p2_text")
        
        self.screenshot_canvas.bind("<Button-1>", lambda event, name = "p2": self.l_line(event, name))
        self.screenshot_canvas.bind("<Button-3>", lambda event, name = "p2": self.l_confirm(event, name))
        self.screenshot_canvas.bind("<Motion>", lambda event, name = "p2": self.l_ghost_line(event, name))
        
        self.old_x, self.old_y = None, None
        
    def l_line(self, event, name):
        coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasx(event.y))
        if self.old_x and self.old_y:
            self.screenshot_canvas.create_line(self.old_x, self.old_y, coords, width = self.line_width, fill = self.length_color,
                                               capstyle = "round", smooth = True, splinesteps = 36, tag = name + "_line")
            if name == "p1":
                self.p1.append((self.old_x, self.old_y, coords[0], coords[1]))
            else:
                self.p2.append((self.old_x, self.old_y, coords[0], coords[1]))
        self.old_x, self.old_y = coords
        
    def l_confirm(self, event, name):
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.unbind("<Motion>")
        self.screenshot_canvas.unbind("<Button-3>")
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.bind("<Button-1>", lambda event, name = name: self.l_reset(event, name))
        
    def l_reset(self, event, name):
        self.screenshot_canvas.delete(name+"_line")
        self.screenshot_canvas.delete(name+"_ghost")
        self.screenshot_canvas.delete(name+"_text")
        
        self.screenshot_canvas.unbind("<Button-1>")
        
        self.screenshot_canvas.bind("<Button-1>", lambda event, name = name: self.l_line(event, name))
        self.screenshot_canvas.bind("<Button-3>", lambda event, name = name: self.l_confirm(event, name))
        self.screenshot_canvas.bind("<Motion>", lambda event, name = name: self.l_ghost_line(event, name))
        
        if name == "p1":
            self.p1 = []
        else:
            self.p2 = []
            
        self.old_x = None
        self.old_y = None
            
    def l_ghost_line(self, event, name):
        old_coords = (self.old_x, self.old_y)
        ghost_coords = (self.screenshot_canvas.canvasx(event.x), self.screenshot_canvas.canvasy(event.y))
        if self.old_x and self.old_y: 
            self.screenshot_canvas.delete("ghost")
            self.screenshot_canvas.create_line(old_coords, ghost_coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "gray", width = self.line_width, tag = "ghost")
            if name == "p1":
                length = self.calc_dist(self.p1)
            else:
                length = self.calc_dist(self.p2)
            self.screenshot_canvas.delete(name + "_text")
            self.screenshot_canvas.create_text(ghost_coords[0] + 10, ghost_coords[1] + 10, fill = self.length_color, font = "Calibri 12",
                                text = str(length), tag = name+"_text", anchor = "nw")
            
    def distance_form(self, coords):
        distance = math.sqrt((coords[0] - coords[2])**2 + (coords[1] - coords[3])**2)
        
        return distance
    
    def calc_dist(self, coords):
        length = 0
        for x in coords:
            length += self.distance_form(x)
        return round(length, 4)
    
    def clear_all(self):
        self.prev_axis_angle = 0
        self.prev_angle = 0
        self.passed = False
        self.rotation = False
        
        self.points = []
        self.old_x = None
        self.old_y = None
        
        self.p1 = []
        self.p2 = []
        
        self.prong1 = None
        self.prong2 = None
        
        self.screenshot_canvas.delete("angle_line")
        self.screenshot_canvas.delete("angle_ghost")
        self.screenshot_canvas.delete("angle_text")
        self.screenshot_canvas.delete("p1_line")
        self.screenshot_canvas.delete("ghost")
        self.screenshot_canvas.delete("p1_text")
        self.screenshot_canvas.delete("p2_line")
        self.screenshot_canvas.delete("p2_text")
        
        if self.active_button == self.a_button:
            self.use_angle()
        elif self.active_button == self.p1_button:
            self.use_p1()
        else:
            self.use_p2

class LilSnippy(tk.Frame):
    """A selection and screenshot tool.
    
    The user can select an area on the screen which is then automatically saved
    in a PIL image file.
    
    Attributes: 
        master (frame): The main frame of the application. 
        rect (tk.Canvas rectangle): A rectangle used to indicate the user's selection area.
        x (int): The x coordinate before a selection is made.
        y (int): the y coordinate before a selection is made.
        start_x (int): The x coordinate when first clicked.
        start_y (int): The y coordinate when first clicked.
        cur_x (int): The x coordinate as the mouse moves.
        cur_y (int): The y coordinate as the mouse moves.
        master_screen (tk.Window): A semi-transparent screen used to black out the rest of the
        screen other than the area being selected.
        picture_frame (tk.Frame): A frame used to change the mouse into a cross.
        body_info (dict): A dictionary of related information on the body being screenshotted.
        folder_path (str): The directory to the folder where images are saved.
        marker_canvas (tk.Canvas): The canvas on the gridfile where the markers are saved.
        
    Typical Usage Example:
        LilSnippy(master, body_info, folder_path, marker_canvas)
    """
    def __init__(self, master, body_info, folder_path, marker_canvas, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.master = master
        self.rect = None
        self.x = self.y = 0
        self.start_x = None
        self.start_y = None
        self.cur_x = None
        self.cur_y = None

        self.master_screen = tk.Toplevel(self.master)
        self.master_screen.withdraw()
        self.master_screen.attributes("-transparent", "blue")
        self.picture_frame = tk.Frame(self.master_screen, background = "blue")
        self.picture_frame.pack(fill=tk.BOTH, expand = True)
        
        self.body_info = body_info
        self.folder_path = folder_path
        self.marker_canvas = marker_canvas
        
    def take_bounded_screenshot(self, x1, y1, x2, y2):
        """Save the screenshot as a PIL file.
        
        Using the diagonal points, this function take that area and saves it as 
        a PIL image. This image is then piped into the Screenshot Editor.
        
        Args:
            x1 (int): X coordinate of the first click.
            y1 (int): Y coordinate of the first click.
            x2 (int): X coordinate when the mouse is released.
            y2 (int): Y coordinate when the mouse is released.
        """
        im = pyautogui.screenshot(region=(x1, y1, x2, y2))
        if self.body_info["body_name"] in config.angler_types:
            Angler(self.body_info, self.folder_path, self.marker_canvas, im, True)
        elif self.body_info["body_name"] == "ring_kettlebell":
            Ringer(self.body_info, self.folder_path, self.marker_canvas, im , True)
        else:
            ScreenshotEditor(self.body_info, self.folder_path, self.marker_canvas, im, True)

    def create_screen_canvas(self):
        """Initializes a screen canvas for button clicks.
        
        Creates a new canvas which then has mouse binds for recording the coordinates
        for screenshot creation. The screen is also dimmed to show the area not selected.
        """
        self.master_screen.deiconify()
        self.master.withdraw()
        
        self.screen_canvas = tk.Canvas(self.picture_frame, cursor="cross", bg="grey11")
        self.screen_canvas.pack(fill=tk.BOTH, expand= True)
        
        self.screen_canvas.focus_set()
        
        self.screen_canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.screen_canvas.bind("<B1-Motion>", self.on_move_press)
        self.screen_canvas.bind("<ButtonRelease-1>", self.on_button_release)
        
        self.master_screen.attributes('-fullscreen', True)
        self.master_screen.attributes('-alpha', .3)
        self.master_screen.lift()
        self.master_screen.attributes("-topmost", True)


    def on_button_release(self, event):
        """Takes a screenshot on the release of mouse1.
        
        A callback function used to take the coordinates when mouse 1 is lifted 
        to then take a screenshot through the take_bound_screenshot method. Checks
        where the final coordinates are to sure that it is diagonal with the starting coordinates.
        
        Returns:
            event
        """
        if self.start_x <= self.cur_x and self.start_y <= self.cur_y:
            self.take_bounded_screenshot(self.start_x, self.start_y, self.cur_x - self.start_x, self.cur_y - self.start_y)

        elif self.start_x >= self.cur_x and self.start_y <= self.cur_y:
            self.take_bounded_screenshot(self.cur_x, self.start_y, self.start_x - self.cur_x, self.cur_y - self.start_y)

        elif self.start_x <= self.cur_x and self.start_y >= self.cur_y:
            self.take_bounded_screenshot(self.start_x, self.cur_y, self.cur_x - self.start_x, self.start_y - self.cur_y)

        elif self.start_x >= self.cur_x and self.start_y >= self.cur_y:
            self.take_bounded_screenshot(self.cur_x, self.cur_y, self.start_x - self.cur_x, self.start_y - self.cur_y)

        self.exit_screenshot_mode()
        return event

    def exit_screenshot_mode(self):
        """Destroys all canvases to end screenshot capturing mode."""
        self.screen_canvas.destroy()
        self.master_screen.withdraw()
        self.master.deiconify()

    def on_button_press(self, event):
        """Records the starting mouse coordinate.
        
        When the mouse is clicked, the starting mouse coordinate is selected and saved
        to record into the rectangle for future rectangle manipulation.
        """
        self.start_x = self.screen_canvas.canvasx(event.x)
        self.start_y = self.screen_canvas.canvasy(event.y)
        self.rect = self.screen_canvas.create_rectangle(self.x, self.y, 1, 1, outline='red', width=3, fill="blue")

    def on_move_press(self, event):
        """Records the coordinates as the mouse moves.
        
        Constantly refreshes cur_x and cur_y to reflect the current mouse position
        to change the rectangle to reflect the selection area.
        """
        self.cur_x, self.cur_y = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.screen_canvas.coords(self.rect, self.start_x, self.start_y, self.cur_x, self.cur_y)

    def rec_position(self):
        """Unused function that can return the coordinates of the rectangle if needed."""
        print(self.start_x)
        print(self.start_y)
        print(self.cur_x)
        print(self.cur_y)

if __name__ == '__main__':
    help(LilSnippy)
    help(ScreenshotEditor)