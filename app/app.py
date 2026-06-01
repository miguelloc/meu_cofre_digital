from flask import Flask, jsonify 
import os 
import logging 
app = Flask(__name__) 

    1. Criando a aplicação Flask: 
#app/app.py - Nossa aplicação que precisa de segredos 
 
from flask import Flask, jsonify 
import os 
import logging 
app = Flask(__name__) 
 
    • Configurando logging (importante para máscaras) 
logging.basicConfig(level=logging.INFO) 
logger = logging.getLogger(__name__) 
@app.route('/') 
def home(): 
    return jsonify({ 
        "message": " Cofre Digital Online!", 
        "environment": os.getenv('ENVIRONMENT', 'unknown'), 
        "version": os.getenv('APP_VERSION', '1.0.0') 
 
    }) 
@app.route('/database') 
def database_info(): 
 
    • Simulando conexão com banco (usando segredos) 
    db_host = os.getenv('DB_HOST', 'localhost') 
    db_user = os.getenv('DB_USER', 'user') 
    db_password = os.getenv('DB_PASSWORD', 'SENHA_NAO_CONFIGURADA')
   
     Atenção! Nunca logar senhas reais!  
    logger.info(f"Conectando ao banco: {db_host} com usuário: {db_user}") 
 
    Nunca façam isso: #logger.info(f"Senha: {db_password}")      
    return jsonify({  
        "status": "connected" if db_password != 'SENHA_NAO_CONFIGURADA' else "not_configured", 
        "host": db_host, 
        "user": db_user,
        "password_configured": db_password != 'SENHA_NAO_CONFIGURADA' 
    }) 
@app.route('/api-key') 
def api_key_info(): 
 
    • Simulando uso de API key externa  
    api_key = os.getenv('EXTERNAL_API_KEY', 'KEY_NAO_CONFIGURADA') 
   
        ◦ Mascarando a chave nos logs  
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****" 
    logger.info(f"Usando API Key: {masked_key}") 
    return jsonify({ 
        "api_configured": api_key != 'KEY_NAO_CONFIGURADA', 
        "key_preview": masked_key
    }) 
