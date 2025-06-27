"""
Gerador de grafos de dependências usando pyvis e networkx.
"""

import networkx as nx
from pyvis.network import Network
from pathlib import Path
from typing import Dict, Any, Tuple

from .models import AnalysisResult


class GraphGenerator:
    """Gera grafos de dependências interativos."""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa o gerador de grafos.

        Args:
            config: Configurações da aplicação
        """
        self.config = config
        self.graph_config = config.get('graph_config', {})

    def generate(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Gera todos os grafos baseados na análise.

        Args:
            analysis_result: Resultado da análise do projeto

        Returns:
            Dicionário contendo os grafos gerados
        """
        graphs = {}

        visualization_types = self.config.get('visualization_types', ['arquivos'])

        if 'arquivos' in visualization_types or 'ambos' in visualization_types:
            graphs['files'] = self._generate_file_graph(analysis_result)

        if 'classes' in visualization_types or 'ambos' in visualization_types:
            graphs['classes'] = self._generate_class_graph(analysis_result)

        return graphs

    def _generate_file_graph(self, analysis_result: AnalysisResult) -> Tuple[Network, nx.DiGraph]:
        """
        Gera grafo de dependências entre arquivos.

        Args:
            analysis_result: Resultado da análise

        Returns:
            Tupla contendo (rede pyvis, grafo networkx)
        """
        # Cria grafo NetworkX
        G = nx.DiGraph()

        # Adiciona nós (arquivos)
        for file_path, file_info in analysis_result.files.items():
            # Calcula métricas do arquivo
            num_classes = len(file_info.classes)
            num_functions = len(file_info.functions)
            num_imports = len(file_info.imports)

            # Determina cor baseada no tipo de arquivo
            color = self._get_file_color(file_path, num_classes, num_functions)

            # Determina tamanho baseado na complexidade
            size = min(50, max(20, (num_classes + num_functions) * 5))

            G.add_node(
                file_path,
                title=self._create_file_tooltip(file_path, file_info),
                color=color,
                size=size,
                label=Path(file_path).name
            )

        # Adiciona arestas (dependências)
        for file_path, dependencies in analysis_result.dependencies_graph.items():
            for dep in dependencies:
                if dep in analysis_result.files:
                    # Determina o tipo de relacionamento baseado nos imports
                    edge_title = self._create_edge_tooltip(file_path, dep, analysis_result)
                    G.add_edge(file_path, dep, title=edge_title, color='#666666', width=2)

        # Cria rede pyvis
        net = Network(
            height=self.graph_config.get('height', '800px'),
            width=self.graph_config.get('width', '100%'),
            bgcolor='#ffffff',
            font_color='#000000',
            directed=True,
            neighborhood_highlight=False,
            select_menu=False
        )

        # Configura física
        if self.graph_config.get('physics_enabled', True):
            net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100},
                "barnesHut": {
                  "gravitationalConstant": -8000,
                  "centralGravity": 0.3,
                  "springLength": 95,
                  "springConstant": 0.04,
                  "damping": 0.09
                }
              }
            }
            """)
        else:
            net.set_options('{"physics": false}')

        # Transfere grafo para pyvis
        net.from_nx(G)

        # Customiza HTML do pyvis
        net = self._customize_pyvis_html(net)

        return net, G

    def _generate_class_graph(self, analysis_result: AnalysisResult) -> Tuple[Network, nx.DiGraph]:
        """
        Gera grafo de dependências entre classes.

        Args:
            analysis_result: Resultado da análise

        Returns:
            Tupla contendo (rede pyvis, grafo networkx)
        """
        # Cria grafo NetworkX
        G = nx.DiGraph()

        # Adiciona nós (classes)
        for class_key, class_info in analysis_result.classes.items():
            file_path = str(class_info.file_path.relative_to(Path(self.config['root_directory'])))

            # Determina cor baseada no arquivo
            color = self._get_class_color(file_path)

            # Determina tamanho baseado no número de métodos
            size = min(60, max(25, len(class_info.methods) * 3))

            G.add_node(
                class_key,
                title=self._create_class_tooltip(class_info),
                color=color,
                size=size,
                label=class_info.name
            )

        # Adiciona arestas baseadas em herança
        for class_key, class_info in analysis_result.classes.items():
            for base_class in class_info.base_classes:
                # Procura a classe base no projeto
                for other_key, other_class in analysis_result.classes.items():
                    if other_class.name == base_class or base_class.endswith(f".{other_class.name}"):
                        G.add_edge(class_key, other_key, title="herda de")
                        break

        # Cria rede pyvis
        net = Network(
            height=self.graph_config.get('height', '800px'),
            width=self.graph_config.get('width', '100%'),
            bgcolor='#ffffff',
            font_color='#000000',
            directed=True,
            neighborhood_highlight=False,
            select_menu=False
        )

        # Configura física
        if self.graph_config.get('physics_enabled', True):
            net.set_options("""
            var options = {
              "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100},
                "hierarchicalRepulsion": {
                  "centralGravity": 0.0,
                  "springLength": 100,
                  "springConstant": 0.01,
                  "nodeDistance": 120,
                  "damping": 0.09
                }
              },
              "layout": {
                "hierarchical": {
                  "enabled": true,
                  "direction": "UD",
                  "sortMethod": "hubsize"
                }
              }
            }
            """)
        else:
            net.set_options('{"physics": false}')

        # Transfere grafo para pyvis
        net.from_nx(G)

        # Customiza HTML do pyvis
        net = self._customize_pyvis_html(net)

        return net, G

    def _customize_pyvis_html(self, net: Network) -> Network:
        """
        Customiza o HTML gerado pelo pyvis para remover dependências locais.

        Args:
            net: Rede pyvis a ser customizada

        Returns:
            Rede pyvis customizada
        """
        # Força uso de CDNs externos apenas
        net.options = {
            "interaction": {"hover": True},
            "manipulation": {"enabled": False},
            "physics": {
                "enabled": self.graph_config.get('physics_enabled', True),
                "stabilization": {"iterations": 100}
            },
            "layout": {
                "improvedLayout": False,
                "randomSeed": 42
            }
        }

        # Sobrescreve template para usar apenas CDNs
        original_save = net.save_graph

        def custom_save_graph(name):
            original_save(name)
            # Lê o arquivo gerado e corrige os imports
            with open(name, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove referências a arquivos locais problemáticos
            content = content.replace('src="lib/bindings/utils.js"', '')
            content = content.replace('<script src="lib/bindings/utils.js"></script>', '')
            content = content.replace('<script ></script>', '')

            # Remove referências ao tom-select local
            content = content.replace('href="lib/tom-select/tom-select.css"', 'href="https://cdn.jsdelivr.net/npm/tom-select@2.2.2/dist/css/tom-select.css"')
            content = content.replace('src="lib/tom-select/tom-select.complete.min.js"', 'src="https://cdn.jsdelivr.net/npm/tom-select@2.2.2/dist/js/tom-select.complete.min.js"')

            # Adiciona definição da função neighbourhoodHighlight se ela estiver sendo usada mas não definida
            if 'neighbourhoodHighlight' in content and 'function neighbourhoodHighlight' not in content:
                # Adiciona a função neighbourhoodHighlight antes do script principal
                neighborhood_function = """
