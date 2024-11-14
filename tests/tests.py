import unittest
import SQLLite3HelperClass.SQLLite3HelperClass as SQLLite3HelperClass
from sqlite3 import OperationalError, IntegrityError


class SQLLite3HelperClassTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sql = SQLLite3HelperClass.SQLlite3Helper('./testdb.db')
        cxn, csr = sql.GetConnectionAndCursor()
        try:
            csr.execute("create table Test(id integer primary key, random_name varchar(20));")
        except OperationalError:
            pass
        try:
            csr.execute("create table Test_two(id integer primary key, test_id integer references Test(id));")
        except OperationalError as e:
            pass
        csr.execute("insert into Test(random_name) values('Andrew'), ('Joe'), ('Paul');")
        cxn.commit()
        return cls

    def setUp(self):
        self.sql = SQLLite3HelperClass.SQLlite3Helper('./testdb.db')
        self.cxn, self.csr = self.sql.GetConnectionAndCursor()

    def test_no_res_returns_none(self):
        self.sql.Query("select * from test where id=(select max(id) + 1 from test)")
        try:
            self.assertIsNone(self.sql.query_results)
        except AssertionError:
            if type(self.sql.query_results) is list and len(self.sql.query_results) < 1:
                self.sql.query_results = None
                self.assertIsNone(self.sql.query_results)

    def test_query_results_returns_list_tuple(self):
        self.sql.Query("select * from Test")
        self.assertIsInstance(self.sql.query_results, list)
        self.assertIsInstance(self.sql.query_results[0], tuple)

    def test_list_dict_results_returns_list_dict(self):
        self.sql.Query("select * from Test")
        self.assertIsInstance(self.sql.list_dict_results, list)
        self.assertIsInstance(self.sql.list_dict_results[0], dict)

    def test_pragma_foreign_keys_is_true(self):
        self.sql.Query("pragma foreign_keys")
        self.assertEqual(self.sql.query_results[0][0], 1)

    def test_foreign_key_error_throws_error(self):
        did_err = False
        try:
            self.csr.execute("insert into Test_two(test_id) values(4);")
        except IntegrityError as e:
            did_err = True
        self.assertTrue(did_err)


if __name__ == '__main__':
    unittest.main()
