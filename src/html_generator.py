"""
Gerador de documentação HTML com templates Jinja2 e Tailwind CSS.
"""

from jinja2 import Environment, FileSystemLoader, DictLoader
from pathlib import Path
from typing import Dict, Any
import json
import shutil
from datetime import datetime

from .models import AnalysisResult
from .syntax_highlighter import PythonSyntaxHighlighter


class HTMLGenerator:
    """Gera documentação HTML completa."""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o gerador HTML.

        Args:
            config: Configurações da aplicação
        """
        self.config = config
        self.output_dir = Path(config['output_directory'])
        self.templates = self._setup_templates()
        self.syntax_highlighter = PythonSyntaxHighlighter()

    def generate(self, analysis_result: AnalysisResult, graphs: Dict[str, Any]) -> None:
        """
        Gera toda a documentação HTML.

        Args:
            analysis_result: Resultado da análise do projeto
            graphs: Grafos gerados
        """
        # Cria diretório de saída
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Gera página principal
        self._generate_index_page(analysis_result, graphs)

        # Gera páginas de módulos
        self._generate_module_pages(analysis_result)

        # Gera páginas de classes
        self._generate_class_pages(analysis_result)

        # Copia assets estáticos
        self._copy_assets()

        print(f"📁 {len(analysis_result.files)} páginas de módulos geradas")
        print(f"📁 {len(analysis_result.classes)} páginas de classes geradas")

    def _setup_templates(self) -> Environment:
        """Configura templates Jinja2."""
        templates_dict = {
            'base.html': self._get_base_template(),
            'index.html': self._get_index_template(),
            'module.html': self._get_module_template(),
            'class.html': self._get_class_template()
        }

        loader = DictLoader(templates_dict)
        env = Environment(loader=loader)
        return env

    def _generate_index_page(self, analysis_result: AnalysisResult, graphs: Dict[str, Any]) -> None:
        """Gera a página principal com o grafo."""
        template = self.templates.get_template('index.html')

        # Salva grafos
        graph_files = {}
        if 'files' in graphs:
            files_net, files_nx = graphs['files']
            files_net.save_graph(str(self.output_dir / 'files_graph.html'))
            graph_files['files'] = 'files_graph.html'

        if 'classes' in graphs:
            classes_net, classes_nx = graphs['classes']
            classes_net.save_graph(str(self.output_dir / 'classes_graph.html'))
            graph_files['classes'] = 'classes_graph.html'

        # Estatísticas do projeto
        stats = {
            'total_files': len(analysis_result.files),
            'total_classes': len(analysis_result.classes),
            'total_functions': sum(len(f.functions) for f in analysis_result.files.values()),
            'total_imports': sum(len(f.imports) for f in analysis_result.files.values())
        }

        # Prepara dados de código fonte para JavaScript
        source_code_data = {}
        ai_documentation_data = {}

        for file_path, file_info in analysis_result.files.items():
            if file_info.source_code:
                highlighted_code = self.syntax_highlighter.highlight(file_info.source_code)
                source_code_data[file_path] = {
                    'code': highlighted_code,
                    'line_count': len(file_info.source_code.splitlines())
                }

            # Adiciona documentação IA se disponível
            if file_info.ai_documentation:
                ai_documentation_data[file_path] = {
                    'markdown': file_info.ai_documentation,
                    'summary': file_info.ai_summary or 'Resumo não disponível',
                    'purpose': file_info.ai_purpose or 'Propósito não especificado'
                }

        content = template.render(
            title="Documentação do Projeto",
            stats=stats,
            graph_files=graph_files,
            files=analysis_result.files,
            classes=analysis_result.classes,
            external_libraries=analysis_result.external_libraries,
            source_code_data=json.dumps(source_code_data),
            ai_documentation_data=json.dumps(ai_documentation_data),
            syntax_css=self.syntax_highlighter.get_css_styles(),
            is_subpage=False,
            current_date=datetime.now().strftime('%d/%m/%Y %H:%M')
        )

        with open(self.output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_module_pages(self, analysis_result: AnalysisResult) -> None:
        """Gera páginas individuais para cada módulo."""
        modules_dir = self.output_dir / 'modules'
        modules_dir.mkdir(exist_ok=True)

        template = self.templates.get_template('module.html')

        for file_path, file_info in analysis_result.files.items():
            # Nome do arquivo de saída
            safe_name = file_path.replace('/', '_').replace('\\', '_').replace('.py', '.html')

            content = template.render(
                title=f"Módulo: {Path(file_path).name}",
                file_path=file_path,
                file_info=file_info,
                all_files=analysis_result.files,
                is_subpage=True,
                current_date=datetime.now().strftime('%d/%m/%Y %H:%M')
            )

            with open(modules_dir / safe_name, 'w', encoding='utf-8') as f:
                f.write(content)

    def _generate_class_pages(self, analysis_result: AnalysisResult) -> None:
        """Gera páginas individuais para cada classe."""
        classes_dir = self.output_dir / 'classes'
        classes_dir.mkdir(exist_ok=True)

        template = self.templates.get_template('class.html')

        for class_key, class_info in analysis_result.classes.items():
            # Nome do arquivo de saída
            safe_name = class_key.replace('::', '_').replace('/', '_').replace('\\', '_') + '.html'

            content = template.render(
                title=f"Classe: {class_info.name}",
                class_key=class_key,
                class_info=class_info,
                all_classes=analysis_result.classes,
                is_subpage=True,
                current_date=datetime.now().strftime('%d/%m/%Y %H:%M')
            )

            with open(classes_dir / safe_name, 'w', encoding='utf-8') as f:
                f.write(content)

    def _copy_assets(self) -> None:
        """Copia arquivos estáticos (CSS, JS)."""
        assets_dir = self.output_dir / 'assets'
        assets_dir.mkdir(exist_ok=True)

        # Cria arquivo CSS customizado
        css_content = self._get_custom_css()
        with open(assets_dir / 'style.css', 'w', encoding='utf-8') as f:
            f.write(css_content)

        # Cria arquivo JavaScript
        js_content = self._get_custom_js()
        with open(assets_dir / 'script.js', 'w', encoding='utf-8') as f:
            f.write(js_content)

    def _get_base_template(self) -> str:
        """Template base com Tailwind CSS."""
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ title }}{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="./assets/style.css">
    <style>
        :root {
            --color-primary: #3b82f6;
            --color-secondary: #64748b;
        }
        .text-primary { color: var(--color-primary); }
        .border-primary { border-color: var(--color-primary); }
        .bg-primary { background-color: var(--color-primary); }
        .hover\:text-primary:hover { color: var(--color-primary); }
        .hover\:border-primary:hover { border-color: var(--color-primary); }
        .text-secondary { color: var(--color-secondary); }
        
        /* Code viewer modal styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal.show {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background-color: #1e1e1e;
            border-radius: 8px;
            max-width: 95vw;
            max-height: 95vh;
            width: 1200px;
            height: 800px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .modal-header {
            background-color: #2d2d30;
            color: #d4d4d4;
            padding: 15px 20px;
            border-bottom: 1px solid #424245;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-body {
            flex: 1;
            overflow: auto;
            background-color: #1e1e1e;
        }
        
        .close-btn {
            background: none;
            border: none;
            color: #d4d4d4;
            font-size: 24px;
            cursor: pointer;
            padding: 0;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
        }
        
        .close-btn:hover {
            background-color: #424245;
        }
        
        .clickable-code {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .clickable-code:hover {
            background-color: rgba(59, 130, 246, 0.1);
        }
        
        /* Estilos específicos para a aba de Documentação IA */
        #documentationContent {
            padding: 20px;
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        
        #documentationContent .prose {
            color: #d4d4d4;
            max-width: none;
        }
        
        #documentationContent h1,
        #documentationContent h2,
        #documentationContent h3,
        #documentationContent h4,
        #documentationContent h5,
        #documentationContent h6 {
            color: #ffffff;
            margin-top: 24px;
            margin-bottom: 16px;
        }
        
        #documentationContent h1 {
            font-size: 1.75rem;
            font-weight: bold;
            border-bottom: 2px solid #424245;
            padding-bottom: 8px;
        }
        
        #documentationContent h2 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        #documentationContent h3 {
            font-size: 1.25rem;
            font-weight: 600;
        }
        
        #documentationContent p {
            color: #d4d4d4;
            margin-bottom: 1rem;
        }
        
        #documentationContent strong {
            color: #ffffff;
            font-weight: 600;
        }
        
        #documentationContent em {
            color: #ffd700;
            font-style: italic;
        }
        
        #documentationContent code {
            background-color: #2d2d30;
            color: #ffd700;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        #documentationContent pre {
            background-color: #2d2d30;
            color: #d4d4d4;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 16px 0;
            border: 1px solid #424245;
        }
        
        #documentationContent pre code {
            background-color: transparent;
            color: inherit;
            padding: 0;
        }
        
        #documentationContent ul,
        #documentationContent ol {
            color: #d4d4d4;
            margin: 16px 0;
            padding-left: 20px;
        }
        
        #documentationContent li {
            margin-bottom: 8px;
            color: #d4d4d4;
        }
        
        #documentationContent blockquote {
            border-left: 4px solid #0066cc;
            padding-left: 16px;
            margin: 16px 0;
            color: #b3b3b3;
            font-style: italic;
        }
        
        #documentationContent a {
            color: #4fc3f7;
            text-decoration: underline;
        }
        
        #documentationContent a:hover {
            color: #81d4fa;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-xl font-semibold text-gray-900">
                        <a href="{{ '../index.html' if is_subpage else 'index.html' }}" class="hover:text-primary">
                            📚 Documentação do Projeto
                        </a>
                    </h1>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="{{ '../index.html' if is_subpage else 'index.html' }}" 
                       class="text-secondary hover:text-primary px-3 py-2 rounded-md text-sm font-medium">
                        🏠 Início
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {% block content %}{% endblock %}
    </main>

    <!-- Code Viewer Modal -->
    <div id="codeModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalTitle">Código Fonte</h3>
                <button class="close-btn" onclick="closeCodeModal()">&times;</button>
            </div>
            <div class="search-container">
                <input type="text" id="searchInput" class="search-input" placeholder="Buscar no código..." onkeyup="searchInCode()" />
                <div class="search-info" id="searchInfo"></div>
            </div>
            <div class="modal-body">
                <div id="codeContainer"></div>
            </div>
        </div>
    </div>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-12">
        <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <p class="text-center text-sm text-gray-500">
                Gerado pela Ferramenta de Documentação Python • {{ current_date }}
            </p>
        </div>
    </footer>

    <script src="./assets/script.js"></script>
</body>
</html>"""

    def _get_index_template(self) -> str:
        """Template da página principal."""
        return """{% extends "base.html" %}

{% block content %}
<div class="space-y-8">
    <!-- Header -->
    <div class="text-center">
        <h1 class="text-4xl font-bold text-gray-900 mb-4">📊 Análise de Dependências</h1>
        <p class="text-lg text-gray-600 max-w-2xl mx-auto">
            Explore as dependências e relacionamentos do seu projeto Python através de grafos interativos
        </p>
    </div>

    <!-- Search Bar -->
    <div class="max-w-2xl mx-auto">
        <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg class="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
                </svg>
            </div>
            <input type="text" id="globalSearch" placeholder="Buscar por nome de arquivo ou conteúdo..." 
                   class="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary focus:border-primary">
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                <button id="clearSearch" class="text-gray-400 hover:text-gray-600 hidden">
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
        <div id="searchInfo" class="mt-2 text-sm text-gray-600 hidden"></div>
    </div>

    <!-- Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <span class="text-2xl">📁</span>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-gray-500">Arquivos</p>
                    <p class="text-2xl font-semibold text-gray-900">{{ stats.total_files }}</p>
                </div>
            </div>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <span class="text-2xl">🏗️</span>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-gray-500">Classes</p>
                    <p class="text-2xl font-semibold text-gray-900">{{ stats.total_classes }}</p>
                </div>
            </div>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <span class="text-2xl">⚙️</span>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-gray-500">Funções</p>
                    <p class="text-2xl font-semibold text-gray-900">{{ stats.total_functions }}</p>
                </div>
            </div>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <span class="text-2xl">🔗</span>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-gray-500">Imports</p>
                    <p class="text-2xl font-semibold text-gray-900">{{ stats.total_imports }}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Graph Tabs -->
    {% if graph_files %}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200">
        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-8 px-6" aria-label="Tabs">
                {% if 'files' in graph_files %}
                <button onclick="showGraph('files')" id="tab-files" 
                        class="tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                    📁 Dependências entre Arquivos
                </button>
                {% endif %}
                {% if 'classes' in graph_files %}
                <button onclick="showGraph('classes')" id="tab-classes"
                        class="tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm">
                    🏗️ Dependências entre Classes
                </button>
                {% endif %}
            </nav>
        </div>
        
        <div class="p-6">
            {% if 'files' in graph_files %}
            <div id="graph-files" class="graph-container">
                <iframe src="{{ graph_files.files }}" class="w-full h-96 border-0 rounded-lg"></iframe>
            </div>
            {% endif %}
            
            {% if 'classes' in graph_files %}
            <div id="graph-classes" class="graph-container hidden">
                <iframe src="{{ graph_files.classes }}" class="w-full h-96 border-0 rounded-lg"></iframe>
            </div>
            {% endif %}
        </div>
    </div>
    {% endif %}

    <!-- Quick Navigation -->
    <div class="grid grid-cols-1 lg:grid-cols-3 md:grid-cols-2 gap-6">
        <!-- Files List -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">📁 Módulos do Projeto</h3>
                <p id="filesCount" class="text-sm text-gray-500">{{ files|length }} arquivo(s)</p>
            </div>
            <div class="p-6">
                <div id="filesList" class="space-y-2 max-h-96 overflow-y-auto">
                    {% for file_path, file_info in files.items() %}
                    <div class="file-item flex items-center justify-between p-3 bg-gray-50 rounded-lg clickable-code" 
                         data-file-path="{{ file_path }}"
                         data-file-name="{{ file_path.split('/')[-1] }}"
                         data-file-content="{{ file_info.source_code|replace('\"', '&quot;')|replace(\"'\", '&#39;')|replace('\n', ' ')|replace('\r', '')|truncate(500) if file_info.source_code else '' }}"
                         onclick="selectFile('{{ file_path }}', '{{ file_path.split('/')[-1] }}')">
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900 truncate">
                                {{ file_path.split('/')[-1] }}
                            </p>
                            <p class="text-xs text-gray-500">{{ file_path }}</p>
                        </div>
                        <div class="flex items-center space-x-2 text-xs text-gray-500">
                            <span>{{ file_info.classes|length }}c</span>
                            <span>{{ file_info.functions|length }}f</span>
                            {% if file_info.ai_documentation %}
                            <span class="text-green-500" title="Documentação IA disponível">🤖</span>
                            {% endif %}
                            <span class="text-blue-500 cursor-pointer" onclick="event.stopPropagation(); showSourceCode('{{ file_path }}', '{{ file_path.split('/')[-1] }}')">👁️</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Classes List -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">🏗️ Classes do Projeto</h3>
                <p id="classesCount" class="text-sm text-gray-500">{{ classes|length }} classe(s)</p>
            </div>
            <div class="p-6">
                <div id="classesList" class="space-y-2 max-h-96 overflow-y-auto">
                    {% for class_key, class_info in classes.items() %}
                    <div class="class-item flex items-center justify-between p-3 bg-gray-50 rounded-lg clickable-code" 
                         data-class-name="{{ class_info.name }}"
                         data-file-path="{{ class_key.split('::')[0] }}"
                         onclick="selectClass('{{ class_key.split('::')[0] }}', '{{ class_info.name }}')">
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900 truncate">
                                {{ class_info.name }}
                            </p>
                            <p class="text-xs text-gray-500">{{ class_key.split('::')[0] }}</p>
                        </div>
                        <div class="flex items-center space-x-2 text-xs text-gray-500">
                            <span>{{ class_info.methods|length }}m</span>
                            <span>{{ class_info.attributes|length }}a</span>
                            <span class="text-blue-500">👁️</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- External Libraries List -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-medium text-gray-900">📦 Bibliotecas Externas</h3>
            </div>
            <div class="p-6">
                {% if external_libraries %}
                <div class="space-y-2 max-h-96 overflow-y-auto">
                    {% for lib_name, count in external_libraries.items() %}
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-gray-900 truncate">
                                {{ lib_name }}
                            </p>
                            <p class="text-xs text-gray-500">Biblioteca externa</p>
                        </div>
                        <div class="flex items-center space-x-2 text-xs text-gray-500">
                            <span>{{ count }} uso{{ 's' if count > 1 else '' }}</span>
                            <span class="text-green-500">📦</span>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <p class="text-sm text-gray-500 text-center py-4">
                    Nenhuma biblioteca externa detectada
                </p>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<script>
function showGraph(type) {
    // Hide all graphs
    document.querySelectorAll('.graph-container').forEach(el => el.classList.add('hidden'));
    // Remove active from all tabs
    document.querySelectorAll('.tab-button').forEach(el => {
        el.classList.remove('border-primary', 'text-primary');
        el.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Show selected graph
    document.getElementById('graph-' + type).classList.remove('hidden');
    // Activate selected tab
    const tab = document.getElementById('tab-' + type);
    tab.classList.remove('border-transparent', 'text-gray-500');
    tab.classList.add('border-primary', 'text-primary');
}

// Code viewer functionality
const sourceCodeData = {{ source_code_data|safe }};
const aiDocumentationData = {{ ai_documentation_data|safe }};
let currentFilePath = '';
let originalCode = '';
let currentFilter = { type: 'all', value: '' };

// Global search and filter functionality
function initializeSearch() {
    const searchInput = document.getElementById('globalSearch');
    const clearButton = document.getElementById('clearSearch');
    const searchInfo = document.getElementById('searchInfo');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.trim();
            if (searchTerm) {
                clearButton.classList.remove('hidden');
                searchInfo.classList.remove('hidden');
                performGlobalSearch(searchTerm);
            } else {
                clearButton.classList.add('hidden');
                searchInfo.classList.add('hidden');
                clearFilters();
            }
        });
    }
    
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            searchInput.value = '';
            clearButton.classList.add('hidden');
            searchInfo.classList.add('hidden');
            clearFilters();
        });
    }
}

function performGlobalSearch(searchTerm) {
    const fileItems = document.querySelectorAll('.file-item');
    const classItems = document.querySelectorAll('.class-item');
    const searchInfo = document.getElementById('searchInfo');
    
    let visibleFiles = 0;
    let visibleClasses = 0;
    
    // Search in files
    fileItems.forEach(item => {
        const fileName = item.getAttribute('data-file-name').toLowerCase();
        const filePath = item.getAttribute('data-file-path').toLowerCase();
        const fileContent = item.getAttribute('data-file-content').toLowerCase();
        const search = searchTerm.toLowerCase();
        
        const matches = fileName.includes(search) || 
                       filePath.includes(search) || 
                       fileContent.includes(search);
        
        if (matches) {
            item.style.display = 'flex';
            visibleFiles++;
            highlightSearchTerm(item, searchTerm);
        } else {
            item.style.display = 'none';
        }
    });
    
    // Search in classes
    classItems.forEach(item => {
        const className = item.getAttribute('data-class-name').toLowerCase();
        const filePath = item.getAttribute('data-file-path').toLowerCase();
        const search = searchTerm.toLowerCase();
        
        const matches = className.includes(search) || filePath.includes(search);
        
        if (matches) {
            item.style.display = 'flex';
            visibleClasses++;
            highlightSearchTerm(item, searchTerm);
        } else {
            item.style.display = 'none';
        }
    });
    
    // Update counters
    document.getElementById('filesCount').textContent = `${visibleFiles} arquivo(s) encontrado(s)`;
    document.getElementById('classesCount').textContent = `${visibleClasses} classe(s) encontrada(s)`;
    
    // Update search info
    searchInfo.textContent = `Encontrados: ${visibleFiles} arquivos, ${visibleClasses} classes`;
    
    // Filter graph
    filterGraphBySearch(searchTerm);
}

function highlightSearchTerm(item, searchTerm) {
    const elements = item.querySelectorAll('p');
    elements.forEach(el => {
        const text = el.textContent;
        const regex = new RegExp(`(${escapeRegex(searchTerm)})`, 'gi');
        const highlightedText = text.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
        if (highlightedText !== text) {
            el.innerHTML = highlightedText;
        }
    });
}

function clearFilters() {
    const fileItems = document.querySelectorAll('.file-item');
    const classItems = document.querySelectorAll('.class-item');
    
    // Show all items
    fileItems.forEach(item => {
        item.style.display = 'flex';
        // Remove highlights
        const elements = item.querySelectorAll('p');
        elements.forEach(el => {
            el.innerHTML = el.textContent;
        });
    });
    
    classItems.forEach(item => {
        item.style.display = 'flex';
        // Remove highlights
        const elements = item.querySelectorAll('p');
        elements.forEach(el => {
            el.innerHTML = el.textContent;
        });
    });
    
    // Reset counters
    document.getElementById('filesCount').textContent = `${fileItems.length} arquivo(s)`;
    document.getElementById('classesCount').textContent = `${classItems.length} classe(s)`;
    
    // Reset filter
    currentFilter = { type: 'all', value: '' };
    
    // Reset graph
    resetGraphFilter();
}

function selectFile(filePath, fileName) {
    // Update current filter
    currentFilter = { type: 'file', value: filePath };
    
    // Highlight selected file
    document.querySelectorAll('.file-item').forEach(item => {
        item.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
    });
    
    const selectedItem = document.querySelector(`[data-file-path="${filePath}"]`);
    if (selectedItem) {
        selectedItem.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50');
    }
    
    // Filter graph to show only relationships of this file
    filterGraphByFile(filePath);
}

function selectClass(filePath, className) {
    // Update current filter
    currentFilter = { type: 'class', value: filePath };
    
    // Highlight selected class
    document.querySelectorAll('.class-item').forEach(item => {
        item.classList.remove('ring-2', 'ring-blue-500', 'bg-blue-50');
    });
    
    const selectedItem = document.querySelector(`[data-file-path="${filePath}"][data-class-name="${className}"]`);
    if (selectedItem) {
        selectedItem.classList.add('ring-2', 'ring-blue-500', 'bg-blue-50');
    }
    
    // Filter graph to show only relationships of this file
    filterGraphByFile(filePath);
}

function filterGraphBySearch(searchTerm) {
    // Send message to iframe to filter graph
    const activeGraph = document.querySelector('.graph-container:not(.hidden) iframe');
    if (activeGraph) {
        activeGraph.contentWindow.postMessage({
            action: 'filterBySearch',
            searchTerm: searchTerm
        }, '*');
    }
}

function filterGraphByFile(filePath) {
    // Send message to iframe to filter graph by file
    const activeGraph = document.querySelector('.graph-container:not(.hidden) iframe');
    if (activeGraph) {
        activeGraph.contentWindow.postMessage({
            action: 'filterByFile',
            filePath: filePath
        }, '*');
    }
}

function resetGraphFilter() {
    // Send message to iframe to reset graph filter
    const activeGraph = document.querySelector('.graph-container:not(.hidden) iframe');
    if (activeGraph) {
        activeGraph.contentWindow.postMessage({
            action: 'resetFilter'
        }, '*');
    }
}

function showSourceCode(filePath, displayName) {
    const codeData = sourceCodeData[filePath];
    if (!codeData) {
        alert('Código fonte não disponível para este arquivo.');
        return;
    }
    
    // Store current file info for search
    currentFilePath = filePath;
    originalCode = codeData.code;
    
    // Generate line numbers
    const lineNumbers = Array.from({length: codeData.line_count}, (_, i) => i + 1).join('\\n');
    
    // Check if AI documentation is available
    const aiDoc = aiDocumentationData[filePath];
    let tabsHtml = `
        <div class="border-b border-gray-200 mb-4">
            <nav class="-mb-px flex space-x-8" aria-label="Tabs">
                <button onclick="showCodeTab()" id="codeTab" 
                        class="tab-button border-primary text-primary hover:text-primary hover:border-primary whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm">
                    📄 Código Fonte
                </button>`;
    
    if (aiDoc) {
        tabsHtml += `
                <button onclick="showDocumentationTab()" id="docTab" 
                        class="tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm">
                    🤖 Documentação IA
                </button>`;
    }
    
    tabsHtml += `
            </nav>
        </div>`;
    
    // Update modal content
    document.getElementById('modalTitle').textContent = displayName + ' - ' + filePath;
    document.getElementById('codeContainer').innerHTML = tabsHtml + `
        <div id="codeContent">
            <div class="code-container">
                <div class="line-numbers">${lineNumbers}</div>
                <div class="source-code with-lines" id="sourceCodeContent">${codeData.code}</div>
            </div>
        </div>
        <div id="documentationContent" class="hidden prose max-w-none">
            ${aiDoc ? convertMarkdownToHtml(aiDoc.markdown) : '<p>Documentação IA não disponível</p>'}
        </div>
    `;
    
    // Clear search
    document.getElementById('searchInput').value = '';
    document.getElementById('searchInfo').textContent = '';
    
    // Show modal
    document.getElementById('codeModal').classList.add('show');
    
    // Focus search input after modal is shown
    setTimeout(() => {
        document.getElementById('searchInput').focus();
    }, 100);
}

function showCodeTab() {
    // Update tab styles
    document.getElementById('codeTab').className = 'tab-button border-primary text-primary hover:text-primary hover:border-primary whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm';
    document.getElementById('docTab').className = 'tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm';
    
    // Show/hide content
    document.getElementById('codeContent').classList.remove('hidden');
    document.getElementById('documentationContent').classList.add('hidden');
}

function showDocumentationTab() {
    // Update tab styles
    document.getElementById('docTab').className = 'tab-button border-primary text-primary hover:text-primary hover:border-primary whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm';
    document.getElementById('codeTab').className = 'tab-button border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm';
    
    // Show/hide content
    document.getElementById('codeContent').classList.add('hidden');
    document.getElementById('documentationContent').classList.remove('hidden');
}

function convertMarkdownToHtml(markdown) {
    // Simple markdown to HTML converter for basic formatting
    return markdown
        .replace(/### (.+)/g, '<h3>$1</h3>')
        .replace(/## (.+)/g, '<h2>$1</h2>')
        .replace(/# (.+)/g, '<h1>$1</h1>')
        .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\*(.+?)\\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>')
        .replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/((<li.*<\\/li>\\s*)+)/g, '<ul>$1</ul>')
        .replace(/\\n\\n/g, '</p><p>')
        .replace(/^(.+)$/gm, '<p>$1</p>')
        .replace(/<p><\\/p>/g, '');
}

function searchInCode() {
    const searchTerm = document.getElementById('searchInput').value;
    const sourceContent = document.getElementById('sourceCodeContent');
    const searchInfo = document.getElementById('searchInfo');
    
    if (!sourceContent || !originalCode) {
        return; // No code loaded yet
    }
    
    if (!searchTerm.trim()) {
        // Restore original code if search is empty
        sourceContent.innerHTML = originalCode;
        searchInfo.textContent = '';
        return;
    }
    
    // Count matches
    const regex = new RegExp(escapeRegex(searchTerm), 'gi');
    const matches = originalCode.match(regex);
    const matchCount = matches ? matches.length : 0;
    
    if (matchCount > 0) {
        // Highlight matches
        const highlightedCode = originalCode.replace(regex, `<mark class="search-highlight">$&</mark>`);
        sourceContent.innerHTML = highlightedCode;
        searchInfo.textContent = `${matchCount} resultado${matchCount > 1 ? 's' : ''}`;
    } else {
        sourceContent.innerHTML = originalCode;
        searchInfo.textContent = 'Nenhum resultado';
    }
}

function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
}

function closeCodeModal() {
    document.getElementById('codeModal').classList.remove('show');
    // Clear search when closing
    document.getElementById('searchInput').value = '';
    document.getElementById('searchInfo').textContent = '';
}

// Initialize with first available graph and setup event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Setup modal event listeners
    const codeModal = document.getElementById('codeModal');
    if (codeModal) {
        // Close modal when clicking outside
        codeModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeCodeModal();
            }
        });
    }
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeCodeModal();
        }
    });
    
    // Listen for messages from iframes (graphs)
    window.addEventListener('message', function(event) {
        // Verifica se a mensagem é para mostrar código fonte
        if (event.data && event.data.action === 'showSourceCode') {
            showSourceCode(event.data.filePath, event.data.displayName);
        }
    });
    
    // Initialize graph
    {% if 'files' in graph_files %}
    showGraph('files');
    {% elif 'classes' in graph_files %}
    showGraph('classes');
    {% endif %}
});
</script>

<style>
{{ syntax_css|safe }}
</style>
{% endblock %}"""

    def _get_module_template(self) -> str:
        """Template para páginas de módulos."""
        return """{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">📁 {{ file_path.split('/')[-1] }}</h1>
                <p class="text-sm text-gray-500 mt-1">{{ file_path }}</p>
            </div>
            <div class="flex space-x-4 text-sm text-gray-500">
                <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded">{{ file_info.classes|length }} classes</span>
                <span class="bg-green-100 text-green-800 px-2 py-1 rounded">{{ file_info.functions|length }} funções</span>
                <span class="bg-purple-100 text-purple-800 px-2 py-1 rounded">{{ file_info.imports|length }} imports</span>
            </div>
        </div>
    </div>

    <!-- Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Classes -->
        {% if file_info.classes %}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h2 class="text-lg font-medium text-gray-900">🏗️ Classes</h2>
            </div>
            <div class="p-6">
                <div class="space-y-4">
                    {% for class_info in file_info.classes %}
                    <div class="border border-gray-200 rounded-lg p-4">
                        <h3 class="font-medium text-gray-900">{{ class_info.name }}</h3>
                        <p class="text-sm text-gray-500 mt-1">Linha {{ class_info.line_number }}</p>
                        
                        {% if class_info.base_classes %}
                        <div class="mt-2">
                            <span class="text-xs text-gray-500">Herda de:</span>
                            <div class="flex flex-wrap gap-1 mt-1">
                                {% for base in class_info.base_classes %}
                                <span class="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">{{ base }}</span>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                        
                        <div class="mt-3 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <span class="text-gray-500">Métodos: {{ class_info.methods|length }}</span>
                                {% if class_info.methods %}
                                <ul class="mt-1 text-xs text-gray-600">
                                    {% for method in class_info.methods[:3] %}
                                    <li>• {{ method }}</li>
                                    {% endfor %}
                                    {% if class_info.methods|length > 3 %}
                                    <li class="text-gray-400">... e mais {{ class_info.methods|length - 3 }}</li>
                                    {% endif %}
                                </ul>
                                {% endif %}
                            </div>
                            <div>
                                <span class="text-gray-500">Atributos: {{ class_info.attributes|length }}</span>
                                {% if class_info.attributes %}
                                <ul class="mt-1 text-xs text-gray-600">
                                    {% for attr in class_info.attributes[:3] %}
                                    <li>• {{ attr }}</li>
                                    {% endfor %}
                                    {% if class_info.attributes|length > 3 %}
                                    <li class="text-gray-400">... e mais {{ class_info.attributes|length - 3 }}</li>
                                    {% endif %}
                                </ul>
                                {% endif %}
                            </div>
                        </div>
                        
                        {% if class_info.docstring %}
                        <div class="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                            {{ class_info.docstring[:100] }}{% if class_info.docstring|length > 100 %}...{% endif %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Functions -->
        {% if file_info.functions %}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h2 class="text-lg font-medium text-gray-900">⚙️ Funções</h2>
            </div>
            <div class="p-6">
                <div class="space-y-3">
                    {% for func_info in file_info.functions %}
                    <div class="border border-gray-200 rounded-lg p-3">
                        <h3 class="font-medium text-gray-900">{{ func_info.name }}</h3>
                        <p class="text-sm text-gray-500">Linha {{ func_info.line_number }}</p>
                        
                        {% if func_info.parameters %}
                        <div class="mt-2">
                            <span class="text-xs text-gray-500">Parâmetros:</span>
                            <div class="flex flex-wrap gap-1 mt-1">
                                {% for param in func_info.parameters %}
                                <span class="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded">{{ param }}</span>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                        
                        {% if func_info.docstring %}
                        <div class="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
                            {{ func_info.docstring[:100] }}{% if func_info.docstring|length > 100 %}...{% endif %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Dependencies -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Imports -->
        {% if file_info.imports %}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h2 class="text-lg font-medium text-gray-900">📦 Imports</h2>
            </div>
            <div class="p-6">
                <div class="space-y-2">
                    {% for import_info in file_info.imports %}
                    <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <span class="text-sm font-mono text-gray-900">{{ import_info.module }}</span>
                        {% if import_info.is_relative %}
                        <span class="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded">relativo</span>
                        {% else %}
                        <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">absoluto</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Dependencies -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h2 class="text-lg font-medium text-gray-900">🔗 Relacionamentos</h2>
            </div>
            <div class="p-6">
                <div class="space-y-4">
                    {% if file_info.dependencies %}
                    <div>
                        <h3 class="text-sm font-medium text-gray-700 mb-2">Depende de ({{ file_info.dependencies|length }}):</h3>
                        <div class="space-y-1">
                            {% for dep in file_info.dependencies %}
                            <div class="text-sm text-gray-600 bg-red-50 p-2 rounded">
                                → {{ dep.split('/')[-1] }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if file_info.dependents %}
                    <div>
                        <h3 class="text-sm font-medium text-gray-700 mb-2">É usado por ({{ file_info.dependents|length }}):</h3>
                        <div class="space-y-1">
                            {% for dep in file_info.dependents %}
                            <div class="text-sm text-gray-600 bg-green-50 p-2 rounded">
                                ← {{ dep.split('/')[-1] }}
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if not file_info.dependencies and not file_info.dependents %}
                    <p class="text-sm text-gray-500 italic">Nenhuma dependência identificada</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""

    def _get_class_template(self) -> str:
        """Template para páginas de classes."""
        return """{% extends "base.html" %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl font-bold text-gray-900">🏗️ {{ class_info.name }}</h1>
                <p class="text-sm text-gray-500 mt-1">{{ class_info.file_path.name }} • Linha {{ class_info.line_number }}</p>
            </div>
            <div class="flex space-x-4 text-sm text-gray-500">
                <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded">{{ class_info.methods|length }} métodos</span>
                <span class="bg-green-100 text-green-800 px-2 py-1 rounded">{{ class_info.attributes|length }} atributos</span>
            </div>
        </div>
    </div>

    <!-- Documentation -->
    {% if class_info.docstring %}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-3">📖 Documentação</h2>
        <div class="prose text-gray-700">
            <pre class="whitespace-pre-wrap bg-gray-50 p-4 rounded text-sm">{{ class_info.docstring }}</pre>
        </div>
    </div>
    {% endif %}

    <!-- Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Methods -->
        {% if class_info.methods %}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h2 class="text-lg font-medium text-gray-900">⚙️ Métodos</h2>
            </div>
            <div class="p-6">
                <div class="space-y-2">
                    {% for method in class_info.methods %}
                    <div class="flex items-center p-3 bg-gray-50 rounded-lg">
                        <span class="text-sm font-mono text-gray-900">{{ method }}()</span>
                        {% if method.startswith('_') and not method.startswith('__') %}
                        <span class="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">privado</span>
                        {% elif method.startswith('__') and method.endswith('__') %}
                        <span class="ml-2 bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">especial</span>
                        {% else %}
                        <span class="ml-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">público</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}

        <!-- Attributes -->
        {% if class_info.attributes %}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="px-6 py-4 border-b border-gray-200">
                <h2 class="text-lg font-medium text-gray-900">📊 Atributos</h2>
            </div>
            <div class="p-6">
                <div class="space-y-2">
                    {% for attr in class_info.attributes %}
                    <div class="flex items-center p-3 bg-gray-50 rounded-lg">
                        <span class="text-sm font-mono text-gray-900">{{ attr }}</span>
                        {% if attr.startswith('_') and not attr.startswith('__') %}
                        <span class="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">privado</span>
                        {% elif attr.startswith('__') and attr.endswith('__') %}
                        <span class="ml-2 bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded">especial</span>
                        {% else %}
                        <span class="ml-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">público</span>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endif %}
    </div>

    <!-- Inheritance -->
    {% if class_info.base_classes %}
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-3">🔗 Herança</h2>
        <div class="space-y-2">
            {% for base_class in class_info.base_classes %}
            <div class="flex items-center p-3 bg-blue-50 rounded-lg">
                <span class="text-sm text-gray-900">
                    <span class="font-medium">{{ class_info.name }}</span> 
                    <span class="text-gray-500">herda de</span> 
                    <span class="font-medium text-blue-700">{{ base_class }}</span>
                </span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <!-- Related Classes -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 class="text-lg font-medium text-gray-900 mb-3">🏗️ Classes Relacionadas</h2>
        <div class="space-y-2">
            {% set related_classes = [] %}
            {% for other_key, other_class in all_classes.items() %}
                {% if other_class.file_path == class_info.file_path and other_class.name != class_info.name %}
                    {% set _ = related_classes.append(other_class) %}
                {% endif %}
            {% endfor %}
            
            {% if related_classes %}
                {% for related in related_classes %}
                <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span class="text-sm font-medium text-gray-900">{{ related.name }}</span>
                    <span class="text-xs text-gray-500">mesmo arquivo</span>
                </div>
                {% endfor %}
            {% else %}
                <p class="text-sm text-gray-500 italic">Nenhuma classe relacionada encontrada no mesmo arquivo</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}"""

    def _get_custom_css(self) -> str:
        """CSS customizado adicional."""
        return """
