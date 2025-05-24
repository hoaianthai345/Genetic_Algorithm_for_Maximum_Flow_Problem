import collections
from typing import List, Tuple, Dict, Set


class FordFulkersonSolver:
    def __init__(self, graph_edges: List[Tuple[int, int, int]], source: int, sink: int):
        """
        Khởi tạo solver với danh sách cạnh, đỉnh nguồn và đỉnh đích
        
        Args:
            graph_edges: Danh sách cạnh dạng [(u, v, capacity)]
            source: Đỉnh nguồn
            sink: Đỉnh đích
        """
        self.graph_edges = graph_edges
        self.source = source
        self.sink = sink
        
        # Xây dựng đồ thị dưới dạng adjacency list
        self.graph = collections.defaultdict(list)
        self.capacities = {}  # (u, v) -> capacity
        
        for u, v, capacity in graph_edges:
            self.graph[u].append(v)
            # Đảm bảo chúng ta cũng có cạnh ngược để xây dựng đồ thị phần dư
            if v not in self.graph or u not in self.graph[v]:
                self.graph[v].append(u)
            
            self.capacities[(u, v)] = capacity
            # Khởi tạo cạnh ngược với capacity 0
            if (v, u) not in self.capacities:
                self.capacities[(v, u)] = 0
    
    def find_augmenting_path(self, flow: Dict[Tuple[int, int], int]) -> Tuple[List[int], int]:
        """
        Tìm đường tăng luồng bằng BFS trong đồ thị phần dư
        
        Returns:
            Tuple gồm đường đi (list các đỉnh) và giá trị bottleneck (luồng có thể đẩy thêm)
        """
        visited = {self.source}
        queue = collections.deque([(self.source, [self.source], float('inf'))])
        
        while queue:
            u, path, bottleneck = queue.popleft()
            
            if u == self.sink:
                return path, bottleneck
            
            for v in self.graph[u]:
                # Tính residual capacity
                if (u, v) in self.capacities:
                    residual = self.capacities[(u, v)] - flow.get((u, v), 0)
                else:
                    residual = 0
                
                if residual > 0 and v not in visited:
                    visited.add(v)
                    new_bottleneck = min(bottleneck, residual)
                    queue.append((v, path + [v], new_bottleneck))
        
        # Không tìm thấy đường tăng luồng
        return [], 0
    
    def solve(self) -> Tuple[Dict[Tuple[int, int], int], int]:
        """
        Thuật toán Ford-Fulkerson tìm luồng cực đại
        
        Returns:
            Tuple gồm dictionary mô tả luồng trên mỗi cạnh và giá trị luồng cực đại
        """
        # Khởi tạo luồng với giá trị 0 trên mọi cạnh
        flow = {edge: 0 for edge in self.capacities}
        max_flow = 0
        
        # Tìm đường tăng luồng cho đến khi không tìm thấy thêm đường nào
        while True:
            path, bottleneck = self.find_augmenting_path(flow)
            if not path:
                break
            
            # Cập nhật luồng dọc theo đường tăng luồng
            for i in range(len(path) - 1):
                u, v = path[i], path[i + 1]
                flow[(u, v)] = flow.get((u, v), 0) + bottleneck
                flow[(v, u)] = flow.get((v, u), 0) - bottleneck
            
            max_flow += bottleneck
        
        # Lọc bỏ các cạnh ngược và cạnh không có luồng từ kết quả
        result_flow = {}
        for (u, v), f_val in flow.items():
            if (u, v) in self.capacities and f_val > 0 and self.capacities[(u, v)] > 0:
                result_flow[(u, v)] = f_val
        
        return result_flow, max_flow


def compare_ga_with_optimal(
    graph_edges: List[Tuple[int, int, int]], 
    source: int, 
    sink: int, 
    ga_flow: Dict[Tuple[int, int], int]
) -> Dict:
    """
    So sánh kết quả GA với thuật toán Ford-Fulkerson
    
    Args:
        graph_edges: Danh sách cạnh của đồ thị
        source: Đỉnh nguồn
        sink: Đỉnh đích
        ga_flow: Dictionary mô tả luồng của GA trên mỗi cạnh
    
    Returns:
        Dict chứa các thông tin so sánh (tỷ lệ, sai lệch, v.v.)
    """
    # Tính luồng từ GA - Tổng luồng ra từ nguồn
    ga_max_flow = sum(flow for (u, v), flow in ga_flow.items() if u == source)
    
    # Tìm luồng tối ưu bằng Ford-Fulkerson
    ff_solver = FordFulkersonSolver(graph_edges, source, sink)
    ff_flow, optimal_max_flow = ff_solver.solve()
    
    # Tính các số liệu so sánh
    optimality_ratio = (ga_max_flow / optimal_max_flow * 100) if optimal_max_flow > 0 else 0
    absolute_diff = optimal_max_flow - ga_max_flow
    
    return {
        "ga_max_flow": ga_max_flow,
        "optimal_max_flow": optimal_max_flow,
        "optimality_ratio": optimality_ratio,
        "absolute_diff": absolute_diff,
        "ga_flow": ga_flow,
        "optimal_flow": ff_flow
    }


# Example usage
if __name__ == "__main__":
    # Example graph
    graph_edges_example = [(0, 1, 10), (0, 2, 5), (1, 2, 15), (1, 3, 5), (2, 3, 10)]
    source_node = 0
    sink_node = 3
    
    # Solve with Ford-Fulkerson
    ff_solver = FordFulkersonSolver(graph_edges_example, source_node, sink_node)
    optimal_flow, max_flow = ff_solver.solve()
    
    print("Optimal Flow:", optimal_flow)
    print("Maximum Flow Value:", max_flow) 