# import time

import geopandas as gpd
from routingpy import Valhalla
from routingpy.exceptions import RouterApiError
from shapely.geometry import LineString
from tqdm import tqdm

# Параметры построения маршрутов
route_profile = "auto"
route_options = {"costing": "auto", "use_tolls": 0, "units": "kilometers"}

# --------------------

# Инициализация клиента Valhalla с автоматической обработкой повторных запросов и ошибок
client = Valhalla(
    base_url="https://valhalla1.openstreetmap.de",
    timeout=10,
    retry_timeout=60,
    retry_over_query_limit=True,
    skip_api_error=True,
)


def build_route(client, start_coord, end_coord):
    try:
        route = client.directions(locations=[start_coord, end_coord], profile=route_profile, options=route_options)
        return route
    except RouterApiError as e:
        print(f"Router API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def build_routes(gdf_start: gpd.GeoDataFrame, start_field_name: str, gdf_end: gpd.GeoDataFrame, end_field_name: str):
    """
    Построение маршрутов между точками

    Args:
        gdf_start: GeoDataFrame с точками начала маршрутов
        start_field_name: Имя поля с идентификатором точек начала маршрутов
        gdf_end: GeoDataFrame с точками конца маршрутов
        end_field_name: Имя поля с идентификатором точек конца маршрутов

    Returns:
        GeoDataFrame с маршрутами
    """
    gdf_start = gdf_start.copy().to_crs("EPSG:4326")
    gdf_end = gdf_end.copy().to_crs("EPSG:4326")

    list_routes = []
    list_from_ids = []
    list_to_ids = []
    list_distances = []

    for _, row_start in tqdm(gdf_start.iterrows(), total=len(gdf_start), desc="Building routes (starts)"):
        start_point = row_start.geometry
        start_coord = [start_point.x, start_point.y]
        from_id = row_start.get(start_field_name, None)

        for _, row_end in gdf_end.iterrows():
            end_point = row_end.geometry
            end_coord = [end_point.x, end_point.y]
            to_id = row_end.get(end_field_name, None)

            # Для определения оптимального timeout
            # start_time = time.time()
            route = build_route(client, start_coord, end_coord)
            # end_time = time.time()
            # print(f"Время построения маршрута: {end_time - start_time} секунд")

            if route:
                shape = LineString([(pt[0], pt[1]) for pt in route.geometry])
                list_routes.append(shape)
                list_distances.append(route.distance)
            else:
                list_routes.append(None)
                list_distances.append(None)

            list_from_ids.append(from_id)
            list_to_ids.append(to_id)

    result_gdf = gpd.GeoDataFrame(
        {
            "geometry": list_routes,
            "from": list_from_ids,
            "to": list_to_ids,
            "distance": list_distances,
        },
        crs="EPSG:4326",
    )

    return result_gdf


# Пример использования
gdf_start = gpd.read_file("start_points.gpkg", use_arrow=True)
gdf_end = gpd.read_file("end_points.gpkg", use_arrow=True)
result = build_routes(gdf_start, "point_id", gdf_end, "point_id")
result.to_file("routes.gpkg")
