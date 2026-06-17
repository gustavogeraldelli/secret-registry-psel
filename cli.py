import os, json, base64, argparse, getpass
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag
import yaml

class Registry:
    """Gerencia o armazenamento e a criptografia dos segredos no disco local"""
    
    def __init__(self, base_dir: Path):
        self.arquivo = base_dir / "vault.json"
        if not base_dir.exists():
            base_dir.mkdir(parents=True)

    def _trancar(self, senha: str, texto: str) -> dict:
        """Auxiliar que criptografa o texto e retorna um dicionário com os dados codificados em base64"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        
        aes = AESGCM(kdf.derive(senha.encode()))
        nonce = os.urandom(12)
        ciphertext = aes.encrypt(nonce, texto.encode(), None)
        
        return {
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode()
        }

    def _destrancar(self, senha: str, dados: dict) -> str:
        """Auxiliar que decodifica os dados em base64 e reverte a cifra usando a senha fornecida"""
        salt = base64.b64decode(dados["salt"])
        nonce = base64.b64decode(dados["nonce"])
        ciphertext = base64.b64decode(dados["ciphertext"])
        
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        aes = AESGCM(kdf.derive(senha.encode()))
        
        try:
            return aes.decrypt(nonce, ciphertext, None).decode()
        except InvalidTag:
            raise PermissionError("senha incorreta ou arquivo adulterado.")

    def init(self, senha: str):
        """Inicializa o cofre criando a senha mestra"""
        if self.arquivo.exists():
            raise ValueError("o cofre ja foi inicializado antes.")
            
        dados = {"__verify__": self._trancar(senha, "ok")}
        with open(self.arquivo, 'w') as f:
            json.dump(dados, f, indent=2)

    def set(self, senha: str, chave: str, valor: str):
        """Valida a senha e guarda uma nova chave criptografada no registry"""
        if chave.startswith("__"):
            raise ValueError("chaves com '__' sao reservadas pelo sistema.")
        if not self.arquivo.exists():
            raise ValueError("cofre nao inicializado. rode 'init' primeiro.")

        with open(self.arquivo, 'r') as f:
            dados = json.load(f)

        self._destrancar(senha, dados["__verify__"]) 
        
        dados[chave] = self._trancar(senha, valor)
        with open(self.arquivo, 'w') as f:
            json.dump(dados, f, indent=2)

    def get(self, senha: str, chave: str) -> str:
        """Valida a senha e recupera um segredo previamente armazenado."""
        if chave.startswith("__"):
            raise ValueError("acesso negado a chaves internas.")
        if not self.arquivo.exists():
            raise ValueError("cofre nao inicializado. rode 'init' primeiro.")

        with open(self.arquivo, 'r') as f:
            dados = json.load(f)

        self._destrancar(senha, dados["__verify__"])
        
        if chave not in dados:
            raise KeyError(f"chave '{chave}' nao existe no cofre.")
            
        return self._destrancar(senha, dados[chave])

def ler_yml(caminho: Path) -> dict:
    """Lê o arquivo de configuração e retorna o bloco de variáveis de ambiente."""
    if not caminho.exists():
        raise FileNotFoundError("arquivo .registry.yml nao encontrado nesta pasta.")
    
    with open(caminho, 'r') as f:
        config = yaml.safe_load(f) or {}
    return config.get("env", {})

def extrair_segredos_do_yml(env_vars: dict, registry: Registry) -> dict:
    """Faz o parse das variáveis, pede a senha mestra se necessário e extrai do cofre."""
    normais = []
    segredos_pendentes = []

    for chave_env, valor_yml in env_vars.items():
        if str(valor_yml).startswith("secret:"):
            nome_segredo = str(valor_yml).split("secret:")[1]
            segredos_pendentes.append((chave_env, nome_segredo))
        else:
            normais.append(chave_env)

    print(f"leitura do .registry.yml concluida: {len(normais)} variaveis estaticas, {len(segredos_pendentes)} segredos pendentes.")
    
    if not segredos_pendentes:
        return {}
    
    senha = getpass.getpass("senha mestra: ")
    
    segredos_extraidos = {}
    for chave_env, chave_vault in segredos_pendentes:
        segredos_extraidos[chave_env] = registry.get(senha, chave_vault)
        
    return segredos_extraidos

def main():
    parser = argparse.ArgumentParser(description="cofre local para segredos")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    subparsers.add_parser("init", help="inicializa o cofre")
    
    cmd_set = subparsers.add_parser("set", help="guarda um segredo")
    cmd_set.add_argument("chave")
    cmd_set.add_argument("valor")

    cmd_get = subparsers.add_parser("get", help="le um segredo")
    cmd_get.add_argument("chave")

    cmd_run = subparsers.add_parser("run", help="le o yml e mapeia os segredos pendentes")
    cmd_run.add_argument("comando_alvo", nargs=argparse.REMAINDER) 

    args = parser.parse_args()
    registry = Registry(Path.home() / ".sec-registry")

    try:
        if args.comando == "init":
            senha = getpass.getpass("crie a senha mestra: ")
            if senha != getpass.getpass("confirme a senha: "):
                print("erro: as senhas nao batem.")
                return
            registry.init(senha)
            print("cofre inicializado.")

        elif args.comando == "set":
            senha = getpass.getpass("senha mestra: ")
            registry.set(senha, args.chave, args.valor)
            print(f"ok. '{args.chave}' guardado.")

        elif args.comando == "get":
            senha = getpass.getpass("senha mestra: ")
            print(registry.get(senha, args.chave))

        elif args.comando == "run":
            ym_path = Path(".registry.yml")
            env_vars = ler_yml(ym_path)
            
            segredos_extraidos = extrair_segredos_do_yml(env_vars, registry)
            
            if segredos_extraidos:
                print("secrets a injetar:")
                for chave, valor in segredos_extraidos.items():
                    print(f"\t{chave}={valor}")

    except Exception as e:
        print(f"erro: {str(e)}")

if __name__ == "__main__":
    main()