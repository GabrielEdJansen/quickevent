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
from datetime import datetime, timedelta
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

from datetime import datetime

from flask import request

@app.route("/cancelarPresenca", methods=['POST'])
def cancelarPresenca():
    global idlogado

    eventoPresenca = request.form.get('eventoPresenca')
    tipo_ingresso = request.form.get("tipoIngresso")

    if not eventoPresenca:
        eventoPresenca = data.get('eventoPresenca')

    if not tipo_ingresso:
        tipo_ingresso = data.get('tipoIngresso')

    print(eventoPresenca)
    print(tipo_ingresso)
    print("teste")

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT e.id_eventos, "
        f"e.hora_fim_evento, "
        f"e.hora_evento, "
        f"e.data_fim_evento, "
        f"e.data_evento, "
        f"c.id_categoria, "
        f"e.categoria, "
        f"e.descricao_evento, "
        f"e.local_evento, "
        f"c.descricao_categoria, "
        f"e.nome_evento, "
        f"e.foto_evento "
        f"FROM eventos e, categoria c "
        f"WHERE e.categoria = c.id_categoria AND e.id_eventos = '{eventoPresenca}';"
    )


    cursur.execute(query)
    eventos = cursur.fetchall()

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT i.titulo_ingresso, "
        f"i.id_ingresso "
        f"FROM eventos e, ingressos i "
        f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = '{eventoPresenca}';"
    )


    cursur.execute(query)
    ingresso = cursur.fetchall()

    if connect_BD.is_connected():
        cursor = connect_BD.cursor()

        # Consulta para obter a foto do usuário logado
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursor.fetchone()

        # Verifica se o usuário tem uma foto
        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
    f"SELECT "
    f"i.id_ingresso, "
    f"p.id_usuario_presente, "
    f"p.id_evento_presente "
    f"FROM "
    f"presencas p, ingressos i "
    f"WHERE "
    f"p.id_evento_presente = i.id_eventos and "
    f"p.id_ingresso = i.id_ingresso and "
    f"p.id_evento_presente = '{eventoPresenca}' and "
    f"p.id_usuario_presente = '{idlogado}' and "
    f"p.id_ingresso = '{tipo_ingresso}';"
    )
    cursur.execute(query)
    presenca = cursur.fetchall()

    if not presenca:
        flash("Presença já cancelada!")
    else:
        # Execute a instrução SQL de inserção
        query = "DELETE FROM presencas WHERE id_evento_presente = %s AND id_usuario_presente = %s AND id_ingresso = %s"

        values = (eventoPresenca, idlogado, tipo_ingresso)

        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        cursur.execute(query, values)
        connect_BD.commit()
        flash("Presença cancelada!")

    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)


@app.route("/confirmaPresenca", methods=['POST'])
def confirmaPresenca():
    global idlogado

    eventoPresenca = request.form.get('eventoPresenca')
    tipo_ingresso = request.form.get("tipoIngresso")

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT e.id_eventos, "
        f"e.hora_fim_evento, "
        f"e.hora_evento, "
        f"e.data_fim_evento, "
        f"e.data_evento, "
        f"c.id_categoria, "
        f"e.categoria, "
        f"e.descricao_evento, "
        f"e.local_evento, "
        f"c.descricao_categoria, "
        f"e.nome_evento, "
        f"e.foto_evento "
        f"FROM eventos e, categoria c "
        f"WHERE e.categoria = c.id_categoria AND e.id_eventos = '{eventoPresenca}';"
    )


    cursur.execute(query)
    eventos = cursur.fetchall()

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT i.titulo_ingresso, "
        f"i.id_ingresso "
        f"FROM eventos e, ingressos i "
        f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = '{eventoPresenca}';"
    )


    cursur.execute(query)
    ingresso = cursur.fetchall()

    if connect_BD.is_connected():
        cursor = connect_BD.cursor()

        # Consulta para obter a foto do usuário logado
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursor.fetchone()

        # Verifica se o usuário tem uma foto
        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
    f"SELECT "
    f"i.id_ingresso, "
    f"p.id_usuario_presente, "
    f"p.id_evento_presente "
    f"FROM "
    f"presencas p, ingressos i "
    f"WHERE "
    f"p.id_evento_presente = i.id_eventos and "
    f"p.id_ingresso = i.id_ingresso and "
    f"p.id_evento_presente = '{eventoPresenca}' and "
    f"p.id_usuario_presente = '{idlogado}' and "
    f"p.id_ingresso = '{tipo_ingresso}';"
    )
    cursur.execute(query)
    presenca = cursur.fetchall()

    if not presenca:
        # Execute a instrução SQL de inserção
        query = "INSERT INTO presencas (id_evento_presente, id_usuario_presente, id_ingresso) VALUES (%s, %s, %s)"
        values = (eventoPresenca, idlogado, tipo_ingresso)

        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        cursur.execute(query, values)
        connect_BD.commit()
        flash("Presença confirmada!")
    else:
        flash("Presença já confirmada!")

    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)

