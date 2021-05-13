import enum
import numpy as np
import napari
from magicgui import magicgui
from PyQt5.QtWidgets import (QApplication, 
                            QLabel, 
                            QWidget, 
                            QVBoxLayout, 
                            QHBoxLayout, 
                            QFormLayout, 
                            QPushButton, 
                            QLineEdit, 
                            QMainWindow, 
                            QDialog, 
                            QDialogButtonBox, 
                            QFileDialog,
                            QComboBox,
                            QAction)
import os
import sys
import threading
# import queue
from database import Database

# enum of all the possible annotations
class ExclusiveCat(enum.Enum):
    NOT_ANNOTATED = ""
    red_core_spear = 'rc-spear'
    green_spear = 'g-spear'
    red_core_rod = 'rc-rod'
    green_rod = 'g-rod'
    ring = 'ring'
    kettlebell = 'kettlebell'
    saturn = 'saturn'
    oreo = 'oreo'
    multiple_speck = 'mult-speck'
    multiple_spear = 'mult-spear'
    drop = 'drop'
    crescent = 'crescent'
    
class threadsafe_iter:
    """Takes an iterator/generator and makes it thread-safe by
    serializing call to the `next` method of given iterator/generator.
    """
    def __init__(self, it):
        self.it = it
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            return self.it.__next__()
        
    def send(self, i):
        self.it.send(i)

def threadsafe_generator(f):
    """A decorator that takes a generator function and makes it thread-safe.
    """
    def g(*a, **kw):
        return threadsafe_iter(f(*a, **kw))
    return g


class OpeningWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # setting some basic formatting properties
        self.setWindowTitle("Biondi Body Classifier")
        
        # setting layout
        self.general_layout = QVBoxLayout()
        
        # setting central widgets
        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        self._central_widget.setLayout(self.general_layout)
        
        self.create_buttons()
    
    def create_buttons(self):
        text = """<h1>Biondi Body Classifer</h1>
                    <body>Continue on Existing Case: Continue work on a previous case. </body> 
                    <body> Initiate New Case: Create a new case </body"""
        self.instruct_label = QLabel(text)
        
        self.init_button = QPushButton("Initiate New Case")
        self.init_button.clicked.connect(self.open_init_window)
        
        self.return_button = QPushButton("Continue on Existing Case")
        self.return_button.clicked.connect(self.open_existing_case)
        
        self.general_layout.addWidget(self.instruct_label)
        self.general_layout.addWidget(self.return_button)
        self.general_layout.addWidget(self.init_button)

    def open_init_window(self):
        # callback function for initializing a new case
        init_window = InitDialog(self)
        init_window.exec_()
        
    def open_existing_case(self):
        main_dir = ""
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.DirectoryOnly)
        if dlg.exec_():
            main_dir = dlg.selectedFiles()[0]
        
        Viewer(main_dir)
        self.close()

class InitDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Initialize a Case")
        self.dlg_layout = QVBoxLayout()
        self.form_layout = QFormLayout()
        self.create_form_buttons()
        
        self.create_dlg_buttons()
        self.dlg_layout.addLayout(self.form_layout)
        self.dlg_layout.addWidget(self.btns)
        self.setLayout(self.dlg_layout)
        
        self.array_path = ""
        self.main_dir = ""
        self.parent = parent
        
    def create_dlg_buttons(self):
        self.btns = QDialogButtonBox()
        self.btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        
        self.btns.accepted.connect(self._on_okay_click)
        self.btns.rejected.connect(self._on_cancel_click)
        
    def create_form_buttons(self):
        self.array_dir_entry = QLineEdit()
        self.array_dir_entry.setPlaceholderText("Numpy Array Path")
        self.array_dir_button = QPushButton("Browse")
        self.array_dir_button.clicked.connect(self._on_array_click)
        
        self.main_dir_entry = QLineEdit()
        self.main_dir_entry.setPlaceholderText("Save Path")
        self.main_dir_button = QPushButton("Browse")
        self.main_dir_button.clicked.connect(self._on_main_click)
        
        array_layout = QHBoxLayout()
        array_layout.addWidget(self.array_dir_entry)
        array_layout.addWidget(self.array_dir_button)
        
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.main_dir_entry)
        main_layout.addWidget(self.main_dir_button)
        self.form_layout.addRow("Array Path (.npy): ", array_layout)
        self.form_layout.addRow("Save Path (folder): ", main_layout)

    def _on_array_click(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)

        if dlg.exec_():
            self.array_path = dlg.selectedFiles()[0]
            
        if os.path.splitext(self.array_path)[-1].lower() != ".npy":
            self.array_path = ""
            return
        
        self.array_dir_entry.setText(self.array_path)
            
    def _on_main_click(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.DirectoryOnly)

        if dlg.exec_():
            self.main_dir = dlg.selectedFiles()[0]
            
        self.main_dir_entry.setText(self.main_dir)

    def _on_okay_click(self):
        Database(self.main_dir).initiate(self.array_path)
        Viewer(self.main_dir)
        if self.parent != None:
            self.parent.close()
    
    def _on_cancel_click(self):
        self.close()
    
    
