#!/bin/bash

# Script de instalação e setup da ferramenta de documentação Python

echo "🔧 Configurando Ferramenta de Documentação Python"
echo "================================================="

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Verifica se pip está disponível
if ! python3 -m pip --version &> /dev/null; then
    echo "⚠️  pip não encontrado. Tentando instalar..."
    
    # Tenta instalar pip
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    else
        echo "❌ Não foi possível instalar pip automaticamente."
        echo "   Por favor, instale pip manualmente e execute este script novamente."
        exit 1
    fi
fi

echo "✅ pip encontrado: $(python3 -m pip --version)"

# Instala dependências
echo "📦 Instalando dependências..."
python3 -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso!"
else
    echo "❌ Erro ao instalar dependências."
    echo "   Tente executar manualmente: python3 -m pip install -r requirements.txt"
    exit 1
fi

# Testa a instalação
echo "🧪 Testando instalação..."
python3 -c "
import ast
import yaml
import jinja2
import networkx
import pyvis
print('✅ Todas as dependências foram importadas com sucesso!')
"

if [ $? -eq 0 ]; then
    echo "✅ Instalação completa!"
    echo ""
    echo "🚀 Como usar:"
    echo "   1. Edite config.yaml com as configurações do seu projeto"
    echo "   2. Execute: python3 generate_docs.py --config config.yaml"
    echo "   3. Abra docs/index.html no seu navegador"
    echo ""
    echo "📖 Para testar com o projeto de exemplo:"
    echo "   python3 generate_docs.py --config config_example.yaml"
    echo ""
    echo "🔍 Para ver uma demonstração:"
    echo "   python3 demo.py"
else
    echo "⚠️  Instalação concluída, mas alguns módulos podem não estar funcionando corretamente."
    echo "   Verifique as mensagens de erro acima."
fi
