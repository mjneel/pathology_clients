import tkinter as tk
import numpy as np
class Application:
    def __init__(self, master):
        self.master = master
        self.master.title("Polygon Tool")
        self.canvas = tk.Canvas(self.master, bg="black", highlightthickness = 0) 
        
        self.canvas.pack(fill = "both", expand = True)
        
        dimensions = f"{500}x{500}"
        self.master.geometry(dimensions)
        
        # binds for initial line creation
        self.canvas.bind("<Button-1>", self.polygon_tool)
        
        self.prev_angle = 0
        self.passed = False
        
        self.points = []
        self.old_x = None
        self.old_y = None

    def polygon_tool(self, event):
        # first point selected
        coords= (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        old_coords = (self.old_x, self.old_y)
        
        if self.old_x and self.old_y:
            self.canvas.create_line(old_coords, coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "white", width = 5, tag = "line")
        self.old_x, self.old_y = coords
        self.points.append(coords)
        
        self.canvas.bind("<Motion>", self.make_ghost)
        self.canvas.bind("<Button-3>", self.finished_annotating)
        
    def finished_annotating(self, event):
        self.canvas.delete("ghost")
        
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<ButtonRelease-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<Motion>")
        
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<Button-1>", self.clear_canvas)
        
        # finishes the polygon for visualization
        self.canvas.create_line(self.points[0], self.points[-1], smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "white", width = 5, tag = "line")
        
        print(self.calc_area())
        p1, p2, distance = self.calc_longest_axis()
        print(distance)
        self.canvas.create_line(p1, p2, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "red", width = 5, tag = "line")
        
    def clear_canvas(self, event):
        self.canvas.delete("line")
        self.canvas.delete("angle")
        
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<Button-1>", self.polygon_tool)
        
        self.points = []
        self.old_x = None
        self.old_y = None
        
    def make_ghost(self, event):
        old_coords = (self.old_x, self.old_y)
        coords = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

        self.canvas.delete("ghost")
        self.canvas.create_line(old_coords, coords,
                                fill = "gray", width = 5, tag = "ghost")
        self.canvas.create_line(self.points[0], coords, smooth = True, splinesteps = 36, capstyle = "round",
                                fill = "gray", width = 5, tag = "ghost")
        
    def calc_area(self):
        points = self.points.copy()
        if len(points) % 2 != 0:
            #ensure even number of coordinates
            points.append(points[0])
        x, y = zip(*points) # unzip the points into x and y 
        
        # calculate the area and return
        x = np.asanyarray(x)
        y = np.asanyarray(y)
        n = len(x)
        shift_up = np.arange(-n+1, 1)
        shift_down = np.arange(-1, n-1)    
        return abs((x * (y.take(shift_up) - y.take(shift_down))).sum() / 2.0)

    def calc_longest_axis(self):
        points = self.points.copy()
        p1 = np.array(points[0])
        p2 = np.array(points[-1])
        points = np.array(points[1:-1])
        
        d = np.cross(p2 - p1, points - p1) / np.linalg.norm(p2 - p1) # array of distances from axis
        
        max_point = points[d.argmax()]
        unit_vector = (p2 - p1) / np.linalg.norm(p2-p1)
        lbda = (unit_vector[0] * (max_point[0] - p1[0])) + (unit_vector[1] * (max_point[1] - p1[1]))
        
        p4 = (unit_vector * lbda) + p1
        
        return tuple(points[d.argmax()]), tuple(p4), d.max()

if __name__ == "__main__":
    root = tk.Tk()
    App = Application(root)
    root.mainloop()

