from sqlite3worker import Sqlite3Worker
from os import path
from prettytable import PrettyTable
import csv
import sqlite3


db_path = "/var/scripts_rd/rotinas/alivescan.db"
sql_worker = False

class DBConnection():

    def __init__(self):
        global sql_worker
        if not sql_worker:

            #Verifica a tabela e se não existir cria na 1ª inicialização do worker
            if not path.exists(db_path):
                self.create_table()

            #Inicia a conexão ao BDD com o worker para Threads
            sql_worker = Sqlite3Worker(db_path)

    def create_table(self):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        table_scan = '''
            CREATE TABLE IF NOT EXISTS HOSTS_ONLINE (
                id INTEGER PRIMARY KEY,
                IP TEXT,
                TYPE TEXT,
                DATE_SCAN DATE
            );
            '''
        
        table_computer = '''
            CREATE TABLE IF NOT EXISTS DESKTOP_INVENTORY (
                id INTEGER PRIMARY KEY,
                IP TEXT,
                SO TEXT,
                GLPI_AGENT TEXT,
                TERMINAL TEXT,
                DATE_SCAN DATE,
                OWNER TEXT
            );
            '''
        
        table_monitor = '''
            CREATE TABLE IF NOT EXISTS PDV_SCREEN_TYPE (
                id INTEGER PRIMARY KEY,
                IP TEXT,
                TYPE TEXT,
                DATE_SCAN DATE,
                OWNER TEXT
            );
            '''
        
        table_devices = '''
            CREATE TABLE IF NOT EXISTS DEVICES_INVENTORY (
                id INTEGER PRIMARY KEY,
                IP TEXT,
                MAC TEXT,
                DEVICE TEXT,
                MODEL TEXT,
                DATE_SCAN DATE,
                OWNER TEXT
            );
            '''
        
        cursor.execute(table_scan)
        cursor.execute(table_computer)
        cursor.execute(table_monitor)
        cursor.execute(table_devices)
        
        conn.close()


    def get_connection(self):
        return sql_worker
    

def db_select_values(table, primarykey="", valueprimarykey="", type_select="COLUMN", columns=""):
    db_instance = DBConnection()
    worker = db_instance.get_connection()

    if type_select == "COLUMN":
        columns_str = ", ".join(columns) if isinstance(columns, (list, tuple)) else columns
        query = f"SELECT {columns_str} FROM {table}" if not primarykey else f"SELECT {columns_str} FROM {table} WHERE {primarykey} = ?"
        resultados = worker.execute(query, (valueprimarykey,)) if primarykey else worker.execute(query)
        # Retorna a lista de tuplas inteiras
        return resultados

    elif type_select in ["LINE", "TABLE"]:
        query = f"SELECT * FROM {table}" if type_select == "TABLE" else f"SELECT * FROM {table} WHERE {primarykey} = ?"
        resultados = worker.execute(query, (valueprimarykey,) if primarykey else ())
        return resultados


def db_insert_line(table, values, columns=[]):
    if not columns == []:
        
        if len(columns) != len(values):
            raise ValueError("O número de colunas e valores deve ser o mesmo")
        
        # Montando a string das colunas e dos placeholders
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['?'] * len(values))

        # Construindo a query SQL
        sql_query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

    db_instance = DBConnection()
    worker = db_instance.get_connection()
    worker.execute(sql_query, values)


def db_update_dynamic_value(table, primarykey, valueprimarykey, keys_list, values_list):

    if isinstance(keys_list, list):
        set_part = ", ".join([f"{k} = ?" for k in keys_list])
    elif isinstance(keys_list, str):
        set_part = f"{keys_list} = ?"
        values_list = [values_list]

    db_instance = DBConnection()
    worker = db_instance.get_connection()
    sql_query = f"UPDATE {table} SET {set_part} WHERE {primarykey} = ?"
    parameters = tuple(values_list) + (valueprimarykey,)
    worker.execute(sql_query, parameters)


def db_delete_all(table):
    db_instance = DBConnection()
    worker = db_instance.get_connection()
    sql_query = f"DELETE FROM {table}"
    worker.execute(sql_query)


def show_tables(table):
    db_instance = DBConnection()
    worker = db_instance.get_connection()
    resultados = worker.execute(f"SELECT * FROM {table}")
    colunas = [descricao[0] for descricao in resultados[0].keys()]
    tabela = PrettyTable(colunas)
    for registro in resultados:
        tabela.add_row(list(registro.values()))
    print(tabela)


def db_extract_table_csv(filename, table):
    table_data = db_select_values(table, type="TABLE")
    with open(filename, mode='w', newline='') as arquivo_csv:
        csvconnect = csv.writer(arquivo_csv, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for line in table_data:
            csvconnect.writerow(line)
