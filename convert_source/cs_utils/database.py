# -*- coding: utf-8 -*-
"""Database utility functions for convert_source, which encapsulates creating and querying databases.
"""
# TODO:
#   * Figure out how to store and follow file_id primary key throughout convert_source
#   * Write unit tests
#   * Integrate database functions into convert_source flow control
#   * Query database to write scans/sessions TSV for each subject

import os
import sqlite3
import pandas as pd
import pathlib

from sqlite3 import (
    DatabaseError,
    IntegrityError,
    OperationalError
)

from typing import (
    Dict,
    List,
    Optional,
    Union
)

from collections import OrderedDict

from convert_source.cs_utils.utils import zeropad

# Tables dictionary
tables: OrderedDict = OrderedDict({
    'file_id':'TEXT',    # PRIMARY KEY
    'rel_path':'TEXT',
    'file_date':'TEXT',
    'acq_date':'TEXT',
    'sub_id':'TEXT',
    'ses_id':'TEXT',
    'bids_name':'TEXT'
})

def create_db(database: str,
            tables: OrderedDict
            ) -> str:
    """Creates database provided an ordered dictionary of table names and types.
    """
    # Create/access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # Construct database tables
    for i in range(1,len(tables)):
        table_name: str = list(tables.keys())[i]
        new_field: str = list(tables.keys())[i]
        field_type: str = tables.get(list(tables.keys())[i],'NULL')
        
        # Create database tables
        try:
            tn: str = table_name
            # Primary Key
            nf1: str = list(tables.keys())[0]
            ft1: str = tables.get(list(tables.keys())[0],'NULL')
            # Child Key
            nf2: str = new_field
            ft2: str = field_type

            query: str = f"CREATE TABLE {tn} ({nf1} {ft1} PRIMARY KEY, {nf2} {ft2})"
            c.execute(query)
        except OperationalError:
            # print(table_name)
            continue
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()
    return database

def insert_row_db(database: str,
                tables: OrderedDict,
                info: Dict[str,str]) -> str:
    """Inserts rows into existing database tables, provided a dictionary of key mapped items of values. 
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # Insert new rows into database tables
    for i in range(1,len(tables)):
        table_name: str = list(tables.keys())[i]
        new_field: str = list(tables.keys())[i]

        tn: str = table_name
        p_key: str = list(tables.keys())[0]
        col: str = new_field

        p_val: str = info[list(tables.keys())[0]]
        col_val: str = info.get(list(tables.keys())[i],'NULL')
        
        query: str = f"INSERT INTO {tn} ({p_key},{col}) VALUES( ?,? )"

        try:
            c.execute(query, (p_val,col_val))
        except IntegrityError:
            continue
    
    conn.commit()
    conn.close()
    return database

def get_len_rows(database: str, 
                tables: OrderedDict
                ) -> int:
    """Gets number of rows in a databases' table.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # Perform database query
    query: str = f"SELECT COUNT(*) from {list(tables.keys())[1]}"
    c.execute(query)

    result: int = c.fetchone()[0]

    conn.commit()
    conn.close()
    return result

def get_file_id(database: str, 
                tables: OrderedDict,
                num_zeros: int = 7
                ) -> str:
    """Returns new file_id for file that does not yet exist in the database.
    """
    file_id: int = get_len_rows(database, tables) + 1
    file_id: str = zeropad(num=file_id, num_zeros=num_zeros)
    return file_id

def update_table_row(database: str,
                    prim_key: str,
                    table_name: str, 
                    col_name: str, 
                    value: Optional[Union[int,str]]
                    ) -> str:
    """Updates a row in a table in some given database.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    # Perform database table update
    query: str = f"UPDATE {table_name} SET {col_name} = ? WHERE {list(tables.keys())[0]} = ?"

    c.execute(query, (value,prim_key))

    conn.commit()
    conn.close()
    return database

def export_dataframe(database: str,
                    tables: OrderedDict
                    ) -> pd.DataFrame:
    """Exports all of the tables from the input database as a dataframe.
    """
    # Access database
    conn = sqlite3.connect(database)

    df_list: List = []

    for i in range(1,len(tables)):
        table = list(tables.keys())[i]
        df_tmp: pd.DataFrame = pd.read_sql_query(f"SELECT * FROM {table}", conn)

        if i == 1:
            pass
        else:
            df_tmp = df_tmp.drop(labels=list(tables.keys())[0],axis=1)

        df_list.append(df_tmp)

    return pd.concat(df_list,axis=1,join='outer')

def export_scans_dataframe(database: str,
                            raise_exec: bool = False,
                            *args: str
                            ) -> pd.DataFrame:
    """Exports a dataframe provided table/column IDs.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    df_list: List = []

    for i in args:
        table = str(i)

        query: str = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}'"

        c.execute(query)

        if c.fetchone()[0] == 1:
            pass
        else:
            if raise_exec:
                raise DatabaseError(f"Table {table} does not exist in database")
            continue
        
        df_tmp: pd.DataFrame = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        df_tmp = df_tmp.drop(labels=list(tables.keys())[0],axis=1)
        df_list.append(df_tmp)

    return pd.concat(df_list,axis=1,join='outer')

def get_dir_relative_path(study_dir: str,
                        file_name: str
                        ) -> str:
    """Returns the relative path provided some parent study directory and some file name.
    """
    path_sep: str = os.path.sep
    dir_tmp = str(pathlib.Path(study_dir).parents[0])
    return file_name.replace(dir_tmp + path_sep,"." + path_sep)
