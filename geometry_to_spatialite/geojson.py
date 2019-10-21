import sys

import geojson

from .utils import (
    Command,
    DataImportError,
    FeatureLoader,
    create_connection,
    filename_to_table_name,
)


def load_geojson(geojson_file):
    with open(geojson_file, "r") as f:
        gj = geojson.load(f)

    if not isinstance(gj, geojson.feature.FeatureCollection) or not gj.is_valid:
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
    db = create_connection(sqlite_db, spatialite_extension)
    featurecollection = load_geojson(geojson_file)
    features = featurecollection["features"]
    name = table_name or filename_to_table_name(geojson_file)
    loader = FeatureLoader(db, features, name, srid, pk, {}, write_mode)
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
