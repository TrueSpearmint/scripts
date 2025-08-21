# import time

import geopandas as gpd
from routingpy import Valhalla
from shapely.geometry import Polygon
from tqdm import tqdm

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
            profile="pedestrian",
            intervals=[interval],
            interval_type="time",
            polygons=True,
            preference="fastest",
        )
        return isochrone
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def build_isochrones(gdf, field_name, interval):
    gdf = gdf.copy()
    gdf["lon"] = gdf.geometry.x
    gdf["lat"] = gdf.geometry.y

    list_isochrones_geoms = []
    list_intervals = []
    list_interval_types = []
    list_start_names = []

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
            list_start_names.append(row.get(field_name, None))
        else:
            print("Не удалось построить ни одну изохрону")

    result_gdf = gpd.GeoDataFrame(
        {
            "geometry": list_isochrones_geoms,
            "interval": list_intervals,
            "interval_type": list_interval_types,
            "start_name": list_start_names,
        },
        geometry="geometry",
        crs=gdf.crs,
    )

    return result_gdf
