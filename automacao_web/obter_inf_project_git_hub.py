import os
import requests
import xml.etree.ElementTree as ET
import markdown
import base64
from datetime import datetime
import webbrowser

# Configurações
GIT_API_URL = "https://api.github.com"
ORG_NAME = "rochaalbuquerque"
OUTPUT_HTML = "meus-repositorios.html"
ACCESS_TOKEN = "github_pat_1"  # Substitua pelo seu token real

def obter_token_git():
    """Obtém o token Git de variáveis de ambiente ou configuração"""
    token = os.getenv("GIT_TOKEN") or ACCESS_TOKEN
    if not token:
        raise ValueError("Token de acesso Git não encontrado.")
    return token

def fazer_requisicao_git(url):
    """Faz requisição à API Git com autenticação"""
    headers = {
        "Authorization": f"token {obter_token_git()}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"Erro ao acessar {url}: {err}")
        return None

def listar_repositorios():
    """Lista todos os repositórios do usuário"""
    url = f"{GIT_API_URL}/users/{ORG_NAME}/repos?per_page=100&sort=updated&type=all"
    repos = fazer_requisicao_git(url)
    return repos or []

def obter_conteudo_arquivo(repo, caminho_arquivo, branch="main"):
    """Obtém conteúdo de um arquivo específico no repositório"""
    url = f"{GIT_API_URL}/repos/{ORG_NAME}/{repo}/contents/{caminho_arquivo}?ref={branch}"
    try:
        conteudo = fazer_requisicao_git(url)
        if conteudo and 'content' in conteudo:
            return base64.b64decode(conteudo['content']).decode('utf-8')
        return None
    except Exception as e:
        print(f"Erro ao obter arquivo {caminho_arquivo} do repositório {repo}: {e}")
        return None

def extrair_versao_pom(conteudo_pom):
    """Extrai a versão exata do arquivo POM.xml incluindo a tag <version>"""
    if not conteudo_pom:
        return "POM não encontrado"
    
    try:
        # Extrai a linha exata que contém a versão
        for line in conteudo_pom.splitlines():
            if "<version>" in line and "</version>" in line:
                return line.strip()
        return "Versão não especificada no POM"
    except Exception as e:
        return f"Erro ao analisar POM: {str(e)}"

def encontrar_swagger(repo, branch="main"):
    """Tenta encontrar URL do Swagger no repositório"""
    arquivos_swagger = [
        'swagger.yaml', 'swagger.json', 
        'openapi.yaml', 'openapi.json'
    ]
    
    for arquivo in arquivos_swagger:
        conteudo = obter_conteudo_arquivo(repo, arquivo, branch)
        if conteudo:
            return f"https://github.com/{ORG_NAME}/{repo}/blob/{branch}/{arquivo}"
    
    return "Não encontrado"

def gerar_html(repositorios):
    """Gera página HTML com os repositórios e informações detalhadas"""
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Repositórios - {ORG_NAME}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; text-align: center; }}
            .info {{ text-align: center; margin-bottom: 20px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .version {{ font-family: monospace; background-color: #f0f0f0; }}
            .branch {{ font-style: italic; color: #555; }}
            .readme {{ max-height: 200px; overflow-y: auto; padding: 10px; }}
            a {{ color: #0366d6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>Meus Repositórios GitHub</h1>
        <div class="info">Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</div>
        <table>
            <thead>
                <tr>
                    <th>Repositório</th>
                    <th>Versão (POM)</th>
                    <th>Branch</th>
                    <th>Swagger</th>
                    <th>README</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for repo in repositorios:
        if not repo or not isinstance(repo, dict):
            continue
            
        nome_repo = repo.get('name', '')
        default_branch = repo.get('default_branch', 'main')
        html_url = repo.get('html_url', '#')
        
        # Obtém informações do POM.xml na branch padrão
        conteudo_pom = obter_conteudo_arquivo(nome_repo, "pom.xml", default_branch)
        versao = extrair_versao_pom(conteudo_pom)
        
        # Busca Swagger e README
        swagger = encontrar_swagger(nome_repo, default_branch)
        readme_content = obter_conteudo_arquivo(nome_repo, "README.md", default_branch)
        readme_html = markdown.markdown(readme_content) if readme_content else "Sem README"
        
        # Formata links
        swagger_html = swagger if not swagger.startswith('http') else f'<a href="{swagger}" target="_blank">Ver Swagger</a>'
        
        html += f"""
                <tr>
                    <td><a href="{html_url}" target="_blank">{nome_repo}</a></td>
                    <td class="version">{versao}</td>
                    <td class="branch">{default_branch}</td>
                    <td>{swagger_html}</td>
                    <td class="readme">{readme_html}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Página HTML gerada com sucesso: {OUTPUT_HTML}")
    return os.path.abspath(OUTPUT_HTML)

def main():
    try:
        print("Obtendo lista de repositórios...")
        repositorios = listar_repositorios()
        
        if not repositorios:
            print("Nenhum repositório encontrado. Verifique seu token e nome de usuário.")
            return
        
        print(f"Encontrados {len(repositorios)} repositórios")
        print("Processando informações...")
        
        caminho_html = gerar_html(repositorios)
        
        # Abrir no navegador
        webbrowser.open(f"file://{caminho_html}")
        
    except Exception as e:
        print(f"Erro durante a execução: {str(e)}")

if __name__ == "__main__":
    main()