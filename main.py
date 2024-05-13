from flask import Flask, session, render_template, request, flash, redirect, jsonify, url_for, get_flashed_messages, flash, session
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
import pytz

app = Flask(__name__)
app.jinja_env.globals.update(datetime=datetime)
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


@app.route('/inserir_avaliacao', methods=['POST'])
def inserir_avaliacao():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    id_usuario = str(session['idlogado'])

    id_evento = request.form['eventoPresenca']
    eventoPresenca = request.form['eventoPresenca']
    nota_avaliacao = request.form['nota']
    comentario = request.form.get('comentario')
    comentario = comentario.strip() if comentario else ' '

    # Verificar se os campos estão presentes no formulário
    if 'eventoPresenca' not in request.form or 'nota' not in request.form or 'comentario' not in request.form:
        flash("Campos incompletos.", "warning")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    if comentario is None or comentario.strip() == '':
        flash("Insira o comentário!", "error")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()
    # Verificar se a avaliação já existe para o usuário logado e o evento
    cursor.execute("SELECT COUNT(*) FROM AvaliacaoEventos WHERE id_evento = %s AND id_usuario = %s",
                   (id_evento, id_usuario))
    avaliacao_existente = cursor.fetchone()[0]

    if avaliacao_existente > 0:
        flash("Você já avaliou este evento.", "warning")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    try:
        fnota_avaliacao = float(request.form['nota'])
        if fnota_avaliacao < 0 or fnota_avaliacao > 5:
            raise ValueError("A nota deve estar entre 0 e 5")
    except ValueError:
        flash("A nota deve ser um número válido", "error")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    if fnota_avaliacao <= 0:
        flash("A nota deve ser maior que 0", "error")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    if not fnota_avaliacao:
        flash("Insira a nota", "error")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    if comentario is None or comentario.strip() == '':
        flash("Insira o comentário!", "error")
        return redirect(url_for('processarPresenca', eventoPresenca=eventoPresenca, acao='complementar'))

    try:
        # Definindo o fuso horário do Brasil
        timezone = pytz.timezone('America/Sao_Paulo')

        # Obtendo a data e hora atual do Brasil
        current_datetime_brazil = datetime.now(timezone)

        # Formatando a data e hora conforme necessário para inserção no MySQL (formato 'YYYY-MM-DD HH:MM:SS')
        current_datetime_brazil_str = current_datetime_brazil.strftime('%Y-%m-%d %H:%M:%S')

        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor()

        # Inserindo os dados, incluindo a data atual do Brasil
        cursor.execute(
            "INSERT INTO AvaliacaoEventos (id_evento, nota_avaliacao, comentario, id_usuario, data_avaliacao) VALUES (%s, %s, %s, %s, %s)",
            (id_evento, nota_avaliacao, comentario, id_usuario, current_datetime_brazil_str))

        connect_BD.commit()
        cursor.close()
        connect_BD.close()

        eventosList = [eventoPresenca]

        connect_BD = configbanco(db_type='mysql-connector')

        if connect_BD.is_connected():
            cursor = connect_BD.cursor()

            # Consulta para obter a foto do usuário logado
            cursor.execute(
                f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
            )
            usuario = cursor.fetchone()

            # Verifica se o usuário tem uma foto
            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"

        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor(dictionary=True)
        query = ("SELECT a.nota_avaliacao, a.data_avaliacao, a.comentario, u.id_usuario, u.nome, u.sobrenome, u.foto FROM AvaliacaoEventos a, usuarios u WHERE a.id_evento = %s and u.id_usuario = a.id_usuario order by a.data_avaliacao")
        cursor.execute(query, (eventoPresenca,))
        avaliacoes = cursor.fetchall()
        cursor.close()
        connect_BD.close()

    except mysql.connector.Error as e:
        return f'Erro ao inserir avaliação: {e}', 500

    return render_template("html/Avaliacoes.html", avaliacoes=avaliacoes, eventos=eventosList, foto=foto)

@app.route('/delete_message', methods=['POST'])
def delete_message():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    # Obtenha os parâmetros de filtragem da solicitação POST
    message_id = request.form.get('message_id')
    user_id = request.form.get('id_usuario')
    event_id = request.form.get('eventoPresenca')
    message_date = request.form.get('data_envio')
    id_usuario = str(session['idlogado'])
    eventoPresenca = request.form.get('eventoPresenca')

    # Verifique se todos os parâmetros foram fornecidos
    if user_id is None or event_id is None or message_date is None:
        return jsonify({"error": "Parâmetros de filtragem incompletos"}), 400

    # Estabeleça a conexão com o banco de dados usando a função configbanco
    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()

    # Execute a consulta SQL para excluir a mensagem com base nos parâmetros fornecidos
    cursor.execute("DELETE FROM chat_organizadores WHERE id_usuario = %s AND id_evento = %s AND id_chat_organizadores = %s", (user_id, event_id, message_id))

     # Confirme as alterações no banco de dados
    connect_BD.commit()

    # Feche o cursor e a conexão com o banco de dados
    cursor.close()
    connect_BD.close()

    eventosList = [event_id]

    # Lógica para lidar com solicitações GET
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursor = connect_BD.cursor()
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{id_usuario}"'
        )
        usuario = cursor.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    # Conecte-se ao banco de dados
    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()

    # Execute a consulta SQL filtrando pelo ID do evento
    cursor.execute(
        "SELECT chat_organizadores.id_evento, chat_organizadores.id_usuario, chat_organizadores.mensagem, chat_organizadores.data_envio, usuarios.nome, usuarios.sobrenome, usuarios.foto, chat_organizadores.id_chat_organizadores  FROM chat_organizadores JOIN usuarios ON chat_organizadores.id_usuario = usuarios.id_usuario WHERE chat_organizadores.id_evento = %s",
        (eventoPresenca,))

    # Recupere todas as linhas do resultado da consulta
    chat_data = cursor.fetchall()

    # Feche o cursor e a conexão com o banco de dados
    cursor.close()
    connect_BD.close()

    # Converta os dados do chat para um formato adequado para JSON e retorne-os como resposta JSON
    chat_json = []

    for row in chat_data:
        chat_json.append({
            'id_evento': row[0],  # Supondo que o ID do evento é o primeiro campo na tupla
            'id_usuario': row[1],  # Supondo que o ID do usuário é o segundo campo na tupla
            'mensagem': row[2],  # Supondo que a mensagem é o terceiro campo na tupla
            'data_envio': row[3].strftime('%d/%m/%y - %H:%M') if row[3] else None,
            # Formate a data e hora como string, se existir
            'nome': row[4],  # Supondo que o nome do usuário é o quarto campo na tupla
            'sobrenome': row[5],  # Supondo que o sobrenome do usuário é o quinto campo na tupla
            'foto': row[6],  # Supondo que a foto do usuário em base64 é o sexto campo na tupla
            'id_chat_organizadores': row[7]
        })

    # Retorne os dados do chat como resposta JSON
    return render_template("html/ChatOrganizadores.html", foto=foto, eventos=eventosList, chat_data=chat_json)

# Função para inserir mensagem no banco de dados
def inserir_mensagem(id_evento, id_usuario, mensagem):
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Inserir a mensagem no banco de dados
        cursor.execute('INSERT INTO chat_organizadores (id_evento, id_usuario, mensagem) VALUES (?, ?, ?)',
                       (id_evento, id_usuario, mensagem))

        # Commit das alterações
        conn.commit()

        # Fechar a conexão
        conn.close()

        return True
    except Exception as e:
        print(f"Erro ao inserir mensagem no banco de dados: {e}")
        return False

@app.route('/enviar_mensagem', methods=['POST'])
def enviar_mensagem():
    if request.method == 'POST':
        # Obter os dados da mensagem do formulário
        if 'idlogado' not in session:
            return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

        id_evento = request.form.get('eventoPresenca')  # Corrigido para obter 'eventoPresenca' do formulário
        eventoPresenca = request.form.get('eventoPresenca')
        id_usuario = str(session['idlogado'])
        mensagem = request.form['mensagem']
        data_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Obtém a data e hora atual

        # Verifique se o ID do evento foi fornecido
        if not id_evento:
            return jsonify({'error': 'ID do evento não fornecido.'}), 400

        try:
            connect_BD = configbanco(db_type='mysql-connector')
            cursor = connect_BD.cursor()
            # Definindo o fuso horário do Brasil
            timezone = pytz.timezone('America/Sao_Paulo')

            # Obtendo a data e hora atual do Brasil
            current_datetime_brazil = datetime.now(timezone)

            # Formatando a data e hora conforme necessário para inserção no MySQL (formato 'YYYY-MM-DD HH:MM:SS')
            current_datetime_brazil_str = current_datetime_brazil.strftime('%Y-%m-%d %H:%M:%S')
            # Executar a inserção da mensagem (ajuste conforme a estrutura da tabela)
            cursor.execute(
                "INSERT INTO chat_organizadores (id_evento, id_usuario, mensagem, data_envio) VALUES (%s, %s, %s, %s)",
                (id_evento, id_usuario, mensagem, current_datetime_brazil_str))

            connect_BD.commit()
            cursor.close()
            connect_BD.close()

            # Lógica para lidar com solicitações GET
            connect_BD = configbanco(db_type='mysql-connector')
            if connect_BD.is_connected():
                cursor = connect_BD.cursor()
                cursor.execute(
                    f'SELECT foto FROM usuarios WHERE id_usuario = "{id_usuario}"'
                )
                usuario = cursor.fetchone()

                if usuario:
                    foto = usuario[0] if usuario[0] else "Sem foto disponível"

            eventosList = [id_evento]

            # Conecte-se ao banco de dados
            connect_BD = configbanco(db_type='mysql-connector')
            cursor = connect_BD.cursor()

            # Execute a consulta SQL filtrando pelo ID do evento
            cursor.execute(
                "SELECT chat_organizadores.id_evento, chat_organizadores.id_usuario, chat_organizadores.mensagem, chat_organizadores.data_envio, usuarios.nome, usuarios.sobrenome, usuarios.foto, chat_organizadores.id_chat_organizadores  FROM chat_organizadores JOIN usuarios ON chat_organizadores.id_usuario = usuarios.id_usuario WHERE chat_organizadores.id_evento = %s",
                (eventoPresenca,))

            # Recupere todas as linhas do resultado da consulta
            chat_data = cursor.fetchall()

            # Feche o cursor e a conexão com o banco de dados
            cursor.close()
            connect_BD.close()

            # Converta os dados do chat para um formato adequado para JSON e retorne-os como resposta JSON
            chat_json = []

            for row in chat_data:
                chat_json.append({
                    'id_evento': row[0],  # Supondo que o ID do evento é o primeiro campo na tupla
                    'id_usuario': row[1],  # Supondo que o ID do usuário é o segundo campo na tupla
                    'mensagem': row[2],  # Supondo que a mensagem é o terceiro campo na tupla
                    'data_envio': row[3].strftime('%d/%m/%y - %H:%M') if row[3] else None,
                    # Formate a data e hora como string, se existir
                    'nome': row[4],  # Supondo que o nome do usuário é o quarto campo na tupla
                    'sobrenome': row[5],  # Supondo que o sobrenome do usuário é o quinto campo na tupla
                    'foto': row[6],  # Supondo que a foto do usuário em base64 é o sexto campo na tupla
                    'id_chat_organizadores': row[7]
                })

            # Retorne os dados do chat como resposta JSON
            return render_template("html/ChatOrganizadores.html", foto=foto, eventos=eventosList, chat_data=chat_json)
        except Exception as e:
            # Imprimir mensagem de erro no console
            print('Erro ao inserir mensagem no banco de dados:', e)
            return jsonify({'status': 'error', 'message': 'Erro ao enviar mensagem.'})


