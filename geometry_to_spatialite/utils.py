import argparse
import copy
import fnmatch
import os
import random
import sqlite3
import string

from shapely.geometry import shape
from sqlite_utils import Database

EXT_NAMES = (
    "mod_spatialite",  # linux
    "mod_spatialite.so",  # linux
    "mod_spatialite.dylib",  # macOS
)


class DataImportError(Exception):
    pass


def files_from_paths(paths, pattern):
    # This copies the csvs_to_sqlite() function from
    # https://github.com/simonw/csvs-to-sqlite/blob/1.0/csvs_to_sqlite/utils.py#L55-L87
    # Given this tool is primarily to be used with datasette,
    # it is good to adopt a similar approach to other common
    # tooling from the datasette ecosystem.
    files = {}

    def add_item(filepath, full_path=None):
        name = os.path.splitext(os.path.basename(filepath))[0]
        if name in files:
            i = 1
            while True:
                name_plus_suffix = "{}-{}".format(name, i)
                if name_plus_suffix not in files:
                    name = name_plus_suffix
                    break
                else:
                    i += 1
        if full_path is None:
            files[name] = filepath
        else:
            files[name] = full_path

    for path in paths:
        if os.path.isfile(path):
            add_item(path)
        elif os.path.isdir(path):
            # Recursively seek out ALL files in directory matching pattern
            for root, dirnames, filenames in os.walk(path):
                for filename in fnmatch.filter(filenames, pattern):
                    relpath = os.path.relpath(root, path)
                    namepath = os.path.join(relpath, os.path.splitext(filename)[0])
                    files[namepath] = os.path.join(root, filename)

    return files


def filename_to_table_name(path):
    _, filename = os.path.split(path)
    table_name, _ = os.path.splitext(filename)
    return table_name


def enable_spatialite_extension(conn, extension):
    if extension:
        conn.load_extension(extension)
    else:
        for ext in EXT_NAMES:
            try:
                conn.load_extension(ext)
                return
            except sqlite3.OperationalError:
                continue
    raise DataImportError(
        "Failed to load the SpatiaLite extension. See "
        "https://github.com/chris48s/geometry-to-spatialite#failed-to-load-the-spatialite-extension "
        "for more info."
    )


def create_connection(sqlite_db, extension):
    conn = sqlite3.connect(sqlite_db)
    conn.enable_load_extension(True)
    enable_spatialite_extension(conn, extension)
    try:
        conn.execute("SELECT srid FROM spatial_ref_sys LIMIT 1;")
    except sqlite3.OperationalError:
        conn.execute("SELECT InitSpatialMetadata(1);")
    return Database(conn)


def escape(name):
    return name.replace('"', '""')


class TempTable:
    def __init__(self, db, columns, pk):
        self.db = db
        self.table = self.get_table()
        self.name = self.table.name
        if columns:
            self.table.create(columns, pk=pk)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.table.drop()
        self.db.conn.commit()

    def get_table(self):
        # generate a random table name
        while True:
            choices = string.ascii_letters
            table_name = "".join([random.choice(choices) for i in range(0, 8)])
            if table_name not in self.db.table_names():
                return self.db[table_name]

    def insert_all(self, records, **kwargs):
        self.table.insert_all(records, **kwargs)


class GeometryTable:
    def __init__(self, db, table_name, srid, geom_type):
        self.db = db
        self.table = table_name
        self.name = self.table.name
        self.srid = srid
        self.geom_type = geom_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.db.conn.commit()

    @property
    def table(self):
        return self._table

    @table.setter
    def table(self, table_name):
        if table_name in self.db.table_names():
            raise DataImportError(f"Table '{table_name}' already exists")
        self._table = self.db[table_name]

    def create_from(self, temp_table):
        # create table based on the structure of temp_table
        table_info = self.db.conn.execute(
            f'PRAGMA table_info("{temp_table.name}");'
        ).fetchall()
        columns = []
        for col in table_info:
            if col[1] == "geometry":
                continue
            if col[5] == 1:
                columns.append(f'"{escape(col[1])}" {col[2]} PRIMARY KEY')
            else:
                columns.append(f'"{escape(col[1])}" {col[2]}')

        columns_clause = ",\n  ".join(columns)
        create_statement = (
            f'CREATE TABLE "{escape(self.table.name)}" ({columns_clause});'
        )
        self.db.conn.execute(create_statement)
        self.db.conn.execute(
            f"SELECT AddGeometryColumn(?, 'geometry', ?, ?, 2);",
            [self.table.name, self.srid, self.geom_type],
        )

    def copy_from(self, temp_table):
        # copy the data from temp_table to self.table
        # transforming the geometry from TEXT to GEOMETRY as we go
        table_info = self.db.conn.execute(
            f'PRAGMA table_info("{escape(self.table.name)}");'
        ).fetchall()
        columns = [
            "ST_GeomFromText(geometry, ?)"
            if col[1] == "geometry"
            else f'"{escape(col[1])}"'
            for col in table_info
        ]
        self.db.conn.execute(
            f'INSERT INTO "{escape(self.table.name)}" SELECT {", ".join(columns)} FROM "{temp_table.name}";',
            [self.srid],
        )

    def create_spatial_index(self):
        self.db.conn.execute(
            f"SELECT CreateSpatialIndex(?, 'geometry');", [self.table.name]
        )