@app.route("/InformacoesEventos", methods=['POST'])
def InformacoesEventos():
    global idlogado
    #eventoPresenca = request.form.get('eventoPresenca')

    eventoPresenca = request.form.get('botaoDetalhes')

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT e.id_eventos, "
        f"e.hora_fim_evento, "
        f"e.hora_evento, "
        f"e.data_fim_evento, "
        f"e.data_evento, "
        f"c.id_categoria, "
        f"e.categoria, "
        f"e.descricao_evento, "
        f"e.local_evento, "
        f"c.descricao_categoria, "
        f"e.nome_evento, "
        f"e.foto_evento "
        f"FROM eventos e, categoria c "
        f"WHERE e.categoria = c.id_categoria AND e.id_eventos = '{eventoPresenca}';"
    )


    cursur.execute(query)
    eventos = cursur.fetchall()

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT i.titulo_ingresso, "
        f"i.id_ingresso "
        f"FROM eventos e, ingressos i "
        f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = '{eventoPresenca}';"
    )


    cursur.execute(query)
    ingresso = cursur.fetchall()

    # Conexão com o banco de dados
    connect_BD = configbanco(db_type='mysql-connector')

    if connect_BD.is_connected():
        cursor = connect_BD.cursor()

        # Consulta para obter a foto do usuário logado
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursor.fetchone()

        # Verifica se o usuário tem uma foto
        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso = ingresso)


