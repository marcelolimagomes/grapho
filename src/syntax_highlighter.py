"""
Syntax highlighter para código Python similar ao VS Code.
"""

import re
from typing import Dict, List, Tuple


class PythonSyntaxHighlighter:
    """Realiza syntax highlighting de código Python para HTML."""

    def __init__(self):
        """Inicializa o highlighter com os padrões de sintaxe."""
        self.patterns = self._setup_patterns()

    def _setup_patterns(self) -> List[Tuple[str, str]]:
        """
        Define os padrões regex para diferentes elementos da sintaxe Python.

        Returns:
            Lista de tuplas (pattern, css_class)
        """
        patterns = [
            # Comentários (deve vir antes de strings para evitar conflitos)
            (r'#.*?$', 'comment'),

            # Strings com aspas triplas (docstrings)
            (r'"""[\s\S]*?"""', 'docstring'),
            (r"'''[\s\S]*?'''", 'docstring'),

            # Strings normais
            (r'"(?:[^"\\]|\\.)*"', 'string'),
            (r"'(?:[^'\\]|\\.)*'", 'string'),

            # F-strings
            (r'f"(?:[^"\\]|\\.)*"', 'fstring'),
            (r"f'(?:[^'\\]|\\.)*'", 'fstring'),

            # Números
            (r'\b\d+\.?\d*\b', 'number'),

            # Palavras-chave Python
            (r'\b(?:False|None|True|__peg_parser__|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b', 'keyword'),

            # Decoradores
            (r'@\w+', 'decorator'),

            # Funções built-in
            (r'\b(?:abs|all|any|ascii|bin|bool|bytearray|bytes|callable|chr|classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|eval|exec|filter|float|format|frozenset|getattr|globals|hasattr|hash|help|hex|id|input|int|isinstance|issubclass|iter|len|list|locals|map|max|memoryview|min|next|object|oct|open|ord|pow|print|property|range|repr|reversed|round|set|setattr|slice|sorted|staticmethod|str|sum|super|tuple|type|vars|zip)\b', 'builtin'),

            # Tipos built-in
            (r'\b(?:int|float|str|bool|list|dict|tuple|set|frozenset|bytes|bytearray)\b', 'type'),

            # Operadores
            (r'[+\-*/%=<>!&|^~]|//|\*\*|<<|>>|<=|>=|==|!=|and|or|not|in|is', 'operator'),

            # Nomes de classes (convenção CamelCase)
            (r'\b[A-Z][a-zA-Z0-9_]*\b', 'class-name'),

            # Nomes de funções (seguidos por parênteses)
            (r'\b[a-zA-Z_][a-zA-Z0-9_]*(?=\s*\()', 'function-name'),

            # Variáveis especiais (dunder)
            (r'__[a-zA-Z0-9_]+__', 'special-var'),

            # Parênteses, colchetes, chaves
            (r'[(){}\[\]]', 'punctuation'),

            # Dois pontos e vírgulas
            (r'[:,;]', 'punctuation'),
        ]

        return patterns

    def highlight(self, code: str) -> str:
        """
        Aplica syntax highlighting ao código Python.

        Args:
            code: Código Python a ser destacado

        Returns:
            HTML com syntax highlighting aplicado
        """
        # Escapa caracteres HTML
        code = self._escape_html(code)

        # Aplica highlighting linha por linha para preservar quebras
        lines = code.split('\n')
        highlighted_lines = []

        for line_num, line in enumerate(lines, 1):
            highlighted_line = self._highlight_line(line)
            highlighted_lines.append(highlighted_line)

        return '\n'.join(highlighted_lines)

    def _escape_html(self, text: str) -> str:
        """Escapa apenas caracteres HTML perigosos."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))
        # Removido escape de aspas para melhor legibilidade

    def _highlight_line(self, line: str) -> str:
        """
        Aplica highlighting a uma linha individual.

        Args:
            line: Linha de código a ser destacada

        Returns:
            Linha com HTML de highlighting
        """
        if not line.strip():
            return line

        # Lista para armazenar segmentos processados
        segments = [(line, None)]  # (texto, classe_css)

        # Aplica cada padrão
        for pattern, css_class in self.patterns:
            new_segments = []

            for segment_text, segment_class in segments:
                if segment_class is not None:
                    # Já foi processado, mantém como está
                    new_segments.append((segment_text, segment_class))
                    continue

                # Procura matches no segmento não processado
                last_end = 0
                for match in re.finditer(pattern, segment_text, re.MULTILINE):
                    start, end = match.span()

                    # Adiciona texto antes do match (se houver)
                    if start > last_end:
                        new_segments.append((segment_text[last_end:start], None))

                    # Adiciona o match com a classe CSS
                    new_segments.append((segment_text[start:end], css_class))

                    last_end = end

                # Adiciona texto restante (se houver)
                if last_end < len(segment_text):
                    new_segments.append((segment_text[last_end:], None))

            segments = new_segments

        # Constrói o HTML final
        html_parts = []
        for text, css_class in segments:
            if css_class:
                html_parts.append(f'<span class="syntax-{css_class}">{text}</span>')
            else:
                html_parts.append(text)

        return ''.join(html_parts)

    def highlight_with_search(self, code: str, search_term: str = None) -> str:
        """
        Aplica syntax highlighting ao código Python com destaque de busca.

        Args:
            code: Código Python a ser destacado
            search_term: Termo a ser destacado na busca

        Returns:
            HTML com syntax highlighting e busca aplicados
        """
        # Aplica highlighting normal primeiro
        highlighted = self.highlight(code)

        # Se há termo de busca, destaca-o
        if search_term and search_term.strip():
            search_term = search_term.strip()
            # Usa regex case-insensitive para busca
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
            highlighted = pattern.sub(
                f'<mark class="search-highlight">{search_term}</mark>',
                highlighted
            )

        return highlighted

    def get_css_styles(self) -> str:
        """
        Retorna os estilos CSS para o syntax highlighting.

        Returns:
            CSS para as classes de highlighting
        """
        return """
