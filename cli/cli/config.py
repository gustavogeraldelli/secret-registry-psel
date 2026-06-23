import json
from pathlib import Path

def carregar_config() -> dict:
    """Lê as configurações globais da CLI na máquina do usuário."""
    config_path = Path.home() / ".sec-registry" / "config.json"
    
    config_padrao = {
        "modo": "local",
        "api_url": "",
        "token": ""
    }

    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_padrao

    with open(config_path, 'r') as f:
        try:
            config_usuario = json.load(f)
            return {**config_padrao, **config_usuario}
        except json.JSONDecodeError:
            return config_padrao