import argparse
import io
import sys
import tempfile
from unittest import TestCase

from geometry_to_spatialite.shapefile import cli
from geometry_to_spatialite.utils import create_connection


class CliTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db")
        db = create_connection(self.tmp.name, None)
        self.conn = db.conn
        sys.stdout = io.StringIO()

    def tearDown(self):
        self.tmp.close()
        sys.stdout = sys.__stdout__

    def test_success(self):
        cli.invoke(
            paths=["tests/fixtures/shp/points.shp"],
            dbname=self.tmp.name,
            table="points",
            primary_key=None,
            write_mode=None,
            srid=4326,
            geom_type="GEOMETRY",
            spatialite_extension=None,
        )
        records = self.conn.execute("SELECT * FROM points ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))

    def test_no_db_extension(self):
        cli.invoke(
            paths=["tests/fixtures/shp/points.shp"],
            dbname=self.tmp.name[:-3],
            table="points",
            primary_key=None,
            write_mode=None,
            srid=4326,
            geom_type="GEOMETRY",
            spatialite_extension=None,
        )
        records = self.conn.execute("SELECT * FROM points ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))

    def test_custom_table_name(self):
        cli.invoke(
            paths=["tests/fixtures/shp/points.shp"],
            dbname=self.tmp.name,
            table="custom",
            primary_key=None,
            write_mode=None,
            srid=4326,
            geom_type="GEOMETRY",
            spatialite_extension=None,
        )
        records = self.conn.execute("SELECT * FROM custom ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))

    def test_multiple_files(self):
        cli.invoke(
            paths=["tests/fixtures/shp/"],
            dbname=self.tmp.name,
            table="irrelevant",
            primary_key=None,
            write_mode=None,
            srid=4326,
            geom_type="GEOMETRY",
            spatialite_extension=None,
        )
        records = self.conn.execute("SELECT * FROM [./points] ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))
        records = self.conn.execute(
            "SELECT * FROM [./polygons] ORDER BY id;"
        ).fetchall()
        self.assertEqual(3, len(records))

    def test_files_not_found(self):
        with self.assertRaises(Exception):
            cli.invoke(
                paths=["tests/fixtures/shp/does_not_exist"],
                dbname=self.tmp.name,
                table="does_not_exist",
                primary_key=None,
                write_mode=None,
                srid=4326,
                geom_type="GEOMETRY",
                spatialite_extension=None,
            )


class ParseArgsTests(TestCase):
    def test_no_db_arg(self):
        with self.assertRaises(argparse.ArgumentError):
            cli.parse_args(["abc.shp", "def.shp"])

    def test_table_with_multiple_files(self):
        with self.assertRaises(argparse.ArgumentError):
            cli.parse_args(["abc.shp", "def.shp", "database.db", "-t", "foobar"])

    def test_no_extra_args(self):
        args = cli.parse_args(["abc.shp", "def.shp", "database.db"])
        self.assertEqual(["abc.shp", "def.shp"], args.paths)
        self.assertEqual("database.db", args.dbname)
        self.assertEqual(None, args.table)
        self.assertEqual(None, args.primary_key)
        self.assertEqual(4326, args.srid)
        self.assertEqual(None, args.spatialite_extension)
        self.assertEqual(None, args.write_mode)

    def test_all_extra_args(self):
        args = cli.parse_args(
            [
                "abc.shp",
                "database.db",
                "-t",
                "foobar",
                "-pk",
                "id",
                "-s",
                "1234",
                "--spatialite-extension",
                "/usr/lib/mod_spatialite.so",
                "--write-mode",
                "append",
            ]
        )
        self.assertEqual(["abc.shp"], args.paths)
        self.assertEqual("database.db", args.dbname)
        self.assertEqual("foobar", args.table)
        self.assertEqual(["id"], args.primary_key)
        self.assertEqual(1234, args.srid)
        self.assertEqual("/usr/lib/mod_spatialite.so", args.spatialite_extension)
        self.assertEqual("append", args.write_mode)
