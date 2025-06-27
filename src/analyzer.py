"""
Analisador de código Python para extração de dependências.
"""

import ast
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

from .models import (
    AnalysisResult, FileInfo, ClassInfo, FunctionInfo,
    ImportInfo
)


class ProjectAnalyzer:
    """Analisa um projeto Python para extrair dependências e estruturas."""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o analisador.

        Args:
            config: Configurações da aplicação
        """
        self.config = config
        self.root_path = Path(config['root_directory']).resolve()
        self.ignore_patterns = config.get('ignore_patterns', [])
        self.ai_analyzer = None  # Será inicializado se IA estiver habilitada

    def set_ai_analyzer(self, ai_analyzer):
        """Define o analisador de IA."""
        self.ai_analyzer = ai_analyzer

    def analyze(self, enable_ai: bool = False) -> AnalysisResult:
        """
        Analisa o projeto completo.

        Args:
            enable_ai: Se deve executar análise com IA

        Returns:
            Resultado da análise contendo todos os dados extraídos
        """
        result = AnalysisResult()

        # Encontra todos os arquivos Python
        python_files = self._find_python_files()

        # Analisa cada arquivo
        for file_path in python_files:
            try:
                file_info = self._analyze_file(file_path)
                if file_info:
                    relative_path = str(file_path.relative_to(self.root_path))
                    result.files[relative_path] = file_info

                    # Adiciona classes ao dicionário global
                    for class_info in file_info.classes:
                        result.classes[f"{relative_path}::{class_info.name}"] = class_info

            except Exception as e:
                print(f"⚠️  Erro ao analisar {file_path}: {e}")

        # Constrói grafos de dependências
        self._build_dependency_graphs(result)

        # Coleta bibliotecas externas
        self._collect_external_libraries(result)

        # Executa análise de IA se habilitada
        if enable_ai and self.ai_analyzer:
            print("🤖 Iniciando análise de IA...")
            try:
                ai_docs = self.ai_analyzer.analyze_all_files(result, self.root_path)

                # Adiciona documentação IA aos arquivos
                for file_path, doc_result in ai_docs.items():
                    if file_path in result.files and not doc_result.error:
                        file_info = result.files[file_path]
                        file_info.ai_documentation = doc_result.markdown_content
                        file_info.ai_summary = doc_result.summary
                        file_info.ai_purpose = doc_result.purpose

                print("✅ Análise de IA concluída!")
            except Exception as e:
                print(f"❌ Erro na análise de IA: {e}")

        return result

    def _find_python_files(self) -> List[Path]:
        """
        Encontra todos os arquivos Python no projeto.

        Returns:
            Lista de caminhos para arquivos Python
        """
        python_files = []

        for file_path in self.root_path.rglob("*.py"):
            # Verifica se deve ignorar o arquivo
            relative_path = file_path.relative_to(self.root_path)

            should_ignore = False
            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(str(relative_path), pattern) or \
                   fnmatch.fnmatch(file_path.name, pattern) or \
                   any(fnmatch.fnmatch(part, pattern) for part in relative_path.parts):
                    should_ignore = True
                    break

            if not should_ignore:
                python_files.append(file_path)

        return python_files

    def _analyze_file(self, file_path: Path) -> FileInfo:
        """
        Analisa um arquivo Python individual.

        Args:
            file_path: Caminho para o arquivo

        Returns:
            Informações extraídas do arquivo
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except UnicodeDecodeError:
            # Tenta com latin-1 se UTF-8 falhar
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"⚠️  Erro de sintaxe em {file_path}: {e}")
            return None

        file_info = FileInfo(path=file_path, source_code=content)

        # Analisa o AST
        analyzer = FileAnalyzer(file_info)
        analyzer.visit(tree)

        return file_info

    def _build_dependency_graphs(self, result: AnalysisResult) -> None:
        """
        Constrói os grafos de dependências entre arquivos e classes.

        Args:
            result: Resultado da análise a ser completado
        """
        # Mapeia módulos para arquivos
        module_to_file = {}
        for file_path, file_info in result.files.items():
            # Converte caminho para nome de módulo
            module_name = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            if module_name.endswith('.__init__'):
                module_name = module_name[:-9]  # Remove .__init__
            module_to_file[module_name] = file_path

            # Também adiciona com prefixo 'app.' para compatibilidade com imports absolutos
            if not module_name.startswith('app.'):
                module_to_file[f'app.{module_name}'] = file_path

        # Mapeia módulos para arquivos
        module_to_file = {}
        for file_path, file_info in result.files.items():
            # Converte caminho para nome de módulo
            module_name = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            if module_name.endswith('.__init__'):
                module_name = module_name[:-9]  # Remove .__init__
            module_to_file[module_name] = file_path

            # Também adiciona com prefixo 'app.' para compatibilidade com imports absolutos
            if not module_name.startswith('app.'):
                module_to_file[f'app.{module_name}'] = file_path

        # Constrói grafo de dependências de arquivos
        for file_path, file_info in result.files.items():
            dependencies = set()

            for import_info in file_info.imports:
                # Usa a nova resolução específica
                target_files = self._resolve_specific_import_target(import_info, module_to_file, file_path)

                for target_file in target_files:
                    if target_file != file_path:  # Não inclui auto-dependências
                        dependencies.add(target_file)

            result.dependencies_graph[file_path] = dependencies

            # Atualiza dependências no FileInfo
            file_info.dependencies = dependencies

        # Constrói dependentes (reverso)
        for file_path, dependencies in result.dependencies_graph.items():
            for dep in dependencies:
                if dep in result.files:
                    result.files[dep].dependents.add(file_path)

        # Também analisa referências de classes para adicionar dependências baseadas em uso
        for file_path, file_info in result.files.items():
            additional_deps = set()

            for ref in file_info.class_references:
                base_name = ref['base_name']

                # Procura por classes importadas que correspondem ao nome base
                for import_info in file_info.imports:
                    if base_name in import_info.names:
                        # Resolve o import para encontrar o arquivo da classe
                        target_files = self._resolve_specific_import_target(import_info, module_to_file, file_path)
                        for target_file in target_files:
                            if target_file != file_path:
                                additional_deps.add(target_file)

            # Adiciona dependências adicionais baseadas em uso
            if additional_deps:
                if file_path in result.dependencies_graph:
                    result.dependencies_graph[file_path].update(additional_deps)
                file_info.dependencies.update(additional_deps)

    def _resolve_import(self, import_info: ImportInfo, current_file: str) -> str:
        """
        Resolve um import para um nome de módulo absoluto.

        Args:
            import_info: Informações do import
            current_file: Arquivo atual (para resolução relativa)

        Returns:
            Nome do módulo resolvido ou None se não conseguir resolver
        """
        if import_info.is_relative:
            # Import relativo
            current_module = current_file.replace('/', '.').replace('\\', '.').replace('.py', '')
            if current_module.endswith('.__init__'):
                current_module = current_module[:-9]

            parts = current_module.split('.')

            # Remove níveis baseado no level do import
            for _ in range(import_info.level):
                if parts:
                    parts.pop()

            if import_info.module:
                parts.append(import_info.module)

            return '.'.join(parts)
        else:
            # Import absoluto
            return import_info.module

    def _resolve_specific_import_target(self, import_info: ImportInfo, module_to_file: dict, current_file: str) -> set:
        """
        Resolve um import para arquivos específicos, não apenas módulos.

        Args:
            import_info: Informações do import
            module_to_file: Mapeamento de módulos para arquivos
            current_file: Arquivo atual

        Returns:
            Set de arquivos alvo específicos
        """
        target_files = set()
        target_module = self._resolve_import(import_info, current_file)

        if not target_module:
            return target_files

        # Se o módulo existe diretamente, adiciona
        if target_module in module_to_file:
            target_files.add(module_to_file[target_module])

        # Para imports específicos (from x import y), tenta encontrar arquivos mais específicos
        if import_info.names and len(import_info.names) > 0:
            for name in import_info.names:
                if name != '*':  # Ignora imports com *
                    # Tenta encontrar um arquivo específico para o item importado
                    specific_module = f"{target_module}.{name}"
                    if specific_module in module_to_file:
                        target_files.add(module_to_file[specific_module])

                    # Se não encontrou arquivo específico, verifica se existe um arquivo
                    # com o nome do item no mesmo diretório do módulo
                    base_module = target_module
                    for module_path, file_path in module_to_file.items():
                        if (module_path.startswith(base_module + '.') and
                                module_path.endswith('.' + name)):
                            target_files.add(file_path)
                        elif file_path.endswith(f'/{name}.py'):
                            # Verifica se o arquivo está no caminho correto do módulo
                            expected_path = target_module.replace('.', '/') + f'/{name}.py'
                            if file_path.endswith(expected_path) or file_path == expected_path:
                                target_files.add(file_path)

        return target_files

    def _collect_external_libraries(self, result: AnalysisResult) -> None:
        """
        Coleta todas as bibliotecas externas utilizadas no projeto.

        Args:
            result: Resultado da análise para adicionar as bibliotecas
        """
        # Bibliotecas padrão do Python que devem ser ignoradas
        standard_libs = {
            'abc', 'argparse', 'ast', 'asyncio', 'base64', 'collections', 'copy',
            'datetime', 'decimal', 'enum', 'fnmatch', 'functools', 'hashlib', 'io',
            'itertools', 'json', 'logging', 'math', 'os', 'pathlib', 'pickle',
            'random', 're', 'shutil', 'subprocess', 'sys', 'tempfile', 'threading',
            'time', 'typing', 'urllib', 'uuid', 'warnings', 'weakref', 'xml'
        }

        library_count = {}

        for file_info in result.files.values():
            for import_info in file_info.imports:
                # Extrai o nome da biblioteca raiz
                lib_name = import_info.module.split('.')[0] if import_info.module else None

                # Ignora imports relativos e bibliotecas padrão
                if (lib_name and
                    not import_info.is_relative and
                    lib_name not in standard_libs and
                    not lib_name.startswith('app') and  # Ignora módulos internos
                        not lib_name.startswith('core')):

                    library_count[lib_name] = library_count.get(lib_name, 0) + 1

        # Ordena por uso (mais usado primeiro)
        result.external_libraries = dict(sorted(
            library_count.items(),
            key=lambda x: x[1],
            reverse=True
        ))


