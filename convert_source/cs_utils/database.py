# -*- coding: utf-8 -*-
"""Database utility functions for convert_source, which encapsulates creating and querying databases.
"""
# TODO:
#   * Create function to get acquisition date from DICOM/PAR REC files

import os
import sqlite3
import pandas as pd
import pathlib
import re
import pydicom

from sqlite3.dbapi2 import (
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

from datetime import datetime
from collections import OrderedDict
from copy import deepcopy

from convert_source.cs_utils.fileio import File
from convert_source.cs_utils.const import DB_TABLES

def construct_db_dict(study_dir: Optional[str] = "",
                    sub_id: Optional[Union[int,str]] = "",
                    file_id: Optional[str] = "",
                    bids_name: Optional[str] = "",
                    ses_id: Union[int,str] = None,
                    file_name: Optional[str] = "",
                    rel_path: Optional[str] = "",
                    file_date: Optional[str] = "",
                    acq_date: Optional[str] = "",
                    database: Optional[str] = "",
                    tables: Optional[OrderedDict] = None,
                    num_zeros: int = 7,
                    use_dcm_dir: bool = False
                    ) -> Dict[str,str]:
    """Function that constructs and organizes a dictionary of table/column names to a series of input values.
    Should a database filename be provided, it does not need to exist at runtime. The database tables and columns
    (which are used synomymously) may be specified via the ``tables`` arguments.

    Usage example:
        >>> # In the case that no file_id is provided
        >>> sub_db_dict = construct_db_dict(study_dir='/<parent>/<dir>',
        ...                                 sub_id='001',
        ...                                 ses_id='001',
        ...                                 file_name='/<parent>/<dir>/<sub_data>/<image_data>/file0001.dcm',
        ...                                 acq_date='2021-05-23T21:53:01',
        ...                                 database='file.db')
        ...
        >>> # OR using **kwargs
        >>> sub_db_dict_2 = construct_db_dict(**sub_db_dict)
        >>>
        >>> sub_db_dict_2
        {'file_id': '001',
        'rel_path': './<dir>/<sub_data>/<image_data>/file0001.dcm',
        'file_date': '2021-05-24T09:45:14',
        'acq_date': '2021-05-23T21:53:01',
        'sub_id': '001',
        'ses_id': '001',
        'bids_name': ''}

    Argments:
        study_dir: Path to study image parent directory that contains all the subjects' source image data.
        sub_id: Unique subject ID.
        file_id: Unique database file ID used to identify source image data.
        bids_name: BIDS output filename.
        ses_id: Session ID.
        file_name: Image filename.
        rel_path: Image file relative path. This path includes the parent study directory, and is relative to the study directory.
        file_date: Date the source image file was added to the database.
        acq_date: Date the image data was acquired.
        database: Database filename.
        tables: (Ordered) dictionary that contains the table/column names of the database as the keys, and the corresponding datatypes as items. The 0th index is the column reserved for the SQL database primary key.
        num_zeros: Number of zeros used to zeropad the file_id.
        use_dcm_dir: If set to true, then only the DICOM directory relative path is used as opposed to just the relative path (which includes the filename).

    Returns:
        Dictionary of SQL database tables/columns names mapped to corresponding input values.
    
    Raises:
        DatabaseError: Error that arises if no file ID AND / OR database to query is provided.
        UnboundLocalError: Error that arises if no relative file path is provided, no file ID is provided, OR the study directory and file name are not provided as arguments.
    """
    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)
    
    if os.path.exists(database):
        database: str = os.path.abspath(database)
    elif database and tables:
        database: str = create_db(database=database,
                                tables=tables)
    else:
        raise DatabaseError("Database was not specified, and thus cannot be queried.")
    
    if file_id:
        pass
    elif database:
        file_id: str = get_file_id(database=database,
                                    tables=tables,
                                    num_zeros=num_zeros)
    else:
        raise DatabaseError("No file_id primary key to index OR database to query.")
    
    if sub_id:
        pass
    elif file_id:
        sub_id: str = query_db(database=database,
                                table='sub_id',
                                prim_key='file_id',
                                value=file_id)

    if ses_id:
        pass
    elif file_id:
        ses_id: str = query_db(database=database,
                                table='ses_id',
                                prim_key='file_id',
                                value=file_id)
    
    if study_dir and file_name:
        rel_path: str = _get_dir_relative_path(study_dir=study_dir,
                                                file_name=file_name,
                                                dcm_dir=use_dcm_dir)
    elif rel_path:
        pass
    elif file_id and database:
        rel_path: str = query_db(database=database,
                                table='rel_path',
                                prim_key='file_id',
                                value=file_id)
    else:
        raise UnboundLocalError("Unalbe to ascertain relative file path. The relative path, \
            or file ID must be provided, OR the study directory and file name.")
    
    if file_date:
        pass
    else:
        now = datetime.now()
        file_date: str = str(now.strftime("%Y-%m-%dT%H:%M:%S"))
    
    if acq_date:
        pass
    elif file_name:
        acq_date: str = get_acq_time(file=file_name)
    elif file_id:
        acq_date: str = query_db(database=database,
                                table='acq_date',
                                prim_key='file_id',
                                value=file_id)
    
    if bids_name:
        pass
    elif file_id:
        bids_name: str = query_db(database=database,
                                table='bids_name',
                                prim_key='file_id',
                                value=file_id)

    info: Dict[str,str] = {
        "file_id":      file_id,     
        "rel_path":     rel_path,
        "file_date":    file_date,
        "acq_date":     acq_date,
        "sub_id":       sub_id,
        "ses_id":       ses_id,
        "bids_name":    bids_name
    }
    return info

