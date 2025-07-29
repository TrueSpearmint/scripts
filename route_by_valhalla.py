import geopandas as gpd
from routingpy import Valhalla
from routingpy.exceptions import RouterApiError
from shapely.geometry import LineString
from tqdm import tqdm

# Инициализация клиента Valhalla с автоматической обработкой повторных запросов и ошибок
client = Valhalla(
    base_url="https://valhalla1.openstreetmap.de",
    timeout=10,  # таймаут на один запрос (сек)
    retry_timeout=60,  # максимальное время повторных попыток (сек)
    retry_over_query_limit=True,  # авто-обработка лимита запросов (HTTP 429)
    skip_api_error=True,  # игнорировать ошибки API (например, маршруты не найдены)
)

route_options = {"costing": "auto", "use_tolls": 0, "units": "kilometers"}


def build_route(client, start_coord, end_coord):
    try:
        route = client.directions(locations=[start_coord, end_coord], profile="auto", options=route_options)
        return route
    except RouterApiError as e:
        print(f"Router API error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def build_routes(start_gdf, end_gdf):
    routes = []
    distances = []
    from_ids = []
    to_names = []

    end_point = end_gdf.geometry.iloc[0]
    end_coord = [end_point.x, end_point.y]
    to_name = end_gdf.iloc[0].get("name", None)

    for _, row in tqdm(start_gdf.iterrows(), total=len(start_gdf), desc="Building routes"):
        start_point = row.geometry
        start_coord = [start_point.x, start_point.y]

        route = build_route(client, start_coord, end_coord)

        if route:
            shape = LineString([(pt[0], pt[1]) for pt in route.geometry])
            routes.append(shape)
            distances.append(route.distance)
        else:
            routes.append(None)
            distances.append(None)

        from_ids.append(row.get("@id", None))
        to_names.append(to_name)

    result_gdf = gpd.GeoDataFrame({"geometry": routes, "distance_km": distances, "from": from_ids, "to": to_names}, crs="EPSG:4326")

    return result_gdf


# Пример использования
start_gdf = gpd.read_file("strart_points.gpkg", use_arrow=True)
start_gdf.to_crs("EPSG:4326", inplace=True)
end_gdf = gpd.read_file("end_points.gpkg", use_arrow=True)
end_gdf.to_crs("EPSG:4326", inplace=True)

result = build_routes(start_gdf, end_gdf)
result.to_file("routes.gpkg")
