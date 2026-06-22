import pandas as pd
from faker import Faker
import random
from datetime import datetime
from sqlalchemy import create_engine

fake = Faker('pt_BR')

print("🚀 Iniciando a geração de dados massivos...\n")

categorias = ['Eletrônicos', 'Vestuário', 'Livros', 'Casa e Decoração', 'Beleza', 'Esportes', 'Brinquedos', 'Alimentos', 'Ferramentas', 'Automotivo']
df_categorias = pd.DataFrame({'id_categoria': range(1, len(categorias) + 1), 'nome_categoria': categorias})

df_lojas = pd.DataFrame({
    'id_loja': [1, 2, 3, 4, 5],
    'nome_loja': ['Matriz SP', 'Filial RJ', 'Filial SC', 'Filial MG', 'Filial RS'],
    'estado_loja': ['SP', 'RJ', 'SC', 'MG', 'RS']
})

df_metodos = pd.DataFrame({
    'id_metodo': [1, 2, 3, 4],
    'tipo_pagamento': ['PIX', 'Cartão de Crédito', 'Boleto', 'Cartão de Débito']
})

clientes_data = []
for i in range(1, 501):
    clientes_data.append({
        'id_cliente': i,
        'nome_completo': fake.name(),
        'cpf': fake.cpf(),
        'email': fake.unique.email(),
        'data_cadastro': fake.date_between(start_date='-3y', end_date='today')
    })
df_clientes = pd.DataFrame(clientes_data)

# NOVO: Geração da tabela de endereços vinculada aos clientes criados acima
enderecos_data = []
for cliente in clientes_data:
    enderecos_data.append({
        'id_endereco': cliente['id_cliente'],
        'id_cliente': cliente['id_cliente'],
        'estado': fake.state_abbr(),
        'cidade': fake.city()
    })
df_enderecos = pd.DataFrame(enderecos_data)

produtos_data = []
for i in range(1, 101):
    produtos_data.append({
        'id_produto': i,
        'id_categoria': random.choice(df_categorias['id_categoria'].tolist()),
        'nome_produto': f"{fake.word().capitalize()} {fake.word().capitalize()}",
        'preco_base': round(random.uniform(10.0, 1500.0), 2)
    })
df_produtos = pd.DataFrame(produtos_data)

vendedores_data = []
for i in range(1, 21):
    vendedores_data.append({
        'id_vendedor': i,
        'id_loja': random.choice(df_lojas['id_loja'].tolist()),
        'nome_vendedor': fake.name()
    })
df_vendedores = pd.DataFrame(vendedores_data)

qtd_pedidos = 10500
pedidos_data = []
itens_pedido_data = []
pagamentos_data = []

id_item_global = 1
id_pagamento_global = 1

print("⏳ Gerando 10.500 Pedidos e seus respectivos Itens...")

for id_pedido in range(1, qtd_pedidos + 1):
    data_pedido = fake.date_time_between(start_date='-3y', end_date='now')
    
    pedidos_data.append({
        'id_pedido': id_pedido,
        'id_cliente': random.choice(df_clientes['id_cliente'].tolist()),
        'id_loja': random.choice(df_lojas['id_loja'].tolist()),
        'id_vendedor': random.choice(df_vendedores['id_vendedor'].tolist()),
        'data_pedido': data_pedido,
        'status_pedido': random.choices(['Concluído', 'Pendente', 'Cancelado'], weights=[80, 15, 5])[0]
    })
    
    qtd_itens = random.randint(1, 4)
    valor_total_pedido = 0
    
    for _ in range(qtd_itens):
        produto_escolhido = random.choice(produtos_data)
        qtd = random.randint(1, 3)
        preco_unit = produto_escolhido['preco_base']
        valor_total_pedido += (qtd * preco_unit)
        
        itens_pedido_data.append({
            'id_item': id_item_global,
            'id_pedido': id_pedido,
            'id_produto': produto_escolhido['id_produto'],
            'quantidade': qtd,
            'preco_unitario': preco_unit
        })
        id_item_global += 1
        
    pagamentos_data.append({
        'id_pagamento': id_pagamento_global,
        'id_pedido': id_pedido,
        'id_metodo': random.choice(df_metodos['id_metodo'].tolist()),
        'valor_pago': round(valor_total_pedido, 2),
        'data_pagamento': data_pedido
    })
    id_pagamento_global += 1

df_pedidos = pd.DataFrame(pedidos_data)
df_itens_pedido = pd.DataFrame(itens_pedido_data)
df_pagamentos = pd.DataFrame(pagamentos_data)

print("✅ Geração concluída com sucesso!\n")
print("📊 Resumo do volume de dados gerado:")
print(f"- Pedidos: {len(df_pedidos)} linhas")
print(f"- Itens de Pedido: {len(df_itens_pedido)} linhas")
print(f"- Pagamentos: {len(df_pagamentos)} linhas")
print(f"- Clientes: {len(df_clientes)} linhas")
print(f"- Endereços: {len(df_enderecos)} linhas")
print(f"- Produtos: {len(df_produtos)} linhas")

print("\n🔌 Preparando conexão com o banco de dados...")

DB_USER = "postgres"
DB_PASS = "admin123"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "ecommerce_db"

engine_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(engine_url)

print("📤 Injetando dados nas tabelas do PostgreSQL...")

try:
    df_categorias.to_sql('categorias', engine, if_exists='append', index=False)
    df_lojas.to_sql('lojas', engine, if_exists='append', index=False)
    df_metodos.to_sql('metodos_pagamento', engine, if_exists='append', index=False)
    df_clientes.to_sql('clientes', engine, if_exists='append', index=False)
    # NOVO: Injeção da tabela de endereços
    df_enderecos.to_sql('enderecos', engine, if_exists='append', index=False)
    df_produtos.to_sql('produtos', engine, if_exists='append', index=False)
    df_vendedores.to_sql('vendedores', engine, if_exists='append', index=False)
    
    df_pedidos.to_sql('pedidos', engine, if_exists='append', index=False)
    df_itens_pedido.to_sql('itens_pedido', engine, if_exists='append', index=False)
    df_pagamentos.to_sql('pagamentos_pedido', engine, if_exists='append', index=False)
    
    print("✅ Sucesso! Todas as 10 tabelas foram populadas no banco de origem.")
except Exception as e:
    print(f"⚠️ Aviso: O banco de dados ainda não está acessível no host configurado.")
    print(f"Erro original: {e}")