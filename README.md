## uso
para salvar uma senha (o sistema vai pedir sua senha mestra)
```bash
python cli.py set projeto.db.senha "root123"
```

para ler a senha salva:
```bash
python cli.py get projeto.db.senha
```

## roadmap
* [x] criptografia segura com aes-256 e pbkdf2
* [x] salvar e ler os dados no disco local
* [ ] ler os arquivos de configuracao do projeto (.registry.yml)
* [ ] criar o comando `run` para injetar a senha direto nos processos