@app.route('/buscar_participanteEvt', methods=['GET'])
def buscar_participanteEvt():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = str(session['idlogado'])
    termo_pesquisa = request.args.get('termo_pesquisa', '')
    eventoPresenca = request.args.get('eventoPresenca', None)
    eventosList = [eventoPresenca]

    # Consulta para buscar os participantes com base no termo de pesquisa
    query = '''
        SELECT 
            presencas.id_evento_presente,
            presencas.id_usuario_presente,
            presencas.id_ingresso,
            presencas.quantidade_convites,
            usuarios.nome,
            usuarios.sobrenome,
            ingressos.titulo_ingresso,
            presencas.quantidade_convites
        FROM 
            presencas
            JOIN usuarios ON presencas.id_usuario_presente = usuarios.id_usuario
            JOIN ingressos ON presencas.id_ingresso = ingressos.id_ingresso
        WHERE 
            presencas.id_evento_presente = %s
            AND (usuarios.nome LIKE %s OR usuarios.sobrenome LIKE %s)
    '''

    # Consulta para calcular o total de convites
    query_total_convites = '''
        SELECT 
            SUM(presencas.quantidade_convites) as qtdtotal
        FROM 
            presencas
            JOIN usuarios ON presencas.id_usuario_presente = usuarios.id_usuario
            JOIN ingressos ON presencas.id_ingresso = ingressos.id_ingresso
        WHERE 
            presencas.id_evento_presente = %s
    '''

    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()

    # Executar a consulta SQL para buscar os participantes
    cursor.execute(query, (eventoPresenca, f'%{termo_pesquisa}%', f'%{termo_pesquisa}%'))
    usuarios_encontrados = cursor.fetchall()

    # Obter o total de convites
    cursor.execute(query_total_convites, (eventoPresenca,))
    total_convites = cursor.fetchone()[0]

    # Formatar os resultados em um formato JSON
    usuarios_formatados = []
    for usuario in usuarios_encontrados:
        usuario_formatado = {
            'id_evento_presente': usuario[0],
            'id_usuario_presente': usuario[1],
            'id_ingresso': usuario[2],
            'quantidade_convites': usuario[3],
            'nome': usuario[4],
            'sobrenome': usuario[5],
            'titulo_ingresso': usuario[6],
            'quantidade_ingresso': usuario[7]
        }
        usuarios_formatados.append(usuario_formatado)

    # Verificar se nenhum participante foi encontrado e exibir um flash
    if not usuarios_formatados:
        flash('Nenhum usuário encontrado.', 'warning')

    # Verificar se nenhum participante foi encontrado
    if not usuarios_formatados:
        # Se nenhum participante foi encontrado, buscar todos os participantes
        cursor.execute(query, (eventoPresenca, '%', '%'))
        usuarios_encontrados = cursor.fetchall()
        for usuario in usuarios_encontrados:
            usuario_formatado = {
                'id_evento_presente': usuario[0],
                'id_usuario_presente': usuario[1],
                'id_ingresso': usuario[2],
                'quantidade_convites': usuario[3],
                'nome': usuario[4],
                'sobrenome': usuario[5],
                'titulo_ingresso': usuario[6],
                'quantidade_ingresso': usuario[7]
            }
            usuarios_formatados.append(usuario_formatado)

    # Obter a foto do usuário
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursor = connect_BD.cursor()
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursor.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"


    connect_BD.close()

    return render_template("html/ListaParticipantes.html", messages=get_flashed_messages(),foto=foto, eventos=eventosList, presentes=usuarios_formatados, total_convites=total_convites)

@app.route('/buscar_participante', methods=['GET'])
def buscar_participante():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = str(session['idlogado'])
    termo_pesquisa = request.args.get('termo_pesquisa', '')
    eventoPresenca = request.args.get('eventoPresenca', None)
    eventosList = [eventoPresenca]

    # Consulta para buscar os participantes com base no termo de pesquisa
    query = '''
        SELECT 
            presencas.id_evento_presente,
            presencas.id_usuario_presente,
            presencas.id_ingresso,
            presencas.quantidade_convites,
            usuarios.nome,
            usuarios.sobrenome,
            ingressos.titulo_ingresso,
            presencas.quantidade_convites
        FROM 
            presencas
            JOIN usuarios ON presencas.id_usuario_presente = usuarios.id_usuario
            JOIN ingressos ON presencas.id_ingresso = ingressos.id_ingresso
        WHERE 
            presencas.id_evento_presente = %s
            AND (usuarios.nome LIKE %s OR usuarios.sobrenome LIKE %s)
    '''

    # Consulta para calcular o total de convites
    query_total_convites = '''
        SELECT 
            SUM(presencas.quantidade_convites) as qtdtotal
        FROM 
            presencas
            JOIN usuarios ON presencas.id_usuario_presente = usuarios.id_usuario
            JOIN ingressos ON presencas.id_ingresso = ingressos.id_ingresso
        WHERE 
            presencas.id_evento_presente = %s
    '''

    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()

    # Executar a consulta SQL para buscar os participantes
    cursor.execute(query, (eventoPresenca, f'%{termo_pesquisa}%', f'%{termo_pesquisa}%'))
    usuarios_encontrados = cursor.fetchall()

    # Obter o total de convites
    cursor.execute(query_total_convites, (eventoPresenca,))
    total_convites = cursor.fetchone()[0]

    # Formatar os resultados em um formato JSON
    usuarios_formatados = []
    for usuario in usuarios_encontrados:
        usuario_formatado = {
            'id_evento_presente': usuario[0],
            'id_usuario_presente': usuario[1],
            'id_ingresso': usuario[2],
            'quantidade_convites': usuario[3],
            'nome': usuario[4],
            'sobrenome': usuario[5],
            'titulo_ingresso': usuario[6],
            'quantidade_ingresso': usuario[7]
        }
        usuarios_formatados.append(usuario_formatado)

    # Verificar se nenhum participante foi encontrado e exibir um flash
    if not usuarios_formatados:
        flash('Nenhum usuário encontrado.', 'warning')

    # Verificar se nenhum participante foi encontrado
    if not usuarios_formatados:
        # Se nenhum participante foi encontrado, buscar todos os participantes
        cursor.execute(query, (eventoPresenca, '%', '%'))
        usuarios_encontrados = cursor.fetchall()
        for usuario in usuarios_encontrados:
            usuario_formatado = {
                'id_evento_presente': usuario[0],
                'id_usuario_presente': usuario[1],
                'id_ingresso': usuario[2],
                'quantidade_convites': usuario[3],
                'nome': usuario[4],
                'sobrenome': usuario[5],
                'titulo_ingresso': usuario[6],
                'quantidade_ingresso': usuario[7]
            }
            usuarios_formatados.append(usuario_formatado)

    # Obter a foto do usuário
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursor = connect_BD.cursor()
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursor.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"


    connect_BD.close()

    return render_template("html/ListaParticipantesOrganizador.html", messages=get_flashed_messages(),foto=foto, eventos=eventosList, presentes=usuarios_formatados, total_convites=total_convites)

@app.route('/buscar_usuario', methods=['GET'])
def buscar_usuario():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = str(session['idlogado'])

    nome_usuario = request.args.get('nome')  # Obtém o parâmetro 'nome' da solicitação GET
    id_evento = request.args.get('eventoPresenca')

    if nome_usuario and id_evento:
        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor()

        # Executa a consulta SQL para buscar usuários pelo nome
        cursor.execute(
            "SELECT id_usuario, nome, sobrenome FROM usuarios WHERE nome LIKE %s AND id_usuario NOT IN (SELECT id_usuario FROM eventos_usuarios WHERE id_evento = %s)",
            ('%' + nome_usuario + '%', id_evento))

        usuarios = cursor.fetchall()  # Obtém todos os resultados da consulta

        connect_BD.close()  # Fecha a conexão com o banco de dados

        # Lista para armazenar os IDs e nomes completos dos usuários
        ids_nomes_usuarios = []

        # Itera sobre os resultados e extrai os IDs e nomes completos dos usuários
        for usuario in usuarios:
            id_usuario = usuario[0]
            nome_completo = f"{usuario[1]} {usuario[2]}"
            ids_nomes_usuarios.append({'id_usuario': id_usuario, 'nome_completo': nome_completo})

        # Retorna os IDs e nomes completos dos usuários como parte da resposta JSON
        return jsonify({'usuarios': ids_nomes_usuarios}), 200
    else:
        return 'Por favor, forneça um nome de usuário e um ID de evento válido para pesquisar.', 400

@app.route('/adicionar_organizador', methods=['GET','POST'])
def adicionar_organizador():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado
    idlogado = str(session['idlogado'])

    # Obtém o ID do usuário e do evento a partir dos dados enviados pelo AJAX
    id_usuario = request.form.get('id_usuario')
    id_evento = request.form.get('eventoPresenca')

    # Conecta-se ao banco de dados
    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()

    # Insere os dados na tabela eventos_usuarios
    cursor.execute("INSERT INTO eventos_usuarios (id_evento, id_usuario) VALUES (%s, %s)", (id_evento, id_usuario))
    connect_BD.commit()  # Confirma a transação

    connect_BD.close()  # Fecha a conexão com o banco de dados

    # Retorna uma resposta para o AJAX
    return 'Usuário adicionado com sucesso!.', 200

@app.route('/remover_usuario', methods=['POST'])
def remover_usuario():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado
    idlogado = str(session['idlogado'])

    # Obtém o ID do usuário a ser removido e o ID do evento dos dados enviados pelo AJAX
    data = request.json
    userId = data.get('userId')
    id_evento = data.get('eventoPresenca')

    # Conecta-se ao banco de dados
    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor()

    # Remover o usuário da tabela eventos_usuarios
    cursor.execute("DELETE FROM eventos_usuarios WHERE id_usuario = %s AND id_evento = %s", (userId, id_evento))
    connect_BD.commit()  # Confirma a transação

    connect_BD.close()  # Fecha a conexão com o banco de dados

    # Retorna uma resposta para o AJAX
    return 'Usuário removido com sucesso!.', 200

@app.route('/obter_organizadores', methods=['GET'])
def obter_organizadores():

    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    eventoPresenca = request.args.get('eventoPresenca')
    eventosList = [eventoPresenca]

    idlogado = str(session['idlogado'])

    # Lógica para lidar com solicitações GET
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    # Verificar se o ID do evento foi fornecido
    if eventoPresenca is None:
        return jsonify({'error': 'ID do evento não fornecido.'}), 400

    # Configurar a conexão com o banco de dados
    conexao_bd = configbanco(db_type='mysql-connector')

    # Consulta SQL para obter os usuários organizadores por evento
    sql = "select eventos_usuarios.id_usuario, usuarios.nome, usuarios.sobrenome from eventos_usuarios, usuarios where eventos_usuarios.id_usuario = usuarios.id_usuario and id_evento = %s"

    # Criar um cursor para executar a consulta
    cursor = conexao_bd.cursor()

    # Executar a consulta e obter os resultados
    cursor.execute(sql, (eventoPresenca,))

    # Obter os resultados da consulta
    resultados = cursor.fetchall()

    # Fechar o cursor e a conexão com o banco de dados
    cursor.close()
    conexao_bd.close()

    # Criar uma lista de usuários
    usuarios_organizadores = []
    for resultado in resultados:
        usuarios_organizadores.append(resultado)

    # Renderizar o template HTML e passar os usuários organizadores para ele
    return render_template("html/UsuariosOrganizadores.html", usuarios=usuarios_organizadores, foto=foto, eventos=eventosList)

@app.route("/logininicio")
def logininicio():
    return render_template("html/login.html")


