#!/usr/bin/env python3
"""
Ferramenta de Documentação de Relacionamento entre Arquivos/Classes Python
Gera documentação HTML interativa com diagramas de dependência.
"""

import argparse
import sys
from pathlib import Path

from src.analyzer import ProjectAnalyzer
from src.graph_generator import GraphGenerator
from src.html_generator import HTMLGenerator
from src.config_loader import ConfigLoader
from src.ai_config import AIConfig
from src.ai_analyzer import AICodeAnalyzer


def main():
    """Função principal da aplicação."""
    parser = argparse.ArgumentParser(
        description="Gera documentação interativa de dependências Python"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Caminho para o arquivo de configuração (padrão: config.yaml)"
    )
    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help="Habilita análise e documentação com IA (requer configuração OpenAI)"
    )
    parser.add_argument(
        "--max-ai-files",
        type=int,
        default=None,
        help="Máximo de arquivos para analisar com IA (None = todos)"
    )

    args = parser.parse_args()

    try:
        # Carrega configurações
        config_loader = ConfigLoader(args.config)
        config = config_loader.load()

        print("🔍 Analisando projeto...")

        # Configura IA se habilitada
        ai_analyzer = None
        if args.enable_ai:
            try:
                ai_config = AIConfig()
                if ai_config.validate():
                    print("🤖 Configuração de IA validada. Habilitando análise com IA...")
                    ai_analyzer = AICodeAnalyzer(ai_config)
                else:
                    print("⚠️  Configuração de IA inválida. Continuando sem IA...")
                    print("   Configure OPENAI_API_KEY no arquivo .env")
            except Exception as e:
                print(f"⚠️  Erro ao configurar IA: {e}")
                print("   Continuando sem análise de IA...")

        # Analisa o projeto
        analyzer = ProjectAnalyzer(config)
        if ai_analyzer:
            analyzer.set_ai_analyzer(ai_analyzer)

        analysis_result = analyzer.analyze(enable_ai=bool(ai_analyzer))

        print(f"📊 Encontrados {len(analysis_result.files)} arquivos e {len(analysis_result.classes)} classes")

        # Gera grafo
        print("🌐 Gerando grafos de dependência...")
        graph_generator = GraphGenerator(config)
        graphs = graph_generator.generate(analysis_result)

        # Gera HTML
        print("📄 Gerando documentação HTML...")
        html_generator = HTMLGenerator(config)
        html_generator.generate(analysis_result, graphs)

        output_dir = Path(config["output_directory"]).resolve()

        # Contabiliza arquivos com documentação IA
        ai_files_count = sum(1 for file_info in analysis_result.files.values()
                             if file_info.ai_documentation)

        ai_errors_count = sum(1 for file_info in analysis_result.files.values()
                              if hasattr(file_info, 'ai_error') and file_info.ai_error)

        print(f"✅ Documentação gerada com sucesso em: {output_dir}")
        if args.enable_ai:
            print(f"🤖 IA: {ai_files_count} documentações geradas")
            if ai_errors_count > 0:
                print(f"⚠️  IA: {ai_errors_count} arquivos com erro/ignorados")
        print(f"🌐 Abra {output_dir}/index.html no seu navegador")

        if args.enable_ai and ai_files_count == 0:
            print("\n💡 Dica: Configure OPENAI_API_KEY no .env para gerar documentação IA")

    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
