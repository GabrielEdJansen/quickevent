import mysql.connector
import pymysql
def configbanco(db_type='pymysql'):
    host = 'roundhouse.proxy.rlwy.net'
    user = 'root'
    password = 'FCG36126fhA2GDbggHGAbe6-B52Hg46A'
    database = 'railway'
    port = 32945
    if db_type == 'pymysql':
        conexao = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        return conexao
    elif db_type == 'mysql-connector':
        connect_BD = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        return connect_BD
    else:
        raise ValueError("Tipo de banco de dados inválido. Use 'pymysql' ou 'mysql-connector'.")