@app.route("/alteraabaparticipante", methods=['GET', 'POST'])
def alteraabaparticipante():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = str(session['idlogado'])
    eventoPresenca = request.form.get('eventoPresenca')
    eventosList = [eventoPresenca]

    # Lógica para lidar com solicitações GET
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    acao = request.form.get('aba')

    if acao == 'dadosEvento':
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
            f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "
            f"i.id_ingresso, "
            f"p.id_usuario_presente, "
            f"p.id_evento_presente "
            f"FROM "
            f"ingressos i "
            f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{idlogado}' "
            f"WHERE "
            f"i.id_eventos = '{eventoPresenca}';"
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

        return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)
    elif acao == 'usuariosOrganizadores':
        eventosList = [eventoPresenca]

        # Verificar se o ID do evento foi fornecido
        if eventoPresenca is None:
            return jsonify({'error': 'ID do evento não fornecido.'}), 400

        # Configurar a conexão com o banco de dados
        conexao_bd = configbanco(db_type='mysql-connector')

        # Consulta SQL para obter os usuários organizadores por evento
        sql = """
            SELECT 
                u.id_usuario,
                u.nome,
                u.sobrenome
            FROM 
                eventos AS e
                LEFT JOIN eventos_usuarios AS eu ON e.id_eventos = eu.id_evento
                LEFT JOIN usuarios AS u ON eu.id_usuario = u.id_usuario OR e.id_usuario_evento = u.id_usuario
            WHERE 
                e.id_eventos = %s
        """

        # Criar um cursor para executar a consulta
        cursor = conexao_bd.cursor()

        # Executar a consulta e obter os resultados
        cursor.execute(sql, (eventoPresenca,))

        # Obter os resultados da consulta
        resultados = cursor.fetchall()

        # Fechar o cursor e a conexão com o banco de dados
        cursor.close()
        conexao_bd.close()

        # Criar uma lista de usuários
        usuarios_organizadores = []
        for resultado in resultados:
            usuarios_organizadores.append(resultado)

        # Renderizar o template HTML e passar os usuários organizadores para ele
        return render_template("html/OrganizadoresParticipantes.html", usuarios=usuarios_organizadores, foto=foto,eventos=eventosList)

    elif acao == 'participantes':

        eventosList = [eventoPresenca]

        # Verificar se o ID do evento foi fornecido

        if eventoPresenca is None:
            return jsonify({'error': 'ID do evento não fornecido.'}), 400

        query = '''
                SELECT 
                    presencas.id_evento_presente,
                    presencas.id_usuario_presente,
                    presencas.id_ingresso,
                    presencas.quantidade_convites,
                    usuarios.nome,
                    usuarios.sobrenome,
                    ingressos.titulo_ingresso,
                    presencas.quantidade_convites
                FROM 
                    presencas, usuarios, ingressos
                WHERE 
                    presencas.id_ingresso = ingressos.id_ingresso
                    AND presencas.id_evento_presente = ingressos.id_eventos
                    AND presencas.id_usuario_presente = usuarios.id_usuario 
                    AND presencas.id_evento_presente = %s
            '''

        # Consulta para calcular o total de quantidade de convites
        query_total_convites = '''
                SELECT 
                    SUM(presencas.quantidade_convites) as qtdtotal
                FROM 
                    presencas
                    JOIN usuarios ON presencas.id_usuario_presente = usuarios.id_usuario
                    JOIN ingressos ON presencas.id_ingresso = ingressos.id_ingresso
                WHERE 
                    presencas.id_evento_presente = %s
            '''

        connect_BD = configbanco(db_type='mysql-connector')

        cursor = connect_BD.cursor()

        cursor.execute(query, (eventoPresenca,))

        usuarios_presentes = cursor.fetchall()

        cursor.execute(query_total_convites, (eventoPresenca,))
        total_convites = cursor.fetchone()[0]

        connect_BD.close()

        # Formate os resultados em um formato JSON

        usuarios_formatados = []

        for usuario in usuarios_presentes:
            usuario_formatado = {
                'id_evento_presente': usuario[0],
                'id_usuario_presente': usuario[1],
                'id_ingresso': usuario[2],
                'quantidade_convites': usuario[3],
                'nome': usuario[4],
                'sobrenome': usuario[5],
                'titulo_ingresso': usuario[6],
                'quantidade_ingresso': usuario[7]
            }

            usuarios_formatados.append(usuario_formatado)

        return render_template("html/ListaParticipantes.html", foto=foto, eventos=eventosList,
                               presentes=usuarios_formatados, total_convites=total_convites)
    elif acao == 'avaliacao':
        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor(dictionary=True)
        query = (
            "SELECT a.nota_avaliacao, a.data_avaliacao, a.comentario, u.id_usuario, u.nome, u.sobrenome, u.foto FROM AvaliacaoEventos a, usuarios u WHERE a.id_evento = %s and u.id_usuario = a.id_usuario order by a.data_avaliacao")
        cursor.execute(query, (eventoPresenca,))
        avaliacoes = cursor.fetchall()
        cursor.close()
        connect_BD.close()

        return render_template("html/Avaliacoes.html", avaliacoes=avaliacoes, eventos=eventosList, foto=foto)

@app.route("/alteraaba", methods=['GET', 'POST'])
def alteraaba():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = str(session['idlogado'])

    # Lógica para lidar com solicitações GET
    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    acao = request.form.get('aba')
    eventoPresenca = request.form.get('eventoPresenca')
    if acao == 'dadosEvento':
        print("evtpre:",eventoPresenca)
        eventosList = []
        if eventoPresenca:
            connect_BD = configbanco(db_type='mysql-connector')
            cursur = connect_BD.cursor()
            cursur.execute(
                f"SELECT * FROM eventos e, categoria c where e.categoria = c.id_categoria and e.id_eventos = %s;",
                (eventoPresenca,)
            )
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
                    f'SELECT foto FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
                )
                usuario = cursur.fetchone()

                if usuario:
                    foto = usuario[0] if usuario[0] else "Sem foto disponível"

            connect_BD = configbanco(db_type='mysql-connector')
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
                f"i.observacao_ingresso,"
                f"i.id_ingresso "
                f"FROM eventos e, ingressos i "
                f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = %s;"
            )

            # Executar a consulta SQL
            cursur.execute(query, (eventoPresenca,))
            ingresso = cursur.fetchall()

            connect_BD = configbanco(db_type='mysql-connector')
            cursur = connect_BD.cursor(dictionary=True)
            query = (
                f"SELECT c.nome_campo, c.id_campo FROM eventos e, campo_adicional c where e.id_eventos = c.id_eventos and e.id_eventos = %s;")

            # Executar a consulta SQL
            cursur.execute(query, (eventoPresenca,))
            campo_adicional = cursur.fetchall()
            eventosList2 = [eventoPresenca]
            return render_template("html/EditarEvento.html", evento=eventosList2,eventos=eventosList, foto=foto, ingresso=ingresso,campo_adicional=campo_adicional)
    elif acao == 'usuariosOrganizadores':
        eventosList = [eventoPresenca]

        # Verificar se o ID do evento foi fornecido
        if eventoPresenca is None:
            return jsonify({'error': 'ID do evento não fornecido.'}), 400

        # Configurar a conexão com o banco de dados
        conexao_bd = configbanco(db_type='mysql-connector')

        # Consulta SQL para obter os usuários organizadores por evento
        sql = "select eventos_usuarios.id_usuario, usuarios.nome, usuarios.sobrenome from eventos_usuarios, usuarios where eventos_usuarios.id_usuario = usuarios.id_usuario and id_evento = %s"

        # Criar um cursor para executar a consulta
        cursor = conexao_bd.cursor()

        # Executar a consulta e obter os resultados
        cursor.execute(sql, (eventoPresenca,))

        # Obter os resultados da consulta
        resultados = cursor.fetchall()

        # Fechar o cursor e a conexão com o banco de dados
        cursor.close()
        conexao_bd.close()

        # Criar uma lista de usuários
        usuarios_organizadores = []
        for resultado in resultados:
            usuarios_organizadores.append(resultado)


        # Renderizar o template HTML e passar os usuários organizadores para ele
        return render_template("html/UsuariosOrganizadores.html", usuarios=usuarios_organizadores, foto=foto, eventos=eventosList)
       #return render_template("html/UsuariosOrganizadores.html", foto=foto, eventos=eventosList)

    elif acao == 'chatOrganizadores':

        # Verifique se o ID do evento foi fornecido

        eventosList = [eventoPresenca]

        if not eventoPresenca:
            return jsonify({'error': 'ID do evento não fornecido.'}), 400

        # Conecte-se ao banco de dados

        connect_BD = configbanco(db_type='mysql-connector')

        cursor = connect_BD.cursor()

        # Execute a consulta SQL filtrando pelo ID do evento

        cursor.execute(
            "SELECT chat_organizadores.id_evento, chat_organizadores.id_usuario, chat_organizadores.mensagem, chat_organizadores.data_envio, usuarios.nome, usuarios.sobrenome, usuarios.foto, chat_organizadores.id_chat_organizadores FROM chat_organizadores JOIN usuarios ON chat_organizadores.id_usuario = usuarios.id_usuario WHERE chat_organizadores.id_evento = %s",
            (eventoPresenca,))

        # Recupere todas as linhas do resultado da consulta

        chat_data = cursor.fetchall()

        # Feche o cursor e a conexão com o banco de dados

        cursor.close()

        connect_BD.close()

        # Converta os dados do chat para um formato adequado para JSON e retorne-os como resposta JSON

        chat_json = []

        for row in chat_data:
            chat_json.append({
                'id_evento': row[0],  # Supondo que o ID do evento é o primeiro campo na tupla
                'id_usuario': row[1],  # Supondo que o ID do usuário é o segundo campo na tupla
                'mensagem': row[2],  # Supondo que a mensagem é o terceiro campo na tupla
                'data_envio': row[3].strftime('%d/%m/%y - %H:%M') if row[3] else None,
                # Formate a data e hora como string, se existir
                'nome': row[4],  # Supondo que o nome do usuário é o quarto campo na tupla
                'sobrenome': row[5],  # Supondo que o sobrenome do usuário é o quinto campo na tupla
                'foto': row[6],  # Supondo que a foto do usuário em base64 é o sexto campo na tupla
                'id_chat_organizadores': row[7]
            })
        # Retorne os dados do chat como resposta JSON
        return render_template("html/ChatOrganizadores.html", foto=foto, eventos=eventosList, chat_data=chat_json)

    elif acao == 'listaParticipantes':

        eventosList = [eventoPresenca]

        # Verificar se o ID do evento foi fornecido

        if eventoPresenca is None:
            return jsonify({'error': 'ID do evento não fornecido.'}), 400

        query = '''
            SELECT 
                presencas.id_evento_presente,
                presencas.id_usuario_presente,
                presencas.id_ingresso,
                presencas.quantidade_convites,
                usuarios.nome,
                usuarios.sobrenome,
                ingressos.titulo_ingresso,
                presencas.quantidade_convites
            FROM 
                presencas, usuarios, ingressos
            WHERE 
                presencas.id_ingresso = ingressos.id_ingresso
                AND presencas.id_evento_presente = ingressos.id_eventos
                AND presencas.id_usuario_presente = usuarios.id_usuario 
                AND presencas.id_evento_presente = %s
        '''

        # Consulta para calcular o total de quantidade de convites
        query_total_convites = '''
            SELECT 
                SUM(presencas.quantidade_convites) as qtdtotal
            FROM 
                presencas
                JOIN usuarios ON presencas.id_usuario_presente = usuarios.id_usuario
                JOIN ingressos ON presencas.id_ingresso = ingressos.id_ingresso
            WHERE 
                presencas.id_evento_presente = %s
        '''

        connect_BD = configbanco(db_type='mysql-connector')

        cursor = connect_BD.cursor()

        cursor.execute(query, (eventoPresenca,))

        usuarios_presentes = cursor.fetchall()

        cursor.execute(query_total_convites, (eventoPresenca,))
        total_convites = cursor.fetchone()[0]

        connect_BD.close()

        # Formate os resultados em um formato JSON

        usuarios_formatados = []

        for usuario in usuarios_presentes:
            usuario_formatado = {
                'id_evento_presente': usuario[0],
                'id_usuario_presente': usuario[1],
                'id_ingresso': usuario[2],
                'quantidade_convites': usuario[3],
                'nome': usuario[4],
                'sobrenome': usuario[5],
                'titulo_ingresso': usuario[6],
                'quantidade_ingresso': usuario[7]
            }

            usuarios_formatados.append(usuario_formatado)

        return render_template("html/ListaParticipantesOrganizador.html", foto=foto, eventos=eventosList,presentes=usuarios_formatados, total_convites=total_convites)

    elif acao == 'avaliacoes':
        eventosList = [eventoPresenca]
        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor(dictionary=True)
        query = (
            "SELECT a.nota_avaliacao, a.data_avaliacao, a.comentario, u.id_usuario, u.nome, u.sobrenome, u.foto FROM AvaliacaoEventos a, usuarios u WHERE a.id_evento = %s and u.id_usuario = a.id_usuario order by a.data_avaliacao")
        cursor.execute(query, (eventoPresenca,))
        avaliacoes = cursor.fetchall()
        cursor.close()
        connect_BD.close()
        return render_template("html/AvaliacoesOrganizadores.html", avaliacoes=avaliacoes, eventos=eventosList, foto=foto)

    return render_template("html/destaques.html", foto=foto)

