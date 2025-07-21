from sys import version_info as PyVersionInfo
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


# noinspection SqlNoDataSourceInspection
class CreateTriggersSQLLite(SQLlite3Helper):
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
        self.GetConnectionAndCursor()
        self._cursor.execute(self.__class__.AUDIT_LOG_CREATE_TABLE)
        self._connection.commit()
        self._logger.info("Audit log table created.")

    @classmethod
    def has_tracked_tables(cls):
        return bool(cls.TABLES_TO_TRACK)

    @property
    def has_audit_log_table(self):
        self.Query(self.__class__.AUDIT_LOG_CREATED_CHECK)
        if self.query_results:
            return True
        return False

    def _has_trigger(self, table):
        self.Query(f"""select tbl_name 
                        from sqlite_master 
                        where type='trigger' 
                            and tbl_name='{table}'""")
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
        if PyVersionInfo.major >= 3 and PyVersionInfo.minor >= 9:
            # Generate the json_object content using explicit column names
            new_row_json = f"json_object({', '.join([f"'{col}', NEW.{col}" for col in columns])})"
            old_row_json = f"json_object({', '.join([f"'{col}', OLD.{col}" for col in columns])})"
        else:
            new_row_json = "json_object({})".format(
                ', '.join(["'{}', NEW.{}".format(col, col) for col in columns])
            )
            old_row_json = "json_object({})".format(
                ', '.join(["'{}', OLD.{}".format(col, col) for col in columns])
            )
        return new_row_json, old_row_json

    def create_triggers_for_table(self, table_name, columns):
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
        # TODO: warning not committed automatically?

    def generate_triggers_for_all_tables(self):
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
