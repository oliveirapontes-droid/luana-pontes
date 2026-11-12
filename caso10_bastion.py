# caso10_bastion.py
import os
import paramiko
from conexao import conectar, executar

bastion = {
    "nome": "BASTION",
    "host": "127.0.0.1",
    "porta": 22,
    "usuario": "bastion",
}

interno = {
    "nome": "R1-INTERNO",
    "host": "127.0.0.1",
    "porta": 2222,
    "usuario": "r1",
}

salto = conectar(bastion)
try:
    _, user_salto, _ = executar(salto, "whoami")
    print(f"[1] Conectado ao servidor de salto como '{user_salto}' (porta 22)")

    # Abre um túnel TCP encaminhado pelo bastion até 127.0.0.1:2222
    transporte = salto.get_transport()
    canal = transporte.open_channel(
        "direct-tcpip",
        (interno["host"], interno["porta"]),
        ("127.0.0.1", 0),
    )

    cliente_interno = paramiko.SSHClient()
    cliente_interno.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cliente_interno.connect(
        hostname=interno["host"],
        port=interno["porta"],
        username=interno["usuario"],
        password=os.environ["SSH_SENHA"],
        sock=canal,
    )
    try:
        _, host_int, _ = executar(cliente_interno, "hostname")
        _, user_int, _ = executar(cliente_interno, "whoami")
        _, ssh_conn, _ = executar(cliente_interno, "echo $SSH_CONNECTION")

        print(f"[2] Tunel estabelecido via {bastion['usuario']}@{bastion['host']}:22 -> {interno['host']}:{interno['porta']}")
        print(f"    hostname       : {host_int}")
        print(f"    whoami         : {user_int}")
        print(f"    SSH_CONNECTION : {ssh_conn}")
    finally:
        cliente_interno.close()
finally:
    salto.close()