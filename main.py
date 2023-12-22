from flask import Flask, render_template, request, flash, redirect, jsonify
from banco import configbanco
import jwt
import mysql.connector
from mysql.connector import Error
import pandas as pd
import pymysql
from datetime import datetime
import re
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = "gg123"
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    return render_template("html/paginainicial.html")

@app.route("/logininicio")
def logininicio():
    return render_template("html/login.html")

@app.route("/cadastrar")
def cadastrar():
    return render_template("html/cadastro.html")

@app.route('/decode-token/<token>', methods=['POST'])
def decode_token(token):
    try:
        token = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IjliMDI4NWMzMWJmZDhiMDQwZTAzMTU3YjE5YzRlOTYwYmRjMTBjNmYiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20iLCJhenAiOiIxMDY1MjY5NDk4MzU1LWI5bHJlNzFwdHZubHFwNWpvbWJwamtnMHNuc2N0aXBlLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tIiwiYXVkIjoiMTA2NTI2OTQ5ODM1NS1iOWxyZTcxcHR2bmxxcDVqb21icGprZzBzbnNjdGlwZS5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbSIsInN1YiI6IjExMTQ1MDkwNDMwNTE1MDE4NjQxMCIsImVtYWlsIjoiZ2FicmllbGphbnMxOEBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmJmIjoxNzAzMjY2MzY4LCJuYW1lIjoiR2FicmllbCBFZHVhcmRvIEphbnNlbiIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMczJSaUhqeFJtTjFvdkxiT0xDNGRGMEVtcndqbHFLWFdIZjNjY3lSVmZJUHM9czk2LWMiLCJnaXZlbl9uYW1lIjoiR2FicmllbCBFZHVhcmRvIiwiZmFtaWx5X25hbWUiOiJKYW5zZW4iLCJsb2NhbGUiOiJwdC1CUiIsImlhdCI6MTcwMzI2NjY2OCwiZXhwIjoxNzAzMjcwMjY4LCJqdGkiOiJmYTM4ZWEyMTI1ZTIwZTA2MTJjNzQ2YzY3MWZlOWNjNjM4ZjI3MmMxIn0.Ttw7tBDzmHe8u5CaGiECf_On75QJ4DucDQ0N3Xs6jH19_Kmh5_yhzKoP_1h-E7dAZ08Ew5d55xS_LSV0_d1kVX7U_S3at8geiCJ_IMGDG1lasH_bFN7ysnxPokKtADL85Ef7zYuXKreDV7_RYLrBxjQMpXAztn8-LVa_BmFA6sN_3ALZNkad_IrRPfZpG6fpFGAEHLYL2_qfqQ96u67_wAEPZw-FGKnWzRGZfzPYgoJMqYx01PnNToG4A5znrItSesD_jNjn7FQKVcUKJsEYXjeD4cjo9q7Scbj8OGQNu-am0NZ8g4qOMvH3ZNeXMnyZDwUqdZNHXA0TU0y1ra9sVA'
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return decoded_token
    except jwt.ExpiredSignatureError:
        return {"error": "Token expirado"}
    except jwt.InvalidTokenError:
        return {"error": "Token inválido"}


@app.route("/cadastro", methods=['POST'])
def cadastro():
    user = []
    nomecad = request.form.get('nomecad')
    sobrenomecad = request.form.get('sobrenomecad')
    emailcad = request.form.get('emailcad')
    senhacad = request.form.get('senhacad')
    confirmaSenhacad = request.form.get('confirmaSenhacad')

    if senhacad != confirmaSenhacad:
        flash('A senha digitada diverge da senha de confirmação! ')
        return render_template("html/cadastro.html")

   # conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
    conexao = configbanco(db_type='pymysql')
    cursor = conexao.cursor()
    cursor.execute(
        f"insert into usuarios values (default, '{nomecad}', '{sobrenomecad}', '{emailcad}', '{senhacad}');")
    conexao.commit()
    conexao.close()

    return render_template("html/login.html", nomecadastro=nomecad + " cadastrado!")


