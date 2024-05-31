import os
import shutil
import subprocess
import re

# Função para limpar o __pycache__
def limpar_pycache():
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            if name.endswith('.pyc') or name.endswith('__pycache__'):
                os.remove(os.path.join(root, name))
        for name in dirs:
            if name.endswith('__pycache__'):
                shutil.rmtree(os.path.join(root, name))

# Função para limpar o ambiente virtual
def limpar_ambiente_virtual():
    if os.path.exists('env'):
        shutil.rmtree('env')

# Função para limpar os arquivos de build
def limpar_build():
    packs = 'dist', 'build', '*.spec'
    for p in packs:
        if os.path.exists(p):
            if os.path.isfile(p):
                os.remove(p)
            else:
                shutil.rmtree(p)

# Função para criar ou atualizar o ambiente virtual
def criar_atualizar_env():
    limpar_ambiente_virtual()
    subprocess.run(['python3.8', '-m', 'venv', 'env'])
    print("Ambiente virtual criado com sucesso.")

# Função para instalar bibliotecas com o ambiente virtual ativo
def instalar_bibliotecas():
    subprocess.run(['bash', '-c', 'source ./env/bin/activate && pip3.8 install --upgrade pip'])
    subprocess.run(['bash', '-c', 'source ./env/bin/activate && pip3.8 install setuptools_rust'])
    subprocess.run(['bash', '-c', 'source ./env/bin/activate && pip3.8 install pyinstaller'])
    subprocess.run(['bash', '-c', 'source ./env/bin/activate && pip3.8 install -r requirements.txt'])

# Função para criar o módulo de versão
def criar_modulo_versao(arquivo_principal):
    versao = input("Digite a versão do módulo (formato: X.Y.Z): ")
    if re.match(r'^\d+\.\d+\.\d+$', versao):
        with open(arquivo_principal, 'r+') as f:
            lines = f.readlines()
            f.seek(0)
            f.truncate()  # Limpa o conteúdo do arquivo
            for line in lines:
                if re.match(r'^VERSION\s*=\s*".*"', line.strip()):
                    f.write(f'VERSION = "{versao}"\n')
                else:
                    f.write(line)
        print(f'Versão atualizada para: {versao}')
    else:
        print("Formato de versão inválido. Use o formato X.Y.Z (ex: 1.0.0)")


# Função para perguntar e atualizar a versão
def perguntar_atualizar_versao(arquivo_principal):
    if os.path.exists(arquivo_principal):
        with open(arquivo_principal, 'r') as file:
            script_content = file.readlines()
        
        version_line_number = None
        current_version = None

        # Encontra a linha que contém a versão
        for i, line in enumerate(script_content):
            if re.match(r'^VERSION\s*=\s*".*"', line.strip()):
                version_line_number = i
                current_version = re.search(r'(?<=").*(?=")', line.strip()).group()
                break

        if current_version:
            resposta = input(f"Versão atual do módulo é {current_version}. Deseja mantê-la? (s/n): ")
            if resposta.lower() == 'n':
                criar_modulo_versao(arquivo_principal)
        else:
            print("A variável de versão não foi encontrada no arquivo principal.")
    else:
        print("O arquivo principal não foi encontrado.")


# Função para perguntar o nome do executável
def perguntar_nome_executavel():
    nome_executavel = input("Digite o nome do executável: ")
    return nome_executavel

# Função para compilar com o PyInstaller
def compilar(nome_executavel, arquivo_principal):
    subprocess.run(['./env/bin/pyinstaller', '--onefile', '--name', nome_executavel, arquivo_principal])

# Função principal
def main():
    limpar_pycache()
    limpar_ambiente_virtual()
    limpar_build()
    criar_atualizar_env()
    instalar_bibliotecas()
    nome_executavel = perguntar_nome_executavel()
    arquivo_principal = 'main.py'
    if not os.path.exists(arquivo_principal):
        arquivo_principal = input("Arquivo principal (ex: main.py): ")
    perguntar_atualizar_versao(arquivo_principal)
    compilar(nome_executavel, arquivo_principal)
    limpar_ambiente_virtual()
    limpar_pycache()

if __name__ == "__main__":
    main()
