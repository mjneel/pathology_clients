import numpy as np

def calc_area(points):
        
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

def calc_longest_axis(points):
    
    p1 = np.array(points[0])
    p2 = np.array(points[-1])
    points = np.array(points[1:-1])
    
    d = np.cross(p2 - p1, points - p1) / np.linalg.norm(p2 - p1) # array of distances from axis
    
    max_point = points[d.argmax()]
    unit_vector = (p2 - p1) / np.linalg.norm(p2-p1)
    lbda = (unit_vector[0] * (max_point[0] - p1[0])) + (unit_vector[1] * (max_point[1] - p1[1]))
    
    p4 = (unit_vector * lbda) + p1
    
    return tuple(points[d.argmax()]), tuple(p4), d.max()