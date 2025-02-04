# 🤖 WebUI: Interface para Browser-Use com Agentes de IA

![GitHub stars](https://img.shields.io/github/stars/browser-use/web-ui?style=social)](https://github.com/browser-use/web-ui/stargazers)
[![Discord](https://img.shields.io/discord/1303749220842340412?color=7289DA&label=Discord&logo=discord&logoColor=white)](https://link.browser-use.com/discord)
[![Documentation](https://img.shields.io/badge/Documentação-📕-blue)](https://docs.browser-use.com)
[![WarmShao](https://img.shields.io/twitter/follow/warmshao?style=social)](https://x.com/warmshao)

Este projeto expande o [browser-use](https://github.com/browser-use/browser-use), projetado para tornar websites acessíveis para agentes de IA.

Agradecemos a [WarmShao](https://github.com/warmshao) por sua contribuição a este projeto.

**WebUI:** Construído com Gradio, suporta a maioria das funcionalidades do `browser-use`. A interface é amigável e facilita a interação com o agente do navegador.

**Suporte Expandido a LLMs:** Integração com diversos modelos de linguagem (LLMs), incluindo: Gemini, OpenAI, Azure OpenAI, Anthropic, DeepSeek, Ollama, etc. Planejamos adicionar suporte para mais modelos no futuro.

**Suporte a Navegadores Customizados:** Use seu próprio navegador, eliminando a necessidade de re-autenticar em sites. Suporta gravação de tela em alta definição.

**Sessões Persistentes do Navegador:** Mantenha a janela do navegador aberta entre tarefas de IA, visualizando o histórico completo e o estado das interações.

<video src="https://github.com/user-attachments/assets/56bc7080-f2e3-4367-af22-6bf2245ff6cb" controls="controls">Seu navegador não suporta a reprodução deste vídeo!</video>

## Guia de Instalação

### Pré-requisitos
- Python 3.11 ou superior
- Git (para clonar o repositório)

### Opção 1: Instalação Local

Leia o [guia de início rápido](https://docs.browser-use.com/quickstart#prepare-the-environment) ou siga os passos abaixo:

#### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

#### Passo 2: Configurar o Ambiente Python
Recomendamos [uv](https://docs.astral.sh/uv/) para gerenciar o ambiente Python.

Usando uv (recomendado):
```bash
uv venv --python 3.11
```

Ative o ambiente virtual:
- Windows (Prompt de Comando):
```cmd
.venv\Scripts\activate
```
- Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
- macOS/Linux:
```bash
source .venv/bin/activate
```

#### Passo 3: Instalar Dependências
Instale os pacotes Python:
```bash
uv pip install -r requirements.txt
```

Instale o Playwright:
```bash
playwright install
```

#### Passo 4: Configurar o Ambiente
1. Crie uma cópia do arquivo de exemplo de ambiente:
- Windows (Prompt de Comando):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
2. Abra o arquivo `.env` em seu editor de texto e adicione suas chaves de API e outras configurações.

### Opção 2: Instalação com Docker

#### Pré-requisitos
- Docker e Docker Compose instalados
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Para Windows/macOS)
  - [Docker Engine](https://docs.docker.com/engine/install/) e [Docker Compose](https://docs.docker.com/compose/install/) (Para Linux)

#### Passos de Instalação
1. Clone o repositório:
```bash
git clone https://github.com/browser-use/web-ui.git
cd web-ui
```

2. Crie e configure o arquivo de ambiente:
- Windows (Prompt de Comando):
```bash
copy .env.example .env
```
- macOS/Linux/Windows (PowerShell):
```bash
cp .env.example .env
```
Edite o arquivo `.env` com seu editor de texto e adicione suas chaves de API.

3. Execute com Docker:
```bash
# Construa e inicie o container com as configurações padrão (navegador fecha após as tarefas de IA)
docker compose up --build
```
```bash
# Ou execute com o navegador persistente (navegador permanece aberto entre as tarefas de IA)
CHROME_PERSISTENT_SESSION=true docker compose up --build
```

4. Acesse a Aplicação:
- Interface Web: Abra `http://localhost:7788` no seu navegador
- VNC Viewer (para visualizar as interações do navegador): Abra `http://localhost:6080/vnc.html`
  - Senha padrão do VNC: "youvncpassword"
  - Pode ser alterada definindo `VNC_PASSWORD` no seu arquivo `.env`

## Uso

### Configuração Local
1.  **Execute a WebUI:**
    Após completar os passos de instalação acima, inicie a aplicação:
    ```bash
    python webui.py --ip 127.0.0.1 --port 7788
    ```
2. Opções da WebUI:
   - `--ip`: O endereço IP para vincular a WebUI. O padrão é `127.0.0.1`.
   - `--port`: A porta para vincular a WebUI. O padrão é `7788`.
   - `--theme`: O tema para a interface do usuário. O padrão é `Ocean`.
     - **Default**: O tema padrão com um design equilibrado.
     - **Soft**: Um esquema de cores suave e silenciado para uma experiência de visualização relaxante.
     - **Monochrome**: Um tema em escala de cinza com cor mínima para simplicidade e foco.
     - **Glass**: Um design elegante e semi-transparente para uma aparência moderna.
     - **Origin**: Um tema clássico, inspirado no retrô para uma sensação nostálgica.
     - **Citrus**: Uma paleta vibrante, inspirada em frutas cítricas com cores brilhantes e frescas.
     - **Ocean** (padrão): Um tema azul, inspirado no oceano, proporcionando um efeito calmante.
   - `--dark-mode`: Ativa o modo escuro para a interface do usuário.
3.  **Acesse a WebUI:** Abra seu navegador e navegue até `http://127.0.0.1:7788`.
4.  **Usando Seu Próprio Navegador (Opcional):**
    - Defina `CHROME_PATH` para o caminho executável do seu navegador e `CHROME_USER_DATA` para o diretório de dados do usuário do seu navegador. Deixe `CHROME_USER_DATA` vazio se você quiser usar os dados locais do usuário.
      - Windows
        ```env
         CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
         CHROME_USER_DATA="C:\Users\SeuNomeDeUsuário\AppData\Local\Google\Chrome\User Data"
        ```
        > Nota: Substitua `SeuNomeDeUsuário` pelo seu nome de usuário real no Windows.
      - Mac
        ```env
         CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
         CHROME_USER_DATA="/Users/SeuNomeDeUsuário/Library/Application Support/Google/Chrome"
        ```
    - Feche todas as janelas do Chrome.
    - Abra a WebUI em um navegador que não seja o Chrome, como Firefox ou Edge. Isso é importante porque o contexto persistente do navegador usará os dados do Chrome ao executar o agente.
    - Marque a opção "Usar Meu Próprio Navegador" nas Configurações do Navegador.
5. **Manter o Navegador Aberto (Opcional):**
    - Defina `CHROME_PERSISTENT_SESSION=true` no arquivo `.env`.

### Configuração com Docker
1. **Variáveis de Ambiente:**
   - Toda a configuração é feita através do arquivo `.env`.
   - Variáveis de ambiente disponíveis:
     ```
     # Chaves de API para LLMs
     OPENAI_API_KEY=sua_chave_aqui
     ANTHROPIC_API_KEY=sua_chave_aqui
     GOOGLE_API_KEY=sua_chave_aqui

     # Configurações do Navegador
     CHROME_PERSISTENT_SESSION=true   # Defina como true para manter o navegador aberto entre as tarefas de IA
     RESOLUTION=1920x1080x24         # Formato de resolução customizado: LARGURAxALTURAxPROFUNDIDADE
     RESOLUTION_WIDTH=1920           # Largura customizada em pixels
     RESOLUTION_HEIGHT=1080          # Altura customizada em pixels

     # Configurações do VNC
     VNC_PASSWORD=sua_senha_vnc  # Opcional, o padrão é "vncpassword"
     ```

2. **Modos de Persistência do Navegador:**
   - **Modo Padrão (CHROME_PERSISTENT_SESSION=false):**
     - O navegador abre e fecha a cada tarefa de IA.
     - Estado limpo para cada interação.
     - Menor uso de recursos.

   - **Modo Persistente (CHROME_PERSISTENT_SESSION=true):**
     - O navegador permanece aberto entre as tarefas de IA.
     - Mantém o histórico e o estado.
     - Permite visualizar as interações anteriores da IA.
     - Defina no arquivo `.env` ou via variável de ambiente ao iniciar o container.

3. **Visualizando as Interações do Navegador:**
   - Acesse o visualizador noVNC em `http://localhost:6080/vnc.html`.
   - Insira a senha do VNC (padrão: "vncpassword" ou o que você definiu em VNC_PASSWORD).
   - Agora você pode ver todas as interações do navegador em tempo real.

4. **Gerenciamento do Container:**
   ```bash
   # Inicie com o navegador persistente
   CHROME_PERSISTENT_SESSION=true docker compose up -d

   # Inicie com o modo padrão (o navegador fecha após as tarefas)
   docker compose up -d

   # Visualize os logs
   docker compose logs -f

   # Pare o container
   docker compose down
   ```

## Changelog
- [x] **2025/01/26:** Obrigado a @vvincent1234. Agora o browser-use-webui pode combinar com o DeepSeek-r1 para se envolver em pensamentos profundos!
- [x] **2025/01/10:** Obrigado a @casistack. Agora temos a opção de configuração do Docker e também o suporte para manter o navegador aberto entre as tarefas.[Vídeo tutorial demo](https://github.com/browser-use/web-ui/issues/1#issuecomment-2582511750).
- [x] **2025/01/06:** Obrigado a @richard-devbot. Uma nova e bem projetada WebUI foi lançada. [Vídeo tutorial demo](https://github.com/warmshao/browser-use-webui/issues/1#issuecomment-2573393113).
