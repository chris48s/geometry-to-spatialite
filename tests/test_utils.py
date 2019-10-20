from unittest import TestCase

from geometry_to_spatialite.utils import TempTable, create_connection


class TempTableTests(TestCase):
    def setUp(self):
        self.db = create_connection(":memory:", None)

    def test_temp_table_deleted_on_context_exit(self):
        with TempTable(self.db, {}, None) as temp_table:
            temp_table.insert_all([{"foo": "bar"}], alter=True)
            self.assertEqual(
                "bar",
                self.db.conn.execute(
                    f"SELECT foo FROM [{temp_table.name}] LIMIT 1"
                ).fetchone()[0],
            )

        tables = self.db.conn.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{temp_table.name}';"
        ).fetchall()
        self.assertEqual(0, len(tables))
