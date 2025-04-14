# Monitoramento de Servicos Docker

Este e um aplicativo Python simples para monitorar o status dos servicos Docker. Ele exibe os servicos em execucao e seus status, colorindo-os de verde se estiverem em execucao e vermelho se estiverem parados.

## Pre-requisitos

* Python 3.x
* Docker instalado e em execucao

## Instalacao

1.  Clone o repositório:

    ```bash
    git clone <URL_do_seu_repositorio>
    cd <nome_do_repositorio>
    ```

2.  Instale as dependências:

    ```bash
    pip install --no-cache-dir -r requirements.txt
    ```

3.  Configure o arquivo `.env`:

    * Verifique e ajuste as variáveis de ambiente no arquivo `.env` conforme necessário.

## Execucao

### Execucao Local

1.  Certifique-se de que o Docker esteja em execucao.
2.  Execute o aplicativo:

    ```bash
    python app.py
    ```

### Execucao com Docker

1.  Construa a imagem Docker:

    ```bash
    ./build.sh
    ```

2.  Implante o contêiner:

    ```bash
    ./deploy.sh
    ```

## Utilizacao

Após a execucao, o aplicativo exibirá uma lista dos servicos Docker com seus respectivos status coloridos.

* **Verde**: Servico em execucao.
* **Vermelho**: Servico parado.

![home](images/web1.png)
![incidentes](images/web2.png)
![tabelas](images/web3.png)
![admin](images/web4.png)

## Contribuicao

Contribuicões sao bem-vindas! Sinta-se à vontade para abrir issues e pull requests para melhorias e correcões.

## Criador

Chat GPT e Gabriel Alpendre 2025 nocopyright (but credits) 