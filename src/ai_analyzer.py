"""
Analisador de código usando LangChain e OpenAI para gerar documentação.
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .ai_config import AIConfig
from .models import AnalysisResult, FileInfo


@dataclass
class DocumentationResult:
    """Resultado da documentação gerada por IA."""
    file_path: str
    markdown_content: str
    summary: str
    purpose: str
    integrations: List[str]
    dependencies: List[str]
    error: Optional[str] = None


class AICodeAnalyzer:
    """Analisador de código usando IA para gerar documentação."""

    def __init__(self, config: AIConfig):
        """
        Inicializa o analisador de código IA.

        Args:
            config: Configuração de IA
        """
        self.config = config
        self.llm = self._setup_llm()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )

    def _setup_llm(self) -> ChatOpenAI:
        """Configura o modelo LLM."""
        return ChatOpenAI(
            openai_api_key=self.config.openai_api_key,
            model_name=self.config.openai_model,
            temperature=self.config.openai_temperature,
            max_tokens=self.config.openai_max_tokens
        )

    def analyze_project_context(self, project_root: Path) -> str:
        """
        Analisa o contexto geral do projeto.

        Args:
            project_root: Diretório raiz do projeto

        Returns:
            String com contexto do projeto
        """
        context_parts = []

        # Analisa README se existir
        readme_files = ['README.md', 'README.txt', 'README.rst', 'README']
        for readme in readme_files:
            readme_path = project_root / readme
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding='utf-8')
                    context_parts.append(f"README do projeto:\n{content[:1000]}")
                    break
                except Exception:
                    continue

        # Analisa requirements.txt
        if self.config.include_config_files:
            config_files = [
                'requirements.txt', 'pyproject.toml', 'setup.py',
                'Pipfile', 'environment.yml', 'conda.yaml'
            ]

            for config_file in config_files:
                config_path = project_root / config_file
                if config_path.exists():
                    try:
                        content = config_path.read_text(encoding='utf-8')
                        context_parts.append(f"{config_file}:\n{content[:500]}")
                    except Exception:
                        continue

        # Analisa estrutura de diretórios
        try:
            structure = self._get_project_structure(project_root)
            context_parts.append(f"Estrutura do projeto:\n{structure}")
        except Exception:
            pass

        return "\n\n".join(context_parts)

    def _get_project_structure(self, project_root: Path, max_depth: int = 3) -> str:
        """Gera representação da estrutura do projeto."""
        structure_lines = []

        def add_directory(path: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return

            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

            for i, item in enumerate(items):
                if item.name.startswith('.'):
                    continue

                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                structure_lines.append(f"{prefix}{current_prefix}{item.name}")

                if item.is_dir() and depth < max_depth:
                    extension = "    " if is_last else "│   "
                    add_directory(item, prefix + extension, depth + 1)

        structure_lines.append(project_root.name)
        add_directory(project_root)

        return "\n".join(structure_lines[:50])  # Limita saída

    def generate_file_documentation(
        self,
        file_info: FileInfo,
        project_context: str,
        analysis_result: AnalysisResult
    ) -> DocumentationResult:
        """
        Gera documentação para um arquivo específico.

        Args:
            file_info: Informações do arquivo
            project_context: Contexto do projeto
            analysis_result: Resultado da análise completa

        Returns:
            Resultado da documentação
        """
        try:
            if not file_info.source_code or len(file_info.source_code.strip()) < 10:
                return DocumentationResult(
                    file_path=str(file_info.path),
                    markdown_content="",
                    summary="Arquivo vazio ou muito pequeno",
                    purpose="Inicializador de módulo ou arquivo vazio",
                    integrations=[],
                    dependencies=[],
                    error="Código fonte insuficiente para análise"
                )

            # Prepara contexto do arquivo específico
            file_context = self._prepare_file_context(file_info, analysis_result)

            # Gera documentação usando LLM
            markdown_content = self._generate_markdown_documentation(
                file_info, file_context, project_context
            )

            # Extrai informações estruturadas
            summary = self._extract_summary(markdown_content)
            purpose = self._extract_purpose(markdown_content)
            integrations = self._extract_integrations(file_info, analysis_result)
            dependencies = list(file_info.dependencies) if file_info.dependencies else []

            return DocumentationResult(
                file_path=str(file_info.path),
                markdown_content=markdown_content,
                summary=summary,
                purpose=purpose,
                integrations=integrations,
                dependencies=dependencies
            )

        except Exception as e:
            return DocumentationResult(
                file_path=str(file_info.path),
                markdown_content="",
                summary="Erro ao gerar documentação",
                purpose="N/A",
                integrations=[],
                dependencies=[],
                error=str(e)
            )

    def _prepare_file_context(self, file_info: FileInfo, analysis_result: AnalysisResult) -> str:
        """Prepara contexto específico do arquivo."""
        context_parts = []

        # Informações básicas do arquivo
        context_parts.append(f"Arquivo: {file_info.path}")
        context_parts.append(f"Classes: {len(file_info.classes)}")
        context_parts.append(f"Funções: {len(file_info.functions)}")
        context_parts.append(f"Imports: {len(file_info.imports)}")

        # Dependências
        if file_info.dependencies:
            deps = list(file_info.dependencies)[:5]  # Primeiras 5
            context_parts.append(f"Dependências: {', '.join(deps)}")

        # Dependentes
        if file_info.dependents:
            dependents = list(file_info.dependents)[:5]  # Primeiros 5
            context_parts.append(f"Usado por: {', '.join(dependents)}")

        # Classes relacionadas
        related_classes = []
        for class_key, class_info in analysis_result.classes.items():
            if str(class_info.file_path) == str(file_info.path):
                related_classes.append(class_info.name)

        if related_classes:
            context_parts.append(f"Classes no arquivo: {', '.join(related_classes)}")

        return "\n".join(context_parts)

    def _generate_markdown_documentation(
        self,
        file_info: FileInfo,
        file_context: str,
        project_context: str
    ) -> str:
        """Gera documentação em Markdown usando LLM."""

        # Quebra código em chunks se muito grande
        code_content = file_info.source_code
        if len(code_content) > 3000:
            chunks = self.text_splitter.split_text(code_content)
            code_content = chunks[0] + "\n\n[... código truncado ...]"

        language = self.config.documentation_language

        system_prompt = f"""Você é um especialista em análise de código Python e documentação técnica. 
        Sua tarefa é analisar o código fornecido e gerar uma documentação completa em Markdown em {language}.

        A documentação deve incluir:
        1. Título e descrição geral do arquivo
        2. Objetivo e propósito no contexto do projeto
        3. Classes e funções principais
        4. Dependências e integrações
        5. Exemplos de uso (se aplicável)
        6. Observações técnicas importantes

        Use formatação Markdown apropriada com seções, códigos, listas, etc.
        Seja técnico mas claro, focando no que é mais importante para entender o código."""

        human_prompt = f"""Contexto do Projeto:
{project_context[:1500]}

