-- Tabela autor
CREATE TABLE autor (
autor_id SERIAL PRIMARY KEY,
nome VARCHAR(100) NOT NULL,
nacionalidade VARCHAR(50)
);

-- Tabela editora
CREATE TABLE editora (
editora_id SERIAL PRIMARY KEY,
nome VARCHAR(100) NOT NULL,
cidade VARCHAR(100)
);

-- Inserir dados na tabela autor
INSERT INTO autor (nome, nacionalidade) VALUES ('Gabriel García Márquez', 'Colombiano');
INSERT INTO autor (nome, nacionalidade) VALUES ('J.K. Rowling', 'Britânica');
INSERT INTO autor (nome, nacionalidade) VALUES ('George Orwell', 'Britânico');
INSERT INTO autor (nome, nacionalidade) VALUES ('Margaret Atwood', 'Canadense');

-- Inserir dados na tabela editora
INSERT INTO editora (nome, cidade) VALUES ('Companhia das Letras', 'São Paulo');
INSERT INTO editora (nome, cidade) VALUES ('Penguin Books', 'Londres');
INSERT INTO editora (nome, cidade) VALUES ('Editora Rocco', 'Rio de Janeiro');
INSERT INTO editora (nome, cidade) VALUES ('HarperCollins', 'Nova York');

-- Correção de Permissões
-- Conceder permissão de uso em todas as sequências no schema public para o grupo API6BD.
-- Isso é necessário para que a inserção de dados em colunas SERIAL funcione.
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO API6BD;