@app.route("/login", methods=['POST'])
def login():
    global idlogado
    idlogado = 0
    email = request.form.get('email')
    senha = request.form.get('senha')

    #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')

    connect_BD  = configbanco(db_type='mysql-connector')

    if connect_BD.is_connected():
        cont = 0
        print('conectado')
        cursur = connect_BD.cursor()
        cursur.execute("select * from usuarios;")
        usuariosBD = cursur.fetchall()

    for usuarios in usuariosBD:
        cont += 1
        idlogado = str(usuarios[0])
        usuariosEmail = str(usuarios[3])
        usuariosSenha = str(usuarios[4])

        if usuariosEmail == email and usuariosSenha == senha:
            print(idlogado)
            return redirect("/InicioBuscarEvento")

        if cont >= len(usuariosBD):
            flash('Usuário inválido!')
            return redirect("/")
    else:
        return redirect("/")


@app.route("/InicioCriarEvento")
def criarevento():
    return render_template("html/CriarEvento.html")


@app.route("/CriarEvento", methods=['POST'])
def CriarEvento():
    global idlogado
    nomeEventocad = request.form.get('nomeEventocad')
    descricaocad = request.form.get('descricaocad')
    categoriacad = request.form.get('categoriacad')
    dataCad = request.form.get('dataCad')
    horCad = request.form.get('horCad')
    localEventocad = request.form.get('localEventocad')
    totalParticipantescad = request.form.get('totalParticipantescad')
    data_atual = datetime.now().date()
    hora_atual = datetime.now().time()

    dataCad = datetime.strptime(dataCad, "%Y-%m-%d").date()
    horCad = datetime.strptime(horCad, "%H:%M").time()
    if dataCad < data_atual:
        flash("A data fornecida é menor que à data atual.")
        return render_template("html/CriarEvento.html")
    elif dataCad == data_atual and horCad < hora_atual:
        flash("A hora fornecida é menor que à hora atual.")
        return render_template("html/CriarEvento.html")

    #conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
    conexao = configbanco(db_type='pymysql')
    cursor = conexao.cursor()
    cursor.execute(
        f"insert into eventos values (default, '{descricaocad}', '{nomeEventocad}', '{dataCad}' , '{horCad}', {idlogado}, '{localEventocad}', {totalParticipantescad}, '{categoriacad}');")
    conexao.commit()
    conexao.close()

    return redirect("/InicioBuscarEvento")


@app.route("/InicioBuscarEvento")
def buscarEvento():
    #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
    connect_BD  = configbanco(db_type='mysql-connector')

    if connect_BD.is_connected():
        print('conectado')
        cursur = connect_BD.cursor()
        cursur.execute(
            'SELECT\
            e.id_eventos,\
            e.descricao_evento,\
            e.nome_evento,\
            e.data_evento,\
            e.hora_evento,\
            c.descricao_categoria,\
            u.nome AS nome_usuario,\
            COUNT(p.id_evento_presente) AS numero_presentes,\
            e.local_evento,\
            e.total_participantes\
            FROM\
            eventos AS e\
            LEFT JOIN\
            presencas AS p ON p.id_evento_presente = e.id_eventos\
            INNER JOIN\
            categoria AS c ON c.id_categoria = e.categoria\
            INNER JOIN\
            usuarios AS u ON u.id_usuario = e.id_usuario_evento\
            GROUP BY\
            e.total_participantes,\
            e.local_evento,\
            e.id_eventos,\
            e.descricao_evento,\
            e.nome_evento,\
            e.data_evento,\
            e.hora_evento,\
            c.descricao_categoria,\
            u.nome;')
        eventos = cursur.fetchall()
    return render_template("html/BuscarEventos.html", eventos=eventos)


