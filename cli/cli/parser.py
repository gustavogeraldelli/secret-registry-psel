import yaml
from pathlib import Path

def ler_yml(caminho: Path) -> dict:
    """Lê o arquivo de configuração e retorna o bloco de variáveis de ambiente."""
    if not caminho.exists():
        raise FileNotFoundError("arquivo .registry.yml nao encontrado nesta pasta.")
    
    with open(caminho, 'r') as f:
        config = yaml.safe_load(f) or {}
    return config.get("env", {})

def separar_variaveis(env_vars: dict) -> tuple[dict, list]:
    """
    Separa as variáveis normais dos segredos.
    """
    estaticas = {}
    secrets_pendentes = []

    for chave_env, valor_yml in env_vars.items():
        if str(valor_yml).startswith("secret:"):
            nome_segredo = str(valor_yml).split("secret:")[1]
            secrets_pendentes.append((chave_env, nome_segredo))
        else:
            estaticas[chave_env] = str(valor_yml)

    return estaticas, secrets_pendentes