/* Syntax highlighting styles - VS Code inspired */
.source-code {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.4;
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
    white-space: pre;
}

.syntax-comment {
    color: #6a9955;
    font-style: italic;
}

.syntax-docstring {
    color: #ce9178;
}

.syntax-string {
    color: #ce9178;
}

.syntax-fstring {
    color: #d7ba7d;
}

.syntax-number {
    color: #b5cea8;
}

.syntax-keyword {
    color: #569cd6;
    font-weight: bold;
}

.syntax-decorator {
    color: #4ec9b0;
}

.syntax-builtin {
    color: #4ec9b0;
}

.syntax-type {
    color: #4ec9b0;
}

.syntax-operator {
    color: #d4d4d4;
}

.syntax-class-name {
    color: #4ec9b0;
    font-weight: bold;
}

.syntax-function-name {
    color: #dcdcaa;
}

.syntax-special-var {
    color: #c586c0;
}

.syntax-punctuation {
    color: #d4d4d4;
}

/* Line numbers */
.line-numbers {
    background-color: #252526;
    color: #858585;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.4;
    padding: 20px 10px;
    border-radius: 8px 0 0 8px;
    text-align: right;
    white-space: pre;
    user-select: none;
    min-width: 40px;
}

.code-container {
    display: flex;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    margin: 20px 0;
}

.source-code.with-lines {
    border-radius: 0 8px 8px 0;
    margin: 0;
}

/* Scrollbar styling for dark theme */
.source-code::-webkit-scrollbar {
    height: 12px;
}

.source-code::-webkit-scrollbar-track {
    background: #2d2d30;
}

.source-code::-webkit-scrollbar-thumb {
    background: #424245;
    border-radius: 6px;
}

.source-code::-webkit-scrollbar-thumb:hover {
    background: #4f4f52;
}

/* Search highlighting */
.search-highlight {
    background-color: #ffd700;
    color: #000;
    padding: 0 2px;
    border-radius: 2px;
    font-weight: bold;
}

/* Search input styling */
.search-container {
    padding: 10px 20px;
    background-color: #2d2d30;
    border-bottom: 1px solid #424245;
    display: flex;
    align-items: center;
    gap: 10px;
}

.search-input {
    flex: 1;
    background-color: #1e1e1e;
    border: 1px solid #424245;
    color: #d4d4d4;
    padding: 8px 12px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 14px;
}

.search-input:focus {
    outline: none;
    border-color: #3b82f6;
}

.search-info {
    color: #858585;
    font-size: 12px;
    min-width: 100px;
}
"""