@app.route("/ConfirmarCancelarPresenca", methods=['POST'])
def CancelarPresenca():
    global idlogado
    eventoPresenca = request.form.get('eventoPresenca')
    botaoConfirma = request.form.get('botaoConfirma')
    botaoCancela = request.form.get('botaoCancela')

    if botaoCancela == 'true':
       # connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
        connect_BD  = configbanco(db_type='mysql-connector')

        if connect_BD.is_connected():
            cont = 0
            # print('conectado')
            cursur = connect_BD.cursor()
            cursur.execute(
                f"select * from presencas where id_evento_presente = '{eventoPresenca}' and id_usuario_presente = '{idlogado}';")
            presencasBD = cursur.fetchall()

        if len(presencasBD) == 0:
            # print('Sua presença já está cancelada!')
            flash('Sua presença já está cancelada!')
            cursur = connect_BD.cursor()
            cursur.execute(
                'SELECT\
                e.id_eventos,\
                e.descricao_evento,\
                e.nome_evento,\
                e.data_evento,\
                e.hora_evento,\
                c.descricao_categoria,\
                u.nome AS nome_usuario,\
                COUNT(p.id_evento_presente) AS numero_presentes,\
                e.local_evento,\
                e.total_participantes\
                FROM\
                eventos AS e\
                LEFT JOIN\
                presencas AS p ON p.id_evento_presente = e.id_eventos\
                INNER JOIN\
                categoria AS c ON c.id_categoria = e.categoria\
                INNER JOIN\
                usuarios AS u ON u.id_usuario = e.id_usuario_evento\
                GROUP BY\
                e.total_participantes,\
                e.local_evento,\
                e.id_eventos,\
                e.descricao_evento,\
                e.nome_evento,\
                e.data_evento,\
                e.hora_evento,\
                c.descricao_categoria,\
                u.nome;')
            eventos = cursur.fetchall()
            return render_template("html/BuscarEventos.html", eventos=eventos)
        else:
           # conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()
            print(eventoPresenca)
            print(idlogado)
            cursor.execute(
                f"DELETE FROM presencas WHERE ID_EVENTO_PRESENTE = '{eventoPresenca}' AND ID_USUARIO_PRESENTE = '{idlogado}';")
            conexao.commit()
            conexao.close()

            #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
            connect_BD  = configbanco(db_type='mysql-connector')

            if connect_BD.is_connected():
                print('conectado')
                cursur = connect_BD.cursor()
                cursur.execute(
                    'SELECT\
                    e.id_eventos,\
                    e.descricao_evento,\
                    e.nome_evento,\
                    e.data_evento,\
                    e.hora_evento,\
                    c.descricao_categoria,\
                    u.nome AS nome_usuario,\
                    COUNT(p.id_evento_presente) AS numero_presentes,\
                    e.local_evento,\
                    e.total_participantes\
                    FROM\
                    eventos AS e\
                    LEFT JOIN\
                    presencas AS p ON p.id_evento_presente = e.id_eventos\
                    INNER JOIN\
                    categoria AS c ON c.id_categoria = e.categoria\
                    INNER JOIN\
                    usuarios AS u ON u.id_usuario = e.id_usuario_evento\
                    GROUP BY\
                    e.total_participantes,\
                    e.local_evento,\
                    e.id_eventos,\
                    e.descricao_evento,\
                    e.nome_evento,\
                    e.data_evento,\
                    e.hora_evento,\
                    c.descricao_categoria,\
                    u.nome;')
                eventos = cursur.fetchall()
                return render_template("html/BuscarEventos.html", eventos=eventos)
    else:
        return ConfirmarPresenca()