Contexto do Arquivo:
{file_context}

Código a ser documentado:
```python
{code_content}
```

Gere uma documentação completa em Markdown para este arquivo Python."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        return response.content

    def _extract_summary(self, markdown_content: str) -> str:
        """Extrai resumo da documentação."""
        lines = markdown_content.split('\n')

        # Procura primeira seção não-título
        for line in lines[1:10]:  # Primeiras 10 linhas após título
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('```'):
                return line[:200] + "..." if len(line) > 200 else line

        return "Documentação gerada por IA"

    def _extract_purpose(self, markdown_content: str) -> str:
        """Extrai propósito/objetivo da documentação."""
        lines = markdown_content.split('\n')

        # Procura seção de objetivo/propósito
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['objetivo', 'propósito', 'purpose', 'goal']):
                # Pega próximas linhas não vazias
                for j in range(i + 1, min(len(lines), i + 5)):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('#'):
                        return next_line[:300]

        return "Objetivo não especificado"

    def _extract_integrations(self, file_info: FileInfo, analysis_result: AnalysisResult) -> List[str]:
        """Extrai informações de integrações."""
        integrations = []

        # Baseado em imports
        for import_info in file_info.imports:
            if not import_info.is_relative and import_info.module:
                # Bibliotecas externas conhecidas
                external_libs = [
                    'django', 'flask', 'fastapi', 'requests', 'pandas',
                    'numpy', 'scipy', 'sqlalchemy', 'redis', 'celery'
                ]

                module_root = import_info.module.split('.')[0]
                if module_root in external_libs:
                    integrations.append(f"Integração com {module_root}")

        # Baseado em dependentes
        if file_info.dependents:
            integrations.append(f"Usado por {len(file_info.dependents)} arquivo(s)")

        return integrations[:5]  # Limita a 5

    def analyze_all_files(
        self,
        analysis_result: AnalysisResult,
        project_root: Path,
        max_files: Optional[int] = None
    ) -> Dict[str, DocumentationResult]:
        """
        Analisa todos os arquivos do projeto.

        Args:
            analysis_result: Resultado da análise estática
            project_root: Diretório raiz do projeto
            max_files: Máximo de arquivos a analisar (None = todos)

        Returns:
            Dicionário com documentação de cada arquivo
        """
        print("🤖 Iniciando análise de código com IA...")

        # Analisa contexto do projeto uma vez
        project_context = self.analyze_project_context(project_root)

        documentation_results = {}

        # Filtra arquivos adequados para análise IA
        files_to_analyze = []
        for file_path, file_info in analysis_result.files.items():
            # Ignora arquivos vazios, muito pequenos ou apenas __init__.py vazios
            if (file_info.source_code and
                len(file_info.source_code.strip()) >= 20 and
                    not (file_path.endswith('__init__.py') and len(file_info.source_code.strip()) < 100)):
                files_to_analyze.append((file_path, file_info))

        if max_files:
            files_to_analyze = files_to_analyze[:max_files]

        total_files = len(files_to_analyze)

        if total_files == 0:
            print("⚠️  Nenhum arquivo adequado encontrado para análise IA")
            return documentation_results

        for i, (file_path, file_info) in enumerate(files_to_analyze, 1):
            filename = Path(file_path).name
            print(f"📝 Analisando {filename} ({i}/{total_files})...")

            try:
                doc_result = self.generate_file_documentation(
                    file_info, project_context, analysis_result
                )
                documentation_results[file_path] = doc_result

                if doc_result.error:
                    print(f"⚠️  {filename}: {doc_result.error}")
                else:
                    summary_preview = doc_result.summary[:50] + "..." if len(doc_result.summary) > 50 else doc_result.summary
                    print(f"✅ {filename}: {summary_preview}")

            except Exception as e:
                print(f"❌ Erro fatal ao analisar {filename}: {e}")
                documentation_results[file_path] = DocumentationResult(
                    file_path=file_path,
                    markdown_content="",
                    summary="Erro ao gerar documentação",
                    purpose="N/A",
                    integrations=[],
                    dependencies=[],
                    error=str(e)
                )

        print(f"🎉 Análise IA concluída! {len(documentation_results)} arquivos processados.")
        return documentation_results