@app.route("/SalvarAlteracoes", methods=['POST'])
def SalvarAlteracoes():
    global idlogado

    foto = request.files["img_divulga"]
    eventoPresenca = request.form.get('eventoPresenca')

    # Verifique se um arquivo de imagem foi enviado
    if foto and allowed_file(foto.filename):
        # Abra a imagem usando PIL
        img = Image.open(foto)

        # Verifique as dimensões da imagem redimensionada
        # if img.size[0] > 200 or img.size[1] > 200:
        #    flash("A foto deve ter dimensões no máximo 200x200 pixels.", "error")
        #    return redirect(url_for("InformacaoConta"))

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

    nomeEventocad = request.form.get('nomeEventocad')
    descricaocad = request.form.get('descricaocad')
    categoriacad = request.form.get('categoriacad')
    classificacaocad = request.form.get('classificacaocad')
    totalParticipantescad = request.form.get('totalParticipantescad')

    endereco = request.form.get('endereco')
    rua = request.form.get('rua')
    cidade = request.form.get('cidade')
    numero = request.form.get('numero')
    estado = request.form.get('estado')
    bairro = request.form.get('bairro')
    complemento = request.form.get('complemento')

    dataCad = request.form.get('dataCad')
    dataCadFin = request.form.get('dataCadFin')

    horCad = request.form.get('horCad')

    horCadFin = request.form.get('horCadFin')
    data_atual = datetime.now().date()
    hora_atual = datetime.now().time()
    dataCad = datetime.strptime(dataCad, "%Y-%m-%d").date() #+ timedelta(days=1)

    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    dataCadFin = datetime.strptime(dataCadFin, "%Y-%m-%d").date() #+ timedelta(days=1)
    #horCadFin = datetime.strptime(horCadFin, "%H:%M").time()

    nome_produtor = request.form.get('nome_produtor')
    descricao_produtor = request.form.get('descricao_produtor')

    try:
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()

        sql = """UPDATE eventos SET
                    descricao_evento = %s,
                    nome_evento = %s,
                    categoria = %s,
                    data_evento = %s,
                    hora_evento = %s,
                    id_usuario_evento = %s,
                    local_evento = %s,
                    total_participantes = %s,
                    classificacao_indicativa = %s,
                    rua = %s,
                    cidade = %s,
                    numero = %s,
                    data_fim_evento = %s,
                    hora_fim_evento = %s,
                    nome_produtor = %s,
                    descricao_produtor = %s,
                    estado = %s,
                    bairro = %s,
                    complemento = %s,
                    latitude = %s,
                    longitude = %s
                WHERE id_eventos = %s"""

        cursor.execute(sql, (descricaocad, nomeEventocad, categoriacad, dataCad, horCad, idlogado, endereco, totalParticipantescad,
        classificacaocad, rua, cidade, numero, dataCadFin, horCadFin, nome_produtor, descricao_produtor, estado, bairro, complemento, latitude, longitude, eventoPresenca))

        if foto and allowed_file(foto.filename):
            cursor = conexao.cursor()

            sql = """UPDATE eventos SET
                        foto_evento = %s,
                        foto_evento_nome = %s
                    WHERE id_eventos = %s"""

            cursor.execute(sql, (foto_texto, foto_nome, eventoPresenca))

        # Recuperar o ID do evento recém-inserido
        sql_last_insert_id = "SELECT LAST_INSERT_ID()"
        cursor.execute(sql_last_insert_id)
        id_eventos = cursor.fetchone()[0]

        sql_delete = "DELETE FROM campo_adicional WHERE id_eventos = %s"
        cursor.execute(sql_delete, (eventoPresenca))
        conexao.commit()

        # Inserir os dados dos campos adicionais
        campos_adicionais = request.form.getlist('nome_campo[]')
        for campo in campos_adicionais:
            sql_campos_adicionais = """INSERT INTO campo_adicional (id_eventos, nome_campo) VALUES (%s, %s)"""
            cursor.execute(sql_campos_adicionais, (eventoPresenca, campo))


        titulos = request.form.getlist('titulo_ingresso[]')
        quantidades = request.form.getlist('quantidade_ingresso[]')
        precos = request.form.getlist('preco_ingresso[]')
        datas_inicio_vendas = request.form.getlist('data_inicio_vendas[]')
        datas_fim_vendas = request.form.getlist('data_fim_vendas[]')
        horas_inicio_vendas = request.form.getlist('hora_inicio_vendas[]')
        horas_fim_vendas = request.form.getlist('hora_fim_vendas[]')
        disponibilidades = request.form.getlist('disponibilidade_ingresso[]')
        quantidades_maximas = request.form.getlist('quantidade_maxima_compra[]')
        observacoes = request.form.getlist('observacao_ingresso[]')

        datas_inicio_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in datas_inicio_vendas]
        #horas_inicio_vendas = [datetime.strptime(hora, "%H:%M").time() for hora in horas_inicio_vendas]

        datas_fim_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in datas_fim_vendas]
        #horas_fim_vendas = [datetime.strptime(hora, "%H:%M").time() for hora in horas_fim_vendas]

        sql_delete = "DELETE FROM ingressos WHERE id_eventos = %s"
        cursor.execute(sql_delete, (eventoPresenca))
        conexao.commit()

        print(titulos)

        for i in range(len(titulos)):
            # Insira os dados do ingresso no banco de dados
            sql = """INSERT INTO ingressos (id_eventos, titulo_ingresso, quantidade, preco, data_ini_venda, 
                     data_fim_venda, hora_ini_venda, hora_fim_venda, disponibilidade, quantidade_maxima, observacao_ingresso) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (eventoPresenca, titulos[i], quantidades[i], precos[i], datas_inicio_vendas[i],
                                 datas_fim_vendas[i], horas_inicio_vendas[i], horas_fim_vendas[i],
                                 disponibilidades[i], quantidades_maximas[i], observacoes[i]))

        conexao.commit()

        flash("Evento alterado com sucesso!")
        return redirect("/InicioGerenciarEventos")
    except Exception as e:
        flash(f"Erro ao criar evento: {str(e)}")
        return render_template("html/EditarEvento.html")
    finally:
        if 'conexao' in locals():
            conexao.close()

@app.route("/buscar")
def buscar():
    global idlogado
    filtro = request.args.get("filtro")
    data_inicial = request.args.get("dataInicial")
    data_final = request.args.get("dataFinal")
    categoria = request.args.get("categoria")


    # Suponho que idlogado já esteja definido em algum lugar do seu código

    # Conexão com o banco de dados
    connect_BD = configbanco(db_type='mysql-connector')

    if connect_BD.is_connected():
        cursor = connect_BD.cursor()

        # Consulta para obter a foto do usuário logado
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursor.fetchone()

        # Verifica se o usuário tem uma foto
        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

        # Consulta SQL para buscar os eventos
        query = '''
            SELECT
                e.id_eventos,
                e.descricao_evento,
                e.nome_evento,
                e.data_evento,
                e.hora_evento,
                e.local_evento,
                e.latitude,
                e.longitude,
                e.foto_evento
            FROM
                eventos AS e WHERE 1 = 1
        '''
        if filtro:
            query += f' AND (e.nome_evento LIKE "%{filtro}%" OR e.local_evento LIKE "%{filtro}%")'

        if data_inicial:
            query += f' AND e.data_evento >= "{data_inicial}"'

        if data_final:
            query += f' AND e.data_evento <= "{data_final}"'

        if categoria:
            query += f' AND e.categoria = "{categoria}"'

        filtro_aplicado = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "categoria": categoria
        }

        # Executa a consulta
        cursor.execute(query)
        eventos = cursor.fetchall()
        print(eventos)

        # Se não houver eventos encontrados, renderizar a página buscarnd.html
        if not eventos:
            return render_template("html/buscarnd.html", foto=foto, filtro=filtro_aplicado)

        return render_template("html/listabusca.html", eventos=eventos, foto=foto, filtro=filtro_aplicado)

@app.route("/InformacaoConta")
def InformacaoConta():
    global idlogado
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT nome, sobrenome, foto_nome, foto, nascimento, endereco, rua, cidade, numero FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            # Verifique se as informações não estão vazias antes de renderizar o template
            nome = usuario[0] if usuario[0] else "Nome não disponível"
            sobrenome = usuario[1] if usuario[1] else "Sobrenome não disponível"
            foto_nome = usuario[2] if usuario[2] else "Sem foto disponível"
            foto = usuario[3] if usuario[3] else "Sem foto disponível"

            # Formatando a data de nascimento, se disponível
            nascimento = usuario[4] if usuario[4] else "0000-00-00"

            endereco = usuario[5] if usuario[5] else "Digite um endereço"
            rua = usuario[6] if usuario[6] else "Rua será preenchida automaticamente"
            cidade = usuario[7] if usuario[7] else "Cidade será preenchida automaticamente"
            numero = usuario[8] if usuario[8] else "Número da residência será preenchido automaticamente"

    return render_template("html/InformacaoConta.html", nome=nome, sobrenome=sobrenome, foto_nome=foto_nome, foto=foto, nascimento=nascimento, endereco=endereco, rua=rua, cidade=cidade, numero=numero)

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
        nascimento = request.form.get("nascimento")
        endereco = request.form.get("endereco")
        numero = request.form.get("numero")
        cidade = request.form.get("cidade")
        rua = request.form.get("rua")
        nascimento = datetime.strptime(nascimento, "%Y-%m-%d")

        connection = configbanco(db_type='mysql-connector')

        if connection.is_connected():
            cursor = connection.cursor()

            # Atualize a foto e o nome do arquivo do usuário com base no idlogado
            cursor.execute(
                f'UPDATE usuarios SET cidade = "{cidade}",rua = "{rua}", nascimento = "{nascimento}", endereco = "{endereco}", numero = "{numero}" WHERE id_usuario = "{idlogado}"'
            )

            # Commit para salvar as alterações no banco de dados
            connection.commit()

        # Verifique se um arquivo de imagem foi enviado
        if foto and allowed_file(foto.filename):
            try:
                # Abra a imagem usando PIL
                img = Image.open(foto)

                # Verifique as dimensões da imagem redimensionada
                #if img.size[0] > 200 or img.size[1] > 200:
                #    flash("A foto deve ter dimensões no máximo 200x200 pixels.", "error")
                #    return redirect(url_for("InformacaoConta"))

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
                #conteudo_arquivo = foto.read()
                #foto_texto = base64.b64encode(conteudo_arquivo).decode('utf-8')

                # Conecte-se ao banco de dados
                try:
                    connection = configbanco(db_type='mysql-connector')

                    if connection.is_connected():
                        cursor = connection.cursor()

                        # Atualize a foto e o nome do arquivo do usuário com base no idlogado
                        cursor.execute(
                            f'UPDATE usuarios SET cidade = "{cidade}",rua = "{rua}",foto = "{foto_texto}", foto_nome = "{foto_nome}", nascimento = "{nascimento}", endereco = "{endereco}", numero = "{numero}" WHERE id_usuario = "{idlogado}"'
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
    global idlogado
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    return render_template("html/destaques.html", foto=foto)

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
                f"insert into usuarios values (default, '{nomecad}', '{sobrenomecad}', '{emailcad}', default, default,'{subId}','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',default,default,default,default,default,default);")
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
            cursor.execute("INSERT INTO usuarios VALUES (default, %s, %s, %s, %s, default, default, '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',default,default,default,default,default,default);",
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
    global idlogado
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    return render_template("html/CriarEvento.html", foto=foto)


@app.route("/CriarEvento", methods=['POST'])
def CriarEvento():
    global idlogado

    foto = request.files["img_divulga"]

    # Verifique se um arquivo de imagem foi enviado
    if foto and allowed_file(foto.filename):
        # Abra a imagem usando PIL
        img = Image.open(foto)

        # Verifique as dimensões da imagem redimensionada
        # if img.size[0] > 200 or img.size[1] > 200:
        #    flash("A foto deve ter dimensões no máximo 200x200 pixels.", "error")
        #    return redirect(url_for("InformacaoConta"))

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

    nomeEventocad = request.form.get('nomeEventocad')
    descricaocad = request.form.get('descricaocad')
    categoriacad = request.form.get('categoriacad')
    classificacaocad = request.form.get('classificacaocad')
    totalParticipantescad = request.form.get('totalParticipantescad')

    endereco = request.form.get('endereco')
    rua = request.form.get('rua')
    cidade = request.form.get('cidade')
    numero = request.form.get('numero')
    estado = request.form.get('estado')
    bairro = request.form.get('bairro')
    complemento = request.form.get('complemento')

    dataCad = request.form.get('dataCad')
    dataCadFin = request.form.get('dataCadFin')
    horCad = request.form.get('horCad')
    horCadFin = request.form.get('horCadFin')
    data_atual = datetime.now().date()
    hora_atual = datetime.now().time()
    dataCad = datetime.strptime(dataCad, "%Y-%m-%d").date() #+ timedelta(days=1)
    horCad = datetime.strptime(horCad, "%H:%M").time()

    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    if dataCad < data_atual or (dataCad == data_atual and horCad < hora_atual):
        flash("A data fornecida é menor que a data atual.")
        return render_template("html/CriarEvento.html")

    dataCadFin = datetime.strptime(dataCadFin, "%Y-%m-%d").date() #+ timedelta(days=1)
    horCadFin = datetime.strptime(horCadFin, "%H:%M").time()

    nome_produtor = request.form.get('nome_produtor')
    descricao_produtor = request.form.get('descricao_produtor')

    try:
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()

        sql = """INSERT INTO eventos (
                    descricao_evento,
                    nome_evento,
                    categoria,
                    data_evento,
                    hora_evento,
                    id_usuario_evento,
                    local_evento,
                    total_participantes,
                    classificacao_indicativa,
                    rua,
                    cidade,
                    numero,
                    data_fim_evento,
                    hora_fim_evento,
                    nome_produtor,
                    descricao_produtor,
                    estado,
                    bairro,
                    complemento,
                    foto_evento,
                    foto_evento_nome,
                    latitude,
                    longitude
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )"""

        cursor.execute(sql, (
        descricaocad, nomeEventocad, categoriacad, dataCad, horCad, idlogado, endereco, totalParticipantescad,
        classificacaocad, rua, cidade, numero, dataCadFin, horCadFin, nome_produtor, descricao_produtor, estado, bairro, complemento, foto_texto, foto_nome, latitude, longitude))

        # Recuperar o ID do evento recém-inserido
        sql_last_insert_id = "SELECT LAST_INSERT_ID()"
        cursor.execute(sql_last_insert_id)
        id_eventos = cursor.fetchone()[0]

        # Inserir os dados dos campos adicionais
        campos_adicionais = request.form.getlist('nome_campo[]')
        for campo in campos_adicionais:
            sql_campos_adicionais = """INSERT INTO campo_adicional (id_eventos, nome_campo) VALUES (%s, %s)"""
            cursor.execute(sql_campos_adicionais, (id_eventos, campo))

        titulos = request.form.getlist('titulo_ingresso[]')
        quantidades = request.form.getlist('quantidade_ingresso[]')
        precos = request.form.getlist('preco_ingresso[]')
        datas_inicio_vendas = request.form.getlist('data_inicio_vendas[]')
        datas_fim_vendas = request.form.getlist('data_fim_vendas[]')
        horas_inicio_vendas = request.form.getlist('hora_inicio_vendas[]')
        horas_fim_vendas = request.form.getlist('hora_fim_vendas[]')
        disponibilidades = request.form.getlist('disponibilidade_ingresso[]')
        quantidades_maximas = request.form.getlist('quantidade_maxima_compra[]')
        observacoes = request.form.getlist('observacao_ingresso[]')

        datas_inicio_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in datas_inicio_vendas]
        horas_inicio_vendas = [datetime.strptime(hora, "%H:%M").time() for hora in horas_inicio_vendas]

        datas_fim_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in datas_fim_vendas]
        horas_fim_vendas = [datetime.strptime(hora, "%H:%M").time() for hora in horas_fim_vendas]

        for i in range(len(titulos)):
            # Insira os dados do ingresso no banco de dados
            sql = """INSERT INTO ingressos (id_eventos, titulo_ingresso, quantidade, preco, data_ini_venda, 
                     data_fim_venda, hora_ini_venda, hora_fim_venda, disponibilidade, quantidade_maxima, observacao_ingresso) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (id_eventos, titulos[i], quantidades[i], precos[i], datas_inicio_vendas[i],
                                 datas_fim_vendas[i], horas_inicio_vendas[i], horas_fim_vendas[i],
                                 disponibilidades[i], quantidades_maximas[i], observacoes[i]))

        conexao.commit()
        flash("Evento criado com sucesso!")
        return redirect("/buscar")
    except Exception as e:
        flash(f"Erro ao criar evento: {str(e)}")
        return render_template("html/CriarEvento.html")
    finally:
        if 'conexao' in locals():
            conexao.close()


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