def create_db(database: str,
            tables: Optional[OrderedDict] = None
            ) -> str:
    """Creates database provided an ordered dictionary of table names and types.

    Usage example:
        >>> db = create_db(database='file.db',
        ...                 tables=db_tables)
        ...

    Arguments:
        database: Input database filename.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.

    Returns:
        String that corresponds to the database filename.
    """
    # Create/access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)

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
            continue
    
    # Commit changes and close the connection
    conn.commit()
    conn.close()
    return database

def insert_row_db(database: str,
                info: Dict[str,str],
                tables: Optional[OrderedDict] = None
                ) -> str:
    """Inserts rows into existing database tables, provided a dictionary of key mapped items of values.

    Usage example:
        Usage example:
        >>> db = insert_row_db(database='file.db',
        ...                     tables=db_tables,
        ...                     info=table_vals)
        ...

    Arguments:
        database: Input database filename.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.
        info: Dictionary with keys that correspond to tables, that contain coresponding values.

    Returns:
        String that corresponds to the database filename.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)
    
    # Query database for duplicates
    file_id: str = query_db(database=database,
                            table='rel_path',
                            prim_key='rel_path',
                            column='file_id',
                            value=info.get('rel_path',''))

    if file_id:
        return database

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
                tables: Optional[OrderedDict] = None
                ) -> int:
    """Gets the number of rows in a databases' first table.

    Usage example:
        Usage example:
        >>> get_len_rows(database='file.db',
        ...              tables=db_tables)
        ...
        45

    Arguments:
        database: Input database filename.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.

    Returns:
        Integer that corresponds to the number of rows in the databases' first table.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)

    # Perform database query
    query: str = f"SELECT COUNT(*) from {list(tables.keys())[1]}"
    c.execute(query)

    result: int = c.fetchone()[0]

    conn.commit()
    conn.close()
    return result

def get_file_id(database: str, 
                tables: Optional[OrderedDict] = None,
                num_zeros: int = 7
                ) -> str:
    """Returns new file_id for file that does not yet exist in the database.

    Usage example:
        Usage example:
        >>> get_file_id(database='file.db',
        ...             tables=db_tables,
        ...             num_zeros=7)
        ...
        '0000045'

    Arguments:
        database: Input database filename.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.
        num_zeros: Number of zeros to use to zeropad the output number.

    Returns:
        Zeropadded string for some unique file_id.
    """
    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)
    file_id: int = get_len_rows(database, tables) + 1
    file_id: str = _zeropad(num=file_id, num_zeros=num_zeros)
    return file_id