@app.route("/obrigacriarconta", methods=['POST'])
def obrigacriarconta():
    flash("Para confirmar presença no evento você deve realizar o login!")
    eventoPresenca = request.form.get('eventoPresenca')
    return render_template("html/paginainicial.html", eventoPresenca=eventoPresenca)


from datetime import datetime

from flask import request


def clear_flash_messages():
    with app.test_request_context():
        get_flashed_messages()



@app.route("/InformacoesEventosLink")
def InformacoesEventosLink():
        # eventoPresenca = request.form.get('eventoPresenca')
        idlogado = 0
        eventoPresenca = request.args.get('eventoLink')

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
            f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
            f"i.id_ingresso, "
            f"p.id_usuario_presente, "
            f"p.id_evento_presente "
            f"FROM "
            f"ingressos i "
            f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{idlogado}' "
            f"WHERE "
            f"i.id_eventos = '{eventoPresenca}';"
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

        return render_template("html/InformacoesEventosLink.html", eventos=eventos, ingresso=ingresso)


@app.route("/InicioEventosParticipados")
def InicioEventosParticipados():
    if 'idlogado' not in session:
        return redirect("/login")

    idlogado = str(session['idlogado'])
    filtro = request.args.get("filtro")
    data_inicial = request.args.get("dataInicial")
    data_final = request.args.get("dataFinal")
    categoria = request.args.get("categoria")
    nome_evento = request.args.get("nomeEvento")

    if nome_evento is None:
        nome_evento = ''

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
            e.foto_evento,
            p.id_evento_presente, 
            p.id_usuario_presente 
        FROM 
            eventos e 
        JOIN 
            presencas p ON e.id_eventos = p.id_evento_presente 
        WHERE 
            p.id_usuario_presente = %s
        '''

        query_params = [idlogado]

        if filtro:
            query += ' AND (e.nome_evento LIKE %s OR e.local_evento LIKE %s)'
            query_params.extend([f'%{filtro}%', f'%{filtro}%'])

        if nome_evento:
            query += f' AND e.nome_evento LIKE %s'
            query_params.append(f'%{nome_evento}%')

        if data_inicial:
            query += ' AND e.data_evento >= %s'
            query_params.append(data_inicial)

        if data_final:
            query += ' AND e.data_evento <= %s'
            query_params.append(data_final)

        if categoria:
            query += ' AND e.categoria = %s'
            query_params.append(categoria)

        # Executa a consulta
        cursor.execute(query, query_params)
        eventos = cursor.fetchall()

        # Se não houver eventos encontrados, renderizar a página buscarnd.html
        if not eventos:
            filtro_aplicado = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "categoria": categoria,
                "nomeEvento": nome_evento
            }
            flash('Nenhum evento encontrado!')

        filtro_aplicado = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "categoria": categoria,
            "filtro": filtro,
            "nomeEvento": nome_evento
        }

        return render_template("html/EventosParticipados.html", eventos=eventos, foto=foto, filtro=filtro_aplicado)

@app.route("/processarPresenca", methods=['POST','GET'])
def processarPresenca():
    if 'idlogado' not in session:
        return redirect("/")

    if request.method == 'POST':
        acao = request.form.get('acao')
        eventoPresenca = request.form.get('eventoPresenca')
    elif request.method == 'GET':
        acao = request.args.get('acao')
        eventoPresenca = request.args.get('eventoPresenca')

    print(acao)
    print(eventoPresenca)

    if acao == 'complementar':
        if request.method == 'POST':
            acao = request.form.get('acao')
            eventoPresenca = request.form.get('eventoPresenca')
        elif request.method == 'GET':
            acao = request.args.get('acao')
            eventoPresenca = request.args.get('eventoPresenca')


        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        query = (
            f"SELECT i.titulo_ingresso, "
            f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
            f"i.id_ingresso, "
            f"p.id_usuario_presente, "
            f"p.id_evento_presente "
            f"FROM "
            f"ingressos i "
            f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
            f"WHERE "
            f"i.id_eventos = '{eventoPresenca}';"
        )
        cursur.execute(query)
        ingresso = cursur.fetchall()

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

        eventosList = [eventoPresenca]

        connect_BD = configbanco(db_type='mysql-connector')

        if connect_BD.is_connected():
            cursor = connect_BD.cursor()

            # Consulta para obter a foto do usuário logado
            cursor.execute(
                f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
            )
            usuario = cursor.fetchone()

            # Verifica se o usuário tem uma foto
            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"

        # Verifica se o usuário já confirmou presença no evento
        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor()
        cursor.execute("SELECT COUNT(*) FROM presencas WHERE id_evento_presente = %s AND id_usuario_presente = %s",
                       (eventoPresenca, session['idlogado']))
        presenca_confirmada = cursor.fetchone()[0]

        if presenca_confirmada == 0:
            flash("Você ainda não confirmou presença neste evento.", "error")
        else:
            connect_BD = configbanco(db_type='mysql-connector')
            cursor = connect_BD.cursor(dictionary=True)
            query = ("SELECT a.nota_avaliacao, a.data_avaliacao, a.comentario, u.id_usuario, u.nome, u.sobrenome, u.foto FROM AvaliacaoEventos a, usuarios u WHERE a.id_evento = %s and u.id_usuario = a.id_usuario order by a.data_avaliacao")
            cursor.execute(query, (eventoPresenca,))
            avaliacoes = cursor.fetchall()
            cursor.close()
            connect_BD.close()
            return render_template("html/Avaliacoes.html", avaliacoes=avaliacoes, eventos=eventosList, foto=foto)


    elif acao == 'cancelar_presenca':
        eventoPresenca = request.form.get('eventoPresenca')
        tipo_ingresso = request.form.get("tipoIngresso")

        if not eventoPresenca:
            x = 1
            data = request.json
            eventoPresenca = data.get('eventoPresenca')

        if not tipo_ingresso:
            x = 1
            data = request.json
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
            f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
            f"i.id_ingresso, "
            f"p.id_usuario_presente, "
            f"p.id_evento_presente "
            f"FROM "
            f"ingressos i "
            f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
            f"WHERE "
            f"i.id_eventos = '{eventoPresenca}';"
        )
        cursur.execute(query)
        ingresso = cursur.fetchall()

        if connect_BD.is_connected():
            cursor = connect_BD.cursor()

            # Consulta para obter a foto do usuário logado
            cursor.execute(
                f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
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
            f"p.id_usuario_presente = '{session['idlogado']}' and "
            f"p.id_ingresso = '{tipo_ingresso}';"
        )
        cursur.execute(query)
        presenca = cursur.fetchall()

        if not presenca:
            flash("Presença já cancelada!")
            return jsonify({"message": "Presença já cancelada!"})
        else:
            # Execute a instrução SQL de inserção
            query = "DELETE FROM presencas WHERE id_evento_presente = %s AND id_usuario_presente = %s AND id_ingresso = %s"

            values = (eventoPresenca, session['idlogado'], tipo_ingresso)

            connect_BD = configbanco(db_type='mysql-connector')
            cursur = connect_BD.cursor(dictionary=True)
            cursur.execute(query, values)
            connect_BD.commit()

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
                f"p.id_usuario_presente = '{session['idlogado']}' and "
                f"p.id_ingresso = '{tipo_ingresso}';"
            )
            cursur.execute(query)
            presenca = cursur.fetchall()

            connect_BD = configbanco(db_type='mysql-connector')
            cursor = connect_BD.cursor()

            # Defina a instrução SQL DELETE com a condição
            query = "DELETE FROM formulario_adicional WHERE id_eventos = %s AND id_usuario = %s"

            # Valores para a condição na instrução DELETE
            values = (eventoPresenca, session['idlogado'])

            # Execute a instrução SQL DELETE
            cursor.execute(query, values)
            connect_BD.commit()

            flash("Presença cancelada!")
            connect_BD = configbanco(db_type='mysql-connector')
            cursur = connect_BD.cursor(dictionary=True)
            query = (
                f"SELECT i.titulo_ingresso, "
                f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
                f"i.id_ingresso, "
                f"p.id_usuario_presente, "
                f"p.id_evento_presente "
                f"FROM "
                f"ingressos i "
                f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
                f"WHERE "
                f"i.id_eventos = '{eventoPresenca}';"
            )
            cursur.execute(query)
            ingresso = cursur.fetchall()

            jsonify({"message": "Presença cancelada!"})

    elif acao == 'confirmar_presenca':
                eventoPresenca = request.form.get('eventoPresenca')
                tipo_ingresso = request.form.get("tipoIngresso")
                quantidadeConvites = request.form.get("quantidadeConvites")

                session.pop('_flashes', None)

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
                    f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
                    f"i.id_ingresso, "
                    f"p.id_usuario_presente, "
                    f"p.id_evento_presente "
                    f"FROM "
                    f"ingressos i "
                    f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
                    f"WHERE "
                    f"i.id_eventos = '{eventoPresenca}';"
                )
                cursur.execute(query)
                ingresso = cursur.fetchall()

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
                    f"p.id_usuario_presente = '{session['idlogado']}' and "
                    f"p.id_ingresso = '{tipo_ingresso}';"
                )
                cursur.execute(query)
                presenca = cursur.fetchall()

                if connect_BD.is_connected():
                    cursor = connect_BD.cursor()

                    # Consulta para obter a foto do usuário logado
                    cursor.execute(
                        f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
                    )
                    usuario = cursor.fetchone()

                    # Verifica se o usuário tem uma foto
                    if usuario:
                        foto = usuario[0] if usuario[0] else "Sem foto disponível"

                if not presenca:
                    intquantidadeConvites = int(request.form.get("quantidadeConvites"))  # Converta para inteiro
                    if intquantidadeConvites <= 0:
                        flash("Quantidade de ingressos deve ser maior que 0!")
                        return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)

                    connect_BD = configbanco(db_type='mysql-connector')
                    cursor = connect_BD.cursor(dictionary=True)
                    cursor.execute(
                            "SELECT quantidade, quantidade_maxima FROM ingressos WHERE id_eventos = %s AND id_ingresso = %s",
                            (eventoPresenca, tipo_ingresso))
                    qtding = cursor.fetchone()
                    cursor.close()
                    connect_BD.close()

                    quantidade_atual = qtding['quantidade']
                    quantidade_maxima = qtding['quantidade_maxima']

                    connect_BD = configbanco(db_type='mysql-connector')
                    cursor = connect_BD.cursor(dictionary=True)
                    cursor.execute(
                            "select sum(quantidade_convites) as qtdpre from presencas where id_evento_presente = %s and id_ingresso = %s",
                            (eventoPresenca, tipo_ingresso))
                    qtding = cursor.fetchone()
                    cursor.close()
                    connect_BD.close()

                    quantidade_presentes = qtding['qtdpre']

                    if quantidade_presentes is None:
                        quantidade_presentes = 0

                    quantidadeConvitesInt = int(quantidadeConvites)
                    quantidade_atual_sum = int(quantidade_presentes) + quantidadeConvitesInt
                    quantidade_restante = int(quantidade_atual) - int(quantidade_presentes)

                    if quantidadeConvitesInt > quantidade_maxima:
                        flash("A quantidade máxima de ingressos por usuário é " + str(quantidade_maxima) + "!")
                        return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto,ingresso=ingresso)

                    print("quantidade_atual_sum:", quantidade_atual_sum)
                    print("quantidade_atual:", quantidade_atual)

                    if quantidade_atual_sum > quantidade_atual:
                        flash("A quantidade de ingressos restantes é " + str(quantidade_restante) + "!")
                        return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto,
                                                   ingresso=ingresso)

                    connect_BD = configbanco(db_type='mysql-connector')
                    cursor = connect_BD.cursor(dictionary=True)

                    query = f"SELECT * FROM campo_adicional WHERE id_eventos = '{eventoPresenca}' and nome_campo is not null"
                    cursor.execute(query)

                    results = cursor.fetchall()

                    if connect_BD.is_connected():
                        cursor = connect_BD.cursor()

                        # Consulta para obter a foto do usuário logado
                        cursor.execute(
                            f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
                        )
                        usuario = cursor.fetchone()

                        # Verifica se o usuário tem uma foto
                        if usuario:
                            foto = usuario[0] if usuario[0] else "Sem foto disponível"

                    connect_BD = configbanco(db_type='mysql-connector')
                    cursur = connect_BD.cursor(dictionary=True)
                    query = (
                        f"SELECT c.nome_campo, c.id_campo FROM eventos e, campo_adicional c where e.id_eventos = c.id_eventos and e.id_eventos = %s and nome_campo is not null;")

                    # Executar a consulta SQL
                    cursur.execute(query, (eventoPresenca,))
                    campo_adicional = cursur.fetchall()

                    if results:
                        eventosList = [eventoPresenca]
                        eventosList2 = [eventoPresenca]
                        quantidadeConvitesaux = [quantidadeConvites]
                        tipoingressoaux = [tipo_ingresso]
                        return render_template("html/FormularioAdicional.html", tipoingresso=tipoingressoaux,quantidadeConvites=quantidadeConvitesaux,evento=eventosList2,eventos=eventosList, foto=foto, campo_adicional=campo_adicional)

                    # Execute a instrução SQL de inserção
                    query = "INSERT INTO presencas (id_evento_presente, id_usuario_presente, id_ingresso, quantidade_convites) VALUES (%s, %s, %s, %s)"
                    values = (eventoPresenca, session['idlogado'], tipo_ingresso, quantidadeConvites)

                    connect_BD = configbanco(db_type='mysql-connector')
                    cursur = connect_BD.cursor(dictionary=True)
                    cursur.execute(query, values)
                    connect_BD.commit()

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
                            f"p.id_usuario_presente = '{session['idlogado']}' and "
                            f"p.id_ingresso = '{tipo_ingresso}';"
                        )
                    cursur.execute(query)
                    presenca = cursur.fetchall()

                    flash("Presença confirmada!")
                else:
                    flash("Presença já confirmada!")

                connect_BD = configbanco(db_type='mysql-connector')
                cursur = connect_BD.cursor(dictionary=True)
                query = (
                        f"SELECT i.titulo_ingresso, "
                        f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
                        f"i.id_ingresso, "
                        f"p.id_usuario_presente, "
                        f"p.id_evento_presente "
                        f"FROM "
                        f"ingressos i "
                        f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
                        f"WHERE "
                        f"i.id_eventos = '{eventoPresenca}';"
                )
                cursur.execute(query)
                ingresso = cursur.fetchall()
    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)


@app.route("/cancelarPresenca", methods=['POST'])
def cancelarPresenca():
    if 'idlogado' not in session:
        return redirect("/")

    # Obter o ID do usuário da sessão
    idlogado = session['idlogado']
    x = 0

    session.pop('_flashes', None)

    eventoPresenca = request.form.get('eventoPresenca')
    tipo_ingresso = request.form.get("tipoIngresso")

    if not eventoPresenca:
        x = 1
        data = request.json
        eventoPresenca = data.get('eventoPresenca')

    if not tipo_ingresso:
        x = 1
        data = request.json
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
        f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
        f"i.id_ingresso, "
        f"p.id_usuario_presente, "
        f"p.id_evento_presente "
        f"FROM "
        f"ingressos i "
        f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{idlogado}' "
        f"WHERE "
        f"i.id_eventos = '{eventoPresenca}';"
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
        jsonify({"message": "Presença já cancelada!"})
    else:
        # Execute a instrução SQL de inserção
        query = "DELETE FROM presencas WHERE id_evento_presente = %s AND id_usuario_presente = %s AND id_ingresso = %s"

        values = (eventoPresenca, idlogado, tipo_ingresso)

        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        cursur.execute(query, values)
        connect_BD.commit()
        flash("Presença cancelada!")

        jsonify({"message": "Presença cancelada!"})
        #if x == 1:
            #flash("Presença cancelada!")
            #return jsonify({"message": "Presença cancelada!"})

    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)

@app.route("/confirmaPresenca", methods=['POST'])
def confirmaPresenca():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = session['idlogado']

    eventoPresenca = request.form.get('eventoPresenca')
    tipo_ingresso = request.form.get("tipoIngresso")
    quantidadeConvites = request.form.get("quantidadeConvites")

    session.pop('_flashes', None)

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
        f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "
        f"i.id_ingresso, "
        f"p.id_usuario_presente, "
        f"p.id_evento_presente "
        f"FROM "
        f"ingressos i "
        f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{idlogado}' "
        f"WHERE "
        f"i.id_eventos = '{eventoPresenca}';"
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
        query = "INSERT INTO presencas (id_evento_presente, id_usuario_presente, id_ingresso, quantidade_convites) VALUES (%s, %s, %s, %s)"
        values = (eventoPresenca, idlogado, tipo_ingresso, quantidadeConvites)

        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        cursur.execute(query, values)
        connect_BD.commit()
        flash("Presença confirmada!")
    else:
        flash("Presença já confirmada!")

    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)


@app.route("/InformacoesEventos", methods=['POST', 'GET'])
def InformacoesEventos():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = session['idlogado']

    eventoPresenca = request.form.get('botaoDetalhes') or request.form.get('eventoPresenca') or request.args.get('eventoPresenca')

    #print("evt2:", eventoPresenca)

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
        f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "
        f"i.id_ingresso, "
        f"p.id_usuario_presente, "
        f"p.id_evento_presente "
        f"FROM "
        f"ingressos i "
        f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{idlogado}' "
        f"WHERE "
        f"i.id_eventos = '{eventoPresenca}';"
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

    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)

@app.route("/ExibirInformacoesComplementares", methods=['POST'])
def ExibirInforacoesComplementares():
    if 'idlogado' not in session:
        return redirect("/login")

    eventoPresenca = request.form.get('eventoPresenca')
    usuarioPresente = request.form.get('usuarioPresente')
    idlogado = session['idlogado']

    connect_BD = configbanco(db_type='mysql-connector')
    cursor = connect_BD.cursor(dictionary=True)

    query = f"SELECT * FROM campo_adicional WHERE id_eventos = '{eventoPresenca}'"
    cursor.execute(query)

    results = cursor.fetchall()

    if connect_BD.is_connected():
        cursor = connect_BD.cursor()

        # Consulta para obter a foto do usuário logado
        cursor.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
        )
        usuario = cursor.fetchone()

        # Verifica se o usuário tem uma foto
        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        "SELECT c.nome_campo, c.id_campo, a.valor_campo, u.nome, u.sobrenome, u.id_usuario "
        "FROM eventos e "
        "JOIN campo_adicional c ON e.id_eventos = c.id_eventos "
        "LEFT JOIN formulario_adicional a ON e.id_eventos = a.id_eventos AND c.id_campo = a.id_campo "
        "LEFT JOIN usuarios u ON a.id_usuario = u.id_usuario "
        "WHERE e.id_eventos = %s AND u.id_usuario = %s;"
    )

    # Executar a consulta SQL
    cursur.execute(query, (eventoPresenca,usuarioPresente,))
    campo_adicional = cursur.fetchall()

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        "select u.nome, u.sobrenome, u.id_usuario from usuarios u WHERE u.id_usuario = %s;"
    )

    # Executar a consulta SQL
    cursur.execute(query, (usuarioPresente,))
    usuariopresente = cursur.fetchall()

    if results:
        eventosList = [eventoPresenca]
        eventosList2 = [eventoPresenca]

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

    return render_template("html/FormularioAdicionalOrganizador.html",  evento=eventosList2, eventos=eventosList, foto=foto,campo_adicional=campo_adicional,usuariopresente=usuariopresente)

@app.route("/EnviarInformacoes", methods=['POST'])
def EnviarInformacoes():
    if 'idlogado' not in session:
        return redirect("/login")

    quantidadeConvites = request.form.get("quantidadeConvites")
    idlogado = session['idlogado']
    eventoPresenca = request.form.get('eventoPresenca')
    #valor_campo = request.form.get('valor_campo')
    #id_campo = request.form.get('id_campo')
    valores_campo = request.form.getlist('valor_campo[]')
    ids_campo = request.form.getlist('id_campo[]')
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
        f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "
        f"i.id_ingresso, "
        f"p.id_usuario_presente, "
        f"p.id_evento_presente "
        f"FROM "
        f"ingressos i "
        f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{idlogado}' "
        f"WHERE "
        f"i.id_eventos = '{eventoPresenca}';"
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

        if not valores_campo or '' in valores_campo:
            flash('Todos os campos devem ser preenchidos', 'error')
            return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)

        connect_BD = configbanco(db_type='mysql-connector')
        cursor = connect_BD.cursor(dictionary=True)
        print(valores_campo)
        # Consultar se a informação já existe para cada campo adicional
        for i in range(len(valores_campo)):
            # Obter o id_campo atual
            id_campo_atual = ids_campo[i]

            # Dados para a consulta ou inserção
            dados = {
                'id_campo': id_campo_atual,  # Usar o id_campo atual aqui
                'id_eventos': eventoPresenca,
                'id_usuario': idlogado,
                'valor_campo': valores_campo[i]
            }

            # Consultar se a informação já existe
            consulta_query = "SELECT * FROM formulario_adicional WHERE id_eventos = %(id_eventos)s AND id_usuario = %(id_usuario)s AND id_campo = %(id_campo)s"
            cursor.execute(consulta_query, dados)
            resultado = cursor.fetchone()

            # Se o resultado existe, execute um UPDATE; caso contrário, execute um INSERT
            if resultado:
                # Informação já existe, então faça um UPDATE
                update_query = "UPDATE formulario_adicional SET valor_campo = %(valor_campo)s WHERE id_eventos = %(id_eventos)s AND id_usuario = %(id_usuario)s AND id_campo = %(id_campo)s"
                cursor.execute(update_query, dados)
                connect_BD.commit()  # Confirmar a transação
                print("Informação atualizada com sucesso!")
            else:
                # Informação não existe, então faça um INSERT
                insert_query = "INSERT INTO formulario_adicional (id_campo, id_eventos, id_usuario, valor_campo) VALUES (%(id_campo)s, %(id_eventos)s, %(id_usuario)s, %(valor_campo)s)"
                cursor.execute(insert_query, dados)
                connect_BD.commit()  # Confirmar a transação
                print("Informação inserida com sucesso!")

        # Fechar o cursor e a conexão com o banco de dados
        cursor.close()
        connect_BD.close()

        session.pop('_flashes', None)

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
                    f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
                    f"i.id_ingresso, "
                    f"p.id_usuario_presente, "
                    f"p.id_evento_presente "
                    f"FROM "
                    f"ingressos i "
                    f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
                    f"WHERE "
                    f"i.id_eventos = '{eventoPresenca}';"
        )
        cursur.execute(query)
        ingresso = cursur.fetchall()

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
                    f"p.id_usuario_presente = '{session['idlogado']}' and "
                    f"p.id_ingresso = '{tipo_ingresso}';"
        )
        cursur.execute(query)
        presenca = cursur.fetchall()

        if connect_BD.is_connected():
            cursor = connect_BD.cursor()

            # Consulta para obter a foto do usuário logado
            cursor.execute(
                        f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"'
            )
            usuario = cursor.fetchone()

            # Verifica se o usuário tem uma foto
            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"

            if not presenca:
                intquantidadeConvites = int(request.form.get("quantidadeConvites"))  # Converta para inteiro
                if intquantidadeConvites <= 0:
                    flash("Quantidade de ingressos deve ser maior que 0!")
                    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)

                connect_BD = configbanco(db_type='mysql-connector')
                cursor = connect_BD.cursor(dictionary=True)
                cursor.execute("SELECT quantidade, quantidade_maxima FROM ingressos WHERE id_eventos = %s AND id_ingresso = %s",
                            (eventoPresenca, tipo_ingresso))
                qtding = cursor.fetchone()
                cursor.close()
                connect_BD.close()

                quantidade_atual = qtding['quantidade']
                quantidade_maxima = qtding['quantidade_maxima']

                connect_BD = configbanco(db_type='mysql-connector')
                cursor = connect_BD.cursor(dictionary=True)
                cursor.execute("select sum(quantidade_convites) as qtdpre from presencas where id_evento_presente = %s and id_ingresso = %s",
                            (eventoPresenca, tipo_ingresso))
                qtding = cursor.fetchone()
                cursor.close()
                connect_BD.close()

                quantidade_presentes = qtding['qtdpre']

                if quantidade_presentes is None:
                    quantidade_presentes = 0

                quantidadeConvitesInt = int(quantidadeConvites)
                quantidade_atual_sum = int(quantidade_presentes) + quantidadeConvitesInt
                quantidade_restante = int(quantidade_atual) - int(quantidade_presentes)

                if quantidadeConvitesInt > quantidade_maxima:
                    flash("A quantidade máxima de ingressos por usuário é " + str(quantidade_maxima) + "!")
                    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto,ingresso=ingresso)

                print("quantidade_atual_sum:", quantidade_atual_sum)
                print("quantidade_atual:", quantidade_atual)

                if quantidade_atual_sum > quantidade_atual:
                    flash("A quantidade de ingressos restantes é " + str(quantidade_restante) + "!")
                    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto,
                                                   ingresso=ingresso)

                connect_BD = configbanco(db_type='mysql-connector')
                cursor = connect_BD.cursor(dictionary=True)

                query = f"SELECT * FROM campo_adicional WHERE id_eventos = '{eventoPresenca}'"
                cursor.execute(query)

                results = cursor.fetchall()

                if connect_BD.is_connected():
                    cursor = connect_BD.cursor()

                    # Consulta para obter a foto do usuário logado
                    cursor.execute(f'SELECT foto FROM usuarios WHERE id_usuario = "{session["idlogado"]}"')
                    usuario = cursor.fetchone()

                    # Verifica se o usuário tem uma foto
                    if usuario:
                        foto = usuario[0] if usuario[0] else "Sem foto disponível"

                # Execute a instrução SQL de inserção
                query = "INSERT INTO presencas (id_evento_presente, id_usuario_presente, id_ingresso, quantidade_convites) VALUES (%s, %s, %s, %s)"
                values = (eventoPresenca, session['idlogado'], tipo_ingresso, quantidadeConvites)

                connect_BD = configbanco(db_type='mysql-connector')
                cursur = connect_BD.cursor(dictionary=True)
                cursur.execute(query, values)
                connect_BD.commit()
                connect_BD.close()

                connect_BD = configbanco(db_type='mysql-connector')
                cursur = connect_BD.cursor(dictionary=True)
                query = (f"SELECT "
                         f"i.id_ingresso, "
                         f"p.id_usuario_presente, "
                         f"p.id_evento_presente "
                         f"FROM "
                         f"presencas p, ingressos i "
                         f"WHERE "
                         f"p.id_evento_presente = i.id_eventos and "
                         f"p.id_ingresso = i.id_ingresso and "
                         f"p.id_evento_presente = '{eventoPresenca}' and "
                         f"p.id_usuario_presente = '{session['idlogado']}' and "
                         f"p.id_ingresso = '{tipo_ingresso}';"
                )
                cursur.execute(query)
                presenca = cursur.fetchall()

                flash("Presença confirmada!")
            else:
                flash("Presença já confirmada!")

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT i.titulo_ingresso, "
        f"IFNULL(p.quantidade_convites, 0) AS quantidade_convites, "  # Usando IFNULL para substituir NULL por 0
        f"i.id_ingresso, "
        f"p.id_usuario_presente, "
        f"p.id_evento_presente "
        f"FROM "
        f"ingressos i "
        f"LEFT JOIN presencas p ON p.id_evento_presente = i.id_eventos AND p.id_ingresso = i.id_ingresso AND p.id_usuario_presente = '{session['idlogado']}' "
        f"WHERE "
        f"i.id_eventos = '{eventoPresenca}';"
    )
    cursur.execute(query)
    ingresso = cursur.fetchall()
    return render_template("html/InformacoesEventos.html", eventos=eventos, foto=foto, ingresso=ingresso)


@app.route("/SalvarAlteracoes", methods=['POST'])
def SalvarAlteracoes():
    if 'idlogado' not in session:
        return redirect("/login")

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

        cursor.execute(sql, (descricaocad, nomeEventocad, categoriacad, dataCad, horCad, session['idlogado'], endereco, totalParticipantescad,
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

        #sql_delete = "DELETE FROM campo_adicional WHERE id_eventos = %s"
        #cursor.execute(sql_delete, (eventoPresenca))
        #conexao.commit()

        # Inserir os dados dos campos adicionais
        id_campo = request.form.getlist('id_campo[]')
        campos_adicionais = request.form.getlist('nome_campo[]')

        # Validar se id_campo tem informações
        if id_campo:
            # Lista para armazenar os IDs dos campos adicionais que foram processados
            campos_processados = []

            # Processar os dados
            for i, id in enumerate(id_campo):
                if id is not None and id != '0':
                    # Se o id do campo adicional existir, atualizar os dados correspondentes (caso necessário)
                    # Como não foi especificado no seu código, vou assumir que o campo adicional pode ser atualizado.
                    print(f"Atualizando campo existente com id_campo = {id}")
                    sql_update_campo = """
                        UPDATE campo_adicional
                        SET nome_campo = %s
                        WHERE id_campo = %s
                    """
                    cursor.execute(sql_update_campo, (campos_adicionais[i], id))
                    campos_processados.append(id)
                else:
                    print(f"Inserindo novo campo com nome = {campos_adicionais[i]}")
                    # Caso contrário, inserir um novo campo adicional
                    sql_insert_campo = """
                        INSERT INTO campo_adicional (id_eventos, nome_campo)
                        VALUES (%s, %s)
                    """
                    cursor.execute(sql_insert_campo, (eventoPresenca, campos_adicionais[i]))
                    # Obtém o ID do último campo adicionado
                    id_campo_inserido = cursor.lastrowid
                    campos_processados.append(id_campo_inserido)

            # Confirmar as alterações no banco de dados
            conexao.commit()

            # Deletar os campos adicionais que não foram processados
            if campos_processados:
                placeholders = ', '.join(['%s'] * len(campos_processados))
                sql_delete_campo = f"""
                    DELETE FROM campo_adicional
                    WHERE id_eventos = %s AND id_campo NOT IN ({placeholders})
                """
                cursor.execute(sql_delete_campo, [eventoPresenca] + campos_processados)
                conexao.commit()

        id_ingresso = request.form.getlist('id_ingresso[]')
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

        # Converter datas de strings para objetos datetime.date
        datas_inicio_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in
                               datas_inicio_vendas]
        datas_fim_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in datas_fim_vendas]

        print(titulos)
        # Validar se id_ingresso tem informações
        if id_ingresso:
            # Lista para armazenar os IDs dos ingressos que foram processados
            ingressos_processados = []

            # Processar os dados dos ingressos
            for i, id in enumerate(id_ingresso):
                if id:
                    # Se o id do ingresso existir, atualizar os dados correspondentes
                    sql_update_ingresso = """
                        UPDATE ingressos 
                        SET 
                            titulo_ingresso = %s,
                            quantidade = %s,
                            preco = %s,
                            data_ini_venda = %s,
                            data_fim_venda = %s,
                            hora_ini_venda = %s,
                            hora_fim_venda = %s,
                            disponibilidade = %s,
                            quantidade_maxima = %s,
                            observacao_ingresso = %s
                        WHERE id_ingresso = %s
                    """
                    cursor.execute(sql_update_ingresso, (
                        titulos[i],
                        quantidades[i],
                        precos[i],
                        datas_inicio_vendas[i],
                        datas_fim_vendas[i],
                        horas_inicio_vendas[i],
                        horas_fim_vendas[i],
                        disponibilidades[i],
                        quantidades_maximas[i],
                        observacoes[i],
                        id
                    ))
                    ingressos_processados.append(id)
                else:
                    # Caso contrário, inserir um novo ingresso
                    sql_insert_ingresso = """
                        INSERT INTO ingressos 
                        (id_eventos, titulo_ingresso, quantidade, preco, data_ini_venda, data_fim_venda, hora_ini_venda, hora_fim_venda, disponibilidade, quantidade_maxima, observacao_ingresso) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert_ingresso, (
                        eventoPresenca,
                        titulos[i],
                        quantidades[i],
                        precos[i],
                        datas_inicio_vendas[i],
                        datas_fim_vendas[i],
                        horas_inicio_vendas[i],
                        horas_fim_vendas[i],
                        disponibilidades[i],
                        quantidades_maximas[i],
                        observacoes[i]
                    ))
                    # Obtém o ID do último ingresso adicionado
                    id_ingresso_inserido = cursor.lastrowid
                    ingressos_processados.append(id_ingresso_inserido)

            # Confirmar as alterações no banco de dados
            conexao.commit()

            # Deletar os ingressos que não foram processados
            if ingressos_processados:
                placeholders = ', '.join(['%s'] * len(ingressos_processados))
                sql_delete_ingresso = f"""
                    DELETE FROM ingressos
                    WHERE id_eventos = %s AND id_ingresso NOT IN ({placeholders})
                """
                cursor.execute(sql_delete_ingresso, [eventoPresenca] + ingressos_processados)
                conexao.commit()

        print(titulos)

       # for i in range(len(titulos)):
       #     # Insira os dados do ingresso no banco de dados
       #     sql = """INSERT INTO ingressos (id_eventos, titulo_ingresso, quantidade, preco, data_ini_venda,
       #              data_fim_venda, hora_ini_venda, hora_fim_venda, disponibilidade, quantidade_maxima, observacao_ingresso)
       #              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
       #     cursor.execute(sql, (eventoPresenca, titulos[i], quantidades[i], precos[i], datas_inicio_vendas[i],
       #                          datas_fim_vendas[i], horas_inicio_vendas[i], horas_fim_vendas[i],
       #                          disponibilidades[i], quantidades_maximas[i], observacoes[i]))
#
       # conexao.commit()
        #return redirect("/InicioGerenciarEventos")

        eventosList = []
        if eventoPresenca:
            connect_BD = configbanco(db_type='mysql-connector')
            cursur = connect_BD.cursor()
        cursur.execute(
            f"SELECT * FROM eventos e, categoria c where e.categoria = c.id_categoria and e.id_eventos = %s;",
            (eventoPresenca,)
        )
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
                f'SELECT foto FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
            )
            usuario = cursur.fetchone()

            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"

        connect_BD = configbanco(db_type='mysql-connector')
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
            f"i.observacao_ingresso,"
            f"i.id_ingresso "
            f"FROM eventos e, ingressos i "
            f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = %s;"
        )

        # Executar a consulta SQL
        cursur.execute(query, (eventoPresenca,))
        ingresso = cursur.fetchall()

        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        query = (
            f"SELECT c.nome_campo, c.id_campo FROM eventos e, campo_adicional c where e.id_eventos = c.id_eventos and e.id_eventos = %s;")

        # Executar a consulta SQL
        cursur.execute(query, (eventoPresenca,))
        campo_adicional = cursur.fetchall()
        flash("Evento alterado com sucesso!")
        eventosList2 = []
        eventosList2 = [eventoPresenca]
        print(eventosList2)
        return render_template("html/EditarEvento.html", evento=eventosList2,eventos=eventosList, foto=foto, ingresso=ingresso,campo_adicional=campo_adicional)

    except Exception as e:
        print(str(e))
        flash(f"Erro ao criar evento: {str(e)}")
        return render_template("html/EditarEvento.html")
    finally:
        if 'conexao' in locals():
            conexao.close()


@app.route("/adicionaringresso", methods=['POST'])
def adicionaringresso():
    if 'idlogado' not in session:
        return redirect("/login")
    eventoPresenca = request.form.get('eventoPresenca')

    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT foto FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    return render_template("html/AdicionarIngresso.html",foto=foto)



@app.route("/adicionaringressoadd", methods=['POST'])
def adicionaringressoadd():
    if 'idlogado' not in session:
        return redirect("/login")
    eventoPresenca = request.form.get('eventoPresenca')

    id_ingresso = request.form.getlist('id_ingresso[]')
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

    # Converter datas de strings para objetos datetime.date
    datas_inicio_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in
                               datas_inicio_vendas]
    datas_fim_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in datas_fim_vendas]

    conexao = configbanco(db_type='pymysql')
    cursor = conexao.cursor()

    sql_insert_ingresso = """
        INSERT INTO ingressos 
        (titulo_ingresso, quantidade, preco, data_ini_venda, data_fim_venda, hora_ini_venda, hora_fim_venda, disponibilidade, quantidade_maxima, observacao_ingresso) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql_insert_ingresso, (
        titulos,
        quantidades,
        precos,
        datas_inicio_vendas,
        datas_fim_vendas,
        horas_inicio_vendas,
        horas_fim_vendas,
        disponibilidades,
        quantidades_maximas,
        observacoes
    ))
    id_ingresso_inserido = cursor.lastrowid
    ingressos_processados.append(id_ingresso_inserido)

    # Confirmar as alterações no banco de dados
    conexao.commit()

    eventosList = []
    if eventoPresenca:
        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor()
    cursur.execute(
        f"SELECT * FROM eventos e, categoria c where e.categoria = c.id_categoria and e.id_eventos = %s;",
        (eventoPresenca,)
    )
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
            f'SELECT foto FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    connect_BD = configbanco(db_type='mysql-connector')
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
        f"i.observacao_ingresso,"
        f"i.id_ingresso "
        f"FROM eventos e, ingressos i "
        f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = %s;"
    )

    cursur.execute(query, (eventoPresenca,))
    ingresso = cursur.fetchall()

    connect_BD = configbanco(db_type='mysql-connector')
    cursur = connect_BD.cursor(dictionary=True)
    query = (
        f"SELECT c.nome_campo, c.id_campo FROM eventos e, campo_adicional c where e.id_eventos = c.id_eventos and e.id_eventos = %s;")

    cursur.execute(query, (eventoPresenca,))
    campo_adicional = cursur.fetchall()
    eventosList2 = []
    eventosList2 = [eventoPresenca]
    print(eventosList2)
    return render_template("html/EditarEvento.html", evento=eventosList2,eventos=eventosList, foto=foto, ingresso=ingresso,campo_adicional=campo_adicional)

@app.route("/buscar", methods=['GET', 'POST'])
def buscar():
    if 'idlogado' not in session:
        return redirect("/")
    idlogado = session['idlogado']
    filtro = request.args.get("filtro")
    data_inicial = request.args.get("dataInicial")
    data_final = request.args.get("dataFinal")
    categoria = request.args.get("categoria")
    acao = request.args.get('acao')
    nome_evento = request.args.get("nomeEvento")

    if nome_evento is None:
        nome_evento = ''


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

        if nome_evento:
            query += f' AND e.nome_evento LIKE "%{nome_evento}%"'

        if data_inicial:
            query += f' AND e.data_evento >= "{data_inicial}"'

        if data_final:
            query += f' AND e.data_evento <= "{data_final}"'

        if categoria:
            query += f' AND e.categoria = "{categoria}"'

        if acao == 'hoje':
            # Tratamento para a ação 'hoje'
            data_atual = datetime.now().date()
            query += f' AND e.data_evento = "{data_atual}"'
        elif acao == 'estefind':
            # Tratamento para a ação 'estefind'
            data_atual = datetime.now().date()
            proximo_fim_de_semana = data_atual + timedelta(days=(5 - data_atual.weekday()))
            query += f' AND e.data_evento BETWEEN "{data_atual}" AND "{proximo_fim_de_semana}"'
        elif acao == 'musica':
            query += ' AND e.categoria = 15'

        filtro_aplicado = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "categoria": categoria,
            "nomeEvento": nome_evento
        }

        # Executa a consulta
        cursor.execute(query)
        eventos = cursor.fetchall()
        print(eventos)

        # Se não houver eventos encontrados, renderizar a página buscarnd.html
        if not eventos:
            flash('Nenhum evento encontrado!')

        return render_template("html/listabusca.html", eventos=eventos, foto=foto, filtro=filtro_aplicado)
@app.route("/InformacaoConta")
def InformacaoConta():
    if 'idlogado' not in session:
        return redirect("/")

    connect_BD = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
        cursur = connect_BD.cursor()
        cursur.execute(
            f'SELECT nome, sobrenome, foto_nome, foto, nascimento, endereco, rua, cidade, numero, id_usuario FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
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
            id_usuario = usuario[9] if usuario[9] else "ID Usuário não disponível"


    return render_template("html/InformacaoConta.html", nome=nome, sobrenome=sobrenome, foto_nome=foto_nome, foto=foto, nascimento=nascimento, endereco=endereco, rua=rua, cidade=cidade, numero=numero, id_usuario=id_usuario)

def allowed_file(filename):
    # Adicione uma lógica para verificar se a extensão do arquivo é permitida
    # Por exemplo, você pode verificar se a extensão está em uma lista de extensões permitidas
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}
# Defina o caminho para a pasta de upload


@app.route("/salvar_informacoes", methods=["POST"])
def salvar_informacoes():
    if 'idlogado' not in session:
        return redirect("/")

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

            # Atualize a foto e o nome do arquivo do usuário com base no idlogado na sessão
            cursor.execute(
                'UPDATE usuarios SET cidade = %s, rua = %s, nascimento = %s, endereco = %s, numero = %s WHERE id_usuario = %s',
                (cidade, rua, nascimento, endereco, numero, session['idlogado'])
            )

            # Commit para salvar as alterações no banco de dados
            connection.commit()

        # Verifique se um arquivo de imagem foi enviado
        if foto and allowed_file(foto.filename):
            try:
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

                # Conecte-se ao banco de dados
                try:
                    connection = configbanco(db_type='mysql-connector')

                    if connection.is_connected():
                        cursor = connection.cursor()

                        # Atualize a foto e o nome do arquivo do usuário com base no idlogado na sessão
                        cursor.execute(
                            'UPDATE usuarios SET cidade = %s, rua = %s, foto = %s, foto_nome = %s, nascimento = %s, endereco = %s, numero = %s WHERE id_usuario = %s',
                            (cidade, rua, foto_texto, foto_nome, nascimento, endereco, numero, session['idlogado'])
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


@app.route("/destaques", methods=['GET', 'POST'])
def destaques():
    if 'idlogado' in session:
        idlogado = session['idlogado']
        connect_BD = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cursur = connect_BD.cursor()
            cursur.execute(
                f'SELECT foto FROM usuarios WHERE id_usuario = "{idlogado}"'
            )
            usuario = cursur.fetchone()

            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"

            query = '''
                SELECT 
                    eventos.id_eventos,
                    eventos.nome_evento,
                    eventos.descricao_evento,
                    eventos.foto_evento,
                    SUM(presencas.quantidade_convites) AS total_convites
                FROM 
                    eventos
                    JOIN presencas ON presencas.id_evento_presente = eventos.id_eventos
                GROUP BY 
                    eventos.id_eventos, eventos.nome_evento, eventos.descricao_evento, eventos.foto_evento
                ORDER BY 
                    total_convites DESC
                LIMIT 12;
            '''

            # Executa a consulta
            connect_BD = configbanco(db_type='mysql-connector')
            if connect_BD.is_connected():
                cursur = connect_BD.cursor()
                cursur.execute(query)
                eventos = cursur.fetchall()

            eventos_json = []
            for evento in eventos:
                evento_dict = {
                    'id_evento': evento[0],
                    'nome_evento': evento[1],
                    'descricao_evento': evento[2],
                    'foto_evento': evento[3],
                    'total_convites': evento[4]
                }
                eventos_json.append(evento_dict)

            return render_template("html/destaques.html", foto=foto, eventos_populares=eventos_json)


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
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO usuarios VALUES (default, %s, %s, %s, %s, default, default, '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',default,default,default,default,default,default);",
                           (nomecad, sobrenomecad, emailcad, senhacad, subId))
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
            cursor.execute(
                "INSERT INTO usuarios VALUES (default, %s, %s, %s, default, default, default, %s, default, default, default, default);",
                (nomecad, sobrenomecad, emailcad, senhacad))
            connect_BD.commit()
            connect_BD.close()
            return redirect(url_for('login', email=emailcad, senha=senhacad))

@app.route("/login", methods=['GET', 'POST'])
def login():
    session.clear()
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        subId = request.form.get('subId')

        connect_BD = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cursor = connect_BD.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()

            if usuario:
                if subId:
                    if usuario[6] == subId:
                        session['idlogado'] = usuario[0]
                        eventoPresenca = request.args.get('eventoPresenca')
                        if eventoPresenca is None or eventoPresenca == 0:
                            return redirect("/destaques")
                        else:
                            return redirect(url_for('InformacoesEventos', eventoPresenca=eventoPresenca))
                elif usuario[4] == senha:
                    session['idlogado'] = usuario[0]
                    eventoPresenca = request.args.get('eventoPresenca')
                    if eventoPresenca is None or eventoPresenca == 0:
                        return redirect("/destaques")
                    else:
                        return redirect(url_for('InformacoesEventos', eventoPresenca=eventoPresenca))
            else:
                if subId:  # Se o usuário tem um subId, mas não está registrado
                    connect_BD = configbanco(db_type='mysql-connector')
                    cursor = connect_BD.cursor()
                    cursor.execute("INSERT INTO usuarios (nome, sobrenome, email, senha, subId, foto) VALUES (%s, %s, %s, %s, %s, %s)",
                                   (request.form.get('nomecad'), request.form.get('sobrenomecad'), email, senha, subId, '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'))
                    connect_BD.commit()
                    connect_BD.close()
                    session['idlogado'] = cursor.lastrowid
                    eventoPresenca = request.args.get('eventoPresenca')
                    if eventoPresenca is None or eventoPresenca == 0:
                        return redirect("/destaques")
                    else:
                        return redirect(url_for('InformacoesEventos', eventoPresenca=eventoPresenca))

            flash('Usuário inválido!')
            return redirect("/")
        else:
            return redirect("/")
    elif request.method == 'GET':
        email = request.args.get('email')
        senha = request.args.get('senha')
        subId = request.args.get('subId')

        connect_BD = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cursor = connect_BD.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()

            if usuario:
                if subId:
                    if usuario[6] == subId:
                        session['idlogado'] = usuario[0]
                        eventoPresenca = request.args.get('eventoPresenca')
                        if eventoPresenca is None or eventoPresenca == 0:
                            return redirect("/destaques")
                        else:
                            return redirect(url_for('InformacoesEventos', eventoPresenca=eventoPresenca))
                elif usuario[4] == senha:
                    session['idlogado'] = usuario[0]
                    eventoPresenca = request.args.get('eventoPresenca')
                    if eventoPresenca is None or eventoPresenca == 0:
                        return redirect("/destaques")
                    else:
                        return redirect(url_for('InformacoesEventos', eventoPresenca=eventoPresenca))
            else:
                if subId:  # Se o usuário tem um subId, mas não está registrado
                    connect_BD = configbanco(db_type='mysql-connector')
                    cursor = connect_BD.cursor()
                    cursor.execute("INSERT INTO usuarios (nome, sobrenome, email, senha, subId, foto) VALUES (%s, %s, %s, %s, %s, %s)",
                                   (request.args.get('nomecad'), request.args.get('sobrenomecad'), email, senha, subId, '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'))
                    connect_BD.commit()
                    connect_BD.close()
                    session['idlogado'] = cursor.lastrowid
                    eventoPresenca = request.args.get('eventoPresenca')
                    if eventoPresenca is None or eventoPresenca == 0:
                        return redirect("/destaques")
                    else:
                        return redirect(url_for('InformacoesEventos', eventoPresenca=eventoPresenca))

            flash('Usuário inválido!')
            return redirect("/")
        else:
            return redirect("/")

@app.route("/InicioCriarEvento")
def criarevento():
    if 'idlogado' in session:
        idlogado = session['idlogado']
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
    else:
        # Redirecionar para a página de login se o usuário não estiver logado
        return redirect("/")


@app.route("/CriarEvento", methods=['POST'])
def CriarEvento():
    if 'idlogado' not in session:
        return redirect("/")

    foto = request.files["img_divulga"]

    # Verifique se um arquivo de imagem foi enviado
    if foto and allowed_file(foto.filename):
        # Abra a imagem usando PIL
        img = Image.open(foto)

        # Gere um nome único para a foto usando secure_filename
        foto_nome = secure_filename(foto.filename)

        # Converta a imagem para dados binários
        img_buffer = BytesIO()
        img.save(img_buffer, format=img.format)
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
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    dataCad = request.form.get('dataCad')
    dataCadFin = request.form.get('dataCadFin')
    horCad = request.form.get('horCad')
    horCadFin = request.form.get('horCadFin')
    data_atual = datetime.now().date()
    hora_atual = datetime.now().time()
    dataCad = datetime.strptime(dataCad, "%Y-%m-%d").date()
    horCad = datetime.strptime(horCad, "%H:%M").time()

    if dataCad < data_atual or (dataCad == data_atual and horCad < hora_atual):
        flash("A data fornecida é menor que a data atual.")
        return render_template("html/CriarEvento.html")

    dataCadFin = datetime.strptime(dataCadFin, "%Y-%m-%d").date()
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
            descricaocad, nomeEventocad, categoriacad, dataCad, horCad, session['idlogado'], endereco,
            totalParticipantescad,
            classificacaocad, rua, cidade, numero, dataCadFin, horCadFin, nome_produtor, descricao_produtor, estado,
            bairro, complemento, foto_texto, foto_nome, latitude, longitude))

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

        datas_inicio_vendas = [datetime.strptime(data, "%Y-%m-%d").date() + timedelta(days=1) for data in
                               datas_inicio_vendas]
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
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    eventoPresenca = request.form.get('eventoPresenca')
    botaoConfirma = request.form.get('botaoConfirma')
    botaoCancela = request.form.get('botaoCancela')

    idlogado = session['idlogado']  # Obter o ID do usuário da sessão

    if botaoCancela == 'true':
        connect_BD  = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cont = 0
            cursur = connect_BD.cursor()
            cursur.execute(
                f"select * from presencas where id_evento_presente = '{eventoPresenca}' and id_usuario_presente = '{idlogado}';")
            presencasBD = cursur.fetchall()

        if len(presencasBD) == 0:
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
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()
            cursor.execute(
                f"DELETE FROM presencas WHERE ID_EVENTO_PRESENTE = '{eventoPresenca}' AND ID_USUARIO_PRESENTE = '{idlogado}';")
            conexao.commit()
            conexao.close()

            connect_BD  = configbanco(db_type='mysql-connector')
            if connect_BD.is_connected():
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
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    eventoPresenca = request.form.get('eventoPresenca')
    botaoConfirma = request.form.get('botaoConfirma')
    botaoCancela = request.form.get('botaoCancela')

    idlogado = session['idlogado']  # Obter o ID do usuário da sessão

    if botaoConfirma == 'true':
        connect_BD  = configbanco(db_type='mysql-connector')
        if connect_BD.is_connected():
            cont = 0

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
            conexao = configbanco(db_type='pymysql')
            cursor = conexao.cursor()
            cursor.execute(
                f"INSERT INTO presencas VALUES ('{eventoPresenca}','{idlogado}');")
            conexao.commit()
            conexao.close()

            connect_BD  = configbanco(db_type='mysql-connector')
            if connect_BD.is_connected():
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
    if 'idlogado' not in session:
        return redirect("/login")

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
        LEFT JOIN
            eventos_usuarios AS eu ON eu.id_evento = e.id_eventos
        WHERE
            (e.id_usuario_evento = %s OR eu.id_usuario = %s)
    '''

    query_params = [session['idlogado'], session['idlogado']]

    if nome_evento:
        query += f' AND e.nome_evento LIKE %s'
        query_params.append(f'%{nome_evento}%')

    if data_inicial:
        query += f' AND e.data_evento >= %s'
        query_params.append(data_inicial)

    if data_final:
        query += f' AND e.data_evento <= %s'
        query_params.append(data_final)

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
        cursur.execute(query, query_params)
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
            f'SELECT foto FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
        )
        usuario = cursur.fetchone()

        if usuario:
            foto = usuario[0] if usuario[0] else "Sem foto disponível"

    return render_template("html/GerenciarEventos.html", eventos=eventos, filtro=filtro_aplicado, foto=foto)