# Outras importações e definições de rotas...

@app.route("/InicioGerenciarEventos")
def InicioGerenciarEventos():
    global idlogado

    # Obtém os parâmetros de filtro do request
    data_inicial = request.args.get("dataInicial")
    data_final = request.args.get("dataFinal")
    nome_evento = request.args.get("nomeEvento")

    if nome_evento is None:
        nome_evento = ''

    # Consulta SQL para buscar os eventos
    query = f'''
        SELECT
            e.id_eventos,
            e.descricao_evento,
            e.nome_evento,
            e.data_evento,
            e.hora_evento,
            e.local_evento,
            e.latitude,
            e.longitude,
            e.foto_evento,
            COUNT(p.id_evento_presente) AS total_participantes,
            c.descricao_categoria,
            u.nome AS nome_usuario
        FROM
            eventos AS e
        INNER JOIN
            categoria AS c ON c.id_categoria = e.categoria
        INNER JOIN
            usuarios AS u ON u.id_usuario = e.id_usuario_evento
        LEFT JOIN
            presencas AS p ON p.id_evento_presente = e.id_eventos
        WHERE
            e.id_usuario_evento = "{idlogado}"
    '''

    if nome_evento:
        query += f' AND e.nome_evento LIKE "%{nome_evento}%"'

    if data_inicial:
        query += f' AND e.data_evento >= "{data_inicial}"'

    if data_final:
        query += f' AND e.data_evento <= "{data_final}"'

    query += '''
        GROUP BY
            e.id_eventos,
            e.descricao_evento,
            e.nome_evento,
            e.data_evento,
            e.hora_evento,
            e.local_evento,
            e.latitude,
            e.longitude,
            e.foto_evento,
            c.descricao_categoria,
            u.nome
    '''

    # Executa a consulta
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(query)
        eventos = cursur.fetchall()

    filtro_aplicado = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "nomeEvento": nome_evento
    }
    if not eventos:
        flash('Nenhum evento encontrado.', 'warning')

    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    return render_template("html/GerenciarEventos.html", eventos=eventos, filtro=filtro_aplicado, foto=foto)


