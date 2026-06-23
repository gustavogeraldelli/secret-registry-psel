# Sec-Registry

O Sec-Registry é um cofre para armazenamento de segredos criptografados a partir de uma senha mestra. A ferramenta opera tanto de forma isolada no disco local quanto conectada a uma API remota.

### Arquitetura e Resumo

O sistema foi arquitetado utilizando inversão de dependência para isolar o motor de criptografia (AES-GCM com PBKDF2) da camada de persistência de dados. Isso permite que a ferramenta transite de forma transparente entre a manipulação de arquivos JSON locais e a comunicação via rede com o servidor central.

Na operação com a API remota, o cliente de rede implementa resiliência nativa. Chamadas HTTP são envelopadas com limites de timeout explícitos e um mecanismo de retentativas com backoff exponencial. Isso garante que a ferramenta não congele o terminal ou cause falhas prematuras em esteiras de CI/CD durante instabilidades de comunicação.

Para gerenciar a senha mestra sem prejudicar a experiência do desenvolvedor, o sistema atua em três camadas de resolução: primeiro busca por variáveis de ambiente (focado em automação), em seguida consulta o chaveiro nativo do sistema operacional (focado no uso local diário) e, como último recurso, aciona o prompt humano. 

A única exceção a este fluxo de resolução é o processo de inicialização do cofre, que é estritamente manual para evitar que scripts automatizados sobrescrevam dados existentes.

No processo de injeção, a ferramenta lê as instruções do arquivo `.registry.yml`, busca os segredos em tempo real e executa processos arbitrários injetando os valores de forma restrita na memória do sistema operacional, sem expor os dados em disco em nenhum momento.

### Comandos de Uso

A interação com a ferramenta ocorre através da interface de linha de comando principal.

`init`
Cria um cofre do zero e define a senha mestra. Este comando exige a digitação e confirmação manual, ignorando caches de memória.

`login`
Inicia a sessão na API remota. A ferramenta envia a credencial de acesso e recebe um token dinâmico gerado pelo servidor, persistindo-o internamente para as chamadas subsequentes.

`mode [local | remoto]`
Alterna o comportamento do armazenamento sem invalidar o token de sessão do desenvolvedor.

`set [chave] [valor]`
Criptografa e guarda um novo segredo no cofre ativo, ou atualiza o valor de uma chave existente.

`get [chave]`
Busca o segredo criptografado, decodifica em memória e imprime o valor resultante.

`run [comando_alvo]`
Lê o arquivo de mapeamento do projeto, substitui as referências aos segredos pelos seus valores reais e inicia o processo alvo repassando o ambiente isolado.

### Estado de Desenvolvimento

[x] Criptografia segura com algoritmos AES-256 e PBKDF2
[x] Abstração de armazenamento para leitura em disco local
[x] Mapeamento dinâmico de dependências via arquivo YAML
[x] Isolamento de memória durante injeção de processos nativos
[x] Comunicação remota via API 
[x] Tratamento de instabilidades de rede e timeouts de comunicação
[x] Autenticação com sessão dinâmica
[x] Integração com cofre nativo do sistema operacional