class FileAnalyzer(ast.NodeVisitor):
    """Visitor do AST para extrair informações de um arquivo."""

    def __init__(self, file_info: FileInfo):
        """
        Inicializa o analisador de arquivo.

        Args:
            file_info: Objeto para armazenar as informações extraídas
        """
        self.file_info = file_info
        self.current_class = None

    def visit_Import(self, node: ast.Import) -> None:
        """Visita um nó de import."""
        for alias in node.names:
            import_info = ImportInfo(
                module=alias.name,
                names=[alias.asname or alias.name],
                is_relative=False
            )
            self.file_info.imports.append(import_info)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visita um nó de import from."""
        if node.module:
            names = []
            for alias in node.names:
                names.append(alias.asname or alias.name)

            import_info = ImportInfo(
                module=node.module,
                names=names,
                is_relative=node.level > 0,
                level=node.level
            )
            self.file_info.imports.append(import_info)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visita uma definição de classe."""
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(self._get_attribute_name(base))

        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_info.path,
            line_number=node.lineno,
            base_classes=base_classes,
            docstring=ast.get_docstring(node)
        )

        # Analisa métodos e atributos
        old_class = self.current_class
        self.current_class = class_info

        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                class_info.methods.append(child.name)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        class_info.attributes.append(target.id)

        self.file_info.classes.append(class_info)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visita uma definição de função."""
        if self.current_class is None:  # Apenas funções de nível superior
            parameters = []
            for arg in node.args.args:
                parameters.append(arg.arg)

            function_info = FunctionInfo(
                name=node.name,
                file_path=self.file_info.path,
                line_number=node.lineno,
                parameters=parameters,
                docstring=ast.get_docstring(node)
            )

            self.file_info.functions.append(function_info)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visita um acesso a atributo para detectar uso de classes/módulos."""
        # Extrai o nome base do atributo
        attr_name = self._get_attribute_name(node)

        # Procura por padrões como ClassName.attribute ou module.Class.attribute
        parts = attr_name.split('.')
        if len(parts) >= 2:
            # Verifica se o primeiro parte é um nome de classe ou módulo conhecido
            base_name = parts[0]

            # Adiciona à lista de referências para análise posterior
            self.file_info.class_references.append({
                'base_name': base_name,
                'full_attribute': attr_name,
                'line': node.lineno if hasattr(node, 'lineno') else None
            })

        self.generic_visit(node)

    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Extrai o nome completo de um atributo."""
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attribute_name(node.value)}.{node.attr}"
        else:
            return node.attr
