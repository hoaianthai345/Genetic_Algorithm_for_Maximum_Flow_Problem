from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QFrame, QPushButton, QGridLayout
)
from PyQt5.QtGui import QFont, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from logic.ford_fulkerson import compare_ga_with_optimal


class ResultPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_graph_edges = None
        self.source_node = None
        self.sink_node = None
        self.ga_solution = None
        self.ff_solution = None
        self.graph_editor = None  # Sẽ được set bởi main_window

    def set_graph_editor(self, graph_editor):
        """Cài đặt tham chiếu đến graph_editor để hiển thị luồng"""
        self.graph_editor = graph_editor

    def init_ui(self):
        layout = QVBoxLayout()

        # Chia layout thành 2 phần ngang: Metrics và GA Results
        top_layout = QHBoxLayout()
        
        # ===== PHẦN 1: METRICS PANEL (bên trái) =====
        metrics_panel = QVBoxLayout()
        
        # GA Results header
        self.ga_label = QLabel("Kết quả thuật toán di truyền")
        self.ga_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white; padding: 5px; border-radius: 3px;")
        metrics_panel.addWidget(self.ga_label)

        # Metrics section
        metrics_frame = QFrame()
        metrics_frame.setFrameShape(QFrame.StyledPanel)
        metrics_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 8px;")
        metrics_layout = QGridLayout(metrics_frame)
        metrics_layout.setSpacing(8)
        metrics_layout.setContentsMargins(5, 5, 5, 5)
        
        # Execution time
        time_label = QLabel("Thời gian thực thi:")
        time_label.setStyleSheet("color: #3498db; font-weight: bold;")
        metrics_layout.addWidget(time_label, 0, 0)
        self.execution_time_label = QLabel("N/A")
        self.execution_time_label.setStyleSheet("color: #2c3e50;")
        metrics_layout.addWidget(self.execution_time_label, 0, 1)
        
        # Thế hệ cuối cùng cải thiện
        last_gen_label = QLabel("Thế hệ cuối cùng cải thiện:")
        last_gen_label.setStyleSheet("color: #9b59b6; font-weight: bold;")
        metrics_layout.addWidget(last_gen_label, 1, 0)
        self.last_improvement_gen_label = QLabel("N/A")
        self.last_improvement_gen_label.setStyleSheet("color: #2c3e50;")
        metrics_layout.addWidget(self.last_improvement_gen_label, 1, 1)
        
        # Tổng số thế hệ
        total_gen_label = QLabel("Tổng số thế hệ:")
        total_gen_label.setStyleSheet("color: #9b59b6; font-weight: bold;")
        metrics_layout.addWidget(total_gen_label, 2, 0)
        self.total_generations_label = QLabel("N/A")
        self.total_generations_label.setStyleSheet("color: #2c3e50;")
        metrics_layout.addWidget(self.total_generations_label, 2, 1)
        
        # Tỷ lệ hội tụ
        conv_label = QLabel("Tỷ lệ hội tụ:")
        conv_label.setStyleSheet("color: #9b59b6; font-weight: bold;")
        metrics_layout.addWidget(conv_label, 3, 0)
        self.convergence_speed_label = QLabel("N/A")
        metrics_layout.addWidget(self.convergence_speed_label, 3, 1)
        
        metrics_panel.addWidget(metrics_frame)
        
        # Comparison boxes in horizontal layout
        comparison_label = QLabel("So sánh với Ford-Fulkerson")
        comparison_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white; padding: 5px; border-radius: 3px;")
        metrics_panel.addWidget(comparison_label)
        
        # Comparison details
        comparison_details = QGridLayout()
        comparison_details.setSpacing(8)
        
        # GA results box
        ga_box = QFrame()
        ga_box.setFrameShape(QFrame.StyledPanel)
        ga_box.setStyleSheet("background-color: #3498db; border-radius: 5px; padding: 5px;")
        ga_box_layout = QVBoxLayout(ga_box)
        ga_box_layout.setContentsMargins(5, 5, 5, 5)
        ga_box_layout.setSpacing(2)
        ga_results_label = QLabel("Kết quả GA:")
        ga_results_label.setStyleSheet("color: white; font-weight: bold;")
        ga_box_layout.addWidget(ga_results_label)
        self.ga_flow_label = QLabel("Max Flow: N/A")
        self.ga_flow_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        ga_box_layout.addWidget(self.ga_flow_label)
        comparison_details.addWidget(ga_box, 0, 0)
        
        # FF results box
        ff_box = QFrame()
        ff_box.setFrameShape(QFrame.StyledPanel)
        ff_box.setStyleSheet("background-color: #9b59b6; border-radius: 5px; padding: 5px;")
        ff_box_layout = QVBoxLayout(ff_box)
        ff_box_layout.setContentsMargins(5, 5, 5, 5)
        ff_box_layout.setSpacing(2)
        ff_results_label = QLabel("Kết quả tối ưu (FF):")
        ff_results_label.setStyleSheet("color: white; font-weight: bold;")
        ff_box_layout.addWidget(ff_results_label)
        self.ff_flow_label = QLabel("Max Flow: N/A")
        self.ff_flow_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        ff_box_layout.addWidget(self.ff_flow_label)
        comparison_details.addWidget(ff_box, 0, 1)
        
        # Optimality ratio box
        ratio_box = QFrame()
        ratio_box.setFrameShape(QFrame.StyledPanel)
        ratio_box.setStyleSheet("background-color: #fcf8e8; border-radius: 5px; padding: 5px;")
        ratio_box_layout = QVBoxLayout(ratio_box)
        ratio_box_layout.setContentsMargins(5, 5, 5, 5)
        ratio_box_layout.setSpacing(2)
        ratio_label = QLabel("Tỷ lệ tối ưu:")
        ratio_label.setStyleSheet("color: #e67e22; font-weight: bold;")
        ratio_box_layout.addWidget(ratio_label)
        self.ratio_label = QLabel("N/A")
        self.ratio_label.setStyleSheet("font-size: 13px;")
        ratio_box_layout.addWidget(self.ratio_label)
        comparison_details.addWidget(ratio_box, 1, 0, 1, 2)
        
        metrics_panel.addLayout(comparison_details)
        
        # Action buttons
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 10, 0, 0)
        
        # Add run comparison button
        self.compare_button = QPushButton("Chạy giải thuật Ford-Fulkerson")
        self.compare_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6; 
                color: white; 
                font-weight: bold; 
                padding: 6px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #d2bbd8;
            }
        """)
        self.compare_button.clicked.connect(self.run_comparison)
        self.compare_button.setEnabled(False)
        buttons_layout.addWidget(self.compare_button)
        
        # Buttons in horizontal layout
        solution_buttons = QHBoxLayout()
        solution_buttons.setSpacing(5)
        
        # Add show FF solution button
        self.show_ff_button = QPushButton("Hiển thị FF")
        self.show_ff_button.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; 
                color: white; 
                font-weight: bold; 
                padding: 6px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
            QPushButton:disabled {
                background-color: #d2bbd8;
            }
        """)
        self.show_ff_button.clicked.connect(self.display_ff_solution)
        self.show_ff_button.setEnabled(False)
        solution_buttons.addWidget(self.show_ff_button)
        
        # Add show GA solution button
        self.show_ga_button = QPushButton("Hiển thị GA")
        self.show_ga_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9; 
                color: white; 
                font-weight: bold; 
                padding: 6px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background-color: #2471a3;
            }
            QPushButton:disabled {
                background-color: #a9cce3;
            }
        """)
        self.show_ga_button.clicked.connect(self.display_ga_solution)
        self.show_ga_button.setEnabled(False)
        solution_buttons.addWidget(self.show_ga_button)
        
        buttons_layout.addLayout(solution_buttons)
        metrics_panel.addLayout(buttons_layout)
        
        # Add a label to show the current displayed solution
        self.displayed_solution_label = QLabel("Đang hiển thị: N/A")
        self.displayed_solution_label.setStyleSheet("font-style: italic; color: #555; margin-top: 5px;")
        metrics_panel.addWidget(self.displayed_solution_label)
        
        # Add metrics panel to left side of top layout
        top_layout.addLayout(metrics_panel, 1)
        
        # ===== PHẦN 2: RESULTS PANEL (bên phải) =====
        results_panel = QVBoxLayout()
        
        # Biểu đồ fitness
        self.figure = Figure(figsize=(4, 2.5))
        self.canvas = FigureCanvas(self.figure)
        results_panel.addWidget(self.canvas)

        # Bảng top 5 lời giải
        table_label = QLabel("Top 5 lời giải tốt nhất:")
        table_label.setStyleSheet("color: #16a085; font-weight: bold; margin-top: 5px;")
        results_panel.addWidget(table_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Fitness", "Flow từ nguồn", "Flow vào đích"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(250)  # Giới hạn chiều cao của bảng
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #16a085;
                color: white;
                font-weight: bold;
                padding: 4px;
            }
            QTableWidget::item {
                color: #27ae60;
            }
            QTableWidget::item:alternate {
                background-color: #ecf0f1;
                color: #27ae60;
            }
        """)
        results_panel.addWidget(self.table)
        
        # Add results panel to right side of top layout
        top_layout.addLayout(results_panel, 2)
        
        # Add top layout to main layout
        layout.addLayout(top_layout)
        
        self.setLayout(layout)

    def update_results(self, fitness_history, top_5, best_solution, graph_edges=None, source=None, sink=None, metrics=None):
        # Store current graph and solution for later comparison
        if graph_edges is not None:
            self.current_graph_edges = graph_edges
            self.source_node = source
            self.sink_node = sink
            self.ga_solution = best_solution
            self.compare_button.setEnabled(True)
            self.show_ga_button.setEnabled(True) # Enable show GA button when GA results are available
            self.displayed_solution_label.setText("Đang hiển thị: GA") # Update status
        
        # Cập nhật các metrics
        if metrics:
            # Thời gian thực thi
            execution_time = metrics.get("execution_time", 0)
            self.execution_time_label.setText(f"{execution_time:.3f} giây")
            
            # Thông tin hội tụ
            last_improvement_gen = metrics.get("last_improvement_gen", 0)
            total_generations = metrics.get("total_generations", 0)
            convergence_speed = metrics.get("convergence_speed", 0)
            
            self.last_improvement_gen_label.setText(f"{last_improvement_gen}")
            self.total_generations_label.setText(f"{total_generations}")
            
            # Hiển thị tỷ lệ hội tụ với màu sắc
            conv_text = f"{convergence_speed:.2f}"
            if convergence_speed < 0.5:
                self.convergence_speed_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif convergence_speed < 0.8:
                self.convergence_speed_label.setStyleSheet("color: #f39c12; font-weight: bold;")
            else:
                self.convergence_speed_label.setStyleSheet("color: #c0392b; font-weight: bold;")
            self.convergence_speed_label.setText(conv_text)
            
        # Cập nhật biểu đồ fitness
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(fitness_history, label="Fitness theo thế hệ", color="#3498db", linewidth=2)
        
        # Đánh dấu thế hệ cuối cùng có cải thiện nếu có metrics
        if metrics and "last_improvement_gen" in metrics and fitness_history:
            last_gen = metrics["last_improvement_gen"]
            if last_gen < len(fitness_history):
                ax.axvline(x=last_gen, color='#e74c3c', linestyle='--', alpha=0.7)
                ax.annotate('Hội tụ', xy=(last_gen, fitness_history[last_gen]),
                           xytext=(last_gen+5, fitness_history[last_gen]), 
                           arrowprops=dict(facecolor='#e74c3c', shrink=0.05),
                           color='#c0392b', fontweight='bold')
                
        ax.set_xlabel("Thế hệ")
        ax.set_ylabel("Fitness")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='lower right')
        ax.set_facecolor('#f8f9fa')
        self.figure.tight_layout()
        self.canvas.draw()

        # Cập nhật bảng kết quả
        self.table.setRowCount(len(top_5))
        for i, (fitness, source_outflow, sink_inflow) in enumerate(top_5):
            fitness_item = QTableWidgetItem(f"{fitness}")
            source_item = QTableWidgetItem(f"{source_outflow}")
            sink_item = QTableWidgetItem(f"{sink_inflow}")
            
            # Highlight hàng đầu tiên (lời giải tốt nhất) với chữ đậm, nhưng giữ màu xanh lá
            if i == 0:
                fitness_item.setFont(QFont("Arial", weight=QFont.Bold))
                source_item.setFont(QFont("Arial", weight=QFont.Bold))
                sink_item.setFont(QFont("Arial", weight=QFont.Bold))
            
            self.table.setItem(i, 0, fitness_item)
            self.table.setItem(i, 1, source_item)
            self.table.setItem(i, 2, sink_item)
            
        # Cập nhật label
        source_flow = sum(flow for (u, v), flow in best_solution.items() if u == self.source_node)
        sink_flow = sum(flow for (u, v), flow in best_solution.items() if v == self.sink_node)
        self.ga_label.setText(f"Kết quả thuật toán di truyền: Max Flow = {source_flow}")
        self.ga_flow_label.setText(f"Max Flow: {source_flow}")

    def run_comparison(self):
        """Run Ford-Fulkerson and compare with GA results"""
        if not self.current_graph_edges or not self.ga_solution:
            return
            
        comparison_results = compare_ga_with_optimal(
            self.current_graph_edges,
            self.source_node,
            self.sink_node,
            self.ga_solution
        )
        
        # Update comparison labels
        ga_flow = comparison_results["ga_max_flow"]
        optimal_flow = comparison_results["optimal_max_flow"]
        ratio = comparison_results["optimality_ratio"]
        
        # Store FF solution for later display
        self.ff_solution = comparison_results["optimal_flow"]
        
        self.ga_flow_label.setText(f"Max Flow: {ga_flow}")
        self.ff_flow_label.setText(f"Max Flow: {optimal_flow}")
        
        # Format and color the ratio based on performance
        ratio_text = f"{ratio:.2f}%"
        if ratio >= 95:
            self.ratio_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        elif ratio >= 80:
            self.ratio_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 14px;")
        else:
            self.ratio_label.setStyleSheet("color: #c0392b; font-weight: bold; font-size: 14px;")
            
        self.ratio_label.setText(ratio_text)
        
        # Enable solution display buttons
        self.show_ff_button.setEnabled(True)
        self.show_ga_button.setEnabled(True)

    def display_ff_solution(self):
        """Hiển thị lời giải của Ford-Fulkerson trên đồ thị"""
        if self.graph_editor and self.ff_solution:
            self.graph_editor.display_flow(self.ff_solution)
            self.displayed_solution_label.setText("Đang hiển thị: Ford-Fulkerson")
            
    def display_ga_solution(self):
        """Hiển thị lại lời giải của GA trên đồ thị"""
        if self.graph_editor and self.ga_solution:
            self.graph_editor.display_flow(self.ga_solution)
            self.displayed_solution_label.setText("Đang hiển thị: GA")
