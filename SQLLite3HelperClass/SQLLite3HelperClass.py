from sys import version_info as py_version_info
import sqlite3
from logging import Logger, getLogger
from typing import List, Union
from pathlib import Path
from collections import ChainMap


class _NoTrackedTablesError(Exception):
    DEFAULT_ERR_MSG = ("No tables have been specified to track. "
                       "Please specify tables to track in the TABLES_TO_TRACK class variable.")
    def __init__(self, msg=None):
        if not msg:
            msg = _NoTrackedTablesError.DEFAULT_ERR_MSG
        super().__init__(msg)


class SQLlite3Helper:
    """ Initializes an SQLlite3 database and has a basic query method.
    This class is meant to be subclassed and expanded.

    IF NO LOGGER IS SPECIFIED, A DUMMY LOGGER IS USED. """
    def __init__(self, db_file_path: Union[str, Path], logger: Logger = None):
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
        """
        :return: The results of a query operation.
        :rtype: object
        """
        return self._query_results

    @query_results.setter
    def query_results(self, value: List[dict] or None):
        """
        :param value: A list of dictionaries representing the query results or None if no results are available.
        :type value: List[dict] or None
        """
        self._query_results = value

    @property
    def list_dict_results(self):
        """
        Fetches and returns the query results as a list of dictionaries if available.
        If no query results exist, it returns None.

        :return: List of dictionaries representing query results, or None if no results exist.
        :rtype: list | None
        """
        if self.query_results:
            return self._ConvertToFinalListDict(self.query_results)
        else:
            return None

    @property
    def results_column_names(self) -> List[str] or None:
        """
        :return: A list of column names from the database results if the cursor provides a description,
            or None if the cursor's description is not available.
        :rtype: List[str] or None
        """
        try:
            return [d[0] for d in self._cursor.description]
        except AttributeError as e:
            return None

    def GetConnectionAndCursor(self):
        """
        Attempts to establish a connection to the SQLite database specified by the `db_file_path`
        and creates a cursor for executing SQL commands. Ensures that foreign key support
        is enabled by setting `PRAGMA foreign_keys` to ON. If successful, returns a tuple
        containing the connection and cursor objects.

        Handles `sqlite3.IntegrityError` and `sqlite3.OperationalError` by logging
        the exception and re-raising it.

        :return: Tuple containing the SQLite connection and cursor objects.
        :rtype: tuple
        """
        try:
            # print(f"Attempting  to connect to {self.db_file_path}")
            self._logger.info(f"Attempting  to connect to {self.db_file_path}")
            self._connection = sqlite3.connect(self.db_file_path)

            # print("Connection was successful")
            self._logger.info("Connection was successful")

            self._cursor = self._connection.cursor()
            self._logger.debug("Cursor created.")

            self._cursor.execute("PRAGMA foreign_keys = ON;")
            self._logger.debug("PRAGMA foreign_keys set to ON")
            self._logger.info("Returning tuple of connection and cursor.")
            self._connection.commit()

            return self._connection, self._cursor

        except sqlite3.IntegrityError as e:
            self._logger.error(e, exc_info=True)
            raise e
        except sqlite3.OperationalError as e:
            self._logger.error(e, exc_info=True)
            raise e

    def _ConvertToFinalListDict(self, results: List[tuple]) -> List[dict] or None:
        """
        :param results: A list of tuples where each tuple represents a row of query results.
        :type results: List[tuple]
        :return: A sorted list of dictionaries where each dictionary represents a row of the query results,
            with column names as keys. Returns None if the results are empty.
        :rtype: List[dict] or None
        """
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
        """
        :param sql_string: The SQL query string to be executed.
        :type sql_string: str
        :return: None
        :rtype: None
        """
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


