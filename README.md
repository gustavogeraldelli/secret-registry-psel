# Sec-Registry

O Sec-Registry é uma ferramenta de interface de linha de comando (CLI) desenvolvida para a gestão centralizada e segura de credenciais. O sistema elimina a necessidade de manter senhas e tokens expostos em arquivos de configuração estáticos, injetando os segredos diretamente na memória durante a execução das aplicações.

## Funcionalidades Principais

* **Injeção de Dependências em Memória:** Os segredos são repassados aos processos alvo através de variáveis de ambiente gerenciadas por subprocessos. Os dados reais nunca são gravados no disco físico da máquina.
* **Mapeamento Declarativo:** A substituição de credenciais hardcoded por um arquivo de contrato (`.registry.yml`), que mapeia quais variáveis o projeto exige e de onde elas devem ser extraídas no cofre.
* **Criptografia Padronizada:** Implementação de algoritmos de mercado (AES-256-GCM com derivação de chave PBKDF2) para garantir a segurança dos dados em repouso.
* **Operação Híbrida (Local e Remota):** Capacidade de alternar entre um cofre isolado na máquina do desenvolvedor e um servidor centralizado na nuvem, mantendo a mesma base de comandos.
* **Resiliência de Rede:** O cliente HTTP integrado possui tolerância a falhas. Em caso de instabilidade na conexão com o servidor, o sistema aplica um mecanismo de recuo exponencial (Exponential Backoff) para evitar a interrupção de processos automatizados.
* **Integração com Chaveiro do Sistema:** Conexão nativa com o gerenciador de credenciais do sistema operacional para armazenamento da senha mestra, garantindo uso diário sem interrupções manuais.

## Arquitetura e Segurança

O sistema foi desenhado sob o princípio de isolamento de ambiente e proteção contra falhas operacionais:

* **Zero Exposição em Disco:** A ferramenta não utiliza arquivos temporários para expor senhas. O ciclo de vida do segredo em texto plano ocorre estritamente dentro da memória (RAM) alocada para o subprocesso durante a execução do comando alvo.
* **Prevenção de Sobrescrita Acidental:** O fluxo operacional separa ações de leitura das ações de configuração. Comandos de injeção (`run`, `get`) funcionam de forma silenciosa para não quebrar pipelines de CI/CD. Em contrapartida, a inicialização de um cofre (`init`) bloqueia a leitura de variáveis de ambiente e força a confirmação manual, mitigando o risco de automações apagarem o banco de dados.
* **Modularidade de Armazenamento:** A implementação utiliza Inversão de Dependência para isolar o motor criptográfico da camada de armazenamento de arquivos. Isso permite que a ferramenta transite de forma imperceptível entre a persistência em um arquivo JSON local e a transmissão segura de pacotes via API.

## Guia de Uso

### 1. Configuração do Projeto
Na raiz do projeto que consumirá os segredos, cria-se o arquivo de mapeamento `.registry.yml`. O prefixo `secret:` indica que o valor deve ser buscado no cofre.

```yaml
env:
  PORT: 8080
  DB_PASS: "secret:DB_PASS"
  API_TOKEN: "secret:API_TOKEN"
```

### 2. Comandos do Cofre

**Inicialização:**
Cria um cofre vazio e estabelece a senha mestra.

```bash
python -m cli.main init
```

**Escrita e Leitura:**
Guarda um valor criptografado e realiza a leitura do mesmo.

```bash
python -m cli.main set DB_PASS senha_banco_real
python -m cli.main get DB_PASS
```

**Execução Isolada:**
Lê o contrato YAML, extrai os segredos do cofre e executa a aplicação alvo (ex: um script Python ou um projeto Node) injetando o ambiente seguro.

```bash
python -m cli.main run python app.py
```

### 3. Gestão de Ambientes

O sistema permite alterar a fonte de dados do cofre sem invalidar credenciais de acesso.

**Alternar para o modo remoto:**

```bash
python -m cli.main mode remoto
```

**Autenticação na API:**
Estabelece sessão com o servidor e armazena o token de acesso dinâmico para comunicações futuras.

```bash
python -m cli.main login
```

*(Após o login, todos os comandos como `init`, `set`, `get` e `run` passam a operar contra a base de dados do servidor remoto automaticamente).*