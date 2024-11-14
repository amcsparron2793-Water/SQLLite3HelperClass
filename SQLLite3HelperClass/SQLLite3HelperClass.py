import sqlite3
from logging import Logger
from typing import List
from collections import ChainMap


class SQLlite3Helper:
    """ Initializes an SQLlite3 database and has a basic query method.
    This class is meant to be subclassed and expanded.

    IF NO LOGGER IS SPECIFIED, A DUMMY LOGGER IS USED. """
    def __init__(self, db_file_path: str, logger: Logger = None):
        if logger:
            self._logger = logger
        else:
            self._logger = Logger("fake")
            # print("DUMMY LOGGER IN USE")

        self.db_file_path = db_file_path
        self._connection = None
        self._cursor = None
        self._query_results = None

    @property
    def query_results(self):
        return self._query_results

    @query_results.setter
    def query_results(self, value: List[dict] or None):
        self._query_results = value

    @property
    def list_dict_results(self):
        if self.query_results:
            return self._ConvertToFinalListDict(self.query_results)
        else:
            return None

    @property
    def results_column_names(self) -> List[str] or None:
        try:
            return [d[0] for d in self._cursor.description]
        except AttributeError as e:
            return None

    def GetConnectionAndCursor(self):
        try:
            # print(f"Attempting  to connect to {self.db_file_path}")
            self._logger.info(f"Attempting  to connect to {self.db_file_path}")
            self._connection = sqlite3.connect(self.db_file_path)

            # print("Connection was successful")
            self._logger.info("Connection was successful")

            self._cursor = self._connection.cursor()
            self._logger.debug("Cursor created, returning tuple of connection and cursor.")

            self._cursor.execute("PRAGMA foreign_keys = ON;")
            self._connection.commit()

            return self._connection, self._cursor

        except sqlite3.IntegrityError as e:
            self._logger.error(e, exc_info=True)
            raise e
        except sqlite3.OperationalError as e:
            self._logger.error(e, exc_info=True)
            raise e

    def _ConvertToFinalListDict(self, results: List[tuple]) -> List[dict] or None:
        row_list_dict = []
        final_list_dict = []

        for row in results:
            if self.results_column_names:
                for cell, col in zip(row, self.results_column_names):
                    row_list_dict.append({col: cell})
                final_list_dict.append(dict(ChainMap(*row_list_dict)))
                row_list_dict.clear()
            else:
                raise AttributeError("A query has not been executed, "
                                     "please execute a query before calling this function.")
        if len(final_list_dict) > 0:
            # this returns a sorted list dict instead of an unsorted list dict
            return [dict(sorted(x.items())) for x in final_list_dict]
        else:
            return None

    def Query(self, sql_string: str):
        try:
            self._cursor.execute(sql_string)

            res = self._cursor.fetchall()

            if res:
                self._logger.info(f"{len(res)} item(s) returned.")
            else:
                self._logger.warning(f"query returned no results")
            self.query_results = res

        except sqlite3.IntegrityError as e:
            self._logger.error(e, exc_info=True)
            raise e
        except sqlite3.OperationalError as e:
            self._logger.error(e, exc_info=True)
            raise e
