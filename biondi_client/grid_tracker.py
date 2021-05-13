import tkinter as tk
from PIL import Image, ImageTk
import random

class GridRandomizer():
    """Randomizes the grid square order for a new instance of a folder.
    
    Uses the original randomizing logic from the excel sheet: Randomizes if set 1 or 2 is first,
    Randomizes if a or b is first for both sets. Combines all into one list
    
    Attributes:
        set1a (list): List of the original set1a
        set1b (list): List of the original set1b
        set2a (list): List of the original set2a
        set2b (list): List of the original set2b
        which_set (int): A random int from 1-2. If 1, set 1 is first. If 2, set 2 is first.
        which_subset1 (int): A random int from 1-2. If 1, set1a is first. If 2, set1b is first.
        which_subset2 (int): A random int from 1-2. If 1, set2a is first. If 2, set2b is first.
        final_order (list): where the combined order of all the sets is stored.


    Typical usage example:
         randomized = GridRandomizer().get_final_order()
    """
    def __init__(self):

        self.set1a = ["A", "C", "E", "G", "O", "Q", "S", "U", "c", "e", "g", "i", "q", "s", "u", "w"] #16
        self.set1b = ["I", "K", "M", "W", "Y", "a", "k", "m", "o"] #9
        self.set2a = ["B", "D", "F", "P", "R", "T", "d", "f", "h", "r", "t", "v"] #12
        self.set2b = ["H", "J", "L", "N", "V", "X", "Z", "b", "j", "l", "n", "p"] #12

        random.shuffle(self.set1a)
        random.shuffle(self.set1b)
        random.shuffle(self.set2a)
        random.shuffle(self.set2b)

        self.which_set = random.randint(1,2) # set 1 or 2
        self.which_subset1 = random.randint(1,2) # 1 = a, 2 = b for set 1
        self.which_subset2 = random.randint(1,2) # for set 2

        self.final_order = []
        self.set_final_order()

    def set_final_order(self):
        """Sets the order of the grid squares to final_order.

        Checks the randomized int vars to assign to final order.
        """
        set1 = []
        set2 = []
        
        #orders subsets
        if self.which_subset1 == 1:
            set1.extend(self.set1a)
            set1.extend(self.set1b)
        else:
            set1.extend(self.set1b)
            set1.extend(self.set1a)

        if self.which_subset2 == 1:
            set2.extend(self.set2a)
            set2.extend(self.set2b)
        else:
            set2.extend(self.set2b)
            set2.extend(self.set2a)

        #orders sets
        if self.which_set == 1:
            self.final_order.extend(set1)
            self.final_order.extend(set2)
        else:
            self.final_order.extend(set2)
            self.final_order.extend(set1)
            
    def get_final_order(self):
        """Returns final_order.

        Used in other classes as easy access to the final_order var.
        """
        return self.final_order


if __name__ == "__main__":
    #root = tk.Tk()
    gr = GridRandomizer()
    gr.set_final_order()
    #root.mainloop()