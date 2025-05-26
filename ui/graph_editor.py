from PyQt5.QtWidgets import QWidget, QMenu, QAction, QInputDialog
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QContextMenuEvent
from PyQt5.QtCore import Qt, QPoint, QRectF
import random
import numpy as np

DEFAULT_NODE_RADIUS = 20

NODE_COLOR = QColor("#3498db")
NODE_SOURCE_COLOR = QColor("#2ecc71")
NODE_SINK_COLOR = QColor("#e74c3c")
EDGE_COLOR = QColor("#7f8c8d")
EDGE_HOVER_COLOR = QColor("#e67e22")
NODE_HOVER_COLOR = QColor("#f1c40f")
EDGE_WIDTH = 2
TEXT_COLOR = Qt.black

from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QSpinBox, QDoubleSpinBox

class GraphEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.node_radius = DEFAULT_NODE_RADIUS

        self.nodes = {}  # {node_id: QPoint}
        self.edges = {}  # {(u, v): capacity}
        self.edge_flows = {}  # {(u, v): flow}
        self.node_labels = {}  # {node_id: str}
        
        self.source_node = None
        self.sink_node = None

        self.dragging_node = None
        self.edge_creation_mode = False
        self.edge_start_node = None
        self.drag_line_end = None
        self.selected_node = None
        self.selected_edge = None

        self.hover_node = None
        self.hover_edge = None

        self.node_id_counter = 1
        self.setMouseTracking(True)

        self.init_source_sink()

        # Add UI controls
        self.num_nodes_input = QSpinBox()
        self.num_nodes_input.setRange(2, 50)
        self.num_nodes_input.setValue(6)
        self.edge_prob_input = QDoubleSpinBox()
        self.edge_prob_input.setRange(0.0, 1.0)
        self.edge_prob_input.setSingleStep(0.05)
        self.edge_prob_input.setValue(0.3)
        self.num_layers_input = QSpinBox()
        self.num_layers_input.setRange(1, 10)
        self.num_layers_input.setValue(3)
        self.clear_button = QPushButton("Clear Graph")
        self.clear_button.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.random_button = QPushButton("Random Graph")
        self.random_button.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")

        self.clear_button.clicked.connect(self.clear_graph)
        self.random_button.clicked.connect(self.run_random_graph)

        control_layout = QHBoxLayout()
        label_nodes = QLabel("Nodes:")
        label_nodes.setStyleSheet("color: black; margin-right: 20px;")
        control_layout.addWidget(label_nodes)
        self.num_nodes_input.setStyleSheet("background-color: #000000; color: white; font-weight: bold; padding: 2px; selection-background-color: #555;")
        control_layout.addWidget(self.num_nodes_input)
        
        label_layers = QLabel("Layers:")
        label_layers.setStyleSheet("color: black; margin-right: 20px;")
        control_layout.addWidget(label_layers)
        self.num_layers_input.setStyleSheet("background-color: #000000; color: white; font-weight: bold; padding: 2px; selection-background-color: #555;")
        control_layout.addWidget(self.num_layers_input)
        
        label_prob = QLabel("Edge Prob:")
        label_prob.setStyleSheet("color: black; margin-right: 20px;")
        control_layout.addWidget(label_prob)
        self.edge_prob_input.setStyleSheet("background-color: #000000; color: white; font-weight: bold; padding: 2px; selection-background-color: #555;")
        control_layout.addWidget(self.edge_prob_input)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.random_button)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(control_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def init_source_sink(self):
        source_id = 0
        sink_id = 1
        self.nodes[source_id] = QPoint(100, self.height() // 2)
        self.nodes[sink_id] = QPoint(self.width() - 100, self.height() // 2)
        self.node_labels[source_id] = "Source"
        self.node_labels[sink_id] = "Sink"
        self.source_node = source_id
        self.sink_node = sink_id
        self.node_id_counter = 2  # Vì đã dùng 0, 1

    def _get_new_node_id(self):
        node_id = self.node_id_counter  # dùng int thay vì str
        self.node_id_counter += 1
        self.node_labels[node_id] = str(node_id)
        return node_id

    def contextMenuEvent(self, event: QContextMenuEvent):
        pos = event.pos()
        clicked_node = self._get_node_at(pos)
        clicked_edge = self._get_edge_at(pos)
        menu = QMenu(self)

        if clicked_node is not None:
            # Không cho phép xóa source và sink
            if clicked_node != self.source_node and clicked_node != self.sink_node:
                delete_action = QAction("Xóa nút", self)
                delete_action.triggered.connect(lambda: self.delete_node(clicked_node))
                menu.addAction(delete_action)
                
            # Luôn cho phép thêm cạnh từ bất kỳ node nào
            add_edge_action = QAction("Bắt đầu thêm cạnh", self)
            add_edge_action.triggered.connect(lambda: self.start_add_edge(clicked_node))
            menu.addAction(add_edge_action)

        elif clicked_edge:
            delete_edge_action = QAction("Xóa cạnh", self)
            delete_edge_action.triggered.connect(lambda: self.delete_edge(clicked_edge))
            menu.addAction(delete_edge_action)

        menu.exec_(event.globalPos())

    def start_add_edge(self, node_id):
        self.edge_creation_mode = True
        self.edge_start_node = node_id
        self.drag_line_end = None

    def delete_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.edges = {k: v for k, v in self.edges.items() if node_id not in k}
            self.edge_flows = {k: v for k, v in self.edge_flows.items() if node_id not in k}
            if self.source_node == node_id:
                self.source_node = None
            if self.sink_node == node_id:
                self.sink_node = None
            self.update()

    def delete_edge(self, edge):
        if edge in self.edges:
            del self.edges[edge]
        if edge in self.edge_flows:
            del self.edge_flows[edge]
        self.update()

    def mousePressEvent(self, event):
        pos = event.pos()
        if event.button() == Qt.LeftButton:
            clicked_edge = self._get_edge_at(pos)
            if clicked_edge:
                current_capacity = self.edges.get(clicked_edge, 1)
                new_cap, ok = QInputDialog.getInt(self, "Chỉnh capacity", f"Capacity hiện tại: {current_capacity}\nNhập giá trị mới:", current_capacity, 1, 1000)
                if ok:
                    self.edges[clicked_edge] = new_cap
                self.update()
                return

            if self.edge_creation_mode and self.edge_start_node is not None:
                target_node = self._get_node_at(pos)
                if target_node is not None and target_node != self.edge_start_node:
                    # Khi tạo cạnh, không sắp xếp theo thứ tự để đảm bảo hướng từ source
                    # Đảm bảo không tạo cạnh vào source hoặc từ sink
                    if target_node != self.source_node and self.edge_start_node != self.sink_node:
                        edge = (self.edge_start_node, target_node)
                        if edge not in self.edges:
                            self.edges[edge] = 1
                            self.edge_flows[edge] = 0
                self.edge_creation_mode = False
                self.edge_start_node = None
                self.drag_line_end = None
            else:
                clicked_node = self._get_node_at(pos)
                if clicked_node is not None:
                    self.dragging_node = clicked_node 
                    self.selected_node = clicked_node
                else:
                    new_node_id = self._get_new_node_id()
                    self.nodes[new_node_id] = pos
                    self.selected_node = new_node_id
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.dragging_node:
            self.nodes[self.dragging_node] = pos
        elif self.edge_creation_mode and self.edge_start_node is not None:
            self.drag_line_end = pos

        self.hover_node = self._get_node_at(pos)
        self.hover_edge = self._get_edge_at(pos)
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_node = None
        self.update()

    def _get_node_at(self, pos):
        # Ưu tiên kiểm tra source và sink đầu tiên
        for special_id in [self.source_node, self.sink_node]:
            if special_id in self.nodes:
                point = self.nodes[special_id]
                if (point - pos).manhattanLength() < self.node_radius:
                    return special_id
                    
        # Sau đó kiểm tra các node thông thường
        for node_id, point in self.nodes.items():
            if node_id != self.source_node and node_id != self.sink_node:
                if (point - pos).manhattanLength() < self.node_radius:
                    return node_id
        return None

    def _get_edge_at(self, pos, tol=5):
        if self._get_node_at(pos):
            return None  # Ưu tiên node khi trùng vị trí
        for (u, v) in self.edges:
            p1, p2 = self.nodes[u], self.nodes[v]
            if self._point_near_line(pos, p1, p2, tol):
                return (u, v)
        return None

    def _point_near_line(self, p, a, b, tol=5):
        if a == b:
            return (p - a).manhattanLength() < tol
        ax, ay = a.x(), a.y()
        bx, by = b.x(), b.y()
        px, py = p.x(), p.y()
        abx, aby = bx - ax, by - ay
        apx, apy = px - ax, py - ay
        ab_len_sq = abx ** 2 + aby ** 2
        if ab_len_sq == 0:
            return (p - a).manhattanLength() < tol
        t = max(0, min(1, (apx * abx + apy * aby) / ab_len_sq))
        closest_x = ax + t * abx
        closest_y = ay + t * aby
        dx = px - closest_x
        dy = py - closest_y
        return dx ** 2 + dy ** 2 <= tol ** 2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), Qt.white)

        for (u, v), capacity in self.edges.items():
            if u in self.nodes and v in self.nodes:
                p1 = self.nodes[u]
                p2 = self.nodes[v]
                is_hovered = self.hover_edge == (u, v) or self.hover_edge == (v, u)
                pen_color = EDGE_HOVER_COLOR if is_hovered else EDGE_COLOR
                painter.setPen(QPen(pen_color, EDGE_WIDTH))
                painter.drawLine(p1, p2)
                mid = QPoint((p1.x() + p2.x()) // 2, (p1.y() + p2.y()) // 2)
                painter.setPen(TEXT_COLOR)
                painter.drawText(mid, f"{self.edge_flows.get((u, v), 0)}/{capacity}")

        if self.edge_creation_mode and self.edge_start_node is not None and self.drag_line_end is not None:
            painter.setPen(QPen(Qt.DashLine))
            start_point = self.nodes[self.edge_start_node]
            painter.drawLine(start_point, self.drag_line_end)

        for node_id, pos in self.nodes.items():
            if node_id == self.source_node:
                color = NODE_SOURCE_COLOR
            elif node_id == self.sink_node:
                color = NODE_SINK_COLOR
            elif node_id == self.hover_node:
                color = NODE_HOVER_COLOR
            else:
                color = NODE_COLOR

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.black)
            painter.drawEllipse(pos, self.node_radius, self.node_radius)

            painter.setPen(Qt.black)
            font = QFont("Arial", 10, QFont.Bold)
            painter.setFont(font)
            text_rect = QRectF(pos.x() - self.node_radius, pos.y() - self.node_radius, 
                               2 * self.node_radius, 2 * self.node_radius)
            painter.drawText(text_rect, Qt.AlignCenter, str(node_id))

    def clear_graph(self):
        self.nodes.clear()
        self.edges.clear()
        self.edge_flows.clear()
        self.node_id_counter = 0
        self.source_node = None
        self.sink_node = None
        self.selected_node = None
        self.selected_edge = None
        self.hover_node = None
        self.hover_edge = None
        self.init_source_sink()
        self.update()

    def run_random_graph(self):
        num_nodes = self.num_nodes_input.value()
        edge_prob = self.edge_prob_input.value()
        num_layers = self.num_layers_input.value()
        self.random_graph(num_layers=num_layers, nodes_per_layer=num_nodes, edge_prob=edge_prob)

    def random_graph(self, num_layers=3, nodes_per_layer=6, edge_prob=0.3):
        self.clear_graph()
        
        # Khởi tạo source và sink
        source_id = 0
        sink_id = 1
        self.source_node = source_id
        self.sink_node = sink_id
        self.nodes[source_id] = QPoint(100, self.height() // 2)
        self.node_labels[source_id] = "Source"
        self.nodes[sink_id] = QPoint(self.width() - 100, self.height() // 2)
        self.node_labels[sink_id] = "Sink"
        self.node_id_counter = 2

        layers = []

        # Tạo các lớp node
        for i in range(num_layers):
            layer = []
            x = int(100 + (self.width() - 200) * (i + 1) / (num_layers + 1))
            for j in range(nodes_per_layer):
                y = int(self.height() / (nodes_per_layer + 1) * (j + 1))
                new_id = self._get_new_node_id()
                self.nodes[new_id] = QPoint(x, y)
                layer.append(new_id)
            layers.append(layer)

        # Tạo cạnh từ source đến lớp đầu tiên
        for node in layers[0]:
            if random.random() < edge_prob + 0.5:
                self.edges[(source_id, node)] = random.randint(10, 30)
                self.edge_flows[(source_id, node)] = 0

        # Tạo cạnh giữa các lớp
        for i in range(num_layers - 1):
            for u in layers[i]:
                for v in layers[i + 1]:
                    if random.random() < edge_prob:
                        self.edges[(u, v)] = random.randint(10, 30)
                        self.edge_flows[(u, v)] = 0

        # Tạo cạnh từ lớp cuối đến sink
        for node in layers[-1]:
            if random.random() < edge_prob + 0.5:
                self.edges[(node, sink_id)] = random.randint(10, 30)
                self.edge_flows[(node, sink_id)] = 0

        self.update()

    def get_graph_edges(self):
        """Trả về danh sách các cạnh dưới dạng (u, v, capacity)"""
        graph_edges = []
        for (u, v), capacity in self.edges.items():
            # Đảm bảo thứ tự u, v chính xác (không sort)
            graph_edges.append((u, v, capacity))
        return graph_edges
    
    def display_flow(self, flow_dict=None):
        """
        Cập nhật giá trị flow trên từng cạnh dựa vào từ điển flow
        
        Args:
            flow_dict: Dictionary với khóa là cạnh (u,v) và giá trị là flow
        """
        if flow_dict is None:
            # Xóa hết flow nếu không có đầu vào
            self.edge_flows.clear()
        else:
            # Cập nhật flow từ dict đầu vào
            self.edge_flows = flow_dict.copy()
        self.update()

