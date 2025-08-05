import json
from datetime import date

import geopandas as gpd
import pandas as pd
from shapely import from_wkt
from tqdm import tqdm

from pynspd import Nspd, NspdFeature  # 1.1.2


def convert_date_to_str(date_value):
    """Преобразует дату в строку (если это datetime.date) или возвращает исходное значение."""
    if isinstance(date_value, date):
        return date_value.isoformat()
    return date_value


contour_test = from_wkt(
    "Polygon((37.81535121 55.76448855, 37.78840248 55.76448855, 37.78840248 55.74968214, 37.81535121 55.74968214, 37.81535121 55.76448855))"
)
contour_moscow = from_wkt(
    "Polygon((36.80313264 55.14221029, 37.96747125 55.14221029, 37.96747125 56.02123908, 36.80313264 56.02123908, 36.80313264 55.14221029))"
)

# Парсинг земельных участков по контуру
with Nspd() as nspd:
    data = []

    for i in tqdm(
        nspd.search_in_contour_iter(contour_moscow, NspdFeature.by_title("Земельные участки из ЕГРН"), only_intersects=True),
        desc="Обработка участков",
    ):

        if not i.properties.options.no_coords:
            data.append(
                {
                    # Поля для выгрузки
                    "cad_num": i.properties.options.cad_num,
                    "quarter_cad_number": i.properties.options.quarter_cad_number,
                    "objdoc_id": i.properties.options.objdoc_id,
                    "registers_id": i.properties.options.registers_id,
                    "land_record_type": i.properties.options.land_record_type,
                    "land_record_subtype": i.properties.options.land_record_subtype,
                    "land_record_reg_date": convert_date_to_str(i.properties.options.land_record_reg_date),
                    "readable_address": i.properties.options.readable_address,
                    "specified_area": i.properties.options.specified_area,
                    "declared_area": i.properties.options.declared_area,
                    "area": i.properties.options.area,
                    "status": i.properties.options.status,
                    "land_record_category_type": i.properties.options.land_record_category_type,
                    "permitted_use_established_by_document": i.properties.options.permitted_use_established_by_document,
                    "ownership_type": i.properties.options.ownership_type,
                    "cost_value": i.properties.options.cost_value,
                    "cost_index": i.properties.options.cost_index,
                    "cost_application_date": convert_date_to_str(i.properties.options.cost_application_date),
                    "cost_approvement_date": convert_date_to_str(i.properties.options.cost_approvement_date),
                    "cost_determination_date": convert_date_to_str(i.properties.options.cost_determination_date),
                    "cost_registration_date": convert_date_to_str(i.properties.options.cost_registration_date),
                    "determination_couse": i.properties.options.determination_couse,
                    "geometry": i.geometry.to_multi_shape(),
                }
            )

    df = pd.DataFrame(data)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    output_gpkg = "land_plots.gpkg"
    gdf.to_file(output_gpkg, driver="GPKG")

    print(f"Данные сохранены в {output_gpkg}")

# Парсинг зданий по контуру
with Nspd() as nspd:
    data = []

    for i in tqdm(
        nspd.search_in_contour_iter(contour_moscow, NspdFeature.by_title("Здания"), only_intersects=True), desc="Обработка зданий"
    ):

        if not i.properties.options.no_coords:
            data.append(
                {
                    "cad_num": i.properties.options.cad_num,
                    "quarter_cad_number": i.properties.options.quarter_cad_number,
                    "objdoc_id": i.properties.options.objdoc_id,
                    "registers_id": i.properties.options.registers_id,
                    "build_record_type_value": i.properties.options.build_record_type_value,
                    "build_record_registration_date": convert_date_to_str(i.properties.options.build_record_registration_date),
                    "readable_address": i.properties.options.readable_address,
                    "building_name": i.properties.options.building_name,
                    "purpose": i.properties.options.purpose,
                    "build_record_area": i.properties.options.build_record_area,
                    "status": i.properties.options.status,
                    "ownership_type": i.properties.options.ownership_type,
                    "cost_value": i.properties.options.cost_value,
                    "cost_index": i.properties.options.cost_index,
                    "floors": i.properties.options.floors,
                    "underground_floors": i.properties.options.underground_floors,
                    "materials": i.properties.options.materials,
                    "year_built": i.properties.options.year_built,
                    "year_commisioning": i.properties.options.year_commisioning,
                    "cultural_heritage_object": i.properties.options.cultural_heritage_object,
                    "united_cad_number": i.properties.options.united_cad_number,
                    "facility_cad_number": i.properties.options.facility_cad_number,
                    "cost_application_date": convert_date_to_str(i.properties.options.cost_application_date),
                    "cost_approvement_date": convert_date_to_str(i.properties.options.cost_approvement_date),
                    "cost_determination_date": convert_date_to_str(i.properties.options.cost_determination_date),
                    "cost_registration_date": convert_date_to_str(i.properties.options.cost_registration_date),
                    "cultural_heritage_val": i.properties.options.cultural_heritage_val,
                    "determination_couse": i.properties.options.determination_couse,
                    "intersected_cad_numbers": i.properties.options.intersected_cad_numbers,
                    "permitted_use_name": i.properties.options.permitted_use_name,
                    # "united_cad_numbers": i.properties.options.united_cad_numbers, # выгружается списком, у всех значение NULL
                    "geometry": i.geometry.to_multi_shape(),
                }
            )

    df = pd.DataFrame(data)
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    output_gpkg = "buildings.gpkg"
    gdf.to_file(output_gpkg, driver="GPKG")

    print(f"Данные сохранены в {output_gpkg}")


