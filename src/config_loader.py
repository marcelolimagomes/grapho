"""
Carregador de configurações da aplicação.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Carrega e valida configurações do arquivo YAML."""

    def __init__(self, config_path: str):
        """
        Inicializa o carregador de configuração.

        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = Path(config_path)

    def load(self) -> Dict[str, Any]:
        """
        Carrega e valida as configurações.

        Returns:
            Dicionário com as configurações carregadas

        Raises:
            FileNotFoundError: Se o arquivo de configuração não existir
            yaml.YAMLError: Se houver erro na sintaxe YAML
            ValueError: Se as configurações forem inválidas
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)

        self._validate_config(config)
        self._set_defaults(config)

        return config

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Valida as configurações carregadas.

        Args:
            config: Configurações a serem validadas

        Raises:
            ValueError: Se alguma configuração for inválida
        """
        required_fields = ['root_directory', 'output_directory']

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado na configuração")

        if not Path(config['root_directory']).exists():
            raise ValueError(f"Diretório raiz não existe: {config['root_directory']}")

        valid_viz_types = {'arquivos', 'classes', 'ambos'}
        if 'visualization_types' in config:
            for viz_type in config['visualization_types']:
                if viz_type not in valid_viz_types:
                    raise ValueError(f"Tipo de visualização inválido: {viz_type}")

        valid_formats = {'html', 'json'}
        if 'output_format' in config and config['output_format'] not in valid_formats:
            raise ValueError(f"Formato de saída inválido: {config['output_format']}")

    def _set_defaults(self, config: Dict[str, Any]) -> None:
        """
        Define valores padrão para configurações opcionais.

        Args:
            config: Configurações a serem completadas com valores padrão
        """
        defaults = {
            'visualization_types': ['arquivos'],
            'output_format': 'html',
            'ignore_patterns': ['__pycache__', '*.pyc', '.git', 'venv', 'env'],
            'graph_config': {
                'width': '100%',
                'height': '800px',
                'physics_enabled': True,
                'hierarchical_layout': False
            }
        }

        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif key == 'graph_config' and isinstance(config[key], dict):
                # Merge com configurações padrão do grafo
                for graph_key, graph_value in value.items():
                    if graph_key not in config[key]:
                        config[key][graph_key] = graph_value
