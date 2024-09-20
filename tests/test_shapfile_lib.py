import tempfile
from sqlite3 import IntegrityError
from unittest import TestCase

from geometry_to_spatialite.shapefile import shp_to_spatialite
from geometry_to_spatialite.utils import DataImportError, create_connection


class ShpToSpatialiteTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db")
        db = create_connection(self.tmp.name, None)
        self.conn = db.conn

    def tearDown(self):
        self.tmp.close()

    def test_points_with_defaults(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp")

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
            {
                "id": "INTEGER",
                "prop0": "TEXT",
                "prop1": "FLOAT",
                "geometry": "GEOMETRY",
            },
            {col[1]: col[2] for col in cols},
        )

        # ensure the spatial index was created
        indexes = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='idx_points_geometry';"
        ).fetchall()
        self.assertEqual(1, len(indexes))

    def test_polygons_with_defaults(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/polygons.shp")

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
                "geometry": "GEOMETRY",
            },
            {col[1]: col[2] for col in cols},
        )

        # ensure the spatial index was created
        indexes = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='idx_polygons_geometry';"
        ).fetchall()
        self.assertEqual(1, len(indexes))

    def test_success_with_table_name(self):
        shp_to_spatialite(
            self.tmp.name, "tests/fixtures/shp/points.shp", table_name="foobar"
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM foobar;").fetchall()))
        tables = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='valid';"
        ).fetchall()
        self.assertEqual(0, len(tables))

    def test_success_with_srid(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp", srid=27700)
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        self.assertEqual(
            27700, self.conn.execute("SELECT srid(geometry) FROM points;").fetchone()[0]
        )

    def test_success_with_string_primary_key(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp", pk="id")
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_with_list_primary_key(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp", pk=["id"])
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_with_composite_key(self):
        shp_to_spatialite(
            self.tmp.name, "tests/fixtures/shp/points.shp", pk=["id", "prop1"]
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM points;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('points');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 2, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_append_to_table(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp")
        shp_to_spatialite(
            self.tmp.name, "tests/fixtures/shp/points.shp", write_mode="append"
        )
        records = self.conn.execute("SELECT * FROM points ORDER BY id;").fetchall()
        self.assertEqual(6, len(records))

    def test_success_overwrite_table(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp")
        shp_to_spatialite(
            self.tmp.name, "tests/fixtures/shp/points.shp", write_mode="replace"
        )
        records = self.conn.execute("SELECT * FROM points ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))

    def test_success_mixed_geometry(self):
        # this shapefile contains a Polygon and a MultiPolygon
        # it should import cleanly
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/mixed_geometry.shp")
        records = self.conn.execute("SELECT * FROM mixed_geometry;").fetchall()
        self.assertEqual(2, len(records))

    def test_success_with_geom_type(self):
        shp_to_spatialite(
            self.tmp.name, "tests/fixtures/shp/points.shp", geom_type="POINT"
        )
        records = self.conn.execute("SELECT * FROM points ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))
        cols = {
            col[1]: col[2]
            for col in self.conn.execute("PRAGMA table_info('points');").fetchall()
        }
        self.assertEqual("POINT", cols["geometry"])

    def test_failure_table_already_exists(self):
        shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp")
        with self.assertRaises(DataImportError):
            shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp")

    def test_failure_cant_append_to_table(self):
        self.conn.execute("CREATE TABLE points (id INT);")
        with self.assertRaises(DataImportError):
            shp_to_spatialite(
                self.tmp.name, "tests/fixtures/shp/points.shp", write_mode="append"
            )

    def test_failure_invalid_srid(self):
        with self.assertRaises(TypeError):
            shp_to_spatialite(
                self.tmp.name, "tests/fixtures/shp/points.shp", srid="foobar"
            )

    def test_failure_invalid_pk(self):
        with self.assertRaises(TypeError):
            shp_to_spatialite(self.tmp.name, "tests/fixtures/shp/points.shp", pk=7)

    def test_failure_invalid_write_mode(self):
        with self.assertRaises(ValueError):
            shp_to_spatialite(
                self.tmp.name, "tests/fixtures/shp/points.shp", write_mode="foobar"
            )

    def test_failure_incorrect_geom_type(self):
        with self.assertRaises(IntegrityError):
            shp_to_spatialite(
                self.tmp.name, "tests/fixtures/shp/points.shp", geom_type="POLYGON"
            )

    def test_failure_invalid_geom_type(self):
        with self.assertRaises(ValueError):
            shp_to_spatialite(
                self.tmp.name,
                "tests/fixtures/shp/points.shp",
                geom_type="NOT-A-GEOM-TYPE",
            )
