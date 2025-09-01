from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import psycopg2
import logging

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configura o logger
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)  # Habilita o CORS para todas as rotas da aplicação


# Função para conectar ao banco de dados
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', 5432)
        )
        return conn
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        return None


# Rota para listar autores e adicionar um novo autor
@app.route('/autores', methods=['GET', 'POST'])
def handle_autores():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Não foi possível conectar ao banco de dados"}), 500

    cur = conn.cursor()

    if request.method == 'GET':
        try:
            cur.execute("SELECT autor_id, nome, nacionalidade FROM autor;")
            autores = cur.fetchall()

            autores_list = []
            for autor in autores:
                autores_list.append({
                    "autor_id": autor[0],
                    "nome": autor[1],
                    "nacionalidade": autor[2]
                })

            return jsonify(autores_list)
        except Exception as e:
            logging.error(f"Erro ao listar autores: {e}")
            return jsonify({"erro": "Erro ao buscar autores"}), 500
        finally:
            cur.close()
            conn.close()

    elif request.method == 'POST':
        try:
            dados = request.get_json()
            if not dados or 'nome' not in dados:
                return jsonify({"erro": "Nome do autor é obrigatório"}), 400

            nome = dados['nome']
            nacionalidade = dados.get('nacionalidade')

            cur.execute(
                "INSERT INTO autor (nome, nacionalidade) VALUES (%s, %s) RETURNING autor_id;",
                (nome, nacionalidade)
            )
            autor_id = cur.fetchone()[0]
            conn.commit()

            return jsonify({"mensagem": "Autor criado com sucesso!", "autor_id": autor_id}), 201
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao criar autor: {e}")
            return jsonify({"erro": "Erro ao criar autor", "detalhes": str(e)}), 500
        finally:
            cur.close()
            conn.close()


# Rota para listar editoras e adicionar uma nova editora
@app.route('/editoras', methods=['GET', 'POST'])
def handle_editoras():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"erro": "Não foi possível conectar ao banco de dados"}), 500

    cur = conn.cursor()

    if request.method == 'GET':
        try:
            cur.execute("SELECT editora_id, nome, cidade FROM editora;")
            editoras = cur.fetchall()

            editoras_list = []
            for editora in editoras:
                editoras_list.append({
                    "editora_id": editora[0],
                    "nome": editora[1],
                    "cidade": editora[2]
                })

            return jsonify(editoras_list)
        except Exception as e:
            logging.error(f"Erro ao listar editoras: {e}")
            return jsonify({"erro": "Erro ao buscar editoras"}), 500
        finally:
            cur.close()
            conn.close()

    elif request.method == 'POST':
        try:
            dados = request.get_json()
            if not dados or 'nome' not in dados:
                return jsonify({"erro": "Nome da editora é obrigatório"}), 400

            nome = dados['nome']
            cidade = dados.get('cidade')

            cur.execute(
                "INSERT INTO editora (nome, cidade) VALUES (%s, %s) RETURNING editora_id;",
                (nome, cidade)
            )
            editora_id = cur.fetchone()[0]
            conn.commit()

            return jsonify({"mensagem": "Editora criada com sucesso!", "editora_id": editora_id}), 201
        except Exception as e:
            conn.rollback()
            logging.error(f"Erro ao criar editora: {e}")
            return jsonify({"erro": "Erro ao criar editora", "detalhes": str(e)}), 500
        finally:
            cur.close()
            conn.close()


if __name__ == '__main__':
    # Define o host para 0.0.0.0 para que a aplicação seja acessível de fora do localhost
    app.run(host='0.0.0.0', port=5000, debug=True)
