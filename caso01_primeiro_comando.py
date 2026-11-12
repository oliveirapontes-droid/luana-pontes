import conexao
import json

# Conectar-se ao equipamento `R1` do inventário

# Lendo o arquivo Json
with open('inventario.json', 'r', encoding='utf-8') as arquivo:
    dados = json.load(arquivo)

# 'dados' agora é um dicionário ou lista Python
cliente = conexao.conectar(dados[0])

# Executar whoami, hostname e uptime -p
comandos = [
    "whoami",
    "hostname",
    "uptime -p",
    "comando-inexistente"
]

# Exibir, para cada comando, o código de saída, a saída padrão e a saída de erro
for cmd in comandos:
    codigo, saida, erro = conexao.executar(cliente, cmd)
    print(f"---Comando: {cmd} ---")
    print(f"Código: {codigo}")
    print(f"Saída: {saida}")
    print(f"Erro: {erro}\n")

