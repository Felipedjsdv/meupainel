
from flask import Flask, render_template, request, redirect, session
import sqlite3, random, requests

app = Flask(__name__)
app.secret_key = 'chave_super_secreta'
API_KEY = 'SUA_API_KEY_AQUI'

def criar_banco():
    with sqlite3.connect('banco.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telefone TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS testes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            username TEXT,
            password TEXT,
            exp_date INTEGER,
            domain TEXT,
            credits INTEGER,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
criar_banco()

@app.route('/', methods=['GET', 'POST'])
def login():
    erro = ''
    if request.method == 'POST':
        telefone = request.form['telefone'].strip()
        senha = request.form['senha'].strip()
        if not telefone.isdigit():
            erro = 'Telefone inválido.'
        elif not senha:
            erro = 'Senha obrigatória.'
        else:
            with sqlite3.connect('banco.db') as conn:
                c = conn.cursor()
                c.execute('SELECT * FROM clientes WHERE telefone=? AND senha=?', (telefone, senha))
                user = c.fetchone()
                if user:
                    session['cliente_id'] = user[0]
                    return redirect('/inicio')
                else:
                    erro = 'Dados incorretos.'
    return render_template('login.html', erro=erro)

@app.route('/inicio')
def inicio():
    if 'cliente_id' not in session: return redirect('/')
    return render_template('painel_inicio.html')

@app.route('/vencimento')
def vencimento():
    if 'cliente_id' not in session: return redirect('/')
    with sqlite3.connect('banco.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM testes WHERE cliente_id = ?', (session['cliente_id'],))
        testes = c.fetchall()
    return render_template('painel_vencimento.html', testes=testes)

@app.route('/gerar', methods=['POST'])
def gerar():
    if 'cliente_id' not in session: return redirect('/')
    prefixo = "cli" + str(session['cliente_id'])
    username = f"{prefixo}{random.randint(1000,9999)}"
    payload = {"username": username, "minutes": "60"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    r = requests.post("https://revenda.pixbot.link/user", json=payload, headers=headers)
    if r.ok:
        resp = r.json()
        with sqlite3.connect('banco.db') as conn:
            c = conn.cursor()
            c.execute('INSERT INTO testes (cliente_id, username, password, exp_date, domain, credits) VALUES (?,?,?,?,?,?)',
                      (session['cliente_id'], resp['username'], resp['password'], resp['exp_date'], resp['domain'], resp['credits']))
        return redirect('/vencimento')
    return "Erro ao gerar teste.", 400

@app.route('/comprovante')
def comprovante():
    if 'cliente_id' not in session: return redirect('/')
    return render_template('painel_comprovante.html')

@app.route('/contato')
def contato():
    if 'cliente_id' not in session: return redirect('/')
    return render_template('painel_contato.html')

@app.route('/pagamento')
def pagamento():
    if 'cliente_id' not in session: return redirect('/')
    return render_template('painel_pagamento.html')

@app.route('/sair')
def sair():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
