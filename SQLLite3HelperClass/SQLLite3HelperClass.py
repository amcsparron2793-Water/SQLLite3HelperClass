import sqlite3
from logging import Logger


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

    def GetConnectionAndCursor(self):
        try:
            # print(f"Attempting  to connect to {self.db_file_path}")
            self._logger.info(f"Attempting  to connect to {self.db_file_path}")
            self._connection = sqlite3.connect(self.db_file_path)

            # print("Connection was successful")
            self._logger.info("Connection was successful")

            self._cursor = self._connection.cursor()
            self._logger.debug("Cursor created, returning tuple of connection and cursor.")

            return self._connection, self._cursor

        except sqlite3.IntegrityError as e:
            self._logger.error(e, exc_info=True)
            raise e
        except sqlite3.OperationalError as e:
            self._logger.error(e, exc_info=True)
            raise e

    def Query(self, sql_string: str):
        try:
            self._cursor.execute(sql_string)
            res = self._cursor.fetchall()
            if res:
                self._logger.info(f"{len(res)} item(s) returned.")
                return res
            else:
                self._logger.warning(f"query returned no results")
                return None
        except sqlite3.IntegrityError as e:
            self._logger.error(e, exc_info=True)
            raise e
        except sqlite3.OperationalError as e:
            self._logger.error(e, exc_info=True)
            raise e