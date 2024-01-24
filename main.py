from flask import Flask, render_template, request, flash, redirect, jsonify, url_for
from banco import configbanco
import jwt
import base64
from PIL import Image
from io import BytesIO
from werkzeug.utils import secure_filename
import os
import mysql.connector
from mysql.connector import Error
import pandas as pd
import pymysql
from datetime import datetime
import re
from flask_cors import CORS
from flask_mail import Mail, Message
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = "gg123"
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'gabrieljans18@gmail.com'
app.config['MAIL_PASSWORD'] = 'tczm ktsn ogwd nble'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route("/")
def home():
    return render_template("html/paginainicial.html")

@app.route("/logininicio")
def logininicio():
    return render_template("html/login.html")

@app.route("/InformacaoConta")
def InformacaoConta():
    global idlogado
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT nome, sobrenome, foto_nome, foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()
    return render_template("html/InformacaoConta.html", nome=usuario[0], sobrenome=usuario[1], foto_nome=usuario[2], foto=usuario[3])

def allowed_file(filename):
    # Adicione uma lógica para verificar se a extensão do arquivo é permitida
    # Por exemplo, você pode verificar se a extensão está em uma lista de extensões permitidas
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}
# Defina o caminho para a pasta de upload


@app.route("/salvar_informacoes", methods=["POST"])
def salvar_informacoes():
    if request.method == "POST":
        # Obtenha o arquivo da imagem do formulário
        foto = request.files["profile_pic"]

        # Verifique se um arquivo de imagem foi enviado
        if foto and allowed_file(foto.filename):
            try:
                # Abra a imagem usando PIL
                img = Image.open(foto)

                # Verifique as dimensões da imagem redimensionada
                if img.size[0] > 200 or img.size[1] > 200:
                    flash("A foto deve ter dimensões no máximo 200x200 pixels.", "error")
                    return redirect(url_for("InformacaoConta"))

                # Gere um nome único para a foto usando secure_filename
                foto_nome = secure_filename(foto.filename)

                # Converta a imagem redimensionada para dados binários
                img_buffer = BytesIO()

                # Salve a imagem no formato apropriado (JPEG, PNG, GIF) com base na extensão original
                file_extension = foto.filename.rsplit('.', 1)[1].lower()
                if file_extension in {'jpg', 'jpeg'}:
                    img.save(img_buffer, format="JPEG")
                elif file_extension == 'png':
                    img.save(img_buffer, format="PNG")
                elif file_extension == 'gif':
                    img.save(img_buffer, format="GIF")

                img_binario = img_buffer.getvalue()

                # Converta os dados binários para base64 (representação de texto)
                foto_texto = base64.b64encode(img_binario).decode('utf-8')

                # Conecte-se ao banco de dados
                try:
                    connection = configbanco(db_type='mysql-connector')

                    if connection.is_connected():
                        cursor = connection.cursor()

                        # Atualize a foto e o nome do arquivo do usuário com base no idlogado
                        cursor.execute(
                            f'UPDATE usuarios SET foto = "{foto_texto}", foto_nome = "{foto_nome}" WHERE id_usuario = "{idlogado}"'
                        )

                        # Commit para salvar as alterações no banco de dados
                        connection.commit()

                        # Redirecione para a rota /InformacaoConta após salvar a foto
                        return redirect(url_for("InformacaoConta"))
                    else:
                        flash("Erro de conexão com o banco de dados.", "error")
                except Error as e:
                    flash(f"Erro no banco de dados: {str(e)}", "error")
                finally:
                    # Feche a conexão
                    if connection.is_connected():
                        cursor.close()
                        connection.close()
            except Exception as e:
                flash(f"Erro ao processar a imagem: {str(e)}", "error")

    # Redirecione para a rota /InformacaoConta sem mensagem de erro
    return redirect(url_for("InformacaoConta"))

@app.route("/destaques")
def destaques():
    return render_template("html/destaques.html")

@app.route("/cadastrar")
def cadastrar():
    return render_template("html/cadastro.html")

@app.route("/esqueceusenha")
def esqueceusenha():
    return render_template("html/esqueceusenha.html")

@app.route("/alterarsenha")
def alterarsenha():
    return render_template("html/alterarsenha.html")

def email_existe(email):
    conexao = configbanco(db_type='pymysql')
    cursor = conexao.cursor()

    cursor.execute(f"SELECT * FROM usuarios WHERE email = '{email}'")
    usuario = cursor.fetchone()

    conexao.close()
    return usuario is not None
@app.route('/esqueci_minha_senha', methods=['GET', 'POST'])
def esqueci_minha_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        email = request.form.get('email')

        if email_existe(email):
            # Verifique se o email existe na sua base de dados
            # Se existir, gere um token exclusivo ou um link de recuperação único
            # Aqui está um exemplo simples usando a biblioteca secrets para gerar um token
            token = secrets.token_urlsafe(16)  # Gera um token de 128 bits

            # Aqui, você precisará inserir o token na tabela de usuários
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()

            # Execute o comando SQL para atualizar o token na tabela de usuários
            cursor.execute(f"UPDATE usuarios SET token_senha = '{token}' WHERE email = '{email}'")
            conexao.commit()
            conexao.close()
            # Agora, você enviaria este token por e-mail para o usuário
            # Usando Flask-Mail (é necessário configurar corretamente o Flask-Mail antes)

            # Envie o e-mail para o usuário com o link de recuperação ou o token
            # Este é apenas um exemplo, personalize com seu próprio template de e-mail
            msg = Message('Recuperação de Senha', sender='gabrieljans18@gmail.com', recipients=[email])
            msg.body = f"Use este token para recuperar sua senha: {token}"
            mail.send(msg)

            # Aqui você redirecionaria para uma página informando que o e-mail foi enviado
            return render_template("html/alterarsenha.html")
    flash('E-mail não encontrado!')
    return render_template("html/esqueceusenha.html")