class FeatureLoader:
    def __init__(self, db, features, table_name, srid, pk, columns):
        self.db = db
        if not isinstance(srid, int):
            raise DataImportError("'srid' must be an int")
        self.srid = srid
        self.features = features
        self.pk = pk
        self.table_name = table_name
        self.columns = columns
        self.geom_type = self.columns.pop("geometry", "GEOMETRY")

    @property
    def pk(self):
        return self._pk

    @pk.setter
    def pk(self, pk):
        if pk is None:
            self._pk = pk
            return
        for feature in self.features:
            if pk not in feature["properties"]:
                raise DataImportError(
                    f"Field '{pk}' must exist in every feature to be used as Primary Key"
                )
        self._pk = pk
        return

    def make_record(self, feature):
        record = copy.deepcopy(feature["properties"])

        record["geometry"] = None
        if feature["geometry"]:
            record["geometry"] = shape(feature["geometry"]).wkt

        return record

    def load(self):
        # parse the input file for data to insert
        records = []
        for feature in self.features:
            records.append(self.make_record(feature))

        """
        The insert_all() method in sqlite_utils does a number of useful things
        such as auto-detecting column types for us and adding columns as we go.
        Unfortunately it doesn't support the GEOMETRY column type, so we will:
        - Use insert_all() to import our data into a temp table
          (storing the WKT representation of geometry in a text column).
        - Make a real table based on the temp table with a GEOMETRY column.
        - Bulk copy the data from the temp table to the real table,
          converting the WKT column from TEXT to GEOMETRY as we go.
        - Clean up the temp table.
        """
        with TempTable(self.db, self.columns, self.pk) as temp_table:
            temp_table.insert_all(records, alter=True, pk=self.pk)
            with GeometryTable(
                self.db, self.table_name, self.srid, self.geom_type
            ) as table:
                table.create_from(temp_table)
                table.copy_from(temp_table)
                table.create_spatial_index()


class Command:
    def __init__(self, function, file_type):
        self.function = function
        self.file_type = file_type
        self.extension = f".{file_type.lower()}"
        self.pattern = f"*.{file_type.lower()}"

    def invoke(self, *, paths, dbname, table, primary_key, srid, spatialite_extension):
        if "." not in dbname:
            dbname += ".db"

        files = files_from_paths(paths, self.pattern)
        if len(files) == 0:
            raise Exception("failed to match any files")

        if len(paths) == 1 and os.path.isfile(paths[0]):
            self.function(
                dbname,
                paths[0],
                table_name=table,
                spatialite_extension=spatialite_extension,
                srid=srid,
                pk=primary_key,
            )
            print(f"Imported {paths[0]} into {dbname}")
        else:
            for tablename, filename in files.items():
                self.function(
                    dbname,
                    filename,
                    table_name=tablename,
                    spatialite_extension=spatialite_extension,
                    srid=srid,
                    pk=primary_key,
                )
                print(f"Imported {filename} into {dbname}")

    def parse_args(self, args):
        arg_parser = argparse.ArgumentParser(
            description=f"Load {self.file_type} files into a SpatiaLite database"
        )
        arg_parser.add_argument(
            "paths",
            nargs="+",
            help=f"Paths to individual {self.file_type} files or to directories containing {self.extension} files",
        )
        dbname_arg = arg_parser.add_argument(
            "dbname", help="Name of the SQLite database file"
        )
        table_arg = arg_parser.add_argument(
            "--table",
            "-t",
            help=f"Table to use (instead of using {self.file_type} filename)",
            default=None,
        )
        arg_parser.add_argument(
            "--primary-key",
            "-pk",
            help="Column to use as the primary key",
            default=None,
        )
        arg_parser.add_argument(
            "--srid",
            "-s",
            help="Spatial Reference ID (SRID) default=4326",
            type=int,
            default=4326,
        )
        arg_parser.add_argument(
            "--spatialite-extension",
            help="Path to the mod_spatialite extension",
            default=None,
        )

        parsed = arg_parser.parse_args(args)

        dbname = parsed.dbname
        if dbname.endswith(self.extension):
            raise argparse.ArgumentError(
                dbname_arg, f"must not end with {self.extension}"
            )

        if len(parsed.paths) > 1 and parsed.table is not None:
            raise argparse.ArgumentError(table_arg, "may not be used with >1 files")

        return parsed