def ConfirmarPresenca():
    global idlogado
    eventoPresenca = request.form.get('eventoPresenca')
    botaoConfirma = request.form.get('botaoConfirma')
    botaoCancela = request.form.get('botaoCancela')
    #print(botaoConfirma)
    if botaoConfirma == 'true':
        #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
        connect_BD  = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cont = 0
            #print('conectado')

            cursur = connect_BD.cursor()
            cursur.execute(
                f"SELECT count(*) FROM presencas where id_evento_presente ='{eventoPresenca}';")
            linhas = cursur.fetchall()

            for linha in linhas:
                numero_participantes = linha[0]

            cursur = connect_BD.cursor()
            cursur.execute(
                f"select total_participantes from eventos where id_eventos = '{eventoPresenca}';")
            linhas = cursur.fetchall()

            for linha in linhas:
                limite_participantes = linha[0]

            cursur = connect_BD.cursor()
            cursur.execute(
                f"select * from presencas where id_evento_presente = '{eventoPresenca}' and id_usuario_presente = '{idlogado}';")
            presencasBD = cursur.fetchall()

        if len(presencasBD) > 0 or numero_participantes == limite_participantes:

            if len(presencasBD) > 0:
                flash('Presença já confirmada!')
            else:
                flash('Limite de presenças já foi atingido!')
            cursur = connect_BD.cursor()
            cursur.execute(
                'SELECT\
                e.id_eventos,\
                e.descricao_evento,\
                e.nome_evento,\
                e.data_evento,\
                e.hora_evento,\
                c.descricao_categoria,\
                u.nome AS nome_usuario,\
                COUNT(p.id_evento_presente) AS numero_presentes,\
                e.local_evento,\
                e.total_participantes\
                FROM\
                eventos AS e\
                LEFT JOIN\
                presencas AS p ON p.id_evento_presente = e.id_eventos\
                INNER JOIN\
                categoria AS c ON c.id_categoria = e.categoria\
                INNER JOIN\
                usuarios AS u ON u.id_usuario = e.id_usuario_evento\
                GROUP BY\
                e.total_participantes,\
                e.local_evento,\
                e.id_eventos,\
                e.descricao_evento,\
                e.nome_evento,\
                e.data_evento,\
                e.hora_evento,\
                c.descricao_categoria,\
                u.nome;')
            eventos = cursur.fetchall()
            return render_template("html/BuscarEventos.html", eventos=eventos)
        else:
            #conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()
            print(eventoPresenca)
            print(idlogado)
            cursor.execute(
                f"INSERT INTO presencas VALUES ('{eventoPresenca}','{idlogado}');")
            conexao.commit()
            conexao.close()

           # connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
            connect_BD  = configbanco(db_type='mysql-connector')
            if connect_BD.is_connected():
                #print('conectado')
                cursur = connect_BD.cursor()
                cursur.execute(
                    'SELECT\
                    e.id_eventos,\
                    e.descricao_evento,\
                    e.nome_evento,\
                    e.data_evento,\
                    e.hora_evento,\
                    c.descricao_categoria,\
                    u.nome AS nome_usuario,\
                    COUNT(p.id_evento_presente) AS numero_presentes,\
                    e.local_evento,\
                    e.total_participantes\
                    FROM\
                    eventos AS e\
                    LEFT JOIN\
                    presencas AS p ON p.id_evento_presente = e.id_eventos\
                    INNER JOIN\
                    categoria AS c ON c.id_categoria = e.categoria\
                    INNER JOIN\
                    usuarios AS u ON u.id_usuario = e.id_usuario_evento\
                    GROUP BY\
                    e.total_participantes,\
                    e.local_evento,\
                    e.id_eventos,\
                    e.descricao_evento,\
                    e.nome_evento,\
                    e.data_evento,\
                    e.hora_evento,\
                    c.descricao_categoria,\
                    u.nome;')
                eventos = cursur.fetchall()
                return render_template("html/BuscarEventos.html", eventos=eventos)