@app.route('/atualizar_senha', methods=['GET', 'POST'])
def atualizar_senha():
    if request.method == 'POST':
        nova_senha = request.form.get('senha')
        confirma_senha = request.form.get('confirmaSenhacad')
        token = request.form.get('token')
        email = request.form.get('email')

        # Verifica se a nova senha e a confirmação são iguais
        if nova_senha != confirma_senha:
            flash('A senha digitada diverge da senha de confirmação!')
            return render_template("html/atualizar_senha.html", token=token)

        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()

        # Verificar se o e-mail existe na tabela usuarios
        cursor.execute(f"SELECT * FROM usuarios WHERE email = '{email}' and  token_senha = '{token}'")
        resultado = cursor.fetchone()  # Retorna None se o e-mail não existir na tabela

        if resultado:
            # Se o e-mail existe, atualize o token
            cursor.execute(f"UPDATE usuarios SET senha = '{nova_senha}' WHERE token_senha = '{token}'")
            conexao.commit()
            conexao.close()
            flash('Senha atualizada com sucesso!')
            return render_template("html/login.html")  # Redirecionar para a página de login após atualizar a senha
        else:
            # Se o e-mail não existe, você pode decidir o que fazer, como exibir uma mensagem de erro ou tomar outra ação
            flash('E-mail ou token está incorreto!')
            return render_template("html/alterarsenha.html")
        conexao.close()

@app.route('/decode-token/<token>', methods=['POST'])
def decode_token(token):
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return jsonify(decoded_token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expirado"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token inválido"}), 400


@app.route("/cadastro", methods=['POST'])
def cadastro():
    global idlogado
    idlogado = 0
    user = []
    nomecad = request.form.get('nomecad')
    sobrenomecad = request.form.get('sobrenomecad')
    emailcad = request.form.get('emailcad')
    senhacad = request.form.get('senhacad')
    confirmaSenhacad = request.form.get('confirmaSenhacad')
    subId = request.form.get('subId')

    if subId is not None:
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        # Verificar se o e-mail já está cadastrado
        cursor.execute(f"SELECT * FROM usuarios WHERE email = '{emailcad}' and subId = '{subId}'")
        existing_user = cursor.fetchone()
        if existing_user:
            return redirect(url_for('login', email=emailcad, subId=subId))
        else:
            # conexao = pymysql.connect(db='quickevent', user='root', passwd='1234')
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()
            cursor.execute(
                f"insert into usuarios values (default, '{nomecad}', '{sobrenomecad}', '{emailcad}', default, default,'{subId}');")
            conexao.commit()
            conexao.close()
            return render_template('/logininicio', nomecadastro=nomecad + " cadastrado!")
    else:
        if senhacad != confirmaSenhacad:
            flash('A senha digitada diverge da senha de confirmação! ')
            return render_template("html/cadastro.html")

        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        # Verificar se o e-mail já está cadastrado
        cursor.execute(f"SELECT * FROM usuarios WHERE email = '{emailcad}'")
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Este e-mail já está cadastrado!')
            return render_template("html/cadastro.html")
        else:
            connect_BD = configbanco(db_type='pymysql')

            cursor = connect_BD.cursor()
            cursor.execute("INSERT INTO usuarios VALUES (default, %s, %s, %s, %s, default, default);",
                            (nomecad, sobrenomecad, emailcad, senhacad))
            connect_BD.commit()
            connect_BD.close()
            return redirect(url_for('login', email=emailcad, senha=senhacad))

@app.route("/login", methods=['GET', 'POST'])
def login():
    global idlogado
    if request.method == 'POST':
        idlogado = 0
        email = request.form.get('email')
        senha = request.form.get('senha')
        subId = request.form.get('subId')

        if subId is not None:
            # connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')

            connect_BD = configbanco(db_type='mysql-connector')

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
                usuariosSenha = str(usuarios[6])

                if usuariosEmail == email and usuariosSenha == subId:
                    print(idlogado)
                    return redirect("/destaques")

                if cont >= len(usuariosBD):
                    #flash('Usuário inválido!')
                    return redirect("/")
            else:
                return redirect("/")
        else:
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
                    return redirect("/destaques")

                if cont >= len(usuariosBD):
                    flash('Usuário inválido!')
                    return redirect("/logininicio")
            else:
                return redirect("/")
    elif request.method == 'GET':
        idlogado = 0
        email = request.args.get('email')
        senha = request.args.get('senha')
        subId = request.args.get('subId')

        if subId is not None:
            # connect_BD = mysql.connector.connect(host='localhost', database='quickevent', user='root', password='1234')

            connect_BD = configbanco(db_type='mysql-connector')

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
                usuariosSenha = str(usuarios[6])

                if usuariosEmail == email and usuariosSenha == subId:
                    print(idlogado)
                    return redirect("/destaques")

                if cont >= len(usuariosBD):
                    flash('Usuário inválido!')
                    return redirect("/")
            else:
                return redirect("/")
        else:
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
                    return redirect("/destaques")

                if cont >= len(usuariosBD):
                    flash('Usuário inválido!')
                    return redirect("/logininicio")
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
        f"insert into eventos values (default, '{descricaocad}', '{nomeEventocad}', '{categoriacad}','{dataCad}' , '{horCad}', {idlogado}, '{localEventocad}', {totalParticipantescad});")
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

