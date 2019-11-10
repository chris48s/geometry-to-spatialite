import tempfile
from unittest import TestCase

from geometry_to_spatialite.geojson import geojson_to_spatialite
from geometry_to_spatialite.utils import DataImportError, create_connection


class GeoJsonToSpatialiteTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db")
        db = create_connection(self.tmp.name, None)
        self.conn = db.conn

    def tearDown(self):
        self.tmp.close()

    def test_success_with_defaults(self):
        geojson_to_spatialite(self.tmp.name, "tests/fixtures/geojson/valid.geojson")

        # ensure all the right data was inserted
        records = self.conn.execute(
            "SELECT id, prop0, prop1, AsText(geometry) as geomtext FROM valid ORDER BY id;"
        ).fetchall()
        self.assertEqual(3, len(records))
        self.assertEqual((1, "string", None, "POINT(102 0.5)"), records[0])
        self.assertEqual(
            (2, "string", 0, "LINESTRING(102 0, 103 1, 104 0, 105 1)"), records[1]
        )
        self.assertEqual(
            (3, "string", 7, "POLYGON((100 0, 101 0, 101 1, 100 1, 100 0))"), records[2]
        )

        # make sure the columns have the corect types
        cols = self.conn.execute("PRAGMA table_info('valid');").fetchall()
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
            "SELECT name FROM sqlite_master WHERE type='table' AND name='idx_valid_geometry';"
        ).fetchall()
        self.assertEqual(1, len(indexes))

    def test_success_with_table_name(self):
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", table_name="foobar"
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM foobar;").fetchall()))
        tables = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='valid';"
        ).fetchall()
        self.assertEqual(0, len(tables))

    def test_success_with_srid(self):
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", srid=27700
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM valid;").fetchall()))
        self.assertEqual(
            27700, self.conn.execute("SELECT srid(geometry) FROM valid;").fetchone()[0]
        )

    def test_success_with_string_primary_key(self):
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", pk="id"
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM valid;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('valid');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_with_list_primary_key(self):
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", pk=["id"]
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM valid;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('valid');").fetchall()
        self.assertDictEqual(
            {"id": 1, "prop0": 0, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_with_composite_key(self):
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", pk=["id", "prop0"]
        )
        self.assertEqual(3, len(self.conn.execute("SELECT * FROM valid;").fetchall()))
        cols = self.conn.execute("PRAGMA table_info('valid');").fetchall()
        self.assertDictEqual(
            {"id": 2, "prop0": 1, "prop1": 0, "geometry": 0},
            {col[1]: col[5] for col in cols},
        )

    def test_success_append_to_table(self):
        geojson_to_spatialite(self.tmp.name, "tests/fixtures/geojson/valid.geojson")
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", write_mode="append"
        )
        records = self.conn.execute("SELECT * FROM valid ORDER BY id;").fetchall()
        self.assertEqual(6, len(records))

    def test_success_overwrite_table(self):
        geojson_to_spatialite(self.tmp.name, "tests/fixtures/geojson/valid.geojson")
        geojson_to_spatialite(
            self.tmp.name, "tests/fixtures/geojson/valid.geojson", write_mode="replace",
        )
        records = self.conn.execute("SELECT * FROM valid ORDER BY id;").fetchall()
        self.assertEqual(3, len(records))

    def test_failure_table_already_exists(self):
        geojson_to_spatialite(self.tmp.name, "tests/fixtures/geojson/valid.geojson")
        with self.assertRaises(DataImportError):
            geojson_to_spatialite(self.tmp.name, "tests/fixtures/geojson/valid.geojson")

    def test_failure_cant_append_to_table(self):
        self.conn.execute("CREATE TABLE valid (id INT);")
        with self.assertRaises(DataImportError):
            geojson_to_spatialite(
                self.tmp.name,
                "tests/fixtures/geojson/valid.geojson",
                write_mode="append",
            )

    def test_failure_invalid_srid(self):
        with self.assertRaises(DataImportError):
            geojson_to_spatialite(
                self.tmp.name, "tests/fixtures/geojson/valid.geojson", srid="foobar"
            )

    def test_failure_geojson_not_featurecollection(self):
        with self.assertRaises(DataImportError):
            geojson_to_spatialite(
                self.tmp.name, "tests/fixtures/geojson/feature.geojson"
            )

    def test_failure_pk_not_in_every_feature(self):
        with self.assertRaises(DataImportError):
            geojson_to_spatialite(
                self.tmp.name, "tests/fixtures/geojson/valid.geojson", pk="prop1"
            )
