import geopandas as gpd
import requests
from shapely.geometry import LineString
from shapely.ops import linemerge
from shapely.wkt import loads as load_wkt

# Параметры запросов
url = "https://server_with_api.com/routing/7.0.0/global"
key_2gis = "0a0bcd00-00f0-00e0-f000-00gh0i00000j"

# Параметры построения маршрутов
ROUTE_MODE = "fastest"
TRAFFIC_MODE = "statistics"
TRANSPORT = "driving"
OUTPUT = "detailed"
LOCALE = "ru"
ALTERNATIVE = 0

# --------------------
exclude_polygons = []
# Раскомментировать, если необходимо задать области, которые следует избегать при построении маршрута
# gdf_exclude_polygons = (
#     gpd.read_file("polygons_to_avoid.gpkg", use_arrow=True).to_crs("EPSG:4326").explode().reset_index(drop=True)
# )
# exclude_polygons = []
# for geom in gdf_exclude_polygons.geometry:
#     coords = [{"lon": x, "lat": y} for x, y in geom.exterior.coords]
#     exclude_polygons.append(
#         {
#             "points": coords,
#             "type": "polygon",
#             "severity": "hard",
#         }
#     )


def find_routes(
    gdf_start: gpd.GeoDataFrame, start_field_name: str, gdf_end: gpd.GeoDataFrame, end_field_name: str
) -> gpd.GeoDataFrame:
    """
    Построение маршрутов между точками с помощью API 2ГИС

    Args:
        gdf_start: GeoDataFrame с точками начала маршрутов
        start_field_name: Имя поля с идентификатором точек начала маршрутов
        gdf_end: GeoDataFrame с точками конца маршрутов
        end_field_name: Имя поля с идентификатором точек конца маршрутов

    Returns:
        GeoDataFrame с маршрутами
    """
    list_routes: list[LineString | None] = []
    list_from_ids = []
    list_to_ids = []
    list_distances: list[float | None] = []
    list_durations: list[float | None] = []

    gdf_start = gdf_start.to_crs("EPSG:4326")
    gdf_end = gdf_end.to_crs("EPSG:4326")

    for _, (start_idx, start_row) in enumerate(gdf_start.iterrows()):
        for _, (end_idx, end_row) in enumerate(gdf_end.iterrows()):
            print(f"Начальная точка {start_idx}, Конечная точка {end_idx}")
            payload = {
                "route_mode": ROUTE_MODE,
                "traffic_mode": TRAFFIC_MODE,
                "transport": TRANSPORT,
                "output": OUTPUT,
                "locale": LOCALE,
                "alternative": ALTERNATIVE,
                "points": [
                    {"type": "stop", "lon": start_row["geometry"].x, "lat": start_row["geometry"].y},
                    {"type": "stop", "lon": end_row["geometry"].x, "lat": end_row["geometry"].y},
                ],
                "exclude": exclude_polygons,
            }

            response = requests.post(
                url, params={"key": key_2gis}, headers={"Content-Type": "application/json"}, json=payload
            )

            if response.status_code != 200:
                print(f"Ошибка: {response.status_code}")
                print(response.text)

            if response.json().get("status") == "OK":
                data = response.json()["result"]

                for route in data:
                    parts = []
                    begin_pedestrian_path = route.get("begin_pedestrian_path", {})
                    if begin_pedestrian_path:
                        geom = begin_pedestrian_path.get("geometry", {})
                        line = load_wkt(geom.get("selection"))
                        parts.append(line)
                    for man in route.get("maneuvers", []):
                        out_path = man.get("outcoming_path", {})
                        for geom in out_path.get("geometry", []):
                            try:  # порой при переходе с пешего пути на автомобильный встречаются линии из одной точки
                                line = load_wkt(geom["selection"])
                                parts.append(line)
                            except Exception:
                                pass
                    end_pedestrian_path = route.get("end_pedestrian_path", {})
                    if end_pedestrian_path:
                        geom = end_pedestrian_path.get("geometry", {})
                        line = load_wkt(geom.get("selection"))
                        parts.append(line)

                    if len(parts) == 1:
                        merged = parts[0]
                    else:
                        merged = linemerge(parts)

                    list_routes.append(merged)
                    list_distances.append(route["total_duration"])
                    list_durations.append(route["total_duration"])
                    list_from_ids.append(start_row[start_field_name])
                    list_to_ids.append(end_row[end_field_name])

            elif response.json().get("status") == "ROUTE_NOT_FOUND":
                list_routes.append(None)
                list_distances.append(0)
                list_durations.append(0)
                list_from_ids.append(start_row[start_field_name])
                list_to_ids.append(end_row[end_field_name])

            else:
                print("Неизвестная ошибка")
                list_routes.append(None)
                list_distances.append(0)
                list_durations.append(0)
                list_from_ids.append(start_row[start_field_name])
                list_to_ids.append(end_row[end_field_name])

            gdf_routes = gpd.GeoDataFrame(
                {
                    "geometry": list_routes,
                    "from": list_from_ids,
                    "to": list_to_ids,
                    "distance_meters": list_distances,
                    "duration_seconds": list_durations,
                },
                crs="EPSG:4326",
            )

    return gdf_routes


# Пример использования
gdf_start = gpd.read_file("start_points.gpkg", use_arrow=True)
gdf_end = gpd.read_file("end_points.gpkg", use_arrow=True)
gdf_routes = find_routes(gdf_start, "point_id", gdf_end, "point_id")
gdf_routes.to_file("routes.gpkg")