# noinspection SqlNoDataSourceInspection
class CreateTriggersSQLLite(SQLlite3Helper):
    """
        Class for managing SQLite triggers and audit logging.

        This class extends `SQLlite3Helper` to handle the creation and management
        of database triggers that log changes (inserts, updates, and deletes) made
        on specific tables into an audit log table.

        Attributes:
        -----------
        TABLES_TO_TRACK : list
            A list of table names to generate audit triggers for.
        AUDIT_LOG_CREATE_TABLE : str
            SQL query to create the audit log table if it does not exist.
        AUDIT_LOG_CREATED_CHECK : str
            SQL query to check if the audit log table already exists.
        HAS_TRIGGER_CHECK : str
            SQL query used to check if a given table has triggers associated with it.
        INSERT_TRIGGER : str
            SQL template used to generate an INSERT trigger for a table.
        UPDATE_TRIGGER : str
            SQL template used to generate an UPDATE trigger for a table.
        DELETE_TRIGGER : str
            SQL template used to generate a DELETE trigger for a table.

        Methods:
        --------
        __init__(db_file_path: Union[str, Path]):
            Initializes the SQLite connection and ensures the audit log table is created.

        __init_subclass__(**kwargs):
            Ensures that all subclasses define tables to track changes for.

        _create_audit_log_table():
            Creates the audit log table in the SQLite database.

        has_tracked_tables() -> bool:
            Class method to check if any tables have been listed for tracking.

        has_audit_log_table() -> bool:
            Property to check if the audit log table exists in the SQLite database.

        _has_trigger(table: str) -> bool:
            Checks whether audit triggers already exist for a given table.

        _get_column_names(table: str) -> list:
            Retrieves the names of all columns for a given table.

        _get_row_json(columns: list) -> tuple:
            Generates JSON object strings for representing old and new rows
            based on the provided column names.

        create_triggers_for_table(table_name: str, columns: list, commit_triggers: bool=False):
            Creates the INSERT, UPDATE, and DELETE triggers for a given table and optionally commits them.

        generate_triggers_for_all_tables():
            Generates triggers for all the tables in `TABLES_TO_TRACK` if they do
            not already exist and commits the changes to the database.
    """
    TABLES_TO_TRACK = []
    AUDIT_LOG_CREATE_TABLE = """create table audit_log
                                (
                                    id           INTEGER
                                        primary key autoincrement,
                                    table_name   TEXT not null,
                                    operation    TEXT not null,
                                    old_row_data TEXT,
                                    new_row_data TEXT,
                                    change_time  TIMESTAMP default CURRENT_TIMESTAMP
                                );"""
    AUDIT_LOG_CREATED_CHECK = "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log';"
    HAS_TRIGGER_CHECK = """select tbl_name 
                        from sqlite_master 
                        where type='trigger' 
                            and tbl_name='{table}';"""

    INSERT_TRIGGER = """
            CREATE TRIGGER after_{table_name}_insert
            AFTER INSERT ON {table_name}
            BEGIN
                INSERT INTO audit_log (table_name, operation, old_row_data, new_row_data)
                VALUES (
                    '{table_name}', 
                    'INSERT', 
                    NULL, 
                    {new_row_json}
                );
            END;
            """

    UPDATE_TRIGGER = """
            CREATE TRIGGER after_{table_name}_update
            AFTER UPDATE ON {table_name}
            BEGIN
                INSERT INTO audit_log (table_name, operation, old_row_data, new_row_data)
                VALUES (
                    '{table_name}', 
                    'UPDATE', 
                    {old_row_json}, 
                    {new_row_json}
                );
            END;
            """

    DELETE_TRIGGER = """
        CREATE TRIGGER after_{table_name}_delete
        AFTER DELETE ON {table_name}
        BEGIN
            INSERT INTO audit_log (table_name, operation, old_row_data, new_row_data)
            VALUES (
                '{table_name}', 
                'DELETE', 
                {old_row_json}, 
                NULL
            );
        END;
        """

    def __init__(self, db_file_path: Union[str, Path]):
        super().__init__(db_file_path)
        if not self.has_audit_log_table:
            self._create_audit_log_table()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.has_tracked_tables():
            raise _NoTrackedTablesError()

    def _create_audit_log_table(self):
        """
        Creates the audit log table in the database.

        :return: None
        :rtype: None
        """
        self.GetConnectionAndCursor()
        self._cursor.execute(self.__class__.AUDIT_LOG_CREATE_TABLE)
        self._connection.commit()
        self._logger.info("Audit log table created.")

    @classmethod
    def has_tracked_tables(cls):
        """
        Checks if there are any tracked tables defined in the TABLES_TO_TRACK attribute.

        :return: True if there are tables to track, False otherwise
        :rtype: bool

        """
        return bool(cls.TABLES_TO_TRACK)

    @property
    def has_audit_log_table(self):
        """
        Checks if the audit log table exists by executing a predefined query.

        :return: True if the audit log table exists, False otherwise
        :rtype: bool
        """
        self.Query(self.__class__.AUDIT_LOG_CREATED_CHECK)
        if self.query_results:
            return True
        return False

    def _has_trigger(self, table):
        """
        :param table: The name of the table to check for associated triggers.
        :type table: str
        :return: Returns True if the table has associated triggers, otherwise False.
        :rtype: bool
        """
        self.Query(self.__class__.HAS_TRIGGER_CHECK)
        if self.query_results:
            return True
        return False

    def _get_column_names(self, table):
        self.Query(f"""SELECT p.name as columnName
                        FROM sqlite_master m
                        left outer join pragma_table_info((m.name)) p
                            on m.name <> p.name
                        where m.name = '{table}';""")
        if self.query_results:
            return [x[0] for x in self.query_results]

    @staticmethod
    def _get_row_json(columns):
        """
        :param columns: List of column names to be used for generating JSON objects.
        :type columns: list of str
        :return: A tuple containing two strings, `new_row_json` and `old_row_json`.
                 Each string is a JSON object representation using the given columns.
        :rtype: tuple
        """
        # changed to .format instead of f-strings to preserve backwards compatibility with py <=3.8
        new_row_json = "json_object({})".format(
            ', '.join(["'{}', NEW.{}".format(col, col) for col in columns])
        )
        old_row_json = "json_object({})".format(
            ', '.join(["'{}', OLD.{}".format(col, col) for col in columns])
        )
        return new_row_json, old_row_json

    def create_triggers_for_table(self, table_name, columns, commit_triggers=False):
        """
        :param table_name: Name of the database table for which triggers are to be created.
        :type table_name: str
        :param columns: List of column names to be included in the triggers.
        :type columns: list
        :param commit_triggers: Flag indicating whether the changes should be committed to the database. Defaults to False.
        :type commit_triggers: bool
        :return: None
        :rtype: None
        """
        new_row_json, old_row_json = self._get_row_json(columns)

        # INSERT Trigger for table_name
        insert_trigger_query = self.__class__.INSERT_TRIGGER.format(table_name=table_name,
                                                                    new_row_json=new_row_json)
        self._cursor.execute(insert_trigger_query)

        # UPDATE Trigger for table_name
        update_trigger_query = self.__class__.UPDATE_TRIGGER.format(table_name=table_name,
                                                                    old_row_json=old_row_json,
                                                                    new_row_json=new_row_json)
        self._cursor.execute(update_trigger_query)

        # DELETE Trigger for table_name
        delete_trigger_query = self.__class__.DELETE_TRIGGER.format(table_name=table_name,
                                                                    old_row_json=old_row_json)
        self._cursor.execute(delete_trigger_query)

        if not commit_triggers:
            self._logger.warning(f"triggers for {table_name} created but NOT COMMITTED.")
        else:
            self._connection.commit()
            self._logger.info(f"triggers for {table_name} created and committed.")

    def generate_triggers_for_all_tables(self):
        """
        Generates database triggers for all the tables listed in `TABLES_TO_TRACK`.

        This function iterates through each table in `TABLES_TO_TRACK` and checks if
        the table already has triggers. If triggers are not present for a table, it
        creates them by calling `create_triggers_for_table` using the table name as
        well as the column names retrieved from `_get_column_names`. Debug and
        informational logging is performed during this process to record trigger
        generation status for each table. After successfully generating triggers for
        all tables, the changes are committed to the database.

        :return: None
        :rtype: None
        """
        self._logger.info(f"Attempting to generate triggers for {len(self.__class__.TABLES_TO_TRACK)} tables")

        for table in self.__class__.TABLES_TO_TRACK:
            if not self._has_trigger(table):
                self.create_triggers_for_table(table, self._get_column_names(table))
                self._logger.debug(f'triggers for {table} created')
                print(f'triggers for {table} created')
            else:
                print(f'{table} already has triggers')
                self._logger.debug(f'{table} already has triggers')

        self._logger.info('triggers generated successfully')

        self._logger.info('committing triggers')
        self._connection.commit()
        self._logger.info('triggers committed successfully')