if __name__ == '__main__': 
    port = int(os.getenv('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port, debug=False)
 
 
    • Criando requirements:  
#app/requirements.txt 
 
Flask==2.3.3 
gunicorn==21.2.0

Parte 3: Containerizando com segurança (o cofre portátil) 
Vamos criar um container image que pode ser usado em qualquer ambiente:  

    1. Dockerfile seguro:  
# docker/Dockerfile - Nosso "cofre portátil" 
 
FROM python:3.11-slim  
# Criando usuário não-root (segurança) 
RUN useradd --create-home --shell /bin/bash appuser
 
# Definindo diretório de trabalho 
WORKDIR /app 
 
    • Copiando requirements primeiro (cache do Docker)  
COPY app/requirements.txt . 
 
    • Instalando dependências  
RUN pip install --no-cache-dir -r requirements.txt 
 
    • Copiando código da aplicação  
COPY app/ .
 
    • Mudando para usuário não-root  
USER appuser 
 
    • Expondo porta (configurável via variável)  
EXPOSE ${PORT:-5000} 
 
    • Comando de inicialização  
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"] 
 
    2. Docker compose para desenvolvimento:  
# docker-compose.yml - Para testes locais  
version: '3.8'  
services:  
  app:  
    build:  
      context: .  
      dockerfile: docker/Dockerfile 
    ports:  
      - "5000:5000" 
    environment:  
      - ENVIRONMENT=development 
      - APP_VERSION=1.0.0  
      - DB_HOST=localhost  
      - DB_USER=dev_user  
      - DB_PASSWORD=dev_password_123 
      - EXTERNAL_API_KEY=dev_key_abcd1234efgh5678  
      - PORT=5000  
    volumes: 
      - ./app:/app
 
Parte 4: Configurando secrets no GitHub (o sistema de cofres) 
Agora, vamos configurar os segredos no GitHub Actions: 

    1. Acessando as configurações de secrets:  
        ◦ Vão para o repositório no GitHub; 
        ◦ Cliquem em "Settings" (Configurações);  
        ◦ No menu lateral, cliquem em "Secrets and variables" → "Actions";  
        ◦ Cliquem em "New repository secret". 
 
    2. Criando secrets organizados:  
SECRETS A CRIAR:  
    • Produção:  
- PROD_DB_HOST: prod-database.company.com 
- PROD_DB_USER: prod_app_user 
- PROD_DB_PASSWORD: SuperSecretProdPassword123! 
- PROD_API_KEY: prod_api_key_xyz789abc456def123 
 
    • Staging:  
- STAGING_DB_HOST: staging-database.company.com 
- STAGING_DB_USER: staging_app_user  
- STAGING_DB_PASSWORD: StagingPassword456! 
- STAGING_API_KEY: staging_api_key_mno321pqr654stu987 
 
    • Docker Registry: 
- DOCKER_USERNAME: seu_usuario_docker
- DOCKER_PASSWORD: sua_senha_docker_hub 

Parte 5: Implementando Configure-once, Deploy-Many 
Vamos criar um workflow que usa os mesmos secrets para múltiplos ambientes: 

    1. Workflow principal (.github/workflows/deploy.yml):  
name:  Cofre Digital - Deploy Automatizado 
on: 
  push:  
    branches: [ main, develop ]  
  pull_request:  
    branches: [ main ]  
env:
 
    •  Configurações globais (Configure-once) 
  REGISTRY: docker.io 
  IMAGE_NAME: cofre-digital-app 
jobs: 
  # Job 1: Build da imagem (uma vez) 
  build:  
    name: Construir Container Image 
    runs-on: ubuntu-latest 
    outputs: 
      image-tag: ${{ steps.meta.outputs.tags }} 
      image-digest: ${{ steps.build.outputs.digest }}
steps: 
    - name: Checkout do código 
      uses: actions/checkout@v4  
      
    - name: Login no Docker Hub 
      uses: docker/login-action@v3 
 
      with: 
        registry: ${{ env.REGISTRY }} 
        username: ${{ secrets.DOCKER_USERNAME }} 
        password: ${{ secrets.DOCKER_PASSWORD }} 
      
    - name:  Extrair metadados 
      id: meta  
      uses: docker/metadata-action@v5 
      with:  
        images: ${{ env.REGISTRY }}/${{ secrets.DOCKER_USERNAME }}/${{ env.IMAGE_NAME }}  
        tags: | 
          type=ref,event=branch 
          type=ref,event=pr 
          type=sha,prefix={{branch}}- 
       
    - name: Build e Push da imagem 
      id: build  
      uses: docker/build-push-action@v5 
      with: 
        context: .  
        file: ./docker/Dockerfile 
        push: true  
        tags: ${{ steps.meta.outputs.tags }}  
        labels: ${{ steps.meta.outputs.labels }} 
 
  # Job 2: Deploy para Staging (Deploy-Many) 
  deploy-staging:  
    name: Deploy Staging  
    runs-on: ubuntu-latest  
    needs: build  
    if: github.ref == 'refs/heads/develop'     
 
    environment: staging  
     
     steps:  
    - name: Deploy para Staging
      run: | 
 
        echo "Iniciando deploy para STAGING..."  
        echo "Imagem: ${{ needs.build.outputs.image-tag }}" 
 
    • Simulando deploy (em produção real, seria kubectl, docker-compose etc.) 
         echo " Configurando secrets para staging..." 
        echo "DB_HOST=${{ secrets.STAGING_DB_HOST }}" >> staging.env  
        echo "DB_USER=${{ secrets.STAGING_DB_USER }}" >> staging.env  
        echo "DB_PASSWORD=***MASKED***" >> staging.env  # Máscara nos logs!  
        echo "EXTERNAL_API_KEY=***MASKED***" >> staging.env  
        echo "ENVIRONMENT=staging" >> staging.env          
 
        echo "Deploy staging concluído!"  
        echo " Verificando configuração..."  
        cat staging.env 
 
  # Job 3: Deploy para Produção (Deploy-Many) 
 
  deploy-production:  
    name: Deploy Produção  
    runs-on: ubuntu-latest  
    needs: build  
    if: github.ref == 'refs/heads/main'
 
    environment: production   
 
    steps:  
    - name: Deploy para Produção  
      run: |  
        echo " Iniciando deploy para PRODUÇÃO..."  
        echo "Imagem: ${{ needs.build.outputs.image-tag }}" 
 
    • Configurando secrets para produção  
        echo "Configurando secrets para produção..."  
        echo "DB_HOST=${{ secrets.PROD_DB_HOST }}" >> production.env  
        echo "DB_USER=${{ secrets.PROD_DB_USER }}" >> production.env  
        echo "DB_PASSWORD=***MASKED***" >> production.env  # Máscara nos logs! 
        echo "EXTERNAL_API_KEY=***MASKED***" >> production.env 
        echo "ENVIRONMENT=production" >> production.env 
         
        echo "Deploy produção concluído!"  
        echo " Verificando configuração..."  
        cat production.env 
 
  # Job 4: Teste de Segurança 
 
  security-check:  
    name: Verificação de Segurança 
    runs-on: ubuntu-latest  
    needs: build 
     
     steps: 
    - name:  Checkout do código 
      uses: actions/checkout@v4 
 
     - name: Verificar vazamentos de secrets 
      run: | 
         echo "Verificando se há secrets expostos no código..." 
 
    • Procurando por padrões suspeitos  
        if grep -r "password.*=" app/ --exclude-dir=.git; then 
          echo "ATENÇÃO: Possível senha hardcoded encontrada!"  
          exit 1  
        fi          
 
        if grep -r "api.*key.*=" app/ --exclude-dir=.git; then  
          echo "ATENÇÃO: Possível API key hardcoded encontrada!" 
          exit 1  
        fi    
         echo "Nenhum secret exposto encontrado!" 

Parte 6: Implementando máscaras de log avançadas 
Vamos criar um sistema robusto de mascaramento:  

    1. Utilitário de mascaramento (app/security_utils.py):  
# app/security_utils.py - Utilitários de segurança 
import re 
import logging 
from functools import wraps 
class SecureLogger: 
    """Logger que automaticamente mascara informações sensíveis""" 
     
 
    def __init__(self, logger_name): 
        self.logger = logging.getLogger(logger_name) 
 
    • Padrões para mascarar  
        self.sensitive_patterns = [ 
 
            (r'password["\s]*[:=]["\s]*([^"\s,}]+)', r'password="***MASKED***"'),  
            (r'api[_-]?key["\s]*[:=]["\s]*([^"\s,}]+)', r'api_key="***MASKED***"'),
 
            (r'token["\s]*[:=]["\s]*([^"\s,}]+)', r'token="***MASKED***"'),  
            (r'secret["\s]*[:=]["\s]*([^"\s,}]+)', r'secret="***MASKED***"'),  
        ]       
 
    def _mask_sensitive_data(self, message):  
        """Mascara dados sensíveis na mensagem"""  
        for pattern, replacement in self.sensitive_patterns:  
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)  
        return message 
       
    def info(self, message):  
        """Log info com mascaramento automático"""  
        masked_message = self._mask_sensitive_data(str(message))  
        self.logger.info(masked_message) 
     
     def error(self, message): 
 
        """Log error com mascaramento automático""" 
 
        masked_message = self._mask_sensitive_data(str(message)) 
 
        self.logger.error(masked_message)       
 
    def debug(self, message): 
 
        """Log debug com mascaramento automático"""  
        masked_message = self._mask_sensitive_data(str(message))  
        self.logger.debug(masked_message)
  
def mask_secret(secret, visible_chars=4):  
    """Mascara um secret mostrando apenas alguns caracteres"""  
    if not secret or len(secret) <= visible_chars * 2:  
        return "***MASKED***" 
    
     return secret[:visible_chars] + "*" * (len(secret) - visible_chars * 2) + secret[-visible_chars:]  
def secure_log_decorator(func): 
     """Decorator que automaticamente mascara logs de funções""" 
 
    @wraps(func)  
    def wrapper(*args, **kwargs):  
        secure_logger = SecureLogger(func.__module__)

        
    •        Mascarando argumentos sensíveis 
 
        safe_kwargs = {}  
        for key, value in kwargs.items(): 
 
            if any(sensitive in key.lower() for sensitive in ['password', 'key', 'token', 'secret']):  
                safe_kwargs[key] = mask_secret(str(value))  
            else:  
                safe_kwargs[key] = value        
 
        secure_logger.info(f"Executando {func.__name__} com args: {safe_kwargs}")  
        try:  
            result = func(*args, **kwargs)  
            secure_logger.info(f"{func.__name__} executado com sucesso")  
            return result  
        except Exception as e:  
            secure_logger.error(f"Erro em {func.__name__}: {str(e)}")  
            raise  
    return wrapper 
 
    2. Usando o sistema de mascaramento: 
 
# app/database.py - Exemplo de uso seguro  
from security_utils import SecureLogger, secure_log_decorator, mask_secret  
import os  
secure_logger = SecureLogger(__name__)  
@secure_log_decorator  
def connect_database(host, user, password, database): 
    """Conecta ao banco de dados de forma segura""" 
 
    • Log seguro da conexão 
 
    secure_logger.info(f"Conectando ao banco {database} em {host}")  
    secure_logger.info(f"Usuário: {user}")  
    secure_logger.info(f"Senha configurada: {password is not None}") 
      
    • Simulando conexão  

    connection_string = f"postgresql://{user}:{mask_secret(password)}@{host}/{database}"  
    secure_logger.info(f"String de conexão: {connection_string}") 
     
     return {"status": "connected", "host": host, "user": user} 
 
        ◦ # Exemplo de uso 
if __name__ == "__main__":  
    db_config = {  
        "host": os.getenv("DB_HOST", "localhost"),  
        "user": os.getenv("DB_USER", "user"),  
        "password": os.getenv("DB_PASSWORD", "password"),  
        "database": "cofre_digital"  
    }     
 
    connect_database(**db_config)

Parte 7: Testando o sistema completo 
Vamos testar nosso cofre digital:  

    1. Script de teste local: 
 
    • #!/bin/bash  
# test_local.sh - Testando localmente  
echo " Testando Cofre Digital Localmente..." 
 
    •  Construindo a imagem 
 
echo "Construindo container image..."  
docker build -f docker/Dockerfile -t cofre-digital-local . 
 
    • Testando com secrets de desenvolvimento 
 
echo "Iniciando aplicação com secrets de dev..."  
docker run -d --name cofre-test \  
  -p 5000:5000 \  
  -e ENVIRONMENT=test \  
  -e DB_HOST=test-db.local \  
  -e DB_USER=test_user \  
  -e DB_PASSWORD=test_password_123 \  
  -e EXTERNAL_API_KEY=test_key_abcd1234 \  
  cofre-digital-local 

    • Aguardando inicialização 
 
sleep 5
 
    • # Testando endpoints 
 
echo "Testando endpoints..." 
curl -s http://localhost:5000/ | jq .  
curl -s http://localhost:5000/database | jq .  
curl -s http://localhost:5000/api-key | jq . 
 
    • Verificando logs (devem estar mascarados) 
 
echo "Verificando logs (secrets devem estar mascarados)..." 
docker logs cofre-test 
 
    • Limpeza 
 
docker stop cofre-test 
docker rm cofre-test  
echo "Teste local concluído!" 
