-- 1. Dimensão: Categorias de Produtos
CREATE TABLE categorias (
    id_categoria SERIAL PRIMARY KEY,
    nome_categoria VARCHAR(100) NOT NULL
);

-- 2. Dimensão: Produtos
CREATE TABLE produtos (
    id_produto SERIAL PRIMARY KEY,
    id_categoria INT REFERENCES categorias(id_categoria),
    nome_produto VARCHAR(200) NOT NULL,
    preco_base DECIMAL(10,2) NOT NULL
);

-- 3. Dimensão: Clientes
CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    data_cadastro DATE NOT NULL
);

-- 4. Dimensão/Apoio: Endereços dos Clientes
CREATE TABLE enderecos (
    id_endereco SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES clientes(id_cliente),
    estado VARCHAR(50) NOT NULL,
    cidade VARCHAR(100) NOT NULL
);

-- 5. Dimensão: Lojas Físicas/Filiais
CREATE TABLE lojas (
    id_loja SERIAL PRIMARY KEY,
    nome_loja VARCHAR(100) NOT NULL,
    estado_loja VARCHAR(50) NOT NULL
);

-- 6. Dimensão: Vendedores
CREATE TABLE vendedores (
    id_vendedor SERIAL PRIMARY KEY,
    id_loja INT REFERENCES lojas(id_loja),
    nome_vendedor VARCHAR(150) NOT NULL
);

-- 7. Dimensão: Métodos de Pagamento
CREATE TABLE metodos_pagamento (
    id_metodo SERIAL PRIMARY KEY,
    tipo_pagamento VARCHAR(50) NOT NULL -- Ex: PIX, Cartão de Crédito, Boleto
);

-- 8. FATO PRINCIPAL: Pedidos (Vai receber +10.000 linhas)
CREATE TABLE pedidos (
    id_pedido SERIAL PRIMARY KEY,
    id_cliente INT REFERENCES clientes(id_cliente),
    id_loja INT REFERENCES lojas(id_loja),
    id_vendedor INT REFERENCES vendedores(id_vendedor),
    data_pedido TIMESTAMP NOT NULL,
    status_pedido VARCHAR(50) NOT NULL
);

-- 9. FATO PRINCIPAL: Itens do Pedido (Vai receber +10.000 linhas)
CREATE TABLE itens_pedido (
    id_item SERIAL PRIMARY KEY,
    id_pedido INT REFERENCES pedidos(id_pedido),
    id_produto INT REFERENCES produtos(id_produto),
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10,2) NOT NULL
);

-- 10. FATO/Apoio: Pagamentos dos Pedidos
CREATE TABLE pagamentos_pedido (
    id_pagamento SERIAL PRIMARY KEY,
    id_pedido INT REFERENCES pedidos(id_pedido),
    id_metodo INT REFERENCES metodos_pagamento(id_metodo),
    valor_pago DECIMAL(10,2) NOT NULL,
    data_pagamento TIMESTAMP NOT NULL
);