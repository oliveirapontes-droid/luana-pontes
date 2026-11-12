# Caso 3 — Autenticação por Chave Pública (SSH)

## Comandos utilizados no WSL

1. Geração do par de chaves Ed25519 sem passphrase:

    ssh-keygen -t ed25519 -f ~/.ssh/id_redes -C "gerente-redes" -N ""

2. Instalação da chave pública nos dispositivos simulados (r1, r2 e r3):

    for u in r1 r2 r3; do
        ssh-copy-id -i ~/.ssh/id_redes.pub $u@127.0.0.1
    done

3. Execução do script de validação:

    python caso03_chaves.py

## Pergunta de Reflexão

- **Se um atacante copiar o arquivo da chave pública, ele consegue acessar os equipamentos?**
  Não. A chave pública pode ser copiada e compartilhada sem risco, pois serve apenas para verificar a identidade no servidor (~/.ssh/authorized_keys), e não para provê-la.

- **E se copiar a chave privada?**
  Sim. A chave privada equivale a uma senha permanente e concede acesso total aos equipamentos. Por isso, ela deve ter permissão 600 e, em ambientes reais, ser protegida por passphrase.
  