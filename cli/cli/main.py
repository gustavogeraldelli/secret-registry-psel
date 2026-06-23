import argparse
import getpass
import os
from pathlib import Path

from core.registry import Registry
from core.storage import LocalFileStorage, RemoteApiStorage
from core.exceptions import VaultError
from cli.parser import ler_yml, separar_variaveis
from cli.injector import executar_com_ambiente
from cli.config import carregar_config

import keyring
import json
import requests

SERVICO = "sec-registry"
USUARIO = "master-key"

def get_password(prompt: str = "senha mestra: ", force_prompt: bool = False) -> str:
    if not force_prompt:
        senha_env = os.environ.get("SEC_REGISTRY_PASSWORD")
        if senha_env:
            return senha_env

        try:
            senha_salva = keyring.get_password(SERVICO, USUARIO)
            if senha_salva:
                return senha_salva
        except Exception:
            pass

    senha_digitada = getpass.getpass(prompt)
    
    # salva a senha digitada para não pedir repetidamente
    try:
        keyring.set_password(SERVICO, USUARIO, senha_digitada)
    except Exception:
        pass
        
    return senha_digitada


def login():
    """autentica na api remota e salva o token de acesso no config.json."""
    url = input("url da api: ").strip("/")
    senha = getpass.getpass("senha do servidor: ")

    try:
        resposta = requests.post(f"{url}/auth", json={"senha": senha}, timeout=5)
        resposta.raise_for_status()
        
        config = {
            "modo": "remoto",
            "api_url": url,
            "token": resposta.json()["access_token"]
        }
        
        dir_config = Path.home() / ".sec-registry"
        dir_config.mkdir(exist_ok=True)
        
        with open(dir_config / "config.json", "w") as f:
            json.dump(config, f, indent=2)
            
        print("login efetuado. modo remoto ativado.")
        
    except requests.exceptions.RequestException:
        print("erro: falha na conexao ou senha invalida.")

def main():
    parser = argparse.ArgumentParser(description="cofre local e remoto para secrets")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    subparsers.add_parser("init", help="inicializa o cofre")
    
    cmd_set = subparsers.add_parser("set", help="guarda um segredo")
    cmd_set.add_argument("chave")
    cmd_set.add_argument("valor")

    cmd_get = subparsers.add_parser("get", help="le um segredo")
    cmd_get.add_argument("chave")

    cmd_run = subparsers.add_parser("run", help="le o yml e mapeia os secrets")
    cmd_run.add_argument("comando_alvo", nargs=argparse.REMAINDER) 

    subparsers.add_parser("login", help="conecta com a API remota")
    
    cmd_mode = subparsers.add_parser("mode", help="alterna entre modo local e remoto")
    cmd_mode.add_argument("tipo", choices=["local", "remoto"], help="escolha 'local' ou 'remoto'")
    
    args = parser.parse_args()

    if args.comando == "login":
        login()
        return
    
    if args.comando == "mode":
        dir_config = Path.home() / ".sec-registry"
        arquivo_config = dir_config / "config.json"
        
        if not arquivo_config.exists():
            dir_config.mkdir(exist_ok=True)
            config = {"modo": args.tipo}
        else:
            with open(arquivo_config, "r") as f:
                config = json.load(f)
            config["modo"] = args.tipo
            
        with open(arquivo_config, "w") as f:
            json.dump(config, f, indent=2)
            
        print(f"modo alterado para: {args.tipo}")
        return

    config = carregar_config()

    # qual implementação de Storage usar baseado na config
    if config.get("modo") == "remoto":
        if not config.get("api_url") or not config.get("token"):
            print("erro: modo remoto ativado, mas api_url ou token faltam no config.json")
            return
        storage = RemoteApiStorage(config["api_url"], config["token"])
    else:
        storage = LocalFileStorage(Path.home() / ".sec-registry")

    registry = Registry(storage)

    try:
        if args.comando == "init":
            senha = get_password("crie a senha mestra: ", force_prompt=True)
            if not os.environ.get("SEC_REGISTRY_PASSWORD"):
                if senha != getpass.getpass("confirme a senha: "):
                    print("erro: as senhas nao batem.")
                    return
            registry.init(senha)
            print("cofre inicializado.")

        elif args.comando == "set":
            senha = get_password()
            registry.set(senha, args.chave, args.valor)
            print(f"secret '{args.chave}' guardado.")

        elif args.comando == "get":
            senha = get_password()
            print(registry.get(senha, args.chave))

        elif args.comando == "run":
            if not args.comando_alvo:
                print("erro: especifique o comando a executar. ex: cli.py run npm start")
                return
            
            yml_path = Path(".registry.yml")
            env_vars = ler_yml(yml_path)
            
            estaticas, secrets_pendentes = separar_variaveis(env_vars)
            print(f"leitura concluida: {len(estaticas)} vars estaticas, {len(secrets_pendentes)} secrets.")

            secrets_extraidos = {}
            if secrets_pendentes:
                senha = get_password()
                for chave_env, chave_vault in secrets_pendentes:
                    secrets_extraidos[chave_env] = registry.get(senha, chave_vault)
            
            novas_variaveis = {**estaticas, **secrets_extraidos}
            executar_com_ambiente(args.comando_alvo, novas_variaveis)
        
    except VaultError as e:
        print(f"erro no cofre: {str(e)}")
    except Exception as e:
        print(f"erro: {str(e)}")

if __name__ == "__main__":
    main()