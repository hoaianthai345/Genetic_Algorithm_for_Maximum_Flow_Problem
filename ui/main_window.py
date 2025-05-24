from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout
from ui.control_panel import ControlPanel
from ui.result_panel import ResultPanel
from ui.graph_editor import GraphEditor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GA - Maximum Flow Solver")
        self.resize(1200, 800)

        main_widget = QWidget()
        layout = QVBoxLayout()

        # Top layout
        top_layout = QHBoxLayout()
        self.graph_editor = GraphEditor()
        self.result_panel = ResultPanel()  # MUST be initialized before passed
        # Connect result panel with graph editor
        self.result_panel.set_graph_editor(self.graph_editor)
        self.control_panel = ControlPanel(self.graph_editor, self.result_panel)

        top_layout.addWidget(self.graph_editor, 3)
        top_layout.addWidget(self.control_panel, 1)

        layout.addLayout(top_layout)
        layout.addWidget(self.result_panel)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