@app.route("/GerenciarEventos", methods=['POST'])
def GerenciarEventos():
    if 'idlogado' not in session:
        return redirect("/")

    eventoPresenca = request.form.get('botaoEditar')
    print(eventoPresenca)
    eventosList = []
    if eventoPresenca:
        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor()
        cursur.execute(
            f"SELECT * FROM eventos e, categoria c where e.categoria = c.id_categoria and e.id_eventos = %s;", (eventoPresenca,)
        )
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
                f'SELECT foto FROM usuarios WHERE id_usuario = %s', (session['idlogado'],)
            )
            usuario = cursur.fetchone()

            if usuario:
                foto = usuario[0] if usuario[0] else "Sem foto disponível"

        connect_BD = configbanco(db_type='mysql-connector')
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
            f"i.observacao_ingresso,"
            f"i.id_ingresso "
            f"FROM eventos e, ingressos i "
            f"WHERE e.id_eventos = i.id_eventos AND e.id_eventos = %s;"
        )

        # Executar a consulta SQL
        cursur.execute(query, (eventoPresenca,))
        ingresso = cursur.fetchall()

        connect_BD = configbanco(db_type='mysql-connector')
        cursur = connect_BD.cursor(dictionary=True)
        query = (f"SELECT c.nome_campo, c.id_campo FROM eventos e, campo_adicional c where e.id_eventos = c.id_eventos and e.id_eventos = %s;")

        # Executar a consulta SQL
        cursur.execute(query, (eventoPresenca,))
        campo_adicional = cursur.fetchall()
        eventosList2 = [eventoPresenca]
        return render_template("html/EditarEvento.html", evento=eventosList2,eventos=eventosList, foto=foto, ingresso=ingresso, campo_adicional=campo_adicional)
    else:
        return ExcluirEvento()


