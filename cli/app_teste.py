import os
print(f"Iniciando na porta: {os.environ.get('PORT')}")
print(f"Senha do banco injetada: {os.environ.get('DB_PASS')}")
