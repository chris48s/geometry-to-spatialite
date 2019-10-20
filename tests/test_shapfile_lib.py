import os
import sqlite3
from unittest import TestCase

from geometry_to_spatialite.shapefile import shp_to_spatialite
from geometry_to_spatialite.utils import DataImportError, create_connection


class ShpToSpatialiteTests(TestCase):
    def setUp(self):
        db = create_connection("unit_tests.db", None)
        self.conn = db.conn

    def tearDown(self):
        os.remove("unit_tests.db")

    def test_points_with_defaults(self):
        shp_to_spatialite("unit_tests.db", "tests/fixtures/shp/points.shp")

        # ensure all the right data was inserted
        records = self.conn.execute(
            "SELECT id, prop0, prop1, AsText(geometry) as geomtext FROM points ORDER BY id;"
        ).fetchall()
        self.assertEqual(3, len(records))
        self.assertEqual((1, "string", None, "POINT(102 0.5)"), records[0])
        self.assertEqual((2, "string", 0, "POINT(102 0)"), records[1])
        self.assertEqual((3, "string", 7, "POINT(100 0)"), records[2])

        # make sure the columns have the corect types
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": "INTEGER", "prop0": "TEXT", "prop1": "FLOAT", "geometry": "POINT"},
            {col[1]: col[2] for col in cols},
        )

        # ensure the spatial index was created
        self.conn.execute("SELECT * FROM idx_points_geometry;")

    def test_polygons_with_defaults(self):
        shp_to_spatialite("unit_tests.db", "tests/fixtures/shp/polygons.shp")

        # ensure all the right data was inserted
        records = self.conn.execute(
            "SELECT id, prop0, prop1, AsText(geometry) as geomtext FROM polygons ORDER BY id;"
        ).fetchall()
        self.assertEqual(3, len(records))
        self.assertEqual(
            (1, "string", True, "POLYGON((102 0, 102 1, 103 1, 103 0, 102 0))"),
            records[0],
        )
        self.assertEqual(
            (2, "string", False, "POLYGON((100 0, 100 1, 101 1, 101 0, 100 0))"),
            records[1],
        )
        self.assertEqual(
            (3, "string", True, "POLYGON((105 0, 104 0, 104 1, 105 1, 105 0))"),
            records[2],
        )

        # make sure the columns have the corect types
        cols = self.conn.execute("PRAGMA table_info('polygons');").fetchall()
        self.assertDictEqual(
            {
                "id": "INTEGER",
                "prop0": "TEXT",
                "prop1": "INTEGER",
                "geometry": "POLYGON",
            },
            {col[1]: col[2] for col in cols},
        )

        # ensure the spatial index was created
        self.conn.execute("SELECT * FROM idx_polygons_geometry;")

    def test_success_with_table_name(self):
        shp_to_spatialite(
            "unit_tests.db", "tests/fixtures/shp/points.shp", table_name="foobar"
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM foobar;").fetchall()))
        with self.assertRaises(sqlite3.OperationalError):
            self.conn.execute("SELECT * FROM valid;")

    def test_success_with_srid(self):
        shp_to_spatialite("unit_tests.db", "tests/fixtures/shp/points.shp", srid=27700)
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        self.assertEqual(
            27700, self.conn.execute("SELECT srid(geometry) FROM points;").fetchone()[0]
        )

    def test_success_with_string_primary_key(self):
        shp_to_spatialite("unit_tests.db", "tests/fixtures/shp/points.shp", pk="id")
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_with_list_primary_key(self):
        shp_to_spatialite("unit_tests.db", "tests/fixtures/shp/points.shp", pk=["id"])
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_with_composite_key(self):
        shp_to_spatialite(
            "unit_tests.db", "tests/fixtures/shp/points.shp", pk=["id", "prop1"]
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": 2, "prop0": 0, "prop1": 1, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_failure_table_already_exists(self):
        self.conn.execute("CREATE TABLE points (id INT);")
        with self.assertRaises(DataImportError):
            shp_to_spatialite("unit_tests.db", "tests/fixtures/shp/points.shp")

    def test_failure_invalid_srid(self):
        with self.assertRaises(DataImportError):
            shp_to_spatialite(
                "unit_tests.db", "tests/fixtures/shp/points.shp", srid="foobar"
            )