@app.route("/InicioGerenciarEventos")
def InicioGerenciarEventos():
    global idlogado
    #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
    connect_BD  = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        print('conectado')
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT\
            e.id_eventos,\
            e.descricao_evento,\
            e.nome_evento,\
            e.data_evento,\
            e.hora_evento,\
            c.descricao_categoria,\
            u.nome AS nome_usuario,\
            COUNT(p.id_evento_presente) AS numero_presentes,\
            e.local_evento,\
            e.total_participantes\
            FROM\
            eventos AS e\
            LEFT JOIN\
            presencas AS p ON p.id_evento_presente = e.id_eventos\
            INNER JOIN\
            categoria AS c ON c.id_categoria = e.categoria\
            INNER JOIN\
            usuarios AS u ON u.id_usuario = e.id_usuario_evento\
            where e.id_usuario_evento = "{idlogado}" \
            GROUP BY\
            e.total_participantes,\
            e.local_evento,\
            e.id_eventos,\
            e.descricao_evento,\
            e.nome_evento,\
            e.data_evento,\
            e.hora_evento,\
            c.descricao_categoria,\
            u.nome;')
        eventos = cursur.fetchall()
    return render_template("html/GerenciarEventos.html", eventos=eventos)


@app.route("/GerenciarEventos", methods=['POST'])
def EditarEvento():
    global idlogado
    eventoPresenca = request.form.get('eventoPresenca')
    botaoEditar = request.form.get('botaoEditar')
    eventosList = []
    if botaoEditar == 'true':
        #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
        connect_BD  = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor()
        cursur.execute(
            f"SELECT * FROM eventos e, categoria c where e.categoria = c.id_categoria and e.id_eventos = '{eventoPresenca}';")
        eventos = cursur.fetchall()

        for linha in eventos:
            horOri = linha[5]

        horAlt = str(horOri)
        horAlt = horAlt[:2]
        horAlt = re.sub(r'[^\w\s]', '', horAlt)

        horAlt = int(horAlt)
        if horAlt < 10:
            horOri = '0' + str(horOri)

        eventosList.append(linha[0])
        eventosList.append(linha[1])
        eventosList.append(linha[2])
        eventosList.append(linha[10])
        eventosList.append(linha[3])
        eventosList.append(linha[4])
        eventosList.append(horOri)
        eventosList.append(linha[6])
        eventosList.append(linha[7])
        eventosList.append(linha[8])
        eventosList.append(linha[9])
        print(eventosList)

        return render_template("html/EditarEvento.html", eventos=eventosList)

    else:
        return ExcluirEvento()


def ExcluirEvento():
    global idlogado
    eventoPresenca = request.form.get('eventoPresenca')
    botaoExcluirEvento = request.form.get('botaoExcluirEvento')

    if botaoExcluirEvento == 'true':

        #conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        cursor.execute(
            f"DELETE FROM presencas WHERE ID_EVENTO_PRESENTE = '{eventoPresenca}';")
        conexao.commit()
        conexao.close()

        #conexao = pymysql.connect(db='usuarios', user='root', passwd='1234')
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        cursor.execute(
            f"DELETE FROM eventos WHERE ID_EVENTOS = '{eventoPresenca}' and ID_USUARIO_EVENTO = '{idlogado}';")
        conexao.commit()
        conexao.close()

        #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
        connect_BD  = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            print('conectado')
            cursur = connect_BD.cursor()
            cursur.execute(
                f'SELECT\
                e.id_eventos,\
                e.descricao_evento,\
                e.nome_evento,\
                e.data_evento,\
                e.hora_evento,\
                c.descricao_categoria,\
                u.nome AS nome_usuario,\
                COUNT(p.id_evento_presente) AS numero_presentes,\
                e.local_evento,\
                e.total_participantes\
                FROM\
                eventos AS e\
                LEFT JOIN\
                presencas AS p ON p.id_evento_presente = e.id_eventos\
                INNER JOIN\
                categoria AS c ON c.id_categoria = e.categoria\
                INNER JOIN\
                usuarios AS u ON u.id_usuario = e.id_usuario_evento\
                where e.id_usuario_evento = "{idlogado}" \
                GROUP BY\
                e.total_participantes,\
                e.local_evento,\
                e.id_eventos,\
                e.descricao_evento,\
                e.nome_evento,\
                e.data_evento,\
                e.hora_evento,\
                c.descricao_categoria,\
                u.nome;')
            eventos = cursur.fetchall()
        return render_template("html/GerenciarEventos.html", eventos=eventos)
    else:
        return Detalhes()


