"""
Route Optimization Module using Google OR-Tools
Zero-cost, production-grade Vehicle Routing Problem solver
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Tuple
import numpy as np


class RouteOptimizer:
    """
    Production-ready route optimizer using Google OR-Tools
    Solves Vehicle Routing Problem (VRP) with time windows
    """
    
    def __init__(self):
        self.solution = None
        
    def optimize(
        self,
        distance_matrix: List[List[float]],
        num_vehicles: int = 1,
        depot: int = 0,
        time_windows: List[Tuple[int, int]] = None,
        vehicle_capacities: List[int] = None,
        demands: List[int] = None
    ) -> List[int]:
        """
        Optimize route using OR-Tools
        
        Args:
            distance_matrix: NxN matrix of distances between locations
            num_vehicles: Number of vehicles
            depot: Starting location index
            time_windows: Optional time windows for each location
            vehicle_capacities: Optional capacity constraints
            demands: Optional demand at each location
            
        Returns:
            List of location indices in optimized order
        """
        
        # Convert distance matrix to integers (OR-Tools works better with integers)
        distance_matrix_int = [[int(d) for d in row] for row in distance_matrix]
        
        # Create routing index manager
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix_int),
            num_vehicles,
            depot
        )
        
        # Create routing model
        routing = pywrapcp.RoutingModel(manager)
        
        # Create distance callback
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix_int[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        
        # Define cost of each arc
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add capacity constraint if provided
        if vehicle_capacities and demands:
            self._add_capacity_constraints(
                routing, manager, demands, vehicle_capacities
            )
        
        # Add time window constraints if provided
        if time_windows:
            self._add_time_window_constraints(
                routing, manager, time_windows, distance_callback
            )
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(30)  # 30 second limit
        
        # Solve the problem
        self.solution = routing.SolveWithParameters(search_parameters)
        
        if not self.solution:
            # Fallback to simple nearest neighbor if optimization fails
            return self._nearest_neighbor_fallback(distance_matrix, depot)
        
        # Extract the route
        route = self._extract_route(manager, routing, self.solution)
        
        return route
    
    def _add_capacity_constraints(
        self,
        routing,
        manager,
        demands: List[int],
        vehicle_capacities: List[int]
    ):
        """Add vehicle capacity constraints"""
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            vehicle_capacities,  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )
    
    def _add_time_window_constraints(
        self,
        routing,
        manager,
        time_windows: List[Tuple[int, int]],
        distance_callback
    ):
        """Add time window constraints"""
        time = 'Time'
        routing.AddDimension(
            distance_callback,
            30,  # allow waiting time
            30000,  # maximum time per vehicle
            False,  # Don't force start cumul to zero
            time
        )
        time_dimension = routing.GetDimensionOrDie(time)
        
        # Add time window constraints for each location
        for location_idx, time_window in enumerate(time_windows):
            if location_idx == 0:
                continue
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        
        # Add time window constraints for the depot
        depot_idx = 0
        index = manager.NodeToIndex(depot_idx)
        time_dimension.CumulVar(index).SetRange(
            time_windows[0][0], time_windows[0][1]
        )
    
    def _extract_route(self, manager, routing, solution) -> List[int]:
        """Extract route from solution"""
        routes = []
        
        for vehicle_id in range(routing.vehicles()):
            index = routing.Start(vehicle_id)
            route = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route.append(node_index)
                index = solution.Value(routing.NextVar(index))
            
            # Add the end node
            route.append(manager.IndexToNode(index))
            routes.append(route)
        
        # For single vehicle, return the route
        # For multiple vehicles, return all routes
        if len(routes) == 1:
            return routes[0]
        else:
            return routes
    
    def _nearest_neighbor_fallback(
        self,
        distance_matrix: List[List[float]],
        start: int = 0
    ) -> List[int]:
        """
        Fallback to simple nearest neighbor algorithm
        if OR-Tools optimization fails
        """
        n = len(distance_matrix)
        unvisited = set(range(n))
        current = start
        route = [current]
        unvisited.remove(current)
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        # Return to depot
        route.append(start)
        
        return route
    
    def get_route_stats(self, distance_matrix: List[List[float]], route: List[int]) -> dict:
        """
        Calculate route statistics
        """
        total_distance = 0
        for i in range(len(route) - 1):
            total_distance += distance_matrix[route[i]][route[i+1]]
        
        return {
            "total_distance_meters": total_distance,
            "total_stops": len(route) - 1,  # Excluding depot
            "route_sequence": route
        }


class MLTravelTimePredictor:
    """
    Machine Learning-based travel time prediction
    Uses historical data to predict more accurate travel times
    """
    
    def __init__(self):
        self.model = None
        
    def train(self, historical_data):
        """Train ML model on historical route data"""
        # Placeholder for ML training
        # In production, use XGBoost or LightGBM
        pass
    
    def predict(self, origin, destination, time_of_day, weather=None):
        """Predict travel time between two points"""
        # Placeholder for ML prediction
        # For now, return simple estimate
        return 600  # 10 minutes in seconds


# Utility functions

def calculate_haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    Returns distance in meters
    """
    import math
    
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def create_distance_matrix_from_coordinates(coordinates: List[Tuple[float, float]]) -> List[List[float]]:
    """
    Create distance matrix from list of coordinates
    Uses Haversine formula for accurate distance calculation
    """
    n = len(coordinates)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            if i != j:
                lat1, lng1 = coordinates[i]
                lat2, lng2 = coordinates[j]
                matrix[i][j] = calculate_haversine_distance(lat1, lng1, lat2, lng2)
    
    return matrix
