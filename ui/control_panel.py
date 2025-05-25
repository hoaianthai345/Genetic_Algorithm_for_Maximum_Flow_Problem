# ui/control_panel.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFormLayout,
    QSpinBox, QDoubleSpinBox, QMessageBox, QCheckBox, QHBoxLayout
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from logic.ga_solver import GASolver
import time
import random

# Thread riêng để chạy thuật toán GA
class GAThread(QThread):
    # Tín hiệu để trả về kết quả từ thread
    finished = pyqtSignal(object, object, object, object, float, int)
    progress = pyqtSignal(int)  # Tín hiệu báo tiến độ (generation hiện tại)
    
    def __init__(self, solver, params):
        super().__init__()
        self.solver = solver
        self.params = params
        self.running = True
        
    def run(self):
        try:
            # Đo thời gian bắt đầu
            start_time = time.time()
            
            # Chạy thuật toán với khả năng dừng
            best_solution, best_fitness, fitness_history, top_solutions, last_improvement_gen = self.solve_with_stop()
            
            # Tính thời gian thực thi
            execution_time = time.time() - start_time
            
            # Phát tín hiệu khi hoàn thành
            self.finished.emit(best_solution, best_fitness, fitness_history, top_solutions, execution_time, last_improvement_gen)
        except Exception as e:
            print(f"Error in GA thread: {e}")
            
    def solve_with_stop(self):
        """Phiên bản có thể dừng của thuật toán GA"""
        solver = self.solver
        
        # Khởi tạo các biến cần thiết từ thuật toán gốc
        solver.graph_edges_keys_only = list(solver.capacity_map.keys())
        solver.current_mutation_rate = solver.mutation_rate
        solver.best_fitness_history = []
        solver.no_improvement_count = 0

        # Khởi tạo quần thể ban đầu
        population = solver.initialize_population()
        best_solution = None
        best_fitness = float('-inf')
        fitness_history = []
        last_improvement_gen = 0  # Lưu thế hệ cuối cùng có cải thiện
        
        # Theo dõi top 5 cá thể tốt nhất
        top_solutions = []

        # Lặp qua các thế hệ
        for generation in range(solver.generations):
            # Kiểm tra nếu thread đã bị yêu cầu dừng
            if not self.running:
                break
                
            # Phát tín hiệu tiến độ
            self.progress.emit(generation)
                
            # Tính độ thích nghi cho mỗi cá thể trong quần thể
            fitness_scores = [solver.compute_fitness(ind) for ind in population]
            
            # Phần còn lại của thuật toán giống như trong GA gốc
            current_max_fitness = float('-inf')
            current_best_individual = None
            if fitness_scores:
                current_max_fitness = max(fitness_scores)
                current_best_individual = population[fitness_scores.index(current_max_fitness)]

            if current_max_fitness > best_fitness:
                best_fitness = current_max_fitness
                best_solution = current_best_individual.copy()
                solver.no_improvement_count = 0
                last_improvement_gen = generation  # Cập nhật thế hệ cuối có cải thiện
            else:
                solver.no_improvement_count += 1

            fitness_history.append(best_fitness)
            
            if solver.adaptive_mutation:
                solver.update_mutation_rate(current_max_fitness)

            if not fitness_scores or not population:
                break

            sorted_population_with_scores = sorted(zip(fitness_scores, population), 
                                                 key=lambda x: x[0], reverse=True)
            
            top_solutions = [(score, ind.copy()) for score, ind in sorted_population_with_scores[:5]]
            
            new_population = [ind for _, ind in sorted_population_with_scores[:solver.top_k]]
            
            while len(new_population) < solver.pop_size and self.running:
                if solver.tournament_size > 0 and len(population) > solver.tournament_size:
                    parent1 = solver.tournament_selection(population, fitness_scores, solver.tournament_size)
                    parent2 = solver.tournament_selection(population, fitness_scores, solver.tournament_size)
                else:
                    parent1 = random.choice(population)
                    parent2 = random.choice(population)
                
                child = solver.crossover_path_based(parent1, parent2)
                child = solver.mutate(child)
                new_population.append(child)
            
            population = new_population[:solver.pop_size]
            
            if generation % max(1, solver.generations // 10) == 0 and generation > 0:
                num_fresh = max(1, solver.pop_size // 20)
                for i in range(num_fresh):
                    if len(population) > i:
                        population[-(i+1)] = solver.initialize_diverse_individual(0.7)
                        
            # Nhỏ độ trễ để không chiếm hoàn toàn CPU
            time.sleep(0.001)

        if not top_solutions and best_solution is not None:
            top_solutions = [(best_fitness, best_solution)]

        while len(top_solutions) < 5:
            top_solutions.append((0, {}))

        return best_solution, best_fitness, fitness_history, top_solutions, last_improvement_gen
            
    def stop(self):
        """Dừng thread chạy thuật toán"""
        self.running = False

class ControlPanel(QWidget):
    def __init__(self, graph_editor, result_panel):
        super().__init__()
        self.graph_editor = graph_editor
        self.result_panel = result_panel
        self.ga_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # Các tham số GA
        self.pop_size_spin = QSpinBox()
        self.pop_size_spin.setRange(2, 200)
        self.pop_size_spin.setValue(30)
        form_layout.addRow("Kích thước quần thể (Population Size):", self.pop_size_spin)

        self.max_gen_spin = QSpinBox()
        self.max_gen_spin.setRange(1, 1000)
        self.max_gen_spin.setValue(100)
        form_layout.addRow("Số thế hệ (Max Generations):", self.max_gen_spin)

        self.mutation_rate_spin = QDoubleSpinBox()
        self.mutation_rate_spin.setDecimals(3)
        self.mutation_rate_spin.setRange(0.001, 1.0)
        self.mutation_rate_spin.setSingleStep(0.01)
        self.mutation_rate_spin.setValue(0.03)
        form_layout.addRow("Tỷ lệ đột biến (Mutation Rate):", self.mutation_rate_spin)

        self.crossover_rate_spin = QDoubleSpinBox()
        self.crossover_rate_spin.setDecimals(2)
        self.crossover_rate_spin.setRange(0.1, 1.0)
        self.crossover_rate_spin.setSingleStep(0.05)
        self.crossover_rate_spin.setValue(0.8)
        form_layout.addRow("Tỷ lệ lai ghép (Crossover Rate):", self.crossover_rate_spin)
        
        self.top_k_spin = QSpinBox()
        self.top_k_spin.setRange(1, 10)
        self.top_k_spin.setValue(3)
        form_layout.addRow("Số cá thể giữ lại (Elitism (Top-K)):", self.top_k_spin)
        
        self.paths_crossover_spin = QSpinBox()
        self.paths_crossover_spin.setRange(1, 5)
        self.paths_crossover_spin.setValue(2)
        form_layout.addRow("Số đường đi lai ghép (Max Paths Crossover):", self.paths_crossover_spin)
        
        self.tournament_size_spin = QSpinBox()
        self.tournament_size_spin.setRange(2, 10)
        self.tournament_size_spin.setValue(3)
        form_layout.addRow("Kích thước đấu chọn (Tournament Size):", self.tournament_size_spin)
        
        self.adaptive_mutation_check = QCheckBox()
        self.adaptive_mutation_check.setChecked(True)
        form_layout.addRow("Đột biến thích nghi (Adaptive Mutation):", self.adaptive_mutation_check)

        layout.addLayout(form_layout)

        # Thêm label trạng thái
        self.status_label = QLabel("Sẵn sàng chạy thuật toán")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Nút Run và Stop GA trong một hàng ngang
        buttons_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("Run GA")
        self.run_btn.clicked.connect(self.run_ga)
        self.run_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        buttons_layout.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop GA")
        self.stop_btn.clicked.connect(self.stop_ga)
        self.stop_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        self.stop_btn.setEnabled(False)  # Ban đầu không cho dừng
        buttons_layout.addWidget(self.stop_btn)
        
        layout.addLayout(buttons_layout)

        layout.addStretch()
        self.setLayout(layout)

    def run_ga(self):
        # Lấy danh sách cạnh từ graph_editor
        graph_edges = self.graph_editor.get_graph_edges()
        source_node = self.graph_editor.source_node
        sink_node = self.graph_editor.sink_node
        
        if not graph_edges:
            QMessageBox.warning(self, "Lỗi", "Không có đồ thị để chạy thuật toán.")
            return
        
        params = {
            "pop_size": self.pop_size_spin.value(),
            "generations": self.max_gen_spin.value(),
            "mutation_rate": self.mutation_rate_spin.value(),
            "crossover_rate": self.crossover_rate_spin.value(),
            "top_k": self.top_k_spin.value(),
            "max_paths_crossover": self.paths_crossover_spin.value(),
            "adaptive_mutation": self.adaptive_mutation_check.isChecked(),
            "tournament_size": self.tournament_size_spin.value()
        }

        # Khởi tạo solver
        solver = GASolver(graph_edges, source_node, sink_node, params)
        
        # Cập nhật trạng thái và nút
        self.status_label.setText("Đang chạy thuật toán...")
        self.status_label.setStyleSheet("font-weight: bold; color: blue;")
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Chạy thuật toán trong thread riêng
        self.ga_thread = GAThread(solver, params)
        self.ga_thread.finished.connect(self.on_ga_finished)
        self.ga_thread.start()

    def stop_ga(self):
        if self.ga_thread and self.ga_thread.isRunning():
            self.ga_thread.stop()
            self.status_label.setText("Đã dừng thuật toán")
            self.status_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
            self.run_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def on_ga_finished(self, best_solution, best_fitness, fitness_history, top_solutions, execution_time, last_improvement_gen):
        # Cập nhật trạng thái và nút khi hoàn thành
        self.status_label.setText("Thuật toán đã hoàn thành")
        self.status_label.setStyleSheet("font-weight: bold; color: green;")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Hiển thị kết quả cá thể tốt nhất
        self.graph_editor.display_flow(best_solution)
        
        # Chuẩn bị top 5 để hiển thị
        formatted_top_5 = []
        source_node = self.graph_editor.source_node
        sink_node = self.graph_editor.sink_node
        
        for fitness, solution in top_solutions:
            source_outflow = sum(flow for (u, v), flow in solution.items() if u == source_node)
            sink_inflow = sum(flow for (u, v), flow in solution.items() if v == sink_node)
            formatted_top_5.append((fitness, source_outflow, sink_inflow))
        
        # Tính các metric bổ sung
        total_generations = len(fitness_history)
        convergence_speed = last_improvement_gen / total_generations if total_generations > 0 else 0
        
        # Chuẩn bị metrics để hiển thị
        metrics = {
            "execution_time": execution_time,
            "total_generations": total_generations,
            "last_improvement_gen": last_improvement_gen,
            "convergence_speed": convergence_speed
        }
        
        # Cập nhật result panel với top 5 cá thể và thông tin đồ thị
        graph_edges = self.graph_editor.get_graph_edges()
        self.result_panel.update_results(
            fitness_history, 
            formatted_top_5, 
            best_solution,
            graph_edges,
            source_node,
            sink_node,
            metrics
        )
