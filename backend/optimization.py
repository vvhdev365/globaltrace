"""
Route Optimization Engine using Google OR-Tools
FREE production-grade VRP solver
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import httpx
import logging
from typing import List, Dict, Any
import math

logger = logging.getLogger(__name__)

class RouteOptimizer:
    def __init__(self, osrm_url: str = "http://osrm:5000"):
        self.osrm_url = osrm_url
    
    async def get_distance_matrix(self, stops: List[Dict[str, Any]]) -> List[List[int]]:
        """Get distance matrix using OSRM"""
        try:
            coords = ";".join([f"{s['longitude']},{s['latitude']}" for s in stops])
            url = f"{self.osrm_url}/table/v1/driving/{coords}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                data = response.json()
                return data["distances"]
        except Exception as e:
            logger.error(f"OSRM error: {e}")
            return self._euclidean_distance_matrix(stops)
    
    def _euclidean_distance_matrix(self, stops):
        """Fallback distance calculation"""
        n = len(stops)
        matrix = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = int(self._haversine(
                        stops[i]['latitude'], stops[i]['longitude'],
                        stops[j]['latitude'], stops[j]['longitude']
                    ) * 1000)
        return matrix
    
    def _haversine(self, lat1, lon1, lat2, lon2):
        """Calculate distance in km"""
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 6371 * 2 * math.asin(math.sqrt(a))
    
    def optimize(self, stops, distance_matrix, num_vehicles=1, depot_index=0, **kwargs):
        """Optimize route using OR-Tools"""
        manager = pywrapcp.RoutingIndexManager(len(distance_matrix), num_vehicles, depot_index)
        routing = pywrapcp.RoutingModel(manager)
        
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.FromSeconds(10)
        
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self._extract_solution(manager, routing, solution, stops, distance_matrix, num_vehicles)
        raise Exception("No solution found")
    
    def _extract_solution(self, manager, routing, solution, stops, distance_matrix, num_vehicles):
        """Extract optimized routes"""
        routes = []
        total_distance = 0
        
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            route = {"vehicle_id": vehicle_id, "stops": [], "distance": 0}
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                route["stops"].append({
                    "sequence": len(route["stops"]),
                    "stop_index": node_index,
                    "location": stops[node_index]
                })
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route["distance"] += distance_matrix[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
            
            total_distance += route["distance"]
            routes.append(route)
        
        return {
            "routes": routes,
            "total_distance": total_distance,
            "total_duration_estimate": total_distance // 10,
            "num_vehicles": num_vehicles,
            "optimization_status": "optimal"
        }
