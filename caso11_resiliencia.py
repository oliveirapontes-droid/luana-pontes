# caso11_resiliencia.py
import os
import socket
import time
import paramiko

MAX_TENTATIVAS = 3
TIMEOUT_CONEXAO = 2.0
SENHA_PADRAO = os.environ.get("SSH_SENHA", "Redes@2026")

inventario_teste = [
    {
        "nome": "R1-SAUDAVEL",
        "host": "127.0.0.1",
        "porta": 22,
        "usuario": "r1",
        "senha": SENHA_PADRAO,
    },
    {
        "nome": "R2-SENHA-ERRADA",
        "host": "127.0.0.1",
        "porta": 22,
        "usuario": "r2",
        "senha": "SenhaIncorreta@999",
    },
    {
        "nome": "R3-PORTA-FECHADA",
        "host": "127.0.0.1",
        "porta": 2299,
        "usuario": "r3",
        "senha": SENHA_PADRAO,
    },
    {
        "nome": "R4-INEXISTENTE",
        "host": "10.255.255.1",
        "porta": 22,
        "usuario": "r1",
        "senha": SENHA_PADRAO,
    },
]


def conectar_e_executar(disp):
    cliente = paramiko.SSHClient()
    cliente.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        cliente.connect(
            hostname=disp["host"],
            port=disp["porta"],
            username=disp["usuario"],
            password=disp["senha"],
            timeout=TIMEOUT_CONEXAO,
            banner_timeout=TIMEOUT_CONEXAO,
            auth_timeout=TIMEOUT_CONEXAO,
            look_for_keys=False,
            allow_agent=False,
        )
        _, stdout, _ = cliente.exec_command("hostname")
        return stdout.read().decode().strip()
    finally:
        cliente.close()


def testar_dispositivo(disp):
    tentativa = 0
    while tentativa < MAX_TENTATIVAS:
        tentativa += 1
        try:
            host_remoto = conectar_e_executar(disp)
            return {
                "nome": disp["nome"],
                "alvo": f"{disp['host']}:{disp['porta']}",
                "status": "OK",
                "tentativas": tentativa,
                "causa": f"Conectado com sucesso (hostname: {host_remoto})",
            }

        except paramiko.AuthenticationException:
            # Nunca repetir falha de autenticação para não bloquear a conta
            return {
                "nome": disp["nome"],
                "alvo": f"{disp['host']}:{disp['porta']}",
                "status": "ERRO_AUTENTICACAO",
                "tentativas": tentativa,
                "causa": "Credenciais invalidas ou senha expirada (retry abortado por seguranca).",
            }

        except (paramiko.ssh_exception.NoValidConnectionsError, ConnectionRefusedError) as e:
            erros_internos = getattr(e, "errors", {})
            if erros_internos and all(
                isinstance(err, (TimeoutError, socket.timeout))
                for err in erros_internos.values()
            ):
                if tentativa < MAX_TENTATIVAS:
                    espera = 2 ** (tentativa - 1)  # espera crescente: 1s, 2s...
                    print(
                        f"[{disp['nome']}] Timeout na tentativa {tentativa}/{MAX_TENTATIVAS}. "
                        f"Aguardando {espera}s..."
                    )
                    time.sleep(espera)
                    continue
                return {
                    "nome": disp["nome"],
                    "alvo": f"{disp['host']}:{disp['porta']}",
                    "status": "TIMEOUT",
                    "tentativas": tentativa,
                    "causa": "Host inacessivel/desligado ou pacotes descartados (DROP) por firewall.",
                }
            return {
                "nome": disp["nome"],
                "alvo": f"{disp['host']}:{disp['porta']}",
                "status": "CONEXAO_RECUSADA",
                "tentativas": tentativa,
                "causa": "Servico SSH parado na porta destino ou bloqueio ativo (REJECT) no firewall.",
            }

        except (TimeoutError, socket.timeout):
            # Retry com espera crescente apenas para falhas temporárias (timeout)
            if tentativa < MAX_TENTATIVAS:
                espera = 2 ** (tentativa - 1)  # espera crescente: 1s, 2s...
                print(
                    f"[{disp['nome']}] Timeout na tentativa {tentativa}/{MAX_TENTATIVAS}. "
                    f"Aguardando {espera}s..."
                )
                time.sleep(espera)
                continue
            return {
                "nome": disp["nome"],
                "alvo": f"{disp['host']}:{disp['porta']}",
                "status": "TIMEOUT",
                "tentativas": tentativa,
                "causa": "Host inexistente/desligado, falha de roteamento ou firewall descartando pacotes.",
            }

        except paramiko.SSHException as e:
            return {
                "nome": disp["nome"],
                "alvo": f"{disp['host']}:{disp['porta']}",
                "status": "ERRO_SSH",
                "tentativas": tentativa,
                "causa": f"Falha no protocolo SSH ({type(e).__name__}: {e}).",
            }

        except OSError as e:
            return {
                "nome": disp["nome"],
                "alvo": f"{disp['host']}:{disp['porta']}",
                "status": "ERRO_REDE",
                "tentativas": tentativa,
                "causa": f"Erro de rede/socket ({type(e).__name__}: {e}).",
            }


print("Iniciando testes de resiliencia...\n")
resultados = [testar_dispositivo(d) for d in inventario_teste]

linhas_relatorio = [
    "=" * 84,
    "RELATORIO DE AUTOMACAO RESILIENTE A FALHAS",
    "=" * 84,
]
for r in resultados:
    linhas_relatorio.append(
        f"[{r['nome']}] ({r['alvo']}) -> {r['status']} (tentativas: {r['tentativas']})"
    )
    linhas_relatorio.append(f"  Causa provavel: {r['causa']}")
linhas_relatorio.append("=" * 84)

texto_relatorio = "\n".join(linhas_relatorio)
print("\n" + texto_relatorio)

with open("relatorio_resiliencia.txt", "w", encoding="utf-8") as f:
    f.write(texto_relatorio + "\n")

print("\nRelatorio salvo em 'relatorio_resiliencia.txt'.")