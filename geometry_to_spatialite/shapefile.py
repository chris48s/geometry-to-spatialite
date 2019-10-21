import sys

import shapefile

from .utils import Command, FeatureLoader, create_connection, filename_to_table_name


def shp_field_to_sql_type(field):
    if field[1] == "L":
        return "INTEGER"
    if field[1] == "F":
        return "FLOAT"
    if field[1] == "N":
        if field[3] == 0:
            return "INTEGER"
        return "FLOAT"
    return "TEXT"


def shp_to_spatialite(
    sqlite_db,
    shp_file,
    table_name=None,
    spatialite_extension=None,
    srid=4326,
    pk=None,
    write_mode=None,
):
    db = create_connection(sqlite_db, spatialite_extension)
    sf = shapefile.Reader(shp_file)
    features = [rec.__geo_interface__ for rec in sf.shapeRecords()]
    columns = {
        f[0]: shp_field_to_sql_type(f) for f in sf.fields if f[0] != "DeletionFlag"
    }
    columns["geometry"] = features[0]["geometry"]["type"].upper()
    name = table_name or filename_to_table_name(shp_file)
    loader = FeatureLoader(db, features, name, srid, pk, columns, write_mode)
    loader.load()
    db.conn.close()


cli = Command(shp_to_spatialite, "SHP")


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