# Парсинг сооружений по контуру
with Nspd() as nspd:
    data = []

    for i in tqdm(
        nspd.search_in_contour_iter(contour_moscow, NspdFeature.by_title("Сооружения"), only_intersects=True), desc="Обработка сооружений"
    ):

        if not i.properties.options.no_coords:
            data.append(
                {
                    "cad_number": i.properties.options.cad_number,
                    "quarter_cad_number": i.properties.options.quarter_cad_number,
                    # "objdoc_id": i.properties.options.objdoc_id,
                    # "registers_id": i.properties.options.registers_id,
                    "object_type_value": i.properties.options.object_type_value,
                    "registration_date": convert_date_to_str(i.properties.options.registration_date),
                    "address_readable_address": i.properties.options.address_readable_address,
                    "params_name": i.properties.options.params_name,
                    "params_purpose": i.properties.options.params_purpose,
                    "params_height": i.properties.options.params_height,
                    "params_depth": i.properties.options.params_depth,
                    "params_occurence_depth": i.properties.options.params_occurence_depth,
                    "params_extension": i.properties.options.params_extension,
                    "params_volume": i.properties.options.params_volume,
                    "params_built_up_area": i.properties.options.params_built_up_area,
                    "params_area": i.properties.options.params_area,
                    "object_previously_posted": i.properties.options.object_previously_posted,
                    "ownership_type": i.properties.options.ownership_type,
                    "cost_value": i.properties.options.cost_value,
                    "cost_index": i.properties.options.cost_index,
                    "params_floors": i.properties.options.params_floors,
                    "params_underground_floors": i.properties.options.params_underground_floors,
                    "params_year_built": i.properties.options.params_year_built,
                    "params_year_commisioning": i.properties.options.params_year_commisioning,
                    # "cultural_heritage_object": i.properties.options.cultural_heritage_object,
                    # "united_cad_number": i.properties.options.united_cad_number,
                    "facility_cad_number": i.properties.options.facility_cad_number,
                    "cost_application_date": convert_date_to_str(i.properties.options.cost_application_date),
                    "cost_approvement_date": convert_date_to_str(i.properties.options.cost_approvement_date),
                    "cost_determination_date": convert_date_to_str(i.properties.options.cost_determination_date),
                    "cost_registration_date": convert_date_to_str(i.properties.options.cost_registration_date),
                    "cultural_heritage_val": i.properties.options.cultural_heritage_val,
                    "determination_couse": i.properties.options.determination_couse,
                    "permitted_uses_name": i.properties.options.permitted_uses_name,
                    # "right_type": i.properties.options.right_type, # не парсится
                    "status": i.properties.options.status,
                    "geometry": i.geometry.to_multi_shape(),
                }
            )

    df = pd.DataFrame(data)
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    output_gpkg = "installations.gpkg"
    gdf.to_file(output_gpkg, driver="GPKG")

    print(f"Данные сохранены в {output_gpkg}")


# Парсинг объектов незавершенного строительства по контуру
with Nspd() as nspd:
    data = []

    for i in tqdm(
        nspd.search_in_contour_iter(contour_moscow, NspdFeature.by_title("Объекты незавершенного строительства"), only_intersects=True),
        desc="Обработка объектов незавершенного строительства",
    ):

        if not i.properties.options.no_coords:
            data.append(
                {
                    "cad_num": i.properties.options.cad_num,
                    "quarter_cad_number": i.properties.options.quarter_cad_number,
                    "objdoc_id": i.properties.options.objdoc_id,
                    "registers_id": i.properties.options.registers_id,
                    "object_under_construction_record_record_type_value": i.properties.options.object_under_construction_record_record_type_value,
                    "registration_date": convert_date_to_str(i.properties.options.registration_date),
                    "readable_address": i.properties.options.readable_address,
                    "object_under_construction_record_name": i.properties.options.object_under_construction_record_name,
                    "height": i.properties.options.height,
                    "depth": i.properties.options.depth,
                    "occurence_depth": i.properties.options.occurence_depth,
                    "extension": i.properties.options.extension,
                    "volume": i.properties.options.volume,
                    "built_up_area": i.properties.options.built_up_area,
                    "common_data_status": i.properties.options.common_data_status,
                    "ownership_type": i.properties.options.ownership_type,
                    "cost_value": i.properties.options.cost_value,
                    "cost_index": i.properties.options.cost_index,
                    "degree_readiness": i.properties.options.degree_readiness,
                    "purpose": i.properties.options.purpose,
                    "facility_cad_number": i.properties.options.facility_cad_number,
                    "area": i.properties.options.area,
                    "cost_application_date": convert_date_to_str(i.properties.options.cost_application_date),
                    "cost_approvement_date": convert_date_to_str(i.properties.options.cost_approvement_date),
                    "cost_determination_date": convert_date_to_str(i.properties.options.cost_determination_date),
                    "cost_registration_date": convert_date_to_str(i.properties.options.cost_registration_date),
                    "determination_couse": i.properties.options.determination_couse,
                    "name": i.properties.options.name,
                    "right_type": i.properties.options.right_type,
                    "status": i.properties.options.status,
                    "type_value": i.properties.options.type_value,
                    "geometry": i.geometry.to_multi_shape(),
                }
            )

    df = pd.DataFrame(data)
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, list) else x)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    output_gpkg = "unfinished_constructions.gpkg"
    gdf.to_file(output_gpkg, driver="GPKG")

    print(f"Данные сохранены в {output_gpkg}")
