import numpy as np
import random
from collections import defaultdict
from typing import List, Tuple, Dict

class GASolver:
    def __init__(self, graph_edges: List[Tuple[int, int, int]], source: int, sink: int, params: Dict):
        self.graph_edges = graph_edges
        self.source = source
        self.sink = sink
        self.capacity_map = {(u, v): cap for u, v, cap in graph_edges}
        self.n = len(set(u for u, _, _ in graph_edges) | set(v for _, v, _ in graph_edges)) # Number of nodes
        self.pop_size = params.get("pop_size", 30)
        self.generations = params.get("generations", 100)
        self.mutation_rate = params.get("mutation_rate", 0.01)
        self.top_k = params.get("top_k", 3)
        self.max_paths_crossover = params.get("max_paths_crossover", 2)
        self.adaptive_mutation = params.get("adaptive_mutation", False)
        self.tournament_size = params.get("tournament_size", 3)
        self.crossover_rate = params.get("crossover_rate", 0.8)
        
        # Create a list of all nodes for flow balancing
        self.all_nodes = set(u for u, _, _ in graph_edges) | set(v for _, v, _ in graph_edges)
        self.intermediate_nodes = self.all_nodes - {source, sink}
        
        # Create adjacency lists for quick access
        self.outgoing_edges = defaultdict(list)
        self.incoming_edges = defaultdict(list)
        for u, v, _ in graph_edges:
            self.outgoing_edges[u].append((u, v))
            self.incoming_edges[v].append((u, v))
            
        # For adaptive mutation
        self.best_fitness_history = []
        self.no_improvement_count = 0
        self.current_mutation_rate = self.mutation_rate

    # Represent flow as a dictionary {(u, v): flow_value}
    def initialize_individual(self) -> Dict[Tuple[int, int], int]:
        individual = {}
        for u, v, cap in self.graph_edges:
            individual[(u, v)] = random.randint(0, cap)
        return self.balance_flow(individual)
    
    def initialize_diverse_individual(self, bias_percentage=None) -> Dict[Tuple[int, int], int]:
        """Initialize individual with optional bias toward certain regions of the graph"""
        individual = {}
        
        if bias_percentage is None:
            # Standard random initialization
            for u, v, cap in self.graph_edges:
                individual[(u, v)] = random.randint(0, cap)
        else:
            # Biased initialization to create diverse initial population
            for u, v, cap in self.graph_edges:
                # Apply different biases based on the layer in the network
                if u == self.source:
                    # Edges from source: higher flow values
                    individual[(u, v)] = int(cap * random.uniform(bias_percentage, 1.0))
                elif v == self.sink:
                    # Edges to sink: higher flow values
                    individual[(u, v)] = int(cap * random.uniform(bias_percentage, 1.0))
                else:
                    # Intermediate edges: random flow values
                    individual[(u, v)] = random.randint(0, cap)
        
        return self.balance_flow(individual)

    def initialize_population(self) -> List[Dict[Tuple[int, int], int]]:
        population = []
        # Khởi tạo một nửa số cá thể với khởi tạo ngẫu nhiên
        standard_count = self.pop_size // 2
        for _ in range(standard_count):
            population.append(self.initialize_individual())
            
        # Tạo các cá thể với bias hướng về đường trực tiếp từ nguồn đến đích
        for i in range(self.pop_size - standard_count):
            # Thay đổi tỷ lệ bias để tạo đa dạng
            bias = 0.5 + (i / (self.pop_size - standard_count)) * 0.4  # Bias từ 0.5 đến 0.9
            population.append(self.initialize_diverse_individual(bias))
            
        return population

    def balance_flow(self, flow: Dict[Tuple[int, int], int]) -> Dict[Tuple[int, int], int]:
        """Cân bằng luồng tại các đỉnh trung gian để đảm bảo tính bảo toàn"""
        # Khởi tạo và áp dụng ràng buộc về capacity
        balanced_flow = {edge: min(flow.get(edge, 0), cap) for edge, cap in self.capacity_map.items()}
        
        # Lặp để lan truyền thay đổi qua mạng
        for _ in range(3):
            for node in self.intermediate_nodes:
                # Tính luồng vào và ra
                inflow = sum(balanced_flow.get(edge, 0) for edge in self.incoming_edges[node])
                outflow = sum(balanced_flow.get(edge, 0) for edge in self.outgoing_edges[node])
                
                if inflow == outflow:
                    continue  # Đỉnh đã cân bằng
                    
                imbalance = inflow - outflow
                
                if imbalance > 0:  # Luồng vào > luồng ra
                    self._adjust_outgoing_flow(balanced_flow, node, imbalance)
                else:  # Luồng ra > luồng vào
                    self._adjust_incoming_flow(balanced_flow, node, -imbalance)
        
        return balanced_flow

    def _adjust_outgoing_flow(self, flow, node, excess):
        """Tăng luồng ra hoặc giảm luồng vào để giảm excess"""
        # 1. Thử tăng luồng ra
        remaining = excess
        outgoing_edges = self.outgoing_edges[node]
        
        for edge in outgoing_edges:
            space = self.capacity_map[edge] - flow[edge]
            if space > 0:
                adjustment = min(space, remaining)
                flow[edge] += adjustment
                remaining -= adjustment
                if remaining <= 0:
                    return
    
        # 2. Nếu vẫn còn dư, giảm luồng vào
        if remaining > 0:
            incoming_edges = self.incoming_edges[node]
            total_inflow = sum(flow[edge] for edge in incoming_edges)
            
            if total_inflow > 0:
                ratio = (total_inflow - remaining) / total_inflow
                for edge in incoming_edges:
                    flow[edge] = int(flow[edge] * ratio)

    def _adjust_incoming_flow(self, flow, node, deficit):
        """Tăng luồng vào hoặc giảm luồng ra để bù đắp deficit"""
        # 1. Thử tăng luồng vào
        remaining = deficit
        incoming_edges = self.incoming_edges[node]
        
        for edge in incoming_edges:
            space = self.capacity_map[edge] - flow[edge]
            if space > 0:
                adjustment = min(space, remaining)
                flow[edge] += adjustment
                remaining -= adjustment
                if remaining <= 0:
                    return
                
        # 2. Nếu vẫn còn thiếu, giảm luồng ra
        if remaining > 0:
            outgoing_edges = self.outgoing_edges[node]
            total_outflow = sum(flow[edge] for edge in outgoing_edges)
            
            if total_outflow > 0:
                ratio = (total_outflow - remaining) / total_outflow
                for edge in outgoing_edges:
                    flow[edge] = int(flow[edge] * ratio)

    def build_residual_graph(self, flow: Dict[Tuple[int, int], int]) -> Dict[int, List[Tuple[int, int]]]:
        residual = defaultdict(list)
        for (u, v), f_val in flow.items():
            cap = self.capacity_map[(u,v)]
            if f_val < cap:
                residual[u].append((v, cap - f_val))
            if f_val > 0:
                residual[v].append((u, f_val))  # backward edge
        return residual

    def find_augmenting_paths(self, flow: Dict[Tuple[int, int], int], max_paths: int) -> List[Tuple[List[int], int]]:
        """
        Tìm các đường tăng luồng từ source đến sink trên đồ thị phần dư
        Trả về danh sách các đường đi (dưới dạng list các đỉnh) và giá trị bottleneck của mỗi đường
        """
        residual = self.build_residual_graph(flow)
        paths = []

        def dfs(u, visited, path_nodes):
            if u == self.sink:
                # Tính bottleneck của đường đi hiện tại
                bottleneck = float('inf')
                
                for i in range(len(path_nodes) - 1):
                    u, v = path_nodes[i], path_nodes[i+1]
                    
                    # Xác định loại cạnh (xuôi/ngược) trong đồ thị phần dư để tính capacity
                    if (u, v) in self.capacity_map:  # Cạnh xuôi trong đồ thị gốc
                        res_cap = self.capacity_map[(u, v)] - flow.get((u, v), 0)
                    else:  # Cạnh ngược trong đồ thị phần dư
                        res_cap = flow.get((v, u), 0)
                    
                    if res_cap <= 0:  # Không hợp lệ
                        return
                    
                    bottleneck = min(bottleneck, res_cap)
                
                if bottleneck > 0 and bottleneck != float('inf'):
                    paths.append((path_nodes[:], bottleneck))
                return

            # Nếu đã tìm đủ số đường cần thiết, dừng lại
            if len(paths) >= max_paths:
                return

            # Duyệt các đỉnh kề trong đồ thị phần dư
            for v, _ in residual.get(u, []):
                if v not in visited:
                    visited.add(v)
                    path_nodes.append(v)
                    dfs(v, visited, path_nodes)
                    path_nodes.pop()
                    visited.remove(v)
        
        # Cố gắng tìm nhiều đường tăng luồng
        for _ in range(max_paths):
            visited = {self.source}
            dfs(self.source, visited, [self.source])
            if len(paths) >= max_paths:
                break
                
        return paths[:max_paths]

    def crossover_path_based(self, F1: Dict[Tuple[int, int], int], F2: Dict[Tuple[int, int], int]) -> Dict[Tuple[int, int], int]:
        """
        Path-Based Crossover như mô tả:
        1. Tìm các đường tăng luồng từ cả F1 và F2
        2. Kết hợp các đường này để tạo cá thể con
        3. Giới hạn theo capacity và cân bằng luồng
        """
        # Có thể bỏ qua crossover với xác suất (1 - crossover_rate)
        if random.random() > self.crossover_rate:
            return random.choice([F1, F2]).copy()
        
        # Bước 1: Tìm đường tăng luồng từ mỗi cá thể cha mẹ
        # Số đường tăng luồng = max_paths_crossover (thường là 2-3)
        paths_F1 = self.find_augmenting_paths(F1, self.max_paths_crossover)
        paths_F2 = self.find_augmenting_paths(F2, self.max_paths_crossover)
        
        # Bước 2: Khởi tạo cá thể con là dictionary rỗng
        child_flow = defaultdict(int)
        
        # Bước 3: Kết hợp các đường tăng luồng từ cả F1 và F2
        for path, bottleneck in paths_F1 + paths_F2:
            # Với mỗi đường đi, thêm bottleneck vào các cạnh trên đường đó
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                
                # Chỉ xử lý các cạnh xuôi (forward edges) trong đồ thị gốc
                if (u, v) in self.capacity_map:
                    child_flow[(u, v)] += bottleneck
        
        # Bước 4: Giới hạn bởi capacity
        for edge in list(child_flow.keys()):
            if edge in self.capacity_map:
                child_flow[edge] = min(child_flow[edge], self.capacity_map[edge])
            else:
                # Xóa các cạnh không tồn tại trong đồ thị gốc
                del child_flow[edge]
        
        # Bước 5: Đảm bảo tất cả các cạnh đều có trong child_flow
        complete_flow = {edge: 0 for edge in self.capacity_map.keys()}
        for edge, flow_val in child_flow.items():
            if edge in complete_flow:
                complete_flow[edge] = flow_val
        
        # Bước 6: Cân bằng luồng để đảm bảo inflow = outflow tại các đỉnh trung gian
        return self.balance_flow(complete_flow)

    def compute_fitness(self, flow: Dict[Tuple[int, int], int]) -> int:
        """
        Tính độ thích nghi của một cá thể (luồng)
        Độ thích nghi = tổng luồng ra từ nguồn (hoặc vào đích)
        Với điều kiện: luồng phải bảo toàn tại các đỉnh trung gian
        """
        # Tính tổng luồng ra từ nguồn
        source_outflow = sum(f_val for (u, v), f_val in flow.items() if u == self.source)
        
        # Tính tổng luồng vào đích
        sink_inflow = sum(f_val for (u, v), f_val in flow.items() if v == self.sink)
        
        # Kiểm tra bảo toàn luồng tại các đỉnh trung gian
        for node in self.intermediate_nodes:
            inflow = sum(flow.get(edge, 0) for edge in self.incoming_edges[node])
            outflow = sum(flow.get(edge, 0) for edge in self.outgoing_edges[node])
            
            if inflow != outflow:
                # Phạt cá thể không bảo toàn luồng
                return -1
        
        # Trả về giá trị nhỏ hơn giữa luồng ra từ nguồn và luồng vào đích
        # Đảm bảo không tạo luồng "từ hư không"
        return min(source_outflow, sink_inflow)

    def mutate(self, flow: Dict[Tuple[int, int], int]) -> Dict[Tuple[int, int], int]:
        """
        Đột biến luồng: thay đổi ngẫu nhiên giá trị luồng trên một số cạnh
        """
        new_flow = flow.copy()
        
        # Sử dụng tỷ lệ đột biến thích ứng nếu được kích hoạt
        mutation_rate = self.current_mutation_rate
        
        # Đảm bảo tỷ lệ đột biến trong khoảng hợp lý
        if not self.adaptive_mutation:
            mutation_rate = min(0.02, max(0.01, mutation_rate))
        
        # Duyệt qua từng cạnh trong đồ thị
        for u, v, cap in self.graph_edges:
            # Áp dụng đột biến với xác suất mutation_rate
            if random.random() < mutation_rate:
                # Đột biến đơn giản: gán giá trị ngẫu nhiên từ 0 đến capacity
                new_flow[(u, v)] = random.randint(0, cap)
        
        # Cân bằng luồng sau khi đột biến
        return self.balance_flow(new_flow)
    
    def tournament_selection(self, population, fitness_scores, tournament_size):
        """Select an individual using tournament selection"""
        # Select tournament_size individuals randomly
        tournament_indices = random.sample(range(len(population)), min(tournament_size, len(population)))
        
        # Find the best individual in the tournament
        best_idx = tournament_indices[0]
        best_fitness = fitness_scores[best_idx]
        
        for idx in tournament_indices[1:]:
            if fitness_scores[idx] > best_fitness:
                best_idx = idx
                best_fitness = fitness_scores[idx]
                
        return population[best_idx]
    
    def update_mutation_rate(self, current_best_fitness):
        """Cập nhật tỷ lệ đột biến dựa trên lịch sử cải thiện"""
        self.best_fitness_history.append(current_best_fitness)
        
        if len(self.best_fitness_history) > 1:
            if self.best_fitness_history[-1] <= self.best_fitness_history[-2]:
                self.no_improvement_count += 1
            else:
                self.no_improvement_count = 0
        
        # Điều chỉnh tỷ lệ đột biến dựa trên mẫu cải thiện
        if self.no_improvement_count > 10:
            # Nếu không có cải thiện trong một thời gian, tăng tỷ lệ đột biến để thoát khỏi cực tiểu cục bộ
            self.current_mutation_rate = min(0.3, self.current_mutation_rate * 1.5)
        else:
            # Nếu vừa cải thiện, từ từ giảm tỷ lệ đột biến để tinh chỉnh
            self.current_mutation_rate = max(0.001, self.current_mutation_rate * 0.95)

    def run(self):
        """
        Thực thi thuật toán di truyền:
        1. Khởi tạo quần thể
        2. Lặp qua các thế hệ
           - Đánh giá độ thích nghi
           - Chọn lọc cá thể ưu tú (top-k)
           - Lai ghép và đột biến để tạo quần thể mới
        3. Trả về cá thể tốt nhất và top 5 các cá thể
        """
        # Khởi tạo các biến cần thiết
        self.graph_edges_keys_only = list(self.capacity_map.keys())
        self.current_mutation_rate = self.mutation_rate
        self.best_fitness_history = []
        self.no_improvement_count = 0

        # Khởi tạo quần thể ban đầu
        population = self.initialize_population()
        best_solution = None
        best_fitness = float('-inf')
        fitness_history = []
        
        # Theo dõi top 5 cá thể tốt nhất
        top_solutions = []

        # Lặp qua các thế hệ
        for generation in range(self.generations):
            # Tính độ thích nghi cho mỗi cá thể trong quần thể
            fitness_scores = [self.compute_fitness(ind) for ind in population]
            
            # Tìm cá thể tốt nhất trong thế hệ hiện tại
            current_max_fitness = float('-inf')
            current_best_individual = None
            if fitness_scores:
                current_max_fitness = max(fitness_scores)
                current_best_individual = population[fitness_scores.index(current_max_fitness)]

            # Cập nhật lời giải tốt nhất
            if current_max_fitness > best_fitness:
                best_fitness = current_max_fitness
                best_solution = current_best_individual.copy()
                self.no_improvement_count = 0
            else:
                self.no_improvement_count += 1

            # Ghi lại lịch sử độ thích nghi tốt nhất
            fitness_history.append(best_fitness)
            
            # Cập nhật tỷ lệ đột biến nếu kích hoạt chế độ thích ứng
            if self.adaptive_mutation:
                self.update_mutation_rate(current_max_fitness)

            # Kiểm tra điều kiện dừng sớm
            if not fitness_scores or not population:
                break

            # Sắp xếp quần thể theo độ thích nghi
            sorted_population_with_scores = sorted(zip(fitness_scores, population), 
                                                 key=lambda x: x[0], reverse=True)
            
            # Cập nhật top 5 sau mỗi thế hệ
            top_solutions = [(score, ind.copy()) for score, ind in sorted_population_with_scores[:5]]
            
            # Chọn lọc: giữ lại top_k cá thể tốt nhất (elitism)
            new_population = [ind for _, ind in sorted_population_with_scores[:self.top_k]]
            
            # Tạo phần còn lại của quần thể thông qua lai ghép và đột biến
            while len(new_population) < self.pop_size:
                # Chọn lọc: Tournament selection
                if self.tournament_size > 0 and len(population) > self.tournament_size:
                    parent1 = self.tournament_selection(population, fitness_scores, self.tournament_size)
                    parent2 = self.tournament_selection(population, fitness_scores, self.tournament_size)
                else:
                    # Hoặc chọn ngẫu nhiên nếu không dùng tournament
                    parent1 = random.choice(population)
                    parent2 = random.choice(population)
                
                # Lai ghép: Path-based crossover
                child = self.crossover_path_based(parent1, parent2)
                
                # Đột biến
                child = self.mutate(child)
                
                # Thêm vào quần thể mới
                new_population.append(child)
            
            # Cập nhật quần thể
            population = new_population[:self.pop_size]

        # Đảm bảo trả về ít nhất một cá thể khi top_solutions rỗng
        if not top_solutions and best_solution is not None:
            top_solutions = [(best_fitness, best_solution)]

        # Đảm bảo có đúng 5 phần tử
        while len(top_solutions) < 5:
            # Điền các phần tử giả nếu thiếu
            top_solutions.append((0, {}))

        # Trả về kết quả: cá thể tốt nhất, độ thích nghi, lịch sử, top 5 cá thể
        return best_solution, best_fitness, fitness_history, top_solutions

# Example usage (outside class, for testing or integration)
# graph_edges_example = [(0, 1, 10), (0, 2, 5), (1, 2, 15), (1, 3, 5), (2, 3, 10)]
# source_node_example = 0
# sink_node_example = 3
# params_example = {"pop_size": 10, "generations": 50, "mutation_rate": 0.05, "top_k": 2, "max_paths_crossover":2}

# solver = GASolver(graph_edges_example, source_node_example, sink_node_example, params_example)
# best_flow_dict, final_best_fitness, history, top_solutions = solver.run()

# print("Best flow:", best_flow_dict)
# print("Best fitness (total flow from source):", final_best_fitness)
# print("Fitness history (sample):", history[-5:])
# print("Top 5 solutions:", top_solutions)