<script>
function neighbourhoodHighlight(params) {
    // Função vazia para evitar erro de referência
    // O highlight será desabilitado para simplificar
    if (params.nodes.length > 0) {
        console.log('Node selected:', params.nodes[0]);
    }
}
</script>
"""
                # Insere antes do fechamento do head
                content = content.replace('</head>', neighborhood_function + '</head>')

            # Remove chamadas ao neighbourhoodHighlight se ainda houver problemas
            content = content.replace('.on("selectNode", neighbourhoodHighlight)', '.on("selectNode", function(params) { console.log("Node selected:", params.nodes[0]); })')
            content = content.replace('.on("deselectNode", neighbourhoodHighlight)', '.on("deselectNode", function() { console.log("Node deselected"); })')

            click_handler = """
<script>
// Variables for filtering (check if they already exist)
if (typeof originalNodes === 'undefined') {
    var originalNodes = null;
}
if (typeof originalEdges === 'undefined') {
    var originalEdges = null;
}
if (typeof isFiltered === 'undefined') {
    var isFiltered = false;
}

// Store original data
function storeOriginalData() {
    if (!originalNodes && !originalEdges) {
        originalNodes = nodes.get();
        originalEdges = edges.get();
    }
}

// Filter functionality
window.addEventListener('message', function(event) {
    if (event.data.action === 'filterBySearch') {
        filterBySearch(event.data.searchTerm);
    } else if (event.data.action === 'filterByFile') {
        filterByFile(event.data.filePath);
    } else if (event.data.action === 'resetFilter') {
        resetFilter();
    }
});

function filterBySearch(searchTerm) {
    storeOriginalData();
    
    const filteredNodes = originalNodes.filter(node => {
        const label = node.label.toLowerCase();
        const id = node.id.toLowerCase();
        const title = (node.title || '').toLowerCase();
        const search = searchTerm.toLowerCase();
        
        return label.includes(search) || id.includes(search) || title.includes(search);
    });
    
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = originalEdges.filter(edge => 
        filteredNodeIds.has(edge.from) && filteredNodeIds.has(edge.to)
    );
    
    nodes.clear();
    edges.clear();
    nodes.add(filteredNodes);
    edges.add(filteredEdges);
    
    isFiltered = true;
    network.fit();
}

