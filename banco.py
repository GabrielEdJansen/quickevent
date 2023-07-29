import mysql.connector
import pymysql
def configbanco(db_type='pymysql'):
    host = 'containers-us-west-171.railway.app'
    user = 'root'
    password = 'eZjRZ12TZO1hRrFaOc2Z'
    database = 'railway'
    port = 7763
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