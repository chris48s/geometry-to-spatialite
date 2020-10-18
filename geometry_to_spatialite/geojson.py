import json
import sys

from sqlite_utils import suggest_column_types

from .utils import (
    Command,
    DataImportError,
    FeatureLoader,
    create_connection,
    filename_to_table_name,
)


def load_geojson(geojson_file):
    with open(geojson_file, "r") as f:
        gj = json.load(f)

    if gj["type"] != "FeatureCollection":
        raise DataImportError(
            f"{geojson_file} must be a valid GeoJSON FeatureCollection"
        )

    for feature in gj["features"]:
        if "id" in feature:
            feature["properties"]["id"] = feature["id"]
            feature.pop("id", None)

    return gj


def geojson_to_spatialite(
    sqlite_db,
    geojson_file,
    table_name=None,
    spatialite_extension=None,
    srid=4326,
    pk=None,
    write_mode=None,
):
    """Load a GeoJSON file into a SpatiaLite database

    Args:
        sqlite_db (str): Name of the SQLite database file
        geojson_file (str): Path to a GeoJSON file to import
        table_name (str, optional): Custom table name.
            Default: ``None`` (use the GeoJSON file name)
        spatialite_extension (str, optional): Path to mod_spatialite extension. In most
            cases the spatialite extension can be automatically detected and loaded.
            If not you can manully pass a path to the .so .dylib or .dll file.
            Default: ``None`` (attempt to load automatically)
        srid (int, optional): Spatial Reference ID (SRID).
            Default: ``4326``
        pk (Union[str, list, tuple], optional): Field (str) or fields (list/tuple) to
            use as a primary key.
            Default: ``None`` (no primary key)
        write_mode (str, optional): By default we assume the target table does not
            already exist. Pass 'replace' or 'append' to overwrite or append to an
            existing table.
            Default: ``None`` (assume the table doesn't already exist)

    Returns:
        ``None``

    Raises:
        DataImportError
    """
    db = create_connection(sqlite_db, spatialite_extension)
    featurecollection = load_geojson(geojson_file)
    features = featurecollection["features"]
    columns = suggest_column_types([f["properties"] for f in features[0:100]])
    name = table_name or filename_to_table_name(geojson_file)
    loader = FeatureLoader(db, features, name, srid, pk, columns, write_mode)
    loader.load()
    db.conn.close()


cli = Command(geojson_to_spatialite, "GeoJSON")


def main():
    args = cli.parse_args(sys.argv[1:])
    cli.invoke(
        paths=args.paths,
        dbname=args.dbname,
        table=args.table,
        primary_key=args.primary_key,
        write_mode=args.write_mode,
        srid=args.srid,
        spatialite_extension=args.spatialite_extension,
    )
