import os, json, base64, argparse, getpass
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidTag

registry_dir = Path.home() / ".sec-registry"
vault_path = registry_dir / "vault.json"

def get_chave(senha: str, salt: bytes = None):
    """
    Deriva a chave AES usando PBKDF2.
    Se nenhum salt for fornecido, gera um novo aleatório.
    """
    if not salt:
        salt = os.urandom(16)
        
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return kdf.derive(senha.encode()), salt

def trancar(senha: str, texto: str):
    """
    Cifra o texto usando AES-GCM.
    Retorna o salt, nonce e o ciphertext.
    """
    chave, salt = get_chave(senha)
    aesgcm = AESGCM(chave)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, texto.encode(), None)
    return salt, nonce, ciphertext

def destrancar(senha: str, salt: bytes, nonce: bytes, ciphertext: bytes):
    """
    Tenta decifrar o texto cifrado.
    Retorna None se a tag de integridade falhar.
    """
    chave, _ = get_chave(senha, salt)
    aesgcm = AESGCM(chave)
    try:
        texto = aesgcm.decrypt(nonce, ciphertext, None)
        return texto.decode()
    except InvalidTag:
        return None

def salvar_no_disco(chave_nome: str, salt: bytes, nonce: bytes, ciphertext: bytes):
    """
    Guarda os bytes convertidos para Base64 no arquivo JSON.
    Cria a estrutura de diretórios se não existir.
    """
    if not registry_dir.exists():
        registry_dir.mkdir(parents=True)
        
    dados = {}
    if vault_path.exists():
        with open(vault_path, 'r') as f:
            try:
                dados = json.load(f)
            except json.JSONDecodeError:
                dados = {}
            
    dados[chave_nome] = {
        "salt": base64.b64encode(salt).decode('utf-8'),
        "nonce": base64.b64encode(nonce).decode('utf-8'),
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
    }
    
    with open(vault_path, 'w') as f:
        json.dump(dados, f, indent=2)

def ler_do_disco(chave_nome: str):
    """
    Lê do arquivo JSON e devolve a tupla de bytes originais.
    Retorna None se a chave não for encontrada.
    """
    if not vault_path.exists():
        return None
        
    with open(vault_path, 'r') as f:
        try:
            dados = json.load(f)
        except json.JSONDecodeError:
            return None
        
    if chave_nome not in dados:
        return None
        
    reg = dados[chave_nome]
    return (
        base64.b64decode(reg["salt"]),
        base64.b64decode(reg["nonce"]),
        base64.b64decode(reg["ciphertext"])
    )

def main():
    parser = argparse.ArgumentParser(description="cofre local para segredos")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    set_parser = subparsers.add_parser("set", help="guarda um segredo")
    set_parser.add_argument("chave", help="nome da chave (ex: db_pass)")
    set_parser.add_argument("valor", help="a chave em si")

    get_parser = subparsers.add_parser("get", help="le um segredo")
    get_parser.add_argument("chave", help="nome da chave que quer ler")

    args = parser.parse_args()

    if args.comando == "set":
        senha = getpass.getpass("senha mestra: ")
        if not senha:
            print("senha nao pode ser vazia")
            return

        salt, nonce, ciphertext = trancar(senha, args.valor)
        salvar_no_disco(args.chave, salt, nonce, ciphertext)
        print(f"ok. segredo '{args.chave}' trancado no cofre.")

    elif args.comando == "get":
        dados = ler_do_disco(args.chave)
        if not dados:
            print(f"chave '{args.chave}' nao encontrada no disco")
            return
            
        salt, nonce, ciphertext = dados
        senha = getpass.getpass("senha mestra pra destrancar: ")
        
        texto_limpo = destrancar(senha, salt, nonce, ciphertext)
        if texto_limpo is None:
            print("erro: senha errada ou cofre adulterado")
        else:
            print(texto_limpo)

if __name__ == "__main__":
    main()