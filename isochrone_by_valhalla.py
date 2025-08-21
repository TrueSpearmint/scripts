# import time

import geopandas as gpd
from routingpy import Valhalla
from shapely.geometry import Polygon
from tqdm import tqdm

# Параметры построения изохрон
PROFILE = "pedestrian"
INTERVAL_TYPE = "time"
POLYGONS = True
PREFERENCE = "fastest"

# --------------------

# Инициализация клиента Valhalla с автоматической обработкой повторных запросов и ошибок
client = Valhalla(
    base_url="https://valhalla1.openstreetmap.de",
    timeout=10,
    retry_timeout=60,
    retry_over_query_limit=True,
    skip_api_error=True,
)


def build_isochrone(client, point, interval):
    try:
        isochrone = client.isochrones(
            locations=[point],
            profile=PROFILE,
            intervals=[interval],
            interval_type=INTERVAL_TYPE,
            polygons=POLYGONS,
            preference=PREFERENCE,
        )
        return isochrone
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def build_isochrones(gdf: gpd.GeoDataFrame, field_name: str, interval: int):
    """
    Построение изохрон для точек

    Args:
        gdf: GeoDataFrame с точками
        field_name: Имя поля с идентификатором точек
        interval: Интервал изохроны в секундах или метрах

    Returns:
        GeoDataFrame с изохронами
    """
    gdf = gdf.copy().to_crs("EPSG:4326")
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    list_isochrones_geoms = []
    list_start_ids = []
    list_intervals = []
    list_interval_types = []

    for _, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Building isochrones"):
        point = row.lon, row.lat
        # Для определения оптимального timeout
        # start_time = time.time()
        isochrones = build_isochrone(client, point, interval)
        # end_time = time.time()
        # print(f"Время построения изохроны: {end_time - start_time} секунд")
        if isochrones:
            for iso in isochrones:
                if iso:
                    try:
                        isochrone_geom = Polygon(iso.geometry[0])
                    except Exception as e:
                        print(f"Ошибка при создании полигона из изохроны: {e}")
                        isochrone_geom = None
                    list_isochrones_geoms.append(isochrone_geom)
                    list_intervals.append(iso.interval)
                    list_interval_types.append(iso.interval_type)
                else:
                    list_isochrones_geoms.append(None)
                    list_intervals.append(None)
                    list_interval_types.append(None)
            list_start_ids.append(row.get(field_name, None))
        else:
            print("Не удалось построить ни одну изохрону")

    result_gdf = gpd.GeoDataFrame(
        {
            "geometry": list_isochrones_geoms,
            "start_id": list_start_ids,
            "interval": list_intervals,
            "interval_type": list_interval_types,
        },
        geometry="geometry",
        crs="EPSG:4326",
    )

    return result_gdf


# Пример использования
gdf_points = gpd.read_file("points.gpkg", use_arrow=True)
result = build_isochrones(gdf_points, "point_id", 15)
result.to_file("isochrones.gpkg")