def Detalhes():
    global idlogado
    eventoPresenca = request.form.get('eventoPresenca')
    #connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
    connect_BD  = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        print('conectado')
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT\
              e.id_eventos,\
              e.descricao_evento,\
              e.nome_evento,\
              e.data_evento,\
              e.hora_evento,\
              c.descricao_categoria,\
              u.nome AS nome_usuario,\
              COUNT(p.id_evento_presente) AS numero_presentes,\
              e.local_evento,\
              e.total_participantes\
              FROM\
              eventos AS e\
              LEFT JOIN\
              presencas AS p ON p.id_evento_presente = e.id_eventos\
              INNER JOIN\
              categoria AS c ON c.id_categoria = e.categoria\
              INNER JOIN\
              usuarios AS u ON u.id_usuario = e.id_usuario_evento\
              where e.id_usuario_evento = "{idlogado}" and e.id_eventos = "{eventoPresenca}" \
              GROUP BY\
              e.total_participantes,\
              e.local_evento,\
              e.id_eventos,\
              e.descricao_evento,\
              e.nome_evento,\
              e.data_evento,\
              e.hora_evento,\
              c.descricao_categoria,\
              u.nome;')
        eventos = cursur.fetchall()

       # connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')
        connect_BD  = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            print('conectado')
            cursur = connect_BD.cursor()
            cursur.execute(
                f'SELECT concat(u.nome, " ",u.sobrenome) as nomeCompleto FROM presencas as p, usuarios as u where p.id_usuario_presente = u.id_usuario and p.id_evento_presente = "{eventoPresenca}";')
            presentes = cursur.fetchall()

    return render_template("html/Detalhes.html", eventos=eventos, presentes=presentes)


@app.route("/EditarEvento", methods=['POST'])
def EditarEventoEfetivo():
    global idlogado
    eventoEditar = request.form.get('eventoEditar')
    nomeEventocad = request.form.get('nomeEventocad')
    descricaocad = request.form.get('descricaocad')
    categoriacad = request.form.get('categoriacad')

    dataCad = request.form.get('dataCad')
    horCad = request.form.get('horCad')
    localEventocad = request.form.get('localEventocad')
    totalParticipantescad = request.form.get('totalParticipantescad')
    data_atual = datetime.now().date()
    hora_atual = datetime.now().time()

    dataCad = datetime.strptime(dataCad, "%Y-%m-%d").date()
    tamHorCad = len(horCad)
    if tamHorCad > 5:
        horCad = horCad[:-3]
    horCad = datetime.strptime(horCad, "%H:%M").time()
    if dataCad < data_atual:
        flash("A data fornecida é menor que à data atual.")
        return render_template("html/CriarEvento.html")
    elif dataCad == data_atual and horCad < hora_atual:
        flash("A hora fornecida é menor que à hora atual.")
    #conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
    conexao = configbanco(db_type='pymysql')
    cursor = conexao.cursor()
    cursor.execute(
        f"UPDATE eventos SET descricao_evento ='{descricaocad}',nome_evento = '{nomeEventocad}',categoria = '{categoriacad}',data_evento = '{dataCad}',hora_evento = '{horCad}',local_evento = '{localEventocad}',total_participantes = {totalParticipantescad} WHERE id_eventos = {eventoEditar};")
    conexao.commit()
    conexao.close()

    return redirect("/InicioGerenciarEventos")


if __name__ == "__main__":
    app.run(debug=True)