def update_table_row(database: str,
                    prim_key: str,
                    table_name: str, 
                    col_name: Optional[str] = "", 
                    value: Optional[Union[int,str]] = None,
                    tables: Optional[OrderedDict] = None
                    ) -> str:
    """Updates a row in a table in some given database provided a table name and a value.

    Usage example:
        >>> db = update_table_row(database='file.db',
        ...                       prim_key='0000001',
        ...                       table_name='bids_name',
        ...                       col_name='bids_name',
        ...                       value='sub-001_ses-001_run-01_T1w')
        ...

    Arguments:
        database: Input database filename.
        prim_key: Required primary key used to index all rows in the database.
        table_name: Table name of table in database to be updated.
        col_name: Column name of the table to be updated. If not provided, then the column name is assumed to be table name.
        value: The value (integer or string) used to update the column in the table/database.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.

    Returns:
        String that corresponds to the database filename.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)

    if col_name:
        pass
    else:
        col_name: str = table_name

    # Perform database table update
    query: str = f"UPDATE {table_name} SET {col_name} = ? WHERE {list(tables.keys())[0]} = ?"

    c.execute(query, (value,prim_key))

    conn.commit()
    conn.close()
    return database

def export_dataframe(database: str,
                    tables: Optional[OrderedDict] = None
                    ) -> pd.DataFrame:
    """Exports all of the tables from the input database as a dataframe.
    Mainly intended for constructing (and exporting) of a dataframe for the
    entire set of study images.

    Usage example:
        >>> df = export_dataframe(database='file.db',
        ...                       tables=db_tables)
        ...

    Arguments:
        database: Input database filename.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.

    Returns:
        Dataframe of all of the tables in the database.
    """
    # Access database
    conn = sqlite3.connect(database)

    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)

    df_list: List = []

    for i in range(1,len(tables)):
        table = list(tables.keys())[i]
        df_tmp: pd.DataFrame = pd.read_sql_query(f"SELECT * FROM {table}", conn)

        if i == 1:
            pass
        else:
            df_tmp = df_tmp.drop(labels=list(tables.keys())[0],axis=1)

        df_list.append(df_tmp)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    return pd.concat(df_list,axis=1,join='outer')

def export_scans_dataframe(database: str,
                            raise_exec: bool = False,
                            tables: Optional[OrderedDict] = None,
                            *args: str
                            ) -> pd.DataFrame:
    """Exports a dataframe provided table/column IDs.

    Usage example:
        >>> df = export_scans_dataframe('file.db',
        ...                             False,
        ...                             None,
        ...                             'sub_id',
        ...                             'ses_id',
        ...                             'bids_name')
        ...

    Arguments:
        database: Input database filename.
        raise_exec: Boolean to raise exception.
        tables: Ordered dictionary, in which the 0th key is the primary key, and the items are the data type.
        *args: Name arguments that correspond to table names of the input database.

    Returns:
        Dataframe of select tables from the database

    Raises:
        DatabaseError: Error that arises should the table not be in the database and 'raise_exec' is True.
    """
    # Access database
    conn = sqlite3.connect(database)
    c = conn.cursor()

    if tables:
        pass
    else:
        tables: OrderedDict = deepcopy(DB_TABLES)

    df_list: List = []

    for i in args:
        table: str = str(i)

        query: str = f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table}'"

        c.execute(query)

        if c.fetchone()[0] == 1:
            pass
        elif raise_exec:
            raise DatabaseError(f"Table {table} does not exist in database")
        else:
            continue
        
        df_tmp: pd.DataFrame = pd.read_sql_query(sql=f"SELECT * FROM {table}", con=conn)
        df_tmp: pd.DataFrame = df_tmp.drop(labels=list(tables.keys())[0],axis=1)
        df_list.append(df_tmp)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    return pd.concat(df_list,axis=1,join='outer',ignore_index=True)

def _get_dir_relative_path(study_dir: str,
                        file_name: str,
                        dcm_dir: bool = False
                        ) -> str:
    """Helper function that returns the relative path provided some parent study directory and some file name - for record keeping purposes.

    Usage example:
        >>> _get_dir_relative_path(study_dir='/<parent>/<dir>',
        ...                        file_name='/<parent>/<dir>/<sub_data>/<image_data>/file0001.dcm',
        ...                        dcm_dir=False)
        ...
        './<dir>/<sub_data>/<image_data>/file0001.dcm'

    Arguments:
        study_dir: Parent study directory that contains all of the subjects' imaging data.
        file_name: Filename/path of image data.
        dcm_dir: If set to true, then only the DICOM directory relative path is returned as opposed to just the relative path (which includes the filename).

    Returns:
        String that corresponds to the relative path of the imaging data.
    """
    study_dir: str = os.path.abspath(study_dir)
    file_name: str = os.path.abspath(file_name)
    path_sep: str = os.path.sep
    dir_tmp = str(pathlib.Path(study_dir).parents[0])

    if ('.dcm' in file_name) and (dcm_dir):
        dcm_img_dir: str = _get_dcm_dir(dcm_file=file_name)
        return dcm_img_dir.replace(dir_tmp + path_sep,"." + path_sep)
    else:
        return file_name.replace(dir_tmp + path_sep,"." + path_sep)


def _export_tmp_bids_df(database: str,
                        sub_id: str,
                        modality_type: str,
                        modality_label: str,
                        gzipped: bool = True,
                        ses_id: Optional[str] = ""
                        ) -> pd.DataFrame:
    """Helper function that constructs modality specificy dataframes pertaining to scan type and acquisition time.

    Usage example:
        >>> df = _export_tmp_bids_df(database='file.db',
        ...                          sub_id='001',
        ...                          modality_type='anat',
        ...                          modality_label='T1w',
        ...                          gzipped=True)
        ...

    Arguments:
        database: Input database filename.
        sub_id: Subject ID.
        modality_type: Modality type for the BIDS related modality.
        modality_label: Modality label for the BIDS related modality.
        gzipped: Whether the output BIDS NIFTI file has been gzipped.
        ses_id: Session ID.

    Returns:
        Scan dataframe for the specified subject, modality label, and modality type.
    """
    if gzipped:
        ext: str = ".nii.gz"
    else:
        ext: str = ".nii"
    
    df_tmp: pd.DataFrame = export_scans_dataframe(database,
                                                    False,
                                                    None,
                                                    'sub_id',
                                                    'ses_id',
                                                    'bids_name',
                                                    'acq_date')
    
    # Rename columns
    #   NOTE: Columns are renamed as column names are not added from the export_scans_dataframe function
    df_cols: Dict[int,str] = {
        0: 'sub_id',
        1: 'ses_id',
        2: 'bids_name',
        3: 'acq_date'
    }

    df_tmp: pd.DataFrame = df_tmp.rename(columns=df_cols)

    # Filter by subject ID
    df: pd.DataFrame = df_tmp.loc[df_tmp['sub_id'] == f'{sub_id}']

    if ses_id:
        df: pd.DataFrame = df.loc[df['ses_id'] == f'{ses_id}']

    # Filter by modality type and modality label
    mod: str = modality_type + "/"

    df: pd.DataFrame = df[df['bids_name'].str.contains(f"{modality_label}")]
    df['bids_name'] = f'{mod}' + df['bids_name'].astype(str) + f'{ext}'
    df: pd.DataFrame = df.dropna(axis=0)
    df: pd.DataFrame = df.reset_index()

    df: pd.DataFrame = df.rename(
                            columns={
                                "bids_name": "filename", 
                                "acq_date": "acq_time"}
                                )
    
    df: pd.DataFrame = df.drop(
                            columns=[
                                "index",
                                "sub_id",
                                "ses_id"]
                                )
    return df

def export_bids_scans_dataframe(database: str,
                                sub_id: str,
                                search_dict: Dict[str,str],
                                gzipped: bool = True,
                                ses_id: Optional[str] = ""
                                ) -> pd.DataFrame:
    """Convenience function that constructs BIDS scan dataframe (that can later be exported as a TSV).
    The resulting dataframe is consistent with the BIDS scan TSV output file 
    (shown here: https://bids-specification.readthedocs.io/en/v1.4.0/03-modality-agnostic-files.html#scans-file).

    Usage example:
        >>> df = export_bids_scans_dataframe(database='file.db',
        ...                                  sub_id='001',
        ...                                  search_dict=search_dict,
        ...                                  gzipped=True)
        ...

    Arguments:
        database: Input database filename.
        sub_id: Subject ID.
        search_dict: Dictionary of modality specific search terms, constructed from the ``read_config`` function.
        gzipped: Whether the output BIDS NIFTI file has been gzipped.
        ses_id: Session ID.

    Returns:
        Scan dataframe for a subject.
    """
    df_list: List = []
    for modality_type,labels in search_dict.items():
        for modality_label,_ in labels.items():
            if modality_type == 'fmap':
                fmap_mods: List[str] = [
                    'phase',
                    'magnitude',
                    'fieldmap',
                    'epi'
                ]

                for fmap_mod in fmap_mods:
                    df_tmp: pd.DataFrame = _export_tmp_bids_df(database=database,
                                                            sub_id=sub_id,
                                                            modality_type=modality_type,
                                                            modality_label=fmap_mod,
                                                            gzipped=gzipped,
                                                            ses_id=ses_id)
                    if len(df_tmp) == 0:
                        continue
                    else:
                        df_list.append(df_tmp)
            else:
                df_tmp: pd.DataFrame = _export_tmp_bids_df(database=database,
                                                            sub_id=sub_id,
                                                            modality_type=modality_type,
                                                            modality_label=modality_label,
                                                            gzipped=gzipped,
                                                            ses_id=ses_id)
                if len(df_tmp) == 0:
                    continue
                else:
                    df_list.append(df_tmp)

    if len(df_list) == 0:
        # Return empty dataframe
        return pd.DataFrame(columns=['filename','acq_time'])
    else:
        df = pd.concat(df_list,axis=0,join='outer',ignore_index=True)
        df.sort_values(by='filename',
                       axis=0,
                       inplace=True)
        return df

def query_db(database:str,
            table: str,
            prim_key: str,
            value: Union[int,str],
            column: Optional[str] = None
            ) -> str:
    """Database query wrapper function that writes and performs a query for some provided value.

    NOTE:
        The SQL query performed in this function assumes that the value is of datatype ``TEXT``.

    Usage example:
        >>> sub_id = query_db(database='file.db',
        ...                   table='sub_id',
        ...                   prim_key='file_id',
        ...                   value='0000001')
        ...
        >>> sub_id
        '001'
        >>> # OR
        >>>
        >>> file_id = query_db(database='file.db',
        ...                   table='sub_id',
        ...                   prim_key='sub_id',
        ...                   column='file_id',
        ...                   value='001')
        ...
        >>> file_id
        '0000001'

    Arguments:
        database: Input database filename.
        table: Table name to be queried.
        prim_key: Primary key or key to be indexed.
        value: Value to be queried or matched for.
        column: Column name to be selected during the query. If not provided, the column name is assumed to be the same as the table name.
    
    Returns:
        Subject ID as a string.
    """
    # Access database
    database: str = os.path.abspath(database)
    conn = sqlite3.connect(database)
    c = conn.cursor()

    if column:
        pass
    else:
        column: str = table

    # Query database
    try:
        query: str = f"SELECT {column} FROM {table} WHERE {prim_key} = '{value}'"
        c.execute(query)
        query_val: str = c.fetchone()[0]

        conn.commit()
        conn.close()
        return query_val
    except (TypeError, OperationalError):
        # Commit changes and close the connection
        conn.commit()
        conn.close()
        return ""

def _zeropad(num: Union[str,int],
             num_zeros: int = 2
             ) -> str:
    """Zeropads a number, should that number be an int or str.

    NOTE:
        This function is also defined in ``convert_source/cs_utils/utils`` as ``zeropad``.

    Usage example:
        >>> zeropad(5,2)
        '05'
        >>> zeropad('5',2)
        '05'

    Arguments:
        num: Input number (as str or int) to zeropad.
        num_zeros: Number of zeroes to pad with.

    Returns:
        Zeropadded string of the number, or the original string if the input string could not be represented as an integer.

    Raises:
        TypeError: Error that arises if floats are passed as an argument.
    """
    if type(num) is float:
        raise TypeError("Only integers and strings can be used with the zeropad function.")
    try:
        num: str = str(num)
        num: str = num.zfill(num_zeros)
        return num
    except ValueError:
        return num

def _get_dcm_dir(dcm_file: str) -> str:
    """Function that returns the absolute directory path of a DICOM directory (excluding the filename).

    Usage example:
        >>> dcm_dir = get_dcm_dir(dcm_file='./<path>/<to>/<dcm>/MR00001.dcm')
        >>> dcm_dir
        '/<system>/<path>/<to>/<dcm>'
    
    Arguments:
        dcm_file: DICOM file path.

    Returns:
        Absolute directory path of the DICOM directory as a string.

    Raises:
        FileNotFoundError: Error that arises if the specified DICOM file does not exist.
    """
    if os.path.exists(dcm_file):
        pass
    else:
        raise FileNotFoundError("The specified DICOM file does not exist.")

    with File(file=dcm_file) as f:
        [dir_path, 
        _, 
        _] = f.file_parts()
    return dir_path

def get_file_creation_date(file: str) -> str:
    """Returns the file creation date or the date the file was last modified.

    Usage example:
        >>> acq_date_time = get_file_creation_date(file='MR0001.dcm')
        >>> acq_date_time
        '2019-04-28T16:34:19'

    Arguments:
        file: Path to file.

    Returns:
        Date-time string of the form: ``YYYY-MM-DD(T)hh:mm:ss``
    """
    file: str = os.path.abspath(file)
    ti_c: str = os.path.getctime(file)
    return datetime.fromtimestamp(ti_c).strftime('%Y-%m-%dT%H:%M:%S')

def get_par_acq_time(par_file: str) -> str:
    """Returns the acquisition date and time for the input PAR header file if possible, or the file creation date and time otherwise.

    NOTE: 
        This is performed via a RegEx search of the PAR file header, and is not guaranteed to work on PAR files from other Philips MR scanners.

    Usage example:
        >>> acq_date_time = get_par_acq_time(par_file='T1_Ax_MPRAGE.PAR')
        >>> acq_date_time
        '2018-12-15T09:09:10'

    Arguments:
        file: Path to PAR header file.

    Returns:
        Date-time string of the form: ``YYYY-MM-DD(T)hh:mm:ss``
    """
    par_file: str = os.path.abspath(par_file)

    regexp: re = re.compile(
        r'.    Examination date/time              :   .*?([0-9.+ /w :*?*]+)')

    with open(par_file) as f:
        tmp_acq_date_time: str = ""
        for line in f:
            match = regexp.match(line)
            if match:
                tmp_acq_date_time: str = match.group(1)
                break
        
        if tmp_acq_date_time == "":
            return get_file_creation_date(file=par_file)
    
    # Date
    year: str = tmp_acq_date_time[:4]
    month: str = tmp_acq_date_time[5:7]
    day: str = tmp_acq_date_time[8:10]
    date: str = f"{year}-{month}-{day}"

    # Time
    hr: str = tmp_acq_date_time[13:15]
    min: str = tmp_acq_date_time[16:18]
    sec: str = tmp_acq_date_time[19:21]
    time: str = f"{hr}:{min}:{sec}"

    return f"{date}T{time}"

def get_dcm_acq_time(dcm_file: str) -> str:
    """Returns the acquisition date and time for the input DICOM file if possible, or the file creation date and time otherwise.

    Usage example:
        >>> acq_date_time = get_dcm_acq_time(dcm_file='MR0002.dcm')
        >>> acq_date_time
        '2016-09-18T20:17:48'

    Arguments:
        file: Path to DICOM file.

    Returns:
        Date-time string of the form: ``YYYY-MM-DD(T)hh:mm:ss``
    """
    dcm_file: str = os.path.abspath(dcm_file)
    try:
        ds = pydicom.dcmread(dcm_file,force=True)
        tmp_acq_date: str = ds.AcquisitionDate
        tmp_acq_time: str = ds.AcquisitionTime

        # Date
        year: str = tmp_acq_date[:4]
        month: str = tmp_acq_date[4:6]
        day: str = tmp_acq_date[6:]
        date: str = f"{year}-{month}-{day}"

        # Time
        hr: str = tmp_acq_time[:2]
        min: str = tmp_acq_time[2:4]
        sec: str = tmp_acq_time[4:6]
        time: str = f"{hr}:{min}:{sec}"

        return f"{date}T{time}"
    except (AttributeError,KeyError):
        return get_file_creation_date(file=dcm_file)

def get_acq_time(file: str) -> str:
    """Returns the acquisition date and time for the input medical image/file if possible, or the file creation date and time otherwise.

    Usage example:
        >>> acq_date_time = get_acq_time(file='MR0002.dcm')
        >>> acq_date_time
        '2016-09-18T20:17:48'

    Arguments:
        file: Path to file.

    Returns:
        Date-time string of the form: ``YYYY-MM-DD(T)hh:mm:ss``
    """
    file: str = os.path.abspath(file)

    if '.dcm' in file.lower():
        return get_dcm_acq_time(dcm_file=file)
    elif '.par' in file.lower():
        return get_par_acq_time(par_file=file)
    else:
        return get_file_creation_date(file=file)
