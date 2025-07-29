import geopandas as gpd
from shapely.ops import nearest_points, snap


def snap_points_to_lines(points_gdf: gpd.GeoDataFrame, lines_gdf: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    """
    Прилипает точки к ближайшим линиям в пределах заданного расстояния.
    Аналогично функции Snap geometries to layer в QGIS с поведением Prefer closest point, insert extra vertices where required.

    Args:
        points_gdf: GeoDataFrame с точками
        lines_gdf: GeoDataFrame с линиями
        tolerance: Максимальное расстояние для прилипания

    Returns:
        GeoDataFrame с прилипшими точками
    """
    # Копируем входные данные
    points = points_gdf.copy()
    lines = lines_gdf.copy()

    # Сохраняем геометрию линии
    lines["linegeom"] = lines.geometry

    # Находим ближайшую линию для каждой точки
    neareast_lines_to_points = gpd.sjoin_nearest(left_df=points, right_df=lines, how="left", max_distance=tolerance)
    # Удаляем дубликаты (точка находится на одинаковом расстоянии от двух линий)
    neareast_lines_to_points = neareast_lines_to_points[~neareast_lines_to_points.index.duplicated()]

    # Находим ближайшую точку
    neareast_lines_to_points["closest_point"] = neareast_lines_to_points.apply(
        lambda x: nearest_points(x.geometry, x.linegeom)[1] if x.linegeom is not None else None, axis=1
    )

    # Если есть точка для прилипания, прилипаем. Иначе оставляем исходную геометрию без изменений
    neareast_lines_to_points["geometry"] = neareast_lines_to_points.apply(
        lambda x: snap(x.geometry, x.closest_point, tolerance) if x.closest_point is not None else x.geometry, axis=1
    )

    # Удаляем все столбцы, созданные в процессе обработки
    neareast_lines_to_points = neareast_lines_to_points[[col for col in neareast_lines_to_points.columns if col in points.columns]]

    return neareast_lines_to_points
