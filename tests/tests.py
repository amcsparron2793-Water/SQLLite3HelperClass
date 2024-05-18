import unittest
import SQLLite3HelperClass.SQLLite3HelperClass as SQLLite3HelperClass
from sqlite3 import OperationalError


class SQLLite3HelperClassTest(unittest.TestCase):
    def setUp(self):
        self.sql = SQLLite3HelperClass.SQLlite3Helper('./testdb.db')
        self.cxn, self.csr = self.sql.GetConnectionAndCursor()
        try:
            self.csr.execute("create table Test(id integer primary key, random_name varchar(20));")
        except OperationalError:
            pass
        self.csr.execute("insert into Test(random_name) values('Andrew'), ('Joe'), ('Paul');")

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


if __name__ == '__main__':
    unittest.main()
