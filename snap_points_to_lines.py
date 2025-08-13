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
    snapped_points = gpd.sjoin_nearest(left_df=points, right_df=lines, how="left", max_distance=tolerance)

    # Удаляем дубликаты (точка находится на одинаковом расстоянии от нескольких линий)
    snapped_points = snapped_points[~snapped_points.index.duplicated()]

    # Определяем ближайшую точку на линии (даже если она не является вершиной линии)
    mask = snapped_points["linegeom"].notna()
    sl = shortest_line(snapped_points.loc[mask, "geometry"].array, snapped_points.loc[mask, "linegeom"].array)
    nearest = get_point(sl, 1)
    """ # Вариант только через geopandas
    sl = snapped_points.loc[mask, "geometry"].shortest_line(snapped_points.loc[mask, "linegeom"])
    nearest = sl.interpolate(1, normalized=True) """
    snapped_points.loc[mask, "geometry"] = nearest

    # Удаляем все столбцы, созданные в процессе обработки
    return snapped_points[points.columns]
