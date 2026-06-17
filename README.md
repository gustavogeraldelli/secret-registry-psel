## secret registry
Cofre que guarda segredos criptografados a partir de uma senha mestra.

## Funcionamento
Ao rodar o comando `run`, a CLI lê o arquivo `.registry.yml`, identifica as chaves marcadas com `secret:`, busca os valores correspondentes no cofre e injeta tudo em memória para o processo alvo.

## comandos
- `init`: inicializa o registry com a senha mestra
- `set <chave> <valor>`: salva um secret criptografado
- `get <chave>`: recupera um secret
- `run <comando>`: executa um processo com secrets injetados

## roadmap
* [x] criptografia segura com aes-256 e pbkdf2
* [x] salvar e ler os dados no disco local
* [x] ler os arquivos de configuracao do projeto (.registry.yml)
* [x] criar o comando `run` para extrair segredos do cofre
* [ ] injetar segredos diretamente nos processos (subprocess)