def ExcluirEvento():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    eventoPresenca = request.form.get('eventoPresenca')
    botaoExcluirEvento = request.form.get('botaoExcluirEvento')
    eventoPresenca = botaoExcluirEvento
    botaoExcluirEvento = 'true'

    if botaoExcluirEvento == 'true':
        idlogado = session['idlogado']  # Obter o ID do usuário da sessão

        # Conexão com o banco de dados e execução das consultas de exclusão
        conexao = configbanco(db_type='pymysql')
        cursor = conexao.cursor()

        cursor.execute(
            f"DELETE FROM presencas WHERE ID_EVENTO_PRESENTE = '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM campo_adicional WHERE id_eventos = '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM ingressos WHERE id_eventos =  '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM eventos WHERE ID_EVENTOS = '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM chat_organizadores WHERE ID_EVENTO = '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM AvaliacaoEventos WHERE ID_EVENTO = '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM eventos_usuarios WHERE ID_EVENTO = '{eventoPresenca}';")
        conexao.commit()

        cursor.execute(
            f"DELETE FROM formulario_adicional WHERE ID_EVENTOS = '{eventoPresenca}';")
        conexao.commit()

        conexao.close()

        flash("Evento excluído com sucesso!")
        return redirect("/InicioGerenciarEventos")
    else:
        return Detalhes()