function filterByFile(filePath) {
    storeOriginalData();
    
    // Find the target node
    const targetNode = originalNodes.find(node => node.id === filePath);
    if (!targetNode) return;
    
    // Find all connected nodes (dependencies and dependents)
    const connectedNodeIds = new Set([filePath]);
    const connectedEdges = [];
    
    originalEdges.forEach(edge => {
        if (edge.from === filePath || edge.to === filePath) {
            connectedNodeIds.add(edge.from);
            connectedNodeIds.add(edge.to);
            connectedEdges.push(edge);
        }
    });
    
    const filteredNodes = originalNodes.filter(node => 
        connectedNodeIds.has(node.id)
    );
    
    nodes.clear();
    edges.clear();
    nodes.add(filteredNodes);
    edges.add(connectedEdges);
    
    isFiltered = true;
    
    // Highlight the selected node
    const updatedTargetNode = {...targetNode, color: {
        background: '#ff6b6b',
        border: '#ff5252',
        highlight: {background: '#ff8a80', border: '#ff5252'}
    }};
    nodes.update(updatedTargetNode);
    
    network.fit();
    
    // Focus on the target node
    network.focus(filePath, {scale: 1.5, animation: true});
}

function resetFilter() {
    if (originalNodes && originalEdges) {
        nodes.clear();
        edges.clear();
        nodes.add(originalNodes);
        edges.add(originalEdges);
        isFiltered = false;
        network.fit();
    }
}

// Adiciona handler de clique nos nós para mostrar código fonte
network.on("click", function(params) {
    if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = nodes.get(nodeId);
        
        if (nodeData && nodeData.label) {
            // Para nós de arquivo, usa o id diretamente
            // Para nós de classe, extrai o arquivo do tooltip
            let filePath = nodeId;
            let displayName = nodeData.label;
            
            // Se o tooltip contém "Arquivo:", é uma classe
            if (nodeData.title && nodeData.title.includes('Arquivo:')) {
                const match = nodeData.title.match(/Arquivo: ([^<]+)/);
                if (match) {
                    // Encontra o arquivo correspondente baseado no nome
                    const fileName = match[1];
                    filePath = nodeId.split('::')[0] || filePath;
                }
            }
            
            // Tenta múltiplas estratégias de comunicação
            try {
                // Estratégia 1: PostMessage (funciona em file:// e http://)
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({
                        action: 'showSourceCode',
                        filePath: filePath,
                        displayName: displayName
                    }, '*');
                    return;
                }
                
                // Estratégia 2: Acesso direto (funciona em http://)
                if (window.parent && 
                    window.parent !== window && 
                    typeof window.parent.showSourceCode === 'function') {
                    window.parent.showSourceCode(filePath, displayName);
                    return;
                }
                
                // Estratégia 3: window.top (alternativa)
                if (window.top && 
                    window.top !== window && 
                    typeof window.top.showSourceCode === 'function') {
                    window.top.showSourceCode(filePath, displayName);
                    return;
                }
                
                // Fallback: exibe informações do nó quando não consegue comunicar
                const info = 'Arquivo: ' + nodeId + '\\\\nClasse/Módulo: ' + nodeData.label;
                if (confirm('Visualizar informações do nó?\\\\n\\\\n' + info + '\\\\n\\\\nClique OK para copiar o caminho.')) {
                    // Tenta copiar para área de transferência
                    if (navigator.clipboard) {
                        navigator.clipboard.writeText(nodeId);
                    }
                }
                
            } catch (e) {
                // Erro de cross-origin ou outro problema
                console.log('Info do nó:', nodeData.label, 'Caminho:', nodeId);
                
                // Fallback silencioso - apenas log
                const info = 'Módulo: ' + nodeData.label + '\\\\nCaminho: ' + nodeId;
                console.log('Para visualizar o código, abra o arquivo diretamente:', info);
            }
        }
    }
});

