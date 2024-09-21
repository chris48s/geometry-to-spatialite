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
    geom_type="GEOMETRY",
):
    """Load a SHP file into a SpatiaLite database

    Args:
        sqlite_db (str): Name of the SQLite database file
        shp_file (str): Path to a SHP file to import
        table_name (str, optional): Custom table name.
            Default: ``None`` (use the SHP file name)
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
        geom_type (str, optional): Data type to use for the geometry column.
            Default: ``"GEOMETRY"``

    Returns:
        ``None``

    Raises:
        DataImportError
    """
    db = create_connection(sqlite_db, spatialite_extension)
    sf = shapefile.Reader(shp_file)
    features = [rec.__geo_interface__ for rec in sf.shapeRecords()]
    columns = {
        f[0]: shp_field_to_sql_type(f) for f in sf.fields if f[0] != "DeletionFlag"
    }
    name = table_name or filename_to_table_name(shp_file)
    loader = FeatureLoader(db, features, name, srid, pk, columns, write_mode, geom_type)
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
        geom_type=args.geom_type,
        spatialite_extension=args.spatialite_extension,
    )
