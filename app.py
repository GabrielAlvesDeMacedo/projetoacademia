from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, methods=['GET', 'POST', 'PUT', 'DELETE'])


load_dotenv()

FB_KEY = json.loads(os.getenv('CONFIG_FIREBASE'))

cred = credentials.Certificate(FB_KEY)
firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/', methods=['GET'])
def index():
    return 'Academia aberta', 200

@app.route('/admin', methods=['POST'])
def cadastrar():
    dados = request.json

    if "cpf" not in dados or "nome" not in dados:
        return jsonify({'mensagem':'Erro. Campos CPF e nome são obrigatórios'}), 400
    
    #Contador
    contador_ref = db.collection('controle_id').document('contador')
    contador_doc = contador_ref.get().to_dict()
    ultimo_id = contador_doc.get('id')
    novo_id = int(ultimo_id) + 1
    contador_ref.update({'id': novo_id}) #atualização da coleção

    db.collection('cadastros').document(str(novo_id)).set({
        "id": novo_id,
        "cpf": dados['cpf'],
        "nome": dados['nome'],
        "status": dados.get('status', 'true'),  # Define o status como 'ativo' por padrão
    })

    return jsonify({'mensagem':'Cadastro realizado com sucesso!'}), 201

@app.route('/admin', methods=['PUT'])
def alterar_cadastro():
    dados = request.json

    if "id" not in dados or "cpf" not in dados or "nome" not in dados:
        return jsonify({'mensagem':'Erro. Campos id, CPF e nome são obrigatórios'}), 400
    
    doc_ref = db.collection('cadastros').document(str(dados['id']))
    doc = doc_ref.get()

    if doc.exists:
        doc_ref.update({
            'cpf': dados['cpf'],
            'nome': dados['nome'],
            'status': dados.get('status', 'true', 'false')  # Atualiza o status se fornecido, caso contrário mantém 'ativo'
        })
        return jsonify({'mensagem':'Cadastro atualizado com sucesso!'}), 201
    else:
        return jsonify({'mensagem':'Erro. Cadastro não encontrado!'}), 404

@app.route('/admin', methods=['DELETE'])
def excluir_cadastro(id):
    doc_ref = db.collection('cadastros').document(str(id))
    doc = doc_ref.get()

    if not doc.exists:
        return jsonify({'mensagem':'Erro. Cadastro não encontrado'}), 404

    doc_ref.delete()
    return jsonify({'mensagem':'Cadastro excluído com sucesso!'}), 200

@app.route('/admin', methods=['GET'])
def lista_cadastros():
    cadastros = []
    lista = db.collection('cadastros').stream()
    
    for item in lista:
        cadastros.append(item.to_dict())

    if cadastros:
        return jsonify((cadastros)), 200
    else:
        return jsonify({'mensagem':'Erro! Nenhum cadastro encontrado'}), 404

@app.route('/admin/consultar_cpf', methods=['GET'])
def consultar_aluno_por_cpf():
    cpf = request.args.get('cpf')

    if not cpf:
        return jsonify({'mensagem': 'CPF não fornecido como parâmetro'}), 400

    alunos_ref = db.collection('cadastros')
    query = alunos_ref.where('cpf', '==', cpf).limit(1)
    resultados = query.stream()

    for aluno in resultados:
        return jsonify({'id': aluno.to_dict()['id'], 'nome': aluno.to_dict()['nome'], 'cpf': aluno.to_dict()['cpf']}), 200

    return jsonify({'mensagem': 'Aluno não encontrado com o CPF fornecido'}), 404

if __name__ == "__main__":
    app.run()