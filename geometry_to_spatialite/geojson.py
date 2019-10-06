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
):
    db = create_connection(sqlite_db, spatialite_extension)
    featurecollection = load_geojson(geojson_file)
    features = featurecollection["features"]
    name = table_name or filename_to_table_name(geojson_file)
    loader = FeatureLoader(db, features, name, srid, pk, {})
    loader.load()
    db.conn.close()


cli = Command(geojson_to_spatialite, "GeoJSON")


if __name__ == "__main__":
    args = cli.parse_args(sys.argv[1:])
    cli.invoke(
        paths=args.paths,
        dbname=args.dbname,
        table=args.table,
        primary_key=args.primary_key,
        srid=args.srid,
        spatialite_extension=args.spatialite_extension,
    )
