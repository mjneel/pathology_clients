import tkinter as tk
from PIL import Image, ImageTk
from file_management import FileManagement
from datetime import datetime
from screenshot import ScreenshotEditor, Angler, Ringer
import config
class ImageViewer(tk.Toplevel):
    """A window to view taken screenshots.
    
    ImageViewer is a tk.Toplevel class that can open to allow users to
    view images, edit information, and edit the annotations themselves. Filter
    options are also included to go through and filter images as needed.
    
    Attributes:
        marker_canvas (tk.Canvas): Tkinter canvas where markers are stored for viewing
            on the grid file image.
        folder_path (str): Directory leading to the save path of images.
        all_bodies (list): A list of all the possible bodies for creating buttons.
        button_list_canvas (tk.Canvas): A canvas holding a window of all buttons that allow
            the user to open an image.
        biondi_image_canvas (tk.Canvas): A canvas storing the image being viewed at the time.
        filter_options_frame (tk.Frame): A frame holding a series of buttons for filtering the buttons
            for selecting what image to view.
        information_frame (tk.Frame): A frame storing the information about the selected image.
        edit_buttons_frame (tk.Frame): A frame within information frame with buttons for editing the 
            selected image.
        var_GR (tk.BooleanVar): Boolean value where True is when user wants to sort by GR.
        var_MAF (tk.BooleanVar): Boolean value where True is when user wants to sort by MAF.
        var_MP (tk.BooleanVar): Boolean value where True is when user wants to sort by MP.
        var_unsure (tk.BooleanVar): Boolean value where True is when user wants to sort by unsure.
        previous_body_time (int): The unix time of the previous body selected.
        
    Typical usage example:
        img_v = ImageViewer(folder_path, marker_canvas)
    """
    def __init__(self, folder_path, marker_canvas):
        tk.Toplevel.__init__(self)
        self.title("Image Viewer")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.folder_path = folder_path
        self.marker_canvas = marker_canvas
            
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        # create a canvas object and a vertical scrollbar for scrolling it
        scrollbar = tk.Scrollbar(self, orient = "vertical")
        self.button_list_canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=scrollbar.set)
        
        scrollbar.config(command=self.button_list_canvas.yview)
        self.button_list_canvas.xview_moveto(0)
        self.button_list_canvas.yview_moveto(0)
        
        self.make_button_frame()

        self.biondi_image_canvas = tk.Canvas(self, bd = 0)
        self.filter_options_frame = tk.Frame(self)
        self.information_frame = tk.Frame(self)
        
        self.button_list_canvas.pack(side = tk.LEFT, fill = tk.Y)
        scrollbar.pack(side = tk.LEFT, fill = tk.BOTH)
        self.filter_options_frame.pack(side = tk.TOP, fill = tk.X)
        self.biondi_image_canvas.pack(side = tk.TOP, expand = True, fill = tk.BOTH)
        self.information_frame.pack(side = tk.BOTTOM, expand = True, fill = tk.X)
        
        self.edit_buttons_frame = tk.Frame(self.information_frame)
        self.edit_buttons_frame.grid(row = 4, column = 0, columnspan = 3, sticky = "w")
        
        self.var_GR = tk.BooleanVar()
        self.var_MAF = tk.BooleanVar()
        self.var_MP = tk.BooleanVar()
        self.var_unsure = tk.BooleanVar()
        
        self.previous_body_time = 0
        
        self.make_filter_buttons()
        self.create_buttons(config.all_bodies, False, False, False, False)
        
    def make_filter_buttons(self):
        """Creates the different filter buttons.
        
        Initializes a series of buttons and checkbuttons for selection to filter the 
        button list. These only change what is shown in the button list.
        """
        # creates a dropdown with the different biondi bodies. 
        # multiple options can be checked for filtering
        filter_bodies = tk.Menubutton(self.filter_options_frame, text="Biondi Bodies", 
                                    indicatoron=True, borderwidth=1, relief="raised")
        menu = tk.Menu(filter_bodies, tearoff=False)
        filter_bodies.configure(menu=menu)
        filter_bodies.pack(padx=10, pady=10, side = tk.LEFT)

        # loops through all possible biondi bodies to file the dorpdown
        self.choices = {}
        for choice in config.all_bodies:
            self.choices[choice] = tk.IntVar(value=0)
            menu.add_checkbutton(label=choice, variable=self.choices[choice], 
                                onvalue=1, offvalue=0)
        
        grC = tk.Checkbutton(self.filter_options_frame, text = "GR", anchor ="w", variable = self.var_GR, onvalue = True, offvalue = False)
        mafC = tk.Checkbutton(self.filter_options_frame, text = "MAF", anchor ="w", variable = self.var_MAF, onvalue = True, offvalue = False)
        mpC = tk.Checkbutton(self.filter_options_frame, text = "MP", anchor ="w", variable = self.var_MP, onvalue = True, offvalue = False)
        unsure = tk.Checkbutton(self.filter_options_frame, text = "UNSURE", variable = self.var_unsure, onvalue = True, offvalue = False)
        apply  = tk.Button(self.filter_options_frame, text = "Apply", command = lambda : self.filter())
        reset = tk.Button(self.filter_options_frame, text = "Reset", command = lambda : self.reset())
        
        grC.pack(padx=10, pady = 10, side = tk.LEFT)
        mafC.pack(padx=10, pady = 10, side = tk.LEFT)
        mpC.pack(padx=10, pady = 10, side = tk.LEFT)
        unsure.pack(padx=10, pady = 10, side = tk.LEFT)
        apply.pack(padx=10, pady = 10, side = tk.LEFT)
        reset.pack(padx=10, pady = 10, side = tk.LEFT)
        
    def make_button_frame(self):
        """Creates a frame within the button list canvas.
        
        Builds a new frame inside the button list canvas to allow from scrolling
        down the list of buttons. This scrolling is adaptive and will change with the 
        number of buttons to reflect the list's length.
        """
        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(self.button_list_canvas)
        self.interior.grid(row = 0, column = 0, sticky = "ns")
        interior_id = self.button_list_canvas.create_window(0, 0, window=interior,
                                            anchor=tk.NW)
        
        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            self.button_list_canvas.config(scrollregion = "0 0 %s %s" % size)
            if interior.winfo_reqwidth() != self.button_list_canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.button_list_canvas.config(width=interior.winfo_reqwidth())

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != self.button_list_canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.button_list_canvas.itemconfigure(interior_id, width=self.button_list_canvas.winfo_width())
        
        self.button_list_canvas.bind('<Configure>', _configure_canvas)
        interior.bind('<Configure>', _configure_interior)
    
    def set_window_size(self, img):
        """Changes window size accordingly.
        
        Checks if the image is larger than the default size of 1200 x 700.
        Then takes the larger dimension to resize the image viewer window.
        
        Args:
            img (PIL image): The image of the biondi body.
        """
        img_w, img_h = img.size
        
        # 180 is added to account for the height of the filter/information frames
        if img_h + 180 < 700:
            h = 700
        else:
            h = img_h + 180
            
        # 230 is added to account for the width of the button frame
        if img_w + 230 < 1200:
            w = 1200
        else:
            w = img_w + 245

        self.geometry("{0}x{1}".format(str(w), str(h)))

    def create_buttons(self, body_param, GR_param, MAF_param, MP_param, unsure_param):
        """Creates the buttons in the button list.
        
        Create a series of buttons reflecting the filter options which the user can click
        to bring up the relevant information and images for the body selected.
        
        Args:
            body_param (list): A list of all the selected bodies for filtering. Enter self.all_bodies
                for a selection of all the body types.
            GR_param (bool): True if sorting by GR.
            MAF_param (bool): True if sorting by MAF.
            MP_param (bool): True if sorting by MP.
            unsure_param (bool): True if sorting by unsure.
        """
        # queries a list of all the selected bodies
        fm = FileManagement(self.folder_path)
        data = fm.query_images(body_param, GR_param, MAF_param, MP_param, unsure_param)
        
        # loops through generating bodies
        for i in data:
            time = i[0]
            name = i[1]
            number = i[2]
            body_name = "{} {}".format(name, number)
            # each button takes a different command depending on its selected data
            btn = tk.Button(self.interior, height = 1, width = 20, relief=tk.FLAT, 
                            bg="gray99", fg="purple3", font="Dosis", text = body_name,
                            command = lambda i = time: self.open_file(i))
            btn.pack(padx = 10, pady = 5, side = tk.TOP)
            
    def make_information_labels(self):
        """Creates the labels for the information data
        
        Generates a series of tk.Labels with the titles of the columns of data
        in the information frame.
        """
        # generates a series of white columns every other column to distinguish the columns
        x = 0
        column_widths =  ("20", "11", "12", "9", "12", "5", "5", "5", "8", "2", "9")
        for i in column_widths:
            if x % 2 == 0: 
                bg_color = "gray99"
            else:
                bg_color = "SystemButtonFace"
            bkgrnd = tk.Label(self.information_frame, width = i, height = "3", bg = bg_color)
            bkgrnd.grid(row = 0, column = x, rowspan = 2)
            x += 1
        # makes background of text alternate between white and gray
        x = 0
        for i in ("Time:", "Annotator:", "Body Type:", "Number:", "Location:", "GR:", "MAF:", "MP:", "UNSURE:", "ANGLE:", "LOG(L/D):"):
            if x % 2 == 0:
                bg_color = "gray99"
            else:
                bg_color = "SystemButtonFace"
            col = tk.Label(self.information_frame, text = i, font = ("Dosis", 10, "bold"), bg = bg_color, anchor = "w")
            col.grid(row = 0, column = x, sticky = "w")
            x += 1
            
            notes = tk.Label(self.information_frame, text = "Notes:", font = ("Dosis", 10, "bold"), anchor = "w")
            notes.grid(row = 2, column = 0, sticky = "w")
    
    def open_file(self, time):
        """Brings up the relevant file information.
        
        When clicking a button, open_file brings up the annotation and body image
        to show in the biondi_image_canvas as well as shows the information about that
        specific body.
        
        Args:
            Time (int): Time added of selected body in unix time.
        """
        body_info = FileManagement(self.folder_path).get_image_time(time)
        self.clear_information_canvas()
        self.show_information(body_info)
        self.open_annotation_image(body_info)
        
        self.marker_canvas.itemconfig("m" + str(time), fill = "red")
        if self.previous_body_time != 0:
            self.marker_canvas.itemconfig("m"+str(self.previous_body_time), fill = "white")
        self.previous_body_time = time
        
    def on_closing(self):
        """Resets marker color on window closing"""
        self.marker_canvas.itemconfig("m"+str(self.previous_body_time), fill = "white")
        self.destroy()
        
    def show_information(self, body_info):
        """Makes the information frame widgets.
        
        Fills the information frame widgets with the relevant labels, buttons
        and information.
        
        Args:
            body_info (tuple): Tuple of selected body's info for display in the frame.
        """
        self.make_information_labels()
        self.make_edit_buttons(body_info)
        self.add_information(body_info)
        
    def clear_information_canvas(self):
        """Resets the information frame.
        
        Destroys the information frame and its relevant buttons and then remakes 
        a new empty frame so that when selecting different images, the frames do not
        just stack on top of each other.
        """
        self.information_frame.destroy()
        self.edit_buttons_frame.destroy()
        self.information_frame = tk.Frame(self)
        self.information_frame.pack(side = tk.BOTTOM, fill = tk.X)
        self.edit_buttons_frame = tk.Frame(self.information_frame)
        self.edit_buttons_frame.grid(row = 4, column = 0, columnspan = 3, sticky = "w")
        
    def make_edit_buttons(self, body_info):
        """Creates the edit buttons for each image.
        
        Builds 3 new buttons for editing info, image, and deleting the image. Packed
        in the edit_buttons_frame which is packed in the information_frame.
        """
        edit_info = tk.Button(self.edit_buttons_frame, text = "Edit Info", 
                            command = lambda : self.create_edit_entries(body_info))
        edit_info.grid(row = 4, column = 0, sticky = "e", padx = 3, pady = 3)
        
        edit_img = tk.Button(self.edit_buttons_frame, text = "Edit Image", 
                            command = lambda: self.edit_image(body_info))
        edit_img.grid(row = 4, column = 1, sticky = "e", padx = 3, pady = 3)
        
        delete = tk.Button(self.edit_buttons_frame, text = "Delete", 
                            command = lambda: self.delete_image(body_info))
        delete.grid(row = 4, column = 2, sticky = "e", padx = 3, pady = 3)
        
        if body_info["body_name"] == "ring_kettlebell":
            edit_log = tk.Button(self.edit_buttons_frame, text = "Edit Log",
                                 command = lambda: self.edit_log(body_info))
            edit_log.grid(row = 4, column = 3, sticky = "e", padx = 3, pady = 3)
        elif body_info["body_name"] in config.angler_types:
            edit_angle = tk.Button(self.edit_buttons_frame, text = "Edit Angle",
                                 command = lambda: self.edit_angle(body_info))
            edit_angle.grid(row =4 , column = 3, sticky = "e", padx =3 , pady = 3)
        
    def create_edit_entries(self, body_info):
        """Creates entry fields when editing info.
        
        Builds a series of checkbuttons, dropdowns, and entry areas so the user
        can change the data as needed.
        
        Args:
            body_info (tuple): Tuple of current body information.
            
        Todo: 
            Make the checkbuttons reflect the old image's information on edit entries startup
        """
        self.clear_information_canvas()
        self.make_information_labels()
        
        edit_body_name = tk.StringVar()
        edit_body_name.set(body_info["body_name"])
        edit_var_GR = tk.BooleanVar()
        edit_var_MAF = tk.BooleanVar()
        edit_var_MP = tk.BooleanVar()
        edit_var_unsure = tk.BooleanVar()
        edit_notes = tk.StringVar()
        edit_notes.set(body_info["notes"])
        
        dropdown = tk.OptionMenu(self.information_frame, edit_body_name, *config.all_bodies)
        edit_gr = tk.Checkbutton(self.information_frame, anchor ="w", variable = edit_var_GR, onvalue = True, offvalue = False)
        edit_maf = tk.Checkbutton(self.information_frame, anchor ="w", variable = edit_var_MAF, onvalue = True, offvalue = False)
        edit_mp = tk.Checkbutton(self.information_frame, anchor ="w", variable = edit_var_MP, onvalue = True, offvalue = False)
        edit_unsure = tk.Checkbutton(self.information_frame, variable = edit_var_unsure, onvalue = True, offvalue = False)
        edit_note_entry = tk.Entry(self.information_frame, textvariable = edit_notes)
        
        edit_button_ok = tk.Button(self.information_frame, text = "OK", 
                                   command = lambda: self.edit_info(body_info["time"], edit_body_name.get(), 
                                                                    edit_var_GR.get(), edit_var_MAF.get(), 
                                                                    edit_var_MP.get(), edit_var_unsure.get(), edit_notes.get(), body_info))
        
        dropdown.grid(row = 1, column = 2)
        edit_gr.grid(row = 1, column = 5)
        edit_maf.grid(row = 1, column = 6)
        edit_mp.grid(row = 1, column = 7)
        edit_unsure.grid(row = 1, column = 8)
        edit_note_entry.grid(row = 3, columnspan = 9, sticky = "w")
        edit_button_ok.grid(row = 4, column = 8, sticky = "w")
        
    def edit_info(self, time, edited_body_name, edited_GR, edited_MAF, edited_MP, edited_unsure, edited_notes, body_info):
        """Changes the information of the body in the database.
        
        Using the user inputted fields in the edit entries, inputs them
        into the database to commit all the changes. Then refreshes the information 
        frame to reflect the changes.
        
        Args:
            edited_body_name (str): The new selected body name.
            edited_GR (bool): New edited GR field.
            edited_MAF (bool): New edited MAF field.
            edited_MP (bool): New edited MP field.
            edited_unsure (bool): New edited unsure field.
            edited_notes (str): New notes added.
            body_info (tuple): The old body info before editing.
        """
        # commit edited parameters into database
        edited = [edited_body_name, edited_GR, 
                  edited_MAF, edited_MP, 
                  edited_unsure, edited_notes]
        if edited_body_name in config.angler_types:
            edited.extend((body_info["angle"], None, body_info["dprong1"], body_info["lprong2"], time))
        elif edited_body_name in config.kbell_types:
            edited.extend((None, body_info["log"], body_info["dprong1"], body_info["lprong2"], time))
        else:
            edited.extend((None, None, None, None, time))
        FileManagement(self.folder_path).edit_info(edited)
        
        fm = FileManagement(self.folder_path)
        new_info = fm.get_image_time(body_info["time"])
        
        # if the body name is changed, renumbers both the old and new type
        # changes the gridfile marker to reflect the new letter
        if body_info["body_name"] != edited_body_name:
            if edited_body_name in config.angler_types:
                body_image = Image.open(self.folder_path + body_info["body_file_name"])
        
                Angler(body_info, self.folder_path, self.marker_canvas, body_image, False)
            elif edited_body_name == "ring_kettlebell":
                body_image = Image.open(self.folder_path + body_info["body_file_name"])
        
                Ringer(body_info, self.folder_path, self.marker_canvas, body_image, False)
            fm = FileManagement(self.folder_path)
            fm.renumber_img(body_info["body_name"], 1)
            fm.renumber_img(edited_body_name, 1)
            fm.close()
            self.filter()
            tag = "m" + str(time)
            self.marker_canvas.itemconfig(tag, text = config.body_index[edited_body_name])
            

        self.clear_information_canvas()
        self.show_information(new_info)
        
        
    def edit_image(self, body_info):
        """Open screenshot editor.
        
        Function opens the selected image as a pillow file for
        entry into the screenshot editor to save a new copy of the annotation.
        
        Args:
            body_info
        """
        body_image = Image.open(self.folder_path + body_info["body_file_name"])
        
        # new = False as the image is already saved in the DB so no need to resave
        ScreenshotEditor(body_info, self.folder_path, self.marker_canvas, body_image, False)

    def edit_angle(self, body_info):
        body_image = Image.open(self.folder_path + body_info["body_file_name"])
        
        Angler(body_info, self.folder_path, self.marker_canvas, body_image, False)
        
    def edit_log(self, body_info):
        body_image = Image.open(self.folder_path + body_info["body_file_name"])
        
        Ringer(body_info, self.folder_path, self.marker_canvas, body_image, False)
        
    def delete_image(self, body_info):
        """Deletes current image.
        
        Deletes the currently selected image's data from the database and resets the information frame and
        button list to reflect the changes.
        
        Args:
            body_info (tuple): Tuple of the information of the body to be deleted
        """
        name = body_info["body_name"]
        number = body_info["body_number"]
        time = body_info["time"]
        fm  = FileManagement(self.folder_path)
        fm.delete_img(name, number)
        # refreshes the button list to reflect the new changes
        self._remake_button_list()
        self.filter()
        self.information_frame.destroy()
        
        # clear the body canvas
        self.biondi_image_canvas.delete("all")
        
        # deletes the associated marker on the gridfile
        tag = "m" + str(time)
        self.marker_canvas.delete(tag)
        self.marker_canvas.update()
        
    def add_information(self, body_info):
        """Fills the information frame with the current information.
        
        Places a series of labels under the existing information labels with the 
        information of the currently selected body.
        
        Args:
            body_info (tuple): Tuple of the currently selected body's information
        """
        info = (datetime.fromtimestamp(body_info["time"]), # converts unix time to datetime
                body_info["annotator_name"],
                body_info["body_name"],
                body_info ["body_number"],
                "{0} {1}, {2}".format(body_info["grid_id"], body_info["x"], body_info["y"]),
                str(body_info["GR"]),
                str(body_info["MAF"]),
                str(body_info["MP"]),
                str(body_info["unsure"]),
                str(body_info["angle"]),
                str(body_info["log"]))
        
        x = 0
        for i in info:
            if x % 2 == 0:
                bg_color = "gray99"
            else:
                bg_color = "SystemButtonFace"
            lbl = tk.Label(self.information_frame, text = str(i), font = ("Dosis", 10), bg = bg_color, anchor = "w")
            lbl.grid(row = 1, column = x, sticky = "w")
            x += 1
            
            notes = tk.Label(self.information_frame, text = body_info["notes"], font = ("Dosis", 10), anchor = "w",
                            wraplength = 200, justify = "left")
            notes.grid(row = 3, columnspan = 9, sticky = "w")
            
    def open_annotation_image(self, body_info):
        """Displays the currently selected biondi image.
        
        Pulls the annotation and body image from the save folder to display in the image_canvas
        when then user selects that body.
        
        Args:
            body_info (tuple): Tuple of the currently selected body's information
            """
        body_file_name = body_info['body_file_name']
        annotation_file_name = body_info['annotation_file_name']
        # exits if there is missing an image
        # should only raise if body images are manually edited/moved
        try:
            body_img = Image.open(self.folder_path + body_file_name)  # open image
        except:
            print("missing biondi image")
            return
        b_img = ImageTk.PhotoImage(body_img)
        self.biondi_image_canvas.create_image(0, 0, image = b_img, anchor = "nw")
        self.biondi_image_canvas.b_img = b_img # a copy of the image is saved for garbage collection
        
        try:
            annotation_img = Image.open(self.folder_path + annotation_file_name)  # open image
        except:
            print("missing annotation image")
            return
        a_img = ImageTk.PhotoImage(annotation_img)
        self.biondi_image_canvas.create_image(0, 0, image = a_img, anchor = "nw")
        self.biondi_image_canvas.a_img = a_img
        
        self.set_window_size(body_img)

    def _remake_button_list(self):
        self.interior.destroy()
        self.make_button_frame()
    
    def _get_body_selection(self):
        body_selection = []
        for name, var in self.choices.items():
            if var.get() == 1:
                body_selection.append(name)
        if body_selection == []:
            body_selection = config.all_bodies
        return body_selection
    
    def filter(self):
        """Refreshes button list to reflect filter selection.
        
        Gets the user inputs into the filter and then remakes the button list
        with only the buttons that fit under the parameters.
        """
        body_param = self._get_body_selection()
        GR_param = self.var_GR.get()
        MAF_param = self.var_MAF.get()
        MP_param = self.var_MP.get()
        unsure_param = self.var_unsure.get()
        
        self._remake_button_list()
        self.create_buttons(body_param, GR_param, MAF_param, MP_param, unsure_param)

    def reset(self):
        """Removes any filters.
        
        Resets all the filter buttons as well as remakes the button list to reflect
        all the possible bodies organized by time.
        """
        self._remake_button_list()
        self.create_buttons(config.all_bodies, False, False, False, False)
        for choice in config.all_bodies:
            self.choices[choice].set(0)
        
        self.var_GR.set(False)
        self.var_MAF.set(False)
        self.var_MP.set(False)
        self.var_unsure.set(False)