/* Estilos customizados para a documentação */
.graph-container iframe {
    min-height: 500px;
}

.tab-button {
    transition: all 0.2s ease-in-out;
}

.tab-button:hover {
    transform: translateY(-1px);
}

/* Melhorias de acessibilidade */
.prose pre {
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.4;
}

/* Animações suaves */
.bg-white {
    transition: box-shadow 0.2s ease-in-out;
}

.bg-white:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

/* Scroll customizado */
.overflow-y-auto::-webkit-scrollbar {
    width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
    background: #a1a1a1;
}
"""

    def _get_custom_js(self) -> str:
        """JavaScript customizado adicional."""
        return """
// Funcionalidades JavaScript customizadas

document.addEventListener('DOMContentLoaded', function() {
    // Adiciona tooltips para elementos truncados
    const truncatedElements = document.querySelectorAll('.truncate');
    truncatedElements.forEach(el => {
        if (el.scrollWidth > el.clientWidth) {
            el.title = el.textContent;
        }
    });
    
    // Adiciona efeitos de hover suaves
    const cards = document.querySelectorAll('.bg-white');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Adiciona funcionalidade de busca rápida
    addQuickSearch();
});

function addQuickSearch() {
    // Adiciona campo de busca se houver listas
    const lists = document.querySelectorAll('.space-y-2');
    lists.forEach(list => {
        if (list.children.length > 5) {
            const searchInput = document.createElement('input');
            searchInput.type = 'text';
            searchInput.placeholder = 'Buscar...';
            searchInput.className = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm mb-4';
            
            searchInput.addEventListener('input', function() {
                const query = this.value.toLowerCase();
                Array.from(list.children).forEach(item => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(query) ? 'block' : 'none';
                });
            });
            
            list.parentNode.insertBefore(searchInput, list);
        }
    });
}

// Utilitários de navegação
function goBack() {
    window.history.back();
}

function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Adiciona botão de voltar ao topo
window.addEventListener('scroll', function() {
    const scrollBtn = document.getElementById('scroll-top-btn');
    if (!scrollBtn) {
        const btn = document.createElement('button');
        btn.id = 'scroll-top-btn';
        btn.innerHTML = '↑';
        btn.className = 'fixed bottom-4 right-4 bg-primary text-white p-3 rounded-full shadow-lg hover:bg-blue-600 transition-all duration-200 opacity-0';
        btn.onclick = scrollToTop;
        document.body.appendChild(btn);
    }
    
    const btn = document.getElementById('scroll-top-btn');
    if (window.pageYOffset > 300) {
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    } else {
        btn.style.opacity = '0';
        btn.style.pointerEvents = 'none';
    }
});
"""
