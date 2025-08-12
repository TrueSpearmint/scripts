import geopandas as gpd
from shapely import get_point, shortest_line


def snap_points_to_lines(points: gpd.GeoDataFrame, lines: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    """
    Привязывает точки к ближайшим линиям в пределах заданного расстояния.
    Аналогична функции Snap geometries to layer в QGIS с поведением Prefer closest point, insert extra vertices where required.

    Args:
        points: GeoDataFrame с точками
        lines: GeoDataFrame с линиями
        tolerance: Максимальное расстояние для прилипания

    Returns:
        GeoDataFrame с привязанными точками
    """
    # Оставляем только геометрию из lines и записываем в отдельный столбец для использования после sjoin_nearest
    lines = lines.assign(linegeom=lines.geometry)[["geometry", "linegeom"]]

    # Для каждой точки находим ближайшую линию
    nearest_points = gpd.sjoin_nearest(left_df=points, right_df=lines, how="left", max_distance=tolerance)
    print(nearest_points)

    # Удаляем дубликаты (точка находится на одинаковом расстоянии от нескольких линий)
    nearest_points = nearest_points[~nearest_points.index.duplicated()]

    # Определяем ближайшую точку на линии (даже если она не является вершиной линии)
    mask = nearest_points["linegeom"].notna()
    sl = shortest_line(nearest_points.loc[mask, "geometry"].array, nearest_points.loc[mask, "linegeom"].array)
    nearest = get_point(sl, 1)
    nearest_points.loc[mask, "geometry"] = nearest

    # Удаляем все столбцы, созданные в процессе обработки
    return nearest_points[points.columns]
