"""
Modelos de dados para representar análise de código.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from pathlib import Path


@dataclass
class ImportInfo:
    """Informações sobre uma importação."""
    module: str
    names: List[str]
    is_relative: bool
    level: int = 0


@dataclass
class ClassInfo:
    """Informações sobre uma classe."""
    name: str
    file_path: Path
    line_number: int
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class FunctionInfo:
    """Informações sobre uma função."""
    name: str
    file_path: Path
    line_number: int
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None


@dataclass
class FileInfo:
    """Informações sobre um arquivo Python."""
    path: Path
    imports: List[ImportInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    source_code: Optional[str] = None
    class_references: List[Dict] = field(default_factory=list)
    ai_documentation: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_purpose: Optional[str] = None
    class_references: List[Dict] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Resultado da análise de um projeto."""
    files: Dict[str, FileInfo] = field(default_factory=dict)
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    dependencies_graph: Dict[str, Set[str]] = field(default_factory=dict)
    class_dependencies_graph: Dict[str, Set[str]] = field(default_factory=dict)
    external_libraries: Dict[str, int] = field(default_factory=dict)  # lib_name -> count
