"""
Configuração e setup para integração com OpenAI e LangChain.
"""

import os
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path


class AIConfig:
    """Configuração para integração com IA."""

    def __init__(self, env_file: Optional[str] = None):
        """
        Inicializa a configuração de IA.

        Args:
            env_file: Caminho para arquivo .env (opcional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Tenta carregar .env do diretório atual ou parent
            current_dir = Path(__file__).parent
            env_paths = [
                current_dir / '.env',
                current_dir.parent / '.env',
                Path('.env')
            ]

            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    break

    @property
    def openai_api_key(self) -> str:
        """Retorna a chave da API OpenAI."""
        key = os.getenv('OPENAI_API_KEY', '')
        if not key or key == 'your_openai_api_key_here':
            raise ValueError(
                "OPENAI_API_KEY não configurada. "
                "Configure no arquivo .env ou variável de ambiente."
            )
        return key

    @property
    def openai_model(self) -> str:
        """Retorna o modelo OpenAI a ser usado."""
        return os.getenv('OPENAI_MODEL', 'gpt-4')

    @property
    def openai_temperature(self) -> float:
        """Retorna a temperatura para geração."""
        return float(os.getenv('OPENAI_TEMPERATURE', '0.3'))

    @property
    def openai_max_tokens(self) -> int:
        """Retorna o máximo de tokens para geração."""
        return int(os.getenv('OPENAI_MAX_TOKENS', '2000'))

    @property
    def enable_ai_documentation(self) -> bool:
        """Retorna se a documentação IA está habilitada."""
        return os.getenv('ENABLE_AI_DOCUMENTATION', 'true').lower() == 'true'

    @property
    def documentation_language(self) -> str:
        """Retorna o idioma para documentação."""
        return os.getenv('DOCUMENTATION_LANGUAGE', 'pt-BR')

    @property
    def include_config_files(self) -> bool:
        """Retorna se deve incluir arquivos de configuração na análise."""
        return os.getenv('INCLUDE_CONFIG_FILES', 'true').lower() == 'true'

    def validate(self) -> bool:
        """
        Valida se a configuração está correta.

        Returns:
            True se válida, False caso contrário
        """
        try:
            # Testa se a chave da API está disponível
            _ = self.openai_api_key
            return True
        except ValueError:
            return False
