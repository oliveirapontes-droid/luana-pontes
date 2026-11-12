# caso09_monitoramento.py
import json
from conexao import conectar, executar

LIMITE_DISCO = 80
LIMITE_CARGA = 2.0


def verificar_dispositivo(disp):
    cliente = conectar(disp)
    try:
        # Coleta ocupação do disco (/), carga média (1 min) e status do sshd
        cod_d, saida_disco, _ = executar(
            cliente, "df --output=pcent / | tail -1 | tr -d ' %'"
        )
        cod_c, saida_carga, _ = executar(
            cliente, "awk '{print $1}' /proc/loadavg"
        )
        cod_s, _, _ = executar(cliente, "pgrep -x sshd")

        if cod_d != 0 or cod_c != 0:
            return {
                "nome": disp["nome"],
                "disco": "-",
                "carga": "-",
                "sshd": "ERRO",
                "status": "FALHA",
                "detalhe": "erro ao coletar metricas",
            }

        disco = int(saida_disco)
        carga = float(saida_carga)
        sshd_ativo = cod_s == 0

        alertas = []
        if disco > LIMITE_DISCO:
            alertas.append(f"disco {disco}% > {LIMITE_DISCO}%")
        if carga > LIMITE_CARGA:
            alertas.append(f"carga {carga:.2f} > {LIMITE_CARGA}")

        if not sshd_ativo:
            status = "FALHA"
            detalhe = "servico sshd inativo"
        elif alertas:
            status = "ALERTA"
            detalhe = ", ".join(alertas)
        else:
            status = "OK"
            detalhe = "dentro dos limiares"

        return {
            "nome": disp["nome"],
            "disco": f"{disco}%",
            "carga": f"{carga:.2f}",
            "sshd": "ATIVO" if sshd_ativo else "INATIVO",
            "status": status,
            "detalhe": detalhe,
        }
    finally:
        cliente.close()


with open("inventario.json", encoding="utf-8") as f:
    inventario = json.load(f)

resultados = []
for disp in inventario:
    try:
        resultados.append(verificar_dispositivo(disp))
    except Exception as e:
        resultados.append({
            "nome": disp["nome"],
            "disco": "-",
            "carga": "-",
            "sshd": "-",
            "status": "FALHA",
            "detalhe": f"{type(e).__name__}: {e}",
        })

print("=" * 72)
print("PAINEL DE MONITORAMENTO DE SAUDE DOS EQUIPAMENTOS")
print("=" * 72)
print(
    f"{'DISP':<6} {'DISCO':<8} {'CARGA(1m)':<11} {'SSHD':<9} {'STATUS':<8}"
    " DETALHES"
)
print("-" * 72)
for r in resultados:
    print(
        f"{r['nome']:<6} {r['disco']:<8} {r['carga']:<11} {r['sshd']:<9}"
        f" {r['status']:<8} {r['detalhe']}"
    )
print("-" * 72)

totais = {
    s: sum(1 for r in resultados if r["status"] == s)
    for s in ("OK", "ALERTA", "FALHA")
}
print(
    f"Resumo: {totais['OK']} OK | {totais['ALERTA']} ALERTA |"
    f" {totais['FALHA']} FALHA (Total: {len(resultados)})"
)