# prototype of annotation gui
@magicgui(call_button="Annotate")
def img_annotation(annotation: ExclusiveCat,
                    GR=False,
                    MAF=False,
                    MP=False):
    return {'Exclusive Category': annotation.value,
            'GR': GR,
            'MAF': MAF,
            'MP': MP
            }
class Viewer:
    def __init__(self, save_path):
        self.save_path = save_path
        self.array_path = os.path.join(self.save_path, "body_array.npy")
        self.array_length = len(np.load(self.array_path, mmap_mode="r"))
        # set starting body 
        self.curr_index = Database(self.save_path).get_starting_row(self.array_length)
        # self.queue = queue.Queue()
        
        # multithreading generator creation
        self.img_iter = self.yield_img()
        self.img_iter.__next__()
        
        with napari.gui_qt():
            self.viewer = napari.Viewer(ndisplay=3)
            # self.img_iter = self.yield_img()
            # self.img_iter.__next__()
            
            self._create_gui_widgets()
            self._change_body()
            
    def run(self, nthreads=1):
        threads = [threading.Thread(target=self.img_iter.__next__)
                                    for x in range(nthreads)]
        
        for t in threads:
            t.start()
            
        for t in threads:
            t.join()

    @threadsafe_generator
    def yield_img(self):
        while True:
            stack = np.load(self.array_path, mmap_mode="r")
            yield stack[[self.curr_index]]
    
    # below is an older version of multithreading
    # def yield_img(self, idx):
    #     stack = np.load(self.array_path, mmap_mode="r")
    #     img = stack[[idx]]
    #     del stack
    #     self.queue.put(img)
    #     # return img
    
    def update_layers(self):
        # print("updated")
        # img = self.run(nthreads=1)
        # self.img_iter.__next__()
        # self.run(nthreads=1)
        
        # pulls new image from generator
        img = self.img_iter.__next__()
        
        names = ['Hoechst', 'Thioflavin S', 'Autofluorescence']
        colors = ['cyan', 'green', 'red']
        if len(self.viewer.layers) != 0:
            for i in reversed(range(3)):
                self.viewer.layers.pop(i)
        for j in range(3):
            self.viewer.add_image(
                img[..., j],
                name=names[j],
                colormap=colors[j],
                blending='additive',
                contrast_limits=[0, 4095]
            )
        p = np.percentile(img, 90, axis=(0, 1, 2, 3))
        self.viewer.layers['Hoechst'].contrast_limits = (int(p[0]), 4095)
        self.viewer.layers['Thioflavin S'].contrast_limits = (int(p[1]), 4095)
        self.viewer.layers['Autofluorescence'].contrast_limits = (int(p[2]), 4095)
        self.viewer.layers['Hoechst'].visible = False
        
        del img
        
    def add_to_database(self, annotations):
        # print(annotations)
        
        # prevents unannotated bodies from being
        if annotations["Exclusive Category"] == "":
            return
        
        db_annotate = [self.curr_index, 
                       annotations["Exclusive Category"],
                       annotations["GR"],
                       annotations["MAF"],
                       annotations["MP"]]
        
        Database(self.save_path).add_change_annotation(db_annotate)
        
        self._next_callback()
            
    
    def _combo_callback(self, current_selection):
        self.curr_index = int(current_selection)
        
        self._change_body()
        
    def _next_callback(self):
        # prevents buttons from iterating beyond numpy array length
        if self.curr_index >= self.array_length:
            self.curr_index = self.array_length - 1
            return
        
        self.curr_index += 1
        self._change_body()
    
    def _previous_callback(self):
        # prevents buttons from iterating beyond numpy array length
        if self.curr_index <= 0:
            self.curr_index= 0
            return
        
        self.curr_index -= 1
        self._change_body()
        
    def _change_body(self):
        self.test_combo.setCurrentText(str(self.curr_index+1))
        self.update_layers()
        print(self.curr_index)
        
        annotations = Database(self.save_path).get_annotation(self.curr_index)
        print(annotations)
        # (idx, body_type, gr, maf, mp)
        
        if annotations == None:
            # resetting all the annotation values
            self.annotate_gui.annotation = ExclusiveCat.NOT_ANNOTATED
            self.annotate_gui.GR = False
            self.annotate_gui.MAF = False
            self.annotate_gui.MP = False
        else:
            self.annotate_gui.annotation = ExclusiveCat._value2member_map_[annotations[1]]
            self.annotate_gui.GR = bool(annotations[2])
            self.annotate_gui.MAF = bool(annotations[3])
            self.annotate_gui.MP = bool(annotations[4])
            
        print(self.annotate_gui)
        
    def _create_gui_widgets(self):
        self.test_combo = QComboBox()
        self.test_combo.addItems([str(i) for i in range(1, self.array_length)])
        self.viewer.window.add_dock_widget(self.test_combo)
        self.test_combo.activated.connect(self._combo_callback)
        
        previous_button = QPushButton("<")
        self.viewer.window.add_dock_widget(previous_button)
        previous_button.clicked.connect(self._previous_callback)
        
        next_button = QPushButton(">")
        self.viewer.window.add_dock_widget(next_button)
        next_button.clicked.connect(self._next_callback)
        
        self.annotate_gui = img_annotation.Gui()
        self.viewer.window.add_dock_widget(self.annotate_gui)
        self.annotate_gui.called.connect(self.add_to_database)

        self.viewer.window.file_menu.clear() # clears default file menu
        
        # file menu additions
        self.save_file = QAction("&Export Case")
        self.save_file.setShortcut("Ctrl+S")
        self.save_file.setStatusTip("Export Case")
        self.save_file.triggered.connect(self.export_case)
        
        self.new_case = QAction("&New Case")
        self.new_case.setShortcut("Ctrl+O")
        self.new_case.setStatusTip("Open Another Case")
        self.new_case.triggered.connect(self.open_new_case)
        
        self.exit_action = QAction("Exit", self.viewer.window._qt_window)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setMenuRole(QAction.QuitRole)
        
        self.viewer.window.file_menu.addAction(self.new_case)
        self.viewer.window.file_menu.addAction(self.save_file)
        self.viewer.window.file_menu.addSeparator()
        self.viewer.window.file_menu.addAction(self.exit_action)
        
        
    def export_case(self):
        name = QFileDialog.getSaveFileName(None, "Export Case", "c:\\", "CSV file (*.csv)")
        print(name[0])
        Database(self.save_path).export(name[0]) # first object is the actual path name
        
    def open_new_case(self):
        name = QFileDialog.getOpenFileName(None, "Open File", "c:\\")
        self.save_path = name[0]
        self.array_path = os.path.join(self.save_path, "body_array.npy")
        self.array_length = len(np.load(self.array_path, mmap_mode="r"))
        # set starting body 
        self.curr_index = Database(self.save_path).get_starting_row(self.array_length)
        

def main():
    app = QApplication(sys.argv)
    gui = OpeningWindow()
    gui.show()
    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()