// Initialize when network is ready
network.once('stabilized', function() {
    storeOriginalData();
});
</script>
"""

            # Insere o handler de clique antes do fechamento do body
            content = content.replace('</body>', click_handler + '</body>')

            with open(name, 'w', encoding='utf-8') as f:
                f.write(content)

        net.save_graph = custom_save_graph

        return net

    def _get_file_color(self, file_path: str, num_classes: int, num_functions: int) -> str:
        """Determina a cor de um nó de arquivo."""
        if file_path.endswith('__init__.py'):
            return '#e1bee7'  # Roxo claro para __init__.py
        elif num_classes > 0 and num_functions > 0:
            return '#81c784'  # Verde para arquivos com classes e funções
        elif num_classes > 0:
            return '#64b5f6'  # Azul para arquivos com classes
        elif num_functions > 0:
            return '#ffb74d'  # Laranja para arquivos com funções
        else:
            return '#e0e0e0'  # Cinza para outros arquivos

    def _get_class_color(self, file_path: str) -> str:
        """Determina a cor de um nó de classe baseado no arquivo."""
        # Usa hash do caminho para cores consistentes
        hash_value = hash(file_path) % 6
        colors = ['#ffcdd2', '#f8bbd9', '#e1bee7', '#d1c4e9', '#c5cae9', '#bbdefb']
        return colors[hash_value]

    def _create_file_tooltip(self, file_path: str, file_info) -> str:
        """Cria tooltip para um arquivo."""
        tooltip = f"<b>{Path(file_path).name}</b><br>"
        tooltip += f"Caminho: {file_path}<br>"
        tooltip += f"Classes: {len(file_info.classes)}<br>"
        tooltip += f"Funções: {len(file_info.functions)}<br>"
        tooltip += f"Imports: {len(file_info.imports)}<br>"

        # Detalhes das dependências
        if file_info.dependencies:
            tooltip += f"<br><b>Dependências ({len(file_info.dependencies)}):</b><br>"
            for dep in sorted(list(file_info.dependencies)[:5]):  # Mostra max 5
                tooltip += f"• {Path(dep).name}<br>"
            if len(file_info.dependencies) > 5:
                tooltip += f"... e mais {len(file_info.dependencies) - 5}<br>"

        # Detalhes dos dependentes
        if file_info.dependents:
            tooltip += f"<br><b>Usado por ({len(file_info.dependents)}):</b><br>"
            for dep in sorted(list(file_info.dependents)[:3]):  # Mostra max 3
                tooltip += f"• {Path(dep).name}<br>"
            if len(file_info.dependents) > 3:
                tooltip += f"... e mais {len(file_info.dependents) - 3}<br>"

        return tooltip

    def _create_class_tooltip(self, class_info) -> str:
        """Cria tooltip para uma classe."""
        tooltip = f"<b>{class_info.name}</b><br>"
        tooltip += f"Arquivo: {Path(class_info.file_path).name}<br>"
        tooltip += f"Linha: {class_info.line_number}<br>"
        tooltip += f"Métodos: {len(class_info.methods)}<br>"
        tooltip += f"Atributos: {len(class_info.attributes)}<br>"
        if class_info.base_classes:
            tooltip += f"Herda de: {', '.join(class_info.base_classes)}"
        return tooltip

    def _create_edge_tooltip(self, source_file: str, target_file: str, analysis_result) -> str:
        """Cria tooltip para uma aresta mostrando o tipo de relacionamento."""
        source_info = analysis_result.files.get(source_file)
        if not source_info:
            return "importa"

        # Analisa os imports para determinar o que está sendo importado
        imported_items = []

        for import_info in source_info.imports:
            # Verifica se este import resolve para o arquivo alvo
            target_module = self._resolve_import_for_edge(import_info, source_file, target_file)
            if target_module:
                if import_info.names and len(import_info.names) > 0:
                    for name in import_info.names:
                        if name != '*':
                            imported_items.append(name)
                else:
                    imported_items.append(import_info.module.split('.')[-1])

        if imported_items:
            if len(imported_items) == 1:
                return f"importa: {imported_items[0]}"
            elif len(imported_items) <= 3:
                return f"importa: {', '.join(imported_items)}"
            else:
                return f"importa: {', '.join(imported_items[:2])} e +{len(imported_items) - 2} itens"

        return "importa"

    def _resolve_import_for_edge(self, import_info, source_file: str, target_file: str) -> bool:
        """Verifica se um import específico resolve para o arquivo alvo."""
        # Implementação simplificada - verifica se o módulo importado
        # corresponde ao caminho do arquivo alvo
        if not import_info.module:
            return False

        # Converte arquivo alvo para módulo
        target_module = target_file.replace('/', '.').replace('\\', '.').replace('.py', '')
        if target_module.endswith('.__init__'):
            target_module = target_module[:-9]

        # Verifica correspondência direta ou com prefixo app.
        return (import_info.module == target_module or
                import_info.module == f'app.{target_module}' or
                target_module.endswith(import_info.module.replace('app.', '')))