def Detalhes():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

    idlogado = session['idlogado']  # Obter o ID do usuário da sessão

    eventoPresenca = request.form.get('eventoPresenca')
    connect_BD  = configbanco(db_type='mysql-connector')
    if connect_BD.is_connected():
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
              where e.id_usuario_evento = %s and e.id_eventos = %s \
              GROUP BY\
              e.total_participantes,\
              e.local_evento,\
              e.id_eventos,\
              e.descricao_evento,\
              e.nome_evento,\
              e.data_evento,\
              e.hora_evento,\
              c.descricao_categoria,\
              u.nome;', (idlogado, eventoPresenca))
        eventos = cursur.fetchall()

        if connect_BD.is_connected():
            cursur = connect_BD.cursor()
            cursur.execute(
                f'SELECT concat(u.nome, " ",u.sobrenome) as nomeCompleto FROM presencas as p, usuarios as u where p.id_usuario_presente = u.id_usuario and p.id_evento_presente = %s;', (eventoPresenca,))
            presentes = cursur.fetchall()

    return render_template("html/Detalhes.html", eventos=eventos, presentes=presentes)

@app.route("/EditarEvento", methods=['POST'])
def EditarEventoEfetivo():
    if 'idlogado' not in session:
        return redirect("/")  # Redirecionar para a página inicial se o usuário não estiver logado

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
        flash("A data fornecida é menor que a data atual.")
        return render_template("html/CriarEvento.html")
    elif dataCad == data_atual and horCad < hora_atual:
        flash("A hora fornecida é menor que a hora atual.")

    idlogado = session['idlogado']  # Obter o ID do usuário da sessão

    conexao = configbanco(db_type='pymysql')
    cursor = conexao.cursor()
    cursor.execute(
        f"UPDATE eventos SET descricao_evento ='{descricaocad}',nome_evento = '{nomeEventocad}',categoria = '{categoriacad}',data_evento = '{dataCad}',hora_evento = '{horCad}',local_evento = '{localEventocad}',total_participantes = {totalParticipantescad} WHERE id_eventos = {eventoEditar} AND id_usuario_evento = {idlogado};")
    conexao.commit()
    conexao.close()

    return redirect("/InicioGerenciarEventos")


if __name__ == "__main__":
    app.run(debug=True)

