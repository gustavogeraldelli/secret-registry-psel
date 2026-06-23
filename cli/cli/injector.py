import os
import subprocess

def executar_com_ambiente(comando_alvo: list, novas_variaveis: dict):
    """Cria um ambiente isolado com o OS atual com os segredos e executa o comando."""
    env_isolado = os.environ.copy()
    env_isolado.update(novas_variaveis)
    
    try:
        subprocess.run(comando_alvo, env=env_isolado)
    except FileNotFoundError:
        print(f"erro: comando '{comando_alvo[0]}' nao encontrado no sistema.")
    except Exception as e:
        print(f"erro na execucao do processo: {str(e)}")