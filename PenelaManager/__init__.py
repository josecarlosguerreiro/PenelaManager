from typing import Dict, Any, Union

import mysql.connector
from mysql.connector import errorcode

from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
import os
import re



app = Flask(__name__)


@app.route('/')
def home():
    data = proxjogo()
    return render_template('index.html', data =data)


@app.route('/base', methods=['GET', 'POST'])
def base():

    is_user_loggedin = session['username']
    data = proxjogo()
    if is_user_loggedin:
        return render_template("base.html", msg=data)
    else:
        return redirect('/', msg=data)


@app.route('/login', methods=['GET', 'POST'])
def login():
    #Output em caso de erro
    msg = ''
    #valida se username e password POST existem
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        print('USERNAME --->', username)
        password = request.form['password']
        print('password --->', password)
        cnx = connection()
        cur = cnx.cursor()
        cur.execute('SELECT * FROM users WHERE nome = %s AND password=%s;', [username, password])
        account = cur.fetchone()
        #Se a conta existe
        if account:
            #Cria sessao
            session['loggedin'] = True
            flash('Estas connectado')
            session['id'] = account[0]
            session['username'] = account[1]
            return redirect('/base') #render_template('base.html')
        else:
            msg = 'Username / Password errada'
    return render_template('login.html', msg=msg)


# http://localhost:5000/python/logout - this will be the logout page
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    # Redirect to login page
    return redirect('/')


# this will be the registration page, we need to use both GET and POST requests
@app.route('/registo', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cnx = connection()
        cursor = cnx.cursor()
        account = cursor.fetchone()
        if account:
            msg = 'Conta já existente!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Endereço de email inválido!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username apenas pode conter letras e numeros!'
        elif not username or not password or not email:
            msg = 'Por favor preencha tudo!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.callproc('inserir_user', [username, password, email])
            cnx.commit()
            msg = 'Utilizador registado com sucesso!'
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Por favor preencha tudo!'
    # Show registration form with message (if any)
    return render_template('registo.html', msg=msg)


#Alterar Password
@app.route('/changepassword', methods=['GET', 'POST'])
def changepassword():
    # Output message if something goes wrong...
    msg = ''

    is_user_loggedin = session['username']

    if is_user_loggedin:
        if request.method == 'POST' and 'password' in request.form:
            username = session['username']
            password = request.form['password']
            print('username --->', username)
            print('password --->', password)
            cnx = connection()
            cur = cnx.cursor()
            cur.execute('UPDATE users SET password = %s WHERE nome = %s;', (password, username))
            cnx.commit()
            return redirect('/base')
        return render_template('changepassword.html', msg=msg)
    else:
        return redirect('/')


@app.route('/sede')
def sede():
    return render_template('sede.html')


@app.route('/calendario')
def page_calendario():
    return render_template('calendario.html')


@app.route('/plantel')
def page_plantel():

    cnx = connection()
    cursor = cnx.cursor()
    query_string = "SELECT * FROM jogador"
    cursor.execute(query_string)

    data = cursor.fetchall()

    for row in data:
        print('===============================================')
        print('nome', row[1])
        print('posicao   :', row[5])
        print('===============================================')

    cnx.close()
    return render_template('plantel.html', data=data)


@app.route('/equipas')
def page_equipas():

    cnx = connection()
    cursor = cnx.cursor()
    query_string = "SELECT * FROM equipa"
    cursor.execute(query_string)
    data = cursor.fetchall()
    for row in data:
        print('===============================================')
        print('nome', row[1])
        print('campo   :', row[2])
        print('===============================================')

    cnx.close()
    return render_template('equipas.html', data=data)

@app.route('/vertreinos', methods=['GET','POST'])
def page_vertreino():
    cnx = connection()
    cursor = cnx.cursor()
    query_string = "select * from view_vertreinos"
    cursor.execute(query_string)
    data = cursor.fetchall()

    if request.method == "POST":
        treino = request.form.to_dict(flat=False)
        treino = treino.keys()
        listaTreino = list(treino)[0]
        idtreino = listaTreino[1]
        cursor.execute('SELECT * FROM view_vertreinos where id_treino = %s;', [idtreino])
        treinos=cursor.fetchall()
        cursor.execute('SELECT * FROM jogador')
        lista_jogador = cursor.fetchall()

        cursor.close()
        phase = request.form.get('check')
        rphase = phase.replace("on", "1")
        print("Checkbox test: {phase} | {rphase}")
        return render_template('verTreinoPromenor.html', data=treinos, listaj=lista_jogador)
    else:
        return render_template('verTreino.html', data=data)


@app.route('/treinocompleto', methods=['GET', 'POST'])
def page_treino_completo(idtreino, lista_jogador):
    cnx = connection()
    cur = cnx.cursor()
    cur.execute('SELECT * FROM view_vertreinos where id_treino = %s;', [idtreino])
    data = cur.fetchall()


    return render_template('verTreinoPromenor.html', data=idtreino, listaj=lista_jogador)

@app.route('/addTreino', methods=['GET', 'POST'])
def page_addTreinos():
    if request.method == 'POST':
        epoca = request.form['inputEpoca']
        meteo = 'Sol'
        tipotreino = request.form['tipotreino']
        datahora = request.form['datahora']
        localtreino = request.form['inputLocaltreino']
        comentario = request.form['comentario']
        print('EPOCA ----->', epoca)
        print('tipotreino ----->', tipotreino)
        print('datahora ----->', datahora)
        print('localtreino ----->', localtreino)
        print('comentario ----->', comentario)
        print('username ---> ', session['username'])

        cnx = connection()
        cursor = cnx.cursor()
        cursor.callproc('inserir_treino', [epoca, meteo, tipotreino, localtreino, datahora, comentario, session['username']])
        cnx.commit()
        cursor.close()
        cnx.close()


    return render_template('addTreino.html')

def connection():
    try:
        cnx = mysql.connector.connect(user='gdpenela', password='gdpenela',
                                      host='joseguerreiro.ddns.net', database='Penela')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        return cnx


def proxjogo():
    cnx = connection()
    cur = cnx.cursor()
    query_string = "select min(cal.dta), cal.epoca, cal.dta, cal.jornada, e.nome, ef.nome, e.campo from calendario cal, jogo jg, equipa e, equipa ef\
                    where cal.dta >= sysdate()\
                        and cal.id_jogo = jg.id_jogo\
                        and e.id_equipa = jg.id_eq_casa\
                        and ef.id_equipa = jg.id_eq_fora"
    cur.execute(query_string)
    data = cur.fetchall()
    dta = data[0]
    print('data -->', dta)
    return dta



if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0')
