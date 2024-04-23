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
        res = self.sql.Query("select * from test where id=1223")
        self.assertIsNone(res)

    def test_res_no_dict_returns_list_tuple(self):
        res = self.sql.Query("select * from test")
        self.assertIsInstance(res, list)
        self.assertIsInstance(res[0], tuple)


if __name__ == '__main__':
    unittest.main()
