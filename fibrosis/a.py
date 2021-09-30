import openslide
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
from PIL import Image, ImageTk, ImageDraw
import constants
import time
from database import Database
import helper

class TileImage:
    """Openslide Image Loader Class"""
    def __init__(self, file_path):
        self.wsi_image = openslide.open_slide(file_path) # create openslide object
        self.width, self.height = self.wsi_image.dimensions
        self.max_tiles = (self.width // constants.tile_size, self.height // constants.tile_size) # (x, y) max tiles

    def calculate_coordinates(self, tile_number):
        # zero indexed tile_number
        if tile_number >= self.max_tiles[0] * self.max_tiles[1]:
            print("invalid tile_number")
            # sys.exit()
            
        x = tile_number % self.max_tiles[0] # zero index
        y = tile_number // self.max_tiles[0] # zero index 
        return [x * constants.tile_size, y * constants.tile_size]

    def load_tile(self, tile_num):
        coords = self.calculate_coordinates(tile_num)
        # adding margins if needed
        # add 600 px padding
        # top, bot, left, right = 0, 0, 0, 0
        
        size_padding_x = 2 * constants.padding_size
        size_padding_y = 2 * constants.padding_size

        if (coords[0] - constants.padding_size > 0):
            coords[0] -= constants.padding_size
        if (coords[1] - constants.padding_size > 0):
            coords[1] -= constants.padding_size

        size = ((constants.tile_size + size_padding_x) //constants.zoom_multiplier , (constants.tile_size + size_padding_y) //constants.zoom_multiplier)
        tile = self.wsi_image.read_region(location=coords, level=constants.downscale_level, size=size)
        # add white margin if needed
        # for side in (top, left, bot, right):
        #     if side != 0:
        #         tile = self.add_margin(tile, top, right, bot, left)
        #         break
        
        
        # adding the box lines to indicate in or out
        # convert this to tkinter 
        draw = ImageDraw.Draw(tile)
        t = constants.tile_size // constants.zoom_multiplier
        p = constants.padding_size // constants.zoom_multiplier
        
        # the +2's are so that the lines are fully square. They change based on exlcusion line width, and I Dont think there is a relation
        draw.line(((p, p), (t+p+2, p)), fill='limegreen', width=constants.exclusion_line_width)
        draw.line(((t+p, p), (t+p, t+p)), fill='limegreen', width=constants.exclusion_line_width)
        draw.line(((p, 0), (p, p+t+2)), fill='red', width=constants.exclusion_line_width)
        draw.line(((p, t+p), (t+p+2, t+p)), fill='red', width=constants.exclusion_line_width)
        draw.line(((t+p, t+p), (t+p, t+2*p)), fill='red', width=constants.exclusion_line_width)
        
        return tile
    
    
    def add_margin(self, pil_img, top, right, bottom, left, color=(255,255,255)):
        width, height = pil_img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(pil_img.mode, (new_width, new_height), color)
        result.paste(pil_img, (left, top))
        return result

class MainWindow(tk.Frame):
    def __init__(self, master, folder_path):
        tk.Frame.__init__(self, master)
        self.master = master
        self.master.geometry("1500x1000")
        self.pack(fill="both", expand=True)
        
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        
        self.inf_frame = InformationFrame(self, folder_path)
        self.inf_frame.grid(row=0, column=0, rowspan=2, sticky="NS")
        
        self.image_window = ImageWindow(self, folder_path)
        self.image_window.grid(row=1, column=1, sticky="NSEW")
        
        self.navigator = Navigator(self, folder_path, self.image_window, self.inf_frame)
        self.navigator.grid(row=2, column=1)
        
        self.toolbar = Toolbar(self, folder_path)
        self.toolbar.grid(row=0, column=1, columnspan=2, sticky="EW")

class Navigator(tk.Frame):
    def __init__(self, master, file_path, image_window, inf_frame):
        tk.Frame.__init__(self, master)
        self.db = Database(file_path)
        self.master = master
        self.image_window = image_window
        self.inf_frame = inf_frame
        
        self.max_tiles = self.db.get_max_tiles() # pull from database later
        self.cur_tile = tk.IntVar()
        first_unfinished = self.db.get_first_unfinished()
        self.cur_tile.set(first_unfinished)# get first tile from database later
        
        self.var_fin = tk.IntVar()
        a = self.db.get_finished_status(self.cur_tile.get())
        self.var_fin.set(a)

        self._create_buttons()
        self.image_window.update_image(self.cur_tile.get())
        
    def _create_buttons(self):
        # making the goto combobox
        combo_values = [str(i) for i in range(1, self.max_tiles+1)]
        self.goto = ttk.Combobox(self, values=combo_values,
                            font=("Calibri", 30), width=3, justify="center", 
                            state="readonly")
        self.goto.bind("<<ComboboxSelected>>", self._nav_goto)
        self.goto.bind("<Return>", self._nav_goto)
        self.goto.set(str(self.cur_tile.get() + 1))
        self.goto.grid(row=1, column=1, pady=25, padx=25)
        
        # forward and backward buttons
        self.n_forward_button = tk.Button(self, text =">", font=("Calibri", 20),
                                           command=lambda: self._increment_tile(1))
        self.n_forward_button.grid(row=1, column=2)
        
        self.n_backward_button = tk.Button(self, text ="<", font=("Calibri", 20),
                                           command=lambda: self._increment_tile(-1))
        self.n_backward_button.grid(row=1, column=0)

        
        self.finished = tk.Checkbutton(self, text="Finished", variable=self.var_fin,
                                       onvalue=1, offvalue=0, command=self._update_finished)

        self.finished.grid(row=3, column=1)
        
    def _update_finished(self):
        self.db.update_completion(self.cur_tile.get(), self.var_fin.get())
        self.inf_frame._update_completed_label(self.var_fin.get())
    
    def _nav_goto(self, event):
        # have to randomize tiles later
        # pull from a saved random list
        
        self.cur_tile.set(int(self.goto.get()) - 1)
        self.image_window.update_image(self.cur_tile.get())
        self.image_window.canvas.focus_set()
        
    def _increment_tile(self, i):
        if (self.cur_tile.get() >= self.max_tiles) & (i == 1):
            return
        elif (self.cur_tile.get() <= 0) & (i == -1):
            return
        else: 
            self.cur_tile.set(self.cur_tile.get() + i)
            self.goto.set(str(self.cur_tile.get() + 1))
            self._update_tile()
        
    def _update_tile(self):
            completion_status = self.db.get_finished_status(self.cur_tile.get())
            self.var_fin.set(completion_status)
            self.image_window.update_image(self.cur_tile.get())
            
            self.finished.configure(variable=self.var_fin)
        
class ImageWindow(tk.Frame):
    def __init__(self, master, folder_path):
        tk.Frame.__init__(self, master)
        self.master = master
        self.folder_path = folder_path
        self.db = Database(folder_path)
        self.wsi_path = self.db.get_wsi_path()
        
        self.image_loader = TileImage(self.wsi_path)
        
        self._create_image_canvas()
        self._create_scrollbar()
        
        # allows resizing of image canvas
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)
        
        self.canvas.bind("q", self._draw_annotation)
        
        self.randomized_tiles = self.db.get_randomized_tiles()
        
        # annotation inits
        self.annotations = []
        # setting current annotation to empty lists
        self.cur_annotation = {}
        for a in constants.fib_types:
            self.cur_annotation[a] = []
        self.cur_type = 0
        
        self.tile_num = 0
        
        self.deleted = False # boolean check to see if a annotation is deleted
        
    def create_existing_annotations(self):
        vals = self.db.pull_tile_annotations(self.tile_num)
        all_tags = self.db.pull_impacted_tags()
        for tag, values in vals.items():
            a = Annotation(self.folder_path, self.canvas, self.tile_num, tag, **values)
            self.annotations.append(a)
            if (tag in all_tags):
                a.impacted = True
        
    def update_image(self, tile_num=0):
        self.canvas.delete("all") # removes previous image
        next_tile = self.randomized_tiles[tile_num] # encodes the tile number in the real tile position
        img = self.image_loader.load_tile(next_tile)
        self._show_img(img, self.canvas)
        self.canvas.configure(scrollregion=self.canvas.bbox("all")) # updates scroll region so scrollbars dont break
        self.tile_num = tile_num
        
        self.create_existing_annotations()
        
    def _create_image_canvas(self):
        self.canvas = tk.Canvas(self, highlightthickness=0, bg='white')
        self.canvas.grid(row=1, column=1, sticky="nswe")
        self.canvas.focus_set()
        
    def _create_scrollbar(self):
        self.vbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.vbar.grid(row=1, column=2, sticky='ns')
        self.hbar = tk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.hbar.grid(row=2, column=1, sticky='we')
        
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set,
                              xscrollincrement='2', yscrollincrement='2', scrollregion=self.canvas.bbox("all"))
        self.canvas.update()
        
        self.canvas.bind('<MouseWheel>', self._verti_wheel)
        self.canvas.bind('<Shift-MouseWheel>', self._hori_wheel)
        
    def _verti_wheel(self, event):
        if event.num == 5 or event.delta == -120:  # scroll down
            self.canvas.yview('scroll', 20, 'units')
        if event.num == 4 or event.delta == 120:
            self.canvas.yview('scroll', -20, 'units')

    def _hori_wheel(self, event):
        if event.num == 5 or event.delta == -120:  # scroll down
            self.canvas.xview('scroll', 20, 'units')
        if event.num == 4 or event.delta == 120:
            self.canvas.xview('scroll', -20, 'units')

    def _show_img(self, img, canvas):
        #img is PIL object
        imagetk = ImageTk.PhotoImage(img)
        imageid = canvas.create_image(0, 0, anchor="nw", image=imagetk, tag="image")
        canvas.lower(imageid)
        canvas.imagetk = imagetk # reference for garbage collection
        
    def _draw_annotation(self, event):
        self._activate_polygon_tool(constants.fib_types[self.cur_type])
        
    def _activate_polygon_tool(self, curr_type):
        self.canvas.bind("<Button-1>", self.polygon_tool)
        self.canvas.bind("<Button-3>", lambda event, x=curr_type, : self.finished_annotating(event, x))
        
        self.old_x = None
        self.old_y = None
        
    def polygon_tool(self, event):
        # first point selected
        if (self.old_x == None) & (self.old_y == None):
            # reset the points list if starting a new polygon
            self.points = []
        self.canvas.unbind("<Escape>")
        self.canvas.bind("<Escape>", self._break_annotation) # can break annotation after making a point
    
        coords= (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        old_coords = (self.old_x, self.old_y)
        
        if self.old_x and self.old_y:
            try: # try for incase user presses down on q for too long
                self.canvas.create_line(old_coords, coords, smooth=True, splinesteps=36, capstyle="round",
                                    fill="gray", width=2, tag=f"temp{self.cur_type}")
            except:
                pass
        self.old_x, self.old_y = coords
        self.points.append(coords)
        self.canvas.bind("<Motion>", self.make_ghost)
        
    def make_ghost(self, event):
        old_coords = (self.old_x, self.old_y)
        coords = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

        self.canvas.delete("ghost")
        self.canvas.create_line(old_coords, coords,
                                fill = "gray", width = 2, tag = "ghost")
        # self.canvas.create_line(self.points[0], coords, smooth = True, splinesteps = 36, capstyle = "round",
        #                         fill = "gray", width = 2, tag = "ghost")
    
    def _draw_last_line(self):
        self.canvas.create_line(self.points[0], self.points[-1],
                                fill = "gray", width = 2, tag = f"temp{self.cur_type}")
         
    def _break_annotation(self, event):
        # cancels the current annotation
        self.points = []
        self.old_x = None
        self.old_y = None
        
        self.canvas.unbind("<Motion>")
        self.canvas.delete("ghost")
        
        self.canvas.delete(f"temp{self.cur_type}")
         
    def _unbind_annotations(self):
        self.canvas.delete("ghost")
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<Escape>")
        self.canvas.unbind("<Button-3>")
        
    def finished_annotating(self, event, curr_type):
        self._draw_last_line()
        self._unbind_annotations()
        self.cur_annotation[curr_type] = self.points
        self.cur_type += 1
        if (self.cur_type == len(constants.fib_types)):
            # annotated all the possible options
            self._finished_annotation()
        else:
            self._activate_polygon_tool(constants.fib_types[self.cur_type])
            self.canvas.bind("<Escape>", self._early_finished_annotation) # stop annotating early
        
    def _early_finished_annotation(self, event):
        self._unbind_annotations()
        self.cur_type -= 1
        self.cur_annotation[constants.fib_types[self.cur_type]] = self.points
        self._finished_annotation()
        
    def _finished_annotation(self):
        for i in range(self.cur_type + 1):
            self.canvas.delete(f"temp{i}")
        self.cur_type = 0
        
        # print(self.cur_annotation)
        
        annotation = Annotation(self.folder_path, self.canvas, self.tile_num, **self.cur_annotation)
        annotation.push_data()
        
        self.annotations.append(annotation)

        self.check_invalid()

        for k in self.cur_annotation.keys(): # reset cur annotation
            self.cur_annotation[k] = []

    def _fix_duplicate_points(self, points):
        if (points[0] == points[-1]):
            points.pop()
        return points

    def check_invalid(self):
        points = self.cur_annotation['papilla']
        #Checks if too long
        pupilla_area = helper.calc_area(points)
        if (pupilla_area >= constants.max_pupilla_area):
            # print(pupilla_area)
            message = ("CAUTION: \n"
                        "Most papilla of these dimensions are TOO LARGE, " 
                        "so you might consider deleting this annotation. \n \n"
                        "Ask yourself: does the traced papilla include a major blood vessel " 
                        "that could not be replaced by fibrosis? \n"
                        "Also ask yourself: could the traced papilla be annotated as several smaller papillae?"
                        ) 
            self.create_invalid_popup(message)
            return

        #Checks if too shallow
        points = self._fix_duplicate_points(points)
        min_depth = helper.calc_min_depth(points)
        curr_depth = helper.calc_longest_axis(points)
        if (helper.check_pupilla_depth(curr_depth, min_depth)):
            message = ("CAUTION: \n"
                        "Most papilla of these dimensions are TOO SHALLOW, " 
                        "so you might consider deleting this annotation. \n \n"
                        "Ask yourself: could nodular fibrosis be contained in the traced papilla?"
                        ) 
            self.create_invalid_popup(message)
        
    def create_invalid_popup(self, message):
        popup = tk.Toplevel(root, takefocus = True)
        popup.transient()
        x = root.winfo_x()
        y = root.winfo_y()
        popup.geometry("+%d+%d" % (x + 500, y + 500))
        tk.Label(popup, text = message, bg = 'red', fg = 'white').pack()

class Annotation:
    def __init__(self, folder_path, canvas, tile_id, tag=None, **kwargs):
        self.canvas = canvas
        self.tile_id = tile_id
        self.impacted = False
        
        self.db = Database(folder_path)
        if tag != None:
            self.tag = tag
        else:
            self.tag = str(int(time.time())) # create a unique tag value
        
        self.annotation_points = {key:[] for key in constants.fib_types}
        
        # not sure if necessary
        self.annotation_areas = {key:-1 for key in constants.fib_types}
        self.pupilla_axis = -1
        
        for key, value in kwargs.items():
            if key not in constants.fib_types: # ensuring all entered keys are valid
                return
            self.annotation_points[key] = value
        
        self.create_existing_annotation()
        
    def _on_click(self, event):
        for fib_type in self.annotation_points.keys():
            tag = self.tag+fib_type
            self.canvas.delete(tag)
            
        # update database here
        self.deleted = True
        self.db.delete_annotation(self.tag)
        
    def _on_enter(self, event):
        for fib_type in self.annotation_points.keys():
            tag = self.tag+fib_type
            if (not self.impacted):
                self.canvas.itemconfig(tag, fill=constants.annotation_hover_color)
            else:
                self.canvas.itemconfig(tag, fill=constants.impacted_color)
    
    def _on_leave(self, event):
        for fib_type in self.annotation_points.keys():
            tag = self.tag+fib_type
            color = constants.fib_colors[fib_type]
            self.canvas.itemconfig(tag, fill=color)
    
    def _mark_impacted(self, event):
        if (self.impacted == True):
            self.db.delete_impacted(self.tag)
            self.impacted = False
        else:
            self.db.add_impacted(self.tag)
            self.impacted = True
        
    def create_existing_annotation(self):
        for key, points in self.annotation_points.items():
            if points == []: # skip annotations that don't exist
                break
            first_coords = points[0]
            old_coords = points[0]

            # create annotation lines
            tag = self.tag + key
            color = constants.fib_colors[key]
            for coords in points[1:]:
                self.canvas.create_line(old_coords, coords, smooth=True, splinesteps=36, capstyle="round",
                                    fill=color, width=3, tag=tag)
                old_coords = coords
            self.canvas.create_line(first_coords, points[-1], smooth=True, splinesteps=36, capstyle="round",
                                    fill=color, width=3, tag=tag)
                
            self.canvas.tag_bind(tag, "<Button-1>", self._on_click)
            self.canvas.tag_bind(tag, "<Enter>", self._on_enter)
            self.canvas.tag_bind(tag, "<Leave>", self._on_leave)
            self.canvas.tag_bind(tag, "<Button-3>", self._mark_impacted)
    
    def push_data(self):
        self.db.push_annotation_data(self.annotation_points, self.tag, self.tile_id)

class InformationFrame(tk.Frame):
    def __init__(self, master, folder_path):
        # can probably make an abstract class for this
        tk.Frame.__init__(self, master)
        self.master = master
        self.db = Database(folder_path)
        
        self._create_graph_canvas()
        self._create_scrollbar()
        self._create_update_button()
        self._create_counter_bar()
        self.update_graph()

        self.completed_label = tk.Label(self, bg="red", font="Calibri 18", height=3)
        self.completed = False

        # allows resizing of image canvas
        self.rowconfigure(0, weight=1)
        
    def _create_graph_canvas(self):
        self.canvas = tk.Canvas(self, highlightthickness=0, bg='white')
        self.canvas.grid(row=0, column=0, sticky="nswe")
        self.canvas.focus_set()
        
    def _create_scrollbar(self):
        self.vbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.vbar.grid(row=0, column=1, sticky='ns')
        
        self.canvas.configure(yscrollcommand=self.vbar.set,
                              yscrollincrement='2', scrollregion=self.canvas.bbox("all"))
        self.canvas.update()
        
        self.canvas.bind('<MouseWheel>', self._verti_wheel)

    def _create_counter_bar(self):
        counts = self.db.get_counts()
        percentages = helper.get_percentages(counts)
        self.counter_frame = tk.Frame(self)
        self.counter_frame.grid(row=2, column=0)
        
        i = 0
        labels = []
        for key, color in constants.fib_colors.items():
            labels.append(tk.Label(self.counter_frame, text=f"{key}", bg=color, font=("Calibri, 10"), width=7))
            labels[i].grid(row=0, column=i, sticky='we')
            i += 1

        i = 0
        labels = []
        for key, color in constants.fib_colors.items():
            labels.append(tk.Label(self.counter_frame, text=f"{counts[i]}", bg=color, font=("Calibri, 10"), width=7))
            labels[i].grid(row=1, column=i, sticky='we')
            i += 1

        i = 0
        labels = []
        for key, color in constants.fib_colors.items():
            labels.append(tk.Label(self.counter_frame, text=f"{percentages[i]}%", bg=color, font=("Calibri, 10"), width=7))
            labels[i].grid(row=2, column=i, sticky='we')
            i += 1

        #impacted
        i_name = tk.Label(self.counter_frame, text=f"impacted", bg=constants.impacted_color, font=("Calibri, 10"), width=7) 
        i_count = tk.Label(self.counter_frame, text=f"{counts[-1]}", bg=constants.impacted_color, font=("Calibri, 10"), width=7) 
        i_perc = tk.Label(self.counter_frame, text=f"{percentages[-1]}%", bg=constants.impacted_color, font=("Calibri, 10"), width=7)
        i_name.grid(row=0, column = 4)
        i_count.grid(row=1, column = 4)
        i_perc.grid(row=2, column = 4)

    def update_graph(self):
        self.canvas.delete("all") # removes previous image
        self._create_counter_bar()
        graph = self.db.create_graphs()
        width, height = graph.size
        self._show_img(graph, self.canvas)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"), width=width) # updates scroll region so scrollbars dont break
        self.canvas.configure 
        
    def _verti_wheel(self, event):
        if event.num == 5 or event.delta == -120:  # scroll down
            self.canvas.yview('scroll', 20, 'units')
        if event.num == 4 or event.delta == 120:
            self.canvas.yview('scroll', -20, 'units')
    
    def _show_img(self, img, canvas):
        #img is PIL object
        imagetk = ImageTk.PhotoImage(img)
        imageid = canvas.create_image(0, 0, anchor="nw", image=imagetk, tag="image")
        canvas.lower(imageid)
        canvas.imagetk = imagetk # reference for garbage collection
        
    def _create_update_button(self):
        self.update_graph_button = tk.Button(self, text="Update Graphs", font=("Calibri 16"), command=self.update_graph)
        self.update_graph_button.grid(row=3, column=0, columnspan=2, sticky="we", padx=3, pady=3)

    def _update_completed_label(self, finished):
        # finished to check when the user checks/unchecks the finished box
        if finished:
            self.completed= self.db.check_completed()
            # self.completed = True
            
            if self.completed:
                completed_text = "COMPLETED - EXPORT IMMEDIATELY"
                self.completed_label.config(text=completed_text)
                self.completed_label.grid(row=1, column=0, columnspan=2, sticky='nsew')
            else:
                self.completed_label.grid_forget()
        else:
            self.completed_label.grid_forget()
        
        
class Toolbar(tk.Frame):
    def __init__(self, master, folder_path):
        tk.Frame.__init__(self, master)
        self.db = Database(folder_path)
        
        self._create_file_menu_button()
        
    def _create_file_menu_button(self):
        self.file_button = tk.Menubutton(self, text="file", relief="raised")
        self.help_button = tk.Button(self, text="help", relief="raised", command=self._show_help_screen)
        self.file_menu = tk.Menu(self.file_button, tearoff=False)
        self.file_button.configure(menu=self.file_menu)
        self.file_button.pack(side="left")
        self.help_button.pack(side="left")
        
        # self.file_menu.add_command (label="Open New Folder", command=self.open_new_folder)
        self.file_menu.add_command(label="Export Data", command=self.export_data)
        self.file_menu.add_command(label="Exit", command=root.quit)

    def _show_help_screen(self):
        message = """ANNOTATING MODE (Q): \n
                    After pressing q to starting annotating, left click to outline points for the annotation.\n
                    Once you are done with a level of annotations, press right click to finish that level.\n
                    From here, you can either left click again to start annotating a second level, or press ESC\n
                    to end the overall annotation.\n
                    If you mess up an annotation in the middle of your left clicks (before right click), you can press \n
                    ESC to cancel that level only.
                    \n\n
                    VIEWING MODE:\n
                    To delete an annotation, hover over it, and left click.\n
                    To mark an annotationg as "impacted", hover over it and right click.\n
                    For non-impacted annotations, the hover cover is red. For impacted \n
                    annotations, the hover cover is pink.
                    """
        popup = tk.Toplevel(root, takefocus = True)
        popup.transient()
        x = root.winfo_x()
        y = root.winfo_y()
        popup.geometry("+%d+%d" % (x + 500, y + 500))
        tk.Label(popup, text = message).pack()
        
    def export_data(self):
        export = tk.Toplevel()
        export.transient(root)
        export.title("Export")
        export.columnconfigure(2, weight = 1)
        
        case_name = tk.StringVar()
        new_folder_path = tk.StringVar()
        
        name = tk.Label(export, text = "Case Name:")
        name.grid(row = 1, column = 0, padx =10, pady = 10, sticky = "nsew")
        
        name_entry = tk.Entry(export, textvariable = case_name)
        name_entry.grid(row = 1, column = 1, padx =10, pady = 10, sticky = "nsew")
        
        folder_entry = tk.Entry(export, textvariable = new_folder_path)
        folder_entry.grid(row = 2, column = 0, padx =10, pady = 10, sticky = "nsew")
        
        def select_folder():
            """Selects folder where exported images should go.

                Gets the image path from file explorer on click of the browse button.
            """
            path = tk.filedialog.askdirectory()
            if path == "":
                return
            else:
                new_folder_path.set(path + "/")
                folder_entry.update()
            
        folder_button = tk.Button(export, text="Browse", command=select_folder)
        folder_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        
        def confirm():
            """Exports images to folder_path.

            Takes case name and folder path and exports biondi images to the designated folder.
            """
            if case_name.get() == "" or new_folder_path.get() == "/":
                return
            else:
                self.db.export_case(new_folder_path.get(), case_name.get())
                export.destroy()
        
        ok_button = tk.Button(export, text="Okay", command=confirm)
        ok_button.grid(row=3, column=1, padx=10, pady=10, sticky="e")

class OpeningWindow(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.pack()
        self.master = master
        self.master.geometry("580x100")
        self.master.title("Fibrosis Annotation Tool")
        
        self._create_buttons()
    
    def _create_buttons(self):
        w1 = f"Welcome to the Fibrosis Tool!\nIf you are returning to a previous session, please click on the \"Open Previous Folder\" button.\nIf you are starting a new session, please create an empty folder and select it using the \"Initiate Folder\" button."

        self.welcome_label1 = tk.Label(self, text=w1)
        self.welcome_label1.grid(row=0, column=2, sticky='nswe')
        
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=4, column=2, sticky ="ns")

        self.find_image_button = tk.Button(self.button_frame, text="Open Previous Folder", command=self.open_previous_folder)
        self.find_image_button.pack(side="left", padx=2 , pady=2)
        
        self.initiate_folder_button = tk.Button(self.button_frame, text="Initiate Folder", command=self.initiate_folder)
        self.initiate_folder_button.pack(side="left", padx=2, pady=2)

    def open_previous_folder(self, path=None):
        if path == None:
            path = tk.filedialog.askdirectory()
            if path == "":
                return

        self.destroy() #destroys the opening window
        main = MainWindow(self.master, path)
        self.pack_forget()

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
            
            folder_button = tk.Button(nf, text = "Browse...", command = lambda: folder_path.set(tk.filedialog.askdirectory()))
            folder_button.grid(row = 1, column = 1)

            file_name = tk.StringVar()
            file_ebox = tk.Entry(nf, textvariable = file_name, width = 50)
            file_ebox.grid(row = 4, column = 0)

            file_button = tk.Button(nf, text = "Browse...", command = lambda: file_name.set(tk.filedialog.askopenfilename()))
            file_button.grid(row = 4, column = 1)

            confirm_button = tk.Button(nf, text = "Confirm", command = lambda: self.confirm_initiate_function(folder_path.get(), file_name.get(), nf))
            confirm_button.grid(row = 8, column = 1)

            folder_label = tk.Label(nf, text = "Enter an empty folder directory:")
            folder_label.grid(row = 0, column = 0, sticky = 'w')

            file_label = tk.Label(nf, text = "Enter the wsi file directory:")
            file_label.grid(row = 3, column = 0, sticky = 'w')

    def confirm_initiate_function(self, folder_path, file_path, nf):
        """Initializes a new folder and creates a success label

        Calls FileManagement to initate a folder. Creates a success window on completion.
        
        Args:
            folder_path (str): Path to folder where images will be saved selected from the askdirectory.
            file_path (str): Path to the hdf5 image to be moved into the saving folder.
            nf (tk.Toplevel): Toplevel window to select the folder path and file path.
        """
        if folder_path == "" or file_path == "":
            return
        nf.destroy()
        
        self.db = Database(folder_path)
        
        # get dimensions to save into database
        tile_image = TileImage(file_path)
        max_tiles = tile_image.max_tiles
        
        Database(folder_path).initiate(file_path, max_tiles)
        done_screen = tk.Toplevel()

        success_label1 = tk.Label(done_screen, text = "Folder sucessfully initialized!")
        success_label1.grid(row = 0, column = 0, sticky = 'nswe')

        def init_confirm():
            done_screen.destroy()
            self.open_previous_folder()
            
        close_button = tk.Button(done_screen, text = "OK", command = lambda: init_confirm())
        close_button.grid(row = 3, column = 0, sticky = 's')
        
if __name__ == "__main__":
    root = tk.Tk()
    app = OpeningWindow(root)
    root.mainloop()