@app.route("/GerenciarEventos", methods=['POST'])
def EditarEvento():
    global idlogado
    #eventoPresenca = request.form.get('eventoPresenca')

    eventoPresenca = request.form.get('botaoEditar')
    print(eventoPresenca)
    eventosList = []
    if eventoPresenca:
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
        eventosList.append(linha[11])
        eventosList.append(linha[12])
        eventosList.append(linha[13])
        eventosList.append(linha[14])
        eventosList.append(linha[15])
        eventosList.append(linha[16])
        eventosList.append(linha[17])
        eventosList.append(linha[18])
        eventosList.append(linha[19])
        eventosList.append(linha[20])
        eventosList.append(linha[21])
        eventosList.append(linha[22])
        eventosList.append(linha[23])
        eventosList.append(linha[24])

        connect_BD = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cursur = connect_BD.cursor()
            cursur.execute(
                f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
            )
            usuario = cursur.fetchone()

            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"


        connect_BD  = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        query = (
            f"SELECT i.titulo_ingresso, "
            f"i.quantidade, "
            f"i.preco, "
            f"i.data_ini_venda, "
            f"i.data_fim_venda, "
            f"i.hora_ini_venda, "
            f"i.hora_fim_venda, "
            f"i.disponibilidade, "
            f"i.quantidade_maxima, "
            f"i.observacao_ingresso "
            f"FROM eventos e, ingressos i "
            f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = '{eventoPresenca}';"
        )

        # Executar a consulta SQL
        cursur.execute(query)
        ingresso = cursur.fetchall()

        connect_BD  = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        query = (f"SELECT c.nome_campo FROM eventos e, campo_adicional c where e.id_eventos = c.id_eventos and e.id_eventos = '{eventoPresenca}';")

        # Executar a consulta SQL
        cursur.execute(query)
        campo_adicional = cursur.fetchall()

        return render_template("html/EditarEvento.html", eventos=eventosList, foto=foto, ingresso=ingresso, campo_adicional=campo_adicional)
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

        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        cursor.execute(
            f"DELETE FROM campo_adicional WHERE id_eventos = '{eventoPresenca}';")
        conexao.commit()
        conexao.close()

        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        cursor.execute(
            f"DELETE FROM ingressos WHERE id_eventos =  '{eventoPresenca}';")
        conexao.commit()
        conexao.close()

        #conexao = pymysql.connect(db='usuarios', user='root', passwd='1234')
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()
        cursor.execute(
            f"DELETE FROM eventos WHERE ID_EVENTOS = '{eventoPresenca}' and ID_USUARIO_EVENTO = '{idlogado}';")
        conexao.commit()
        conexao.close()

        flash("Evento excluído com sucesso!")
        return redirect("/InicioGerenciarEventos")
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

