#!/usr/bin/env python3
"""
Knowledge Extraction Engine
Extracts structured knowledge from different file types and repository contexts.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class KnowledgeExtractor:
    """
    Extracts knowledge from files based on repository type and file content.
    Adapts extraction patterns to different project types.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.repo_type = config.get("repo_type", "generic")
        self.keywords = set(kw.lower() for kw in config.get("keywords", []))
        self.extraction_focus = config.get("extraction_focus", [])
    
    def extract_knowledge(self, content: str, filepath: str, file_extension: str) -> Dict:
        """
        Extract structured knowledge from file content based on file type and repo context.
        """
        knowledge = {
            "concepts": [],
            "commands": [],
            "configurations": [],
            "troubleshooting": [],
            "dependencies": [],
            "cross_references": [],
            "code_blocks": [],
            "functions": [],
            "variables": []
        }
        
        lines = content.split('\n')
        
        # Apply file-type specific extractors
        if file_extension in ['.md', '.rst', '.txt']:
            self._extract_from_markdown(lines, knowledge, filepath)
        elif file_extension in ['.yml', '.yaml']:
            self._extract_from_yaml(lines, knowledge, filepath)
        elif file_extension == '.py':
            self._extract_from_python(lines, knowledge, filepath)
        elif file_extension in ['.sh', '.bash']:
            self._extract_from_shell(lines, knowledge, filepath)
        elif file_extension == '.js':
            self._extract_from_javascript(lines, knowledge, filepath)
        elif file_extension == '.ipynb':
            self._extract_from_notebook(content, knowledge, filepath)
        
        # Apply repository-specific enhancements
        if self.repo_type == "mlops-platform":
            self._enhance_mlops_knowledge(knowledge, lines, filepath)
        elif self.repo_type == "ml-model":
            self._enhance_ml_model_knowledge(knowledge, lines, filepath)
        
        return knowledge
    
    def _extract_from_markdown(self, lines: List[str], knowledge: Dict, filepath: str):
        """Extract knowledge from Markdown files."""
        in_code_block = False
        code_block_lang = None
        code_block_content = []
        current_section = None
        
        for i, line in enumerate(lines):
            # Track code blocks
            if line.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_block_lang = line[3:].strip()
                    code_block_content = []
                else:
                    # Process completed code block
                    if code_block_content:
                        knowledge["code_blocks"].append({
                            "language": code_block_lang,
                            "content": '\n'.join(code_block_content),
                            "line": i - len(code_block_content),
                            "file": filepath
                        })
                        
                        # Extract commands from code blocks
                        if code_block_lang in ['bash', 'shell', 'sh']:
                            self._extract_commands_from_block('\n'.join(code_block_content), knowledge, filepath, i)
                    
                    in_code_block = False
                continue
            
            if in_code_block:
                code_block_content.append(line)
                continue
            
            # Extract headers as concepts
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                concept = line.strip('#').strip()
                current_section = concept
                
                knowledge["concepts"].append({
                    "name": concept,
                    "level": level,
                    "line": i,
                    "context": self._get_context(lines, i, 2),
                    "section": current_section
                })
            
            # Extract configurations (key: value patterns)
            if ':' in line and not line.strip().startswith('#'):
                if any(keyword in line.lower() for keyword in ['namespace', 'image', 'port', 'enabled', 'ip', 'url']):
                    knowledge["configurations"].append({
                        "line": i,
                        "content": line.strip(),
                        "type": self._classify_configuration(line),
                        "section": current_section
                    })
            
            # Extract troubleshooting information
            if any(word in line.lower() for word in ['error', 'failed', 'issue', 'problem', 'fix', 'solution', 'resolved']):
                knowledge["troubleshooting"].append({
                    "line": i,
                    "content": line.strip(),
                    "type": self._classify_troubleshooting(line),
                    "section": current_section
                })
            
            # Extract cross-references
            refs = self._extract_file_references(line)
            if refs:
                for ref in refs:
                    ref.update({"line": i, "section": current_section})
                knowledge["cross_references"].extend(refs)
            
            # Extract dependencies
            if any(word in line.lower() for word in ['requires', 'depends on', 'prerequisite', 'needs']):
                knowledge["dependencies"].append({
                    "line": i,
                    "content": line.strip(),
                    "section": current_section
                })
    
    def _extract_from_yaml(self, lines: List[str], knowledge: Dict, filepath: str):
        """Extract knowledge from YAML files."""
        current_key_path = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue
            
            # Extract key-value configurations
            if ':' in stripped:
                key_part = stripped.split(':')[0].strip()
                value_part = ':'.join(stripped.split(':')[1:]).strip()
                
                # Determine indentation level
                indent_level = (len(line) - len(line.lstrip())) // 2
                
                # Update current path
                if indent_level < len(current_key_path):
                    current_key_path = current_key_path[:indent_level]
                
                if indent_level == len(current_key_path):
                    current_key_path.append(key_part)
                else:
                    current_key_path = current_key_path[:indent_level] + [key_part]
                
                full_key = '.'.join(current_key_path)
                
                # Store configuration
                knowledge["configurations"].append({
                    "line": i,
                    "key": full_key,
                    "value": value_part,
                    "content": stripped,
                    "type": self._classify_yaml_config(key_part, value_part),
                    "indent_level": indent_level
                })
                
                # Extract variables
                if value_part and not value_part.startswith('[') and not value_part.startswith('{'):
                    knowledge["variables"].append({
                        "name": key_part,
                        "value": value_part,
                        "path": full_key,
                        "line": i,
                        "type": "yaml_variable"
                    })
    
    def _extract_from_python(self, lines: List[str], knowledge: Dict, filepath: str):
        """Extract knowledge from Python files."""
        in_docstring = False
        docstring_quotes = None
        current_class = None
        current_function = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Track docstrings
            if '"""' in stripped or "'''" in stripped:
                if not in_docstring:
                    in_docstring = True
                    docstring_quotes = '"""' if '"""' in stripped else "'''"
                elif docstring_quotes in stripped:
                    in_docstring = False
                continue
            
            if in_docstring:
                continue
            
            # Extract class definitions
            if stripped.startswith('class '):
                match = re.match(r'class\s+(\w+)', stripped)
                if match:
                    current_class = match.group(1)
                    knowledge["concepts"].append({
                        "name": f"Class: {current_class}",
                        "line": i,
                        "type": "python_class",
                        "context": self._get_context(lines, i, 1)
                    })
            
            # Extract function definitions
            if stripped.startswith('def '):
                match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', stripped)
                if match:
                    func_name, params = match.groups()
                    current_function = func_name
                    
                    knowledge["functions"].append({
                        "name": func_name,
                        "parameters": params,
                        "line": i,
                        "class": current_class,
                        "context": self._get_context(lines, i, 1)
                    })
            
            # Extract imports
            if stripped.startswith(('import ', 'from ')):
                knowledge["dependencies"].append({
                    "line": i,
                    "content": stripped,
                    "type": "python_import"
                })
            
            # Extract variable assignments
            if '=' in stripped and not stripped.startswith('#'):
                # Simple variable assignment detection
                match = re.match(r'(\w+)\s*=\s*(.+)', stripped)
                if match and not stripped.startswith('def ') and not stripped.startswith('class '):
                    var_name, var_value = match.groups()
                    knowledge["variables"].append({
                        "name": var_name,
                        "value": var_value,
                        "line": i,
                        "function": current_function,
                        "class": current_class,
                        "type": "python_variable"
                    })
    
    def _extract_from_shell(self, lines: List[str], knowledge: Dict, filepath: str):
        """Extract knowledge from shell scripts."""
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip comments and empty lines
            if not stripped or stripped.startswith('#'):
                continue
            
            # Extract commands
            if not stripped.startswith('if ') and not stripped.startswith('for ') and not stripped.startswith('while '):
                knowledge["commands"].append({
                    "command": stripped,
                    "line": i,
                    "file": filepath,
                    "type": self._classify_shell_command(stripped)
                })
            
            # Extract variable assignments
            if '=' in stripped and not ' = ' in stripped:  # Shell variable, not comparison
                parts = stripped.split('=', 1)
                if len(parts) == 2 and parts[0].isidentifier():
                    knowledge["variables"].append({
                        "name": parts[0],
                        "value": parts[1],
                        "line": i,
                        "type": "shell_variable"
                    })
    
    def _extract_from_javascript(self, lines: List[str], knowledge: Dict, filepath: str):
        """Extract knowledge from JavaScript files."""
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Extract function declarations
            if stripped.startswith('function ') or ' function ' in stripped:
                match = re.search(r'function\s+(\w+)\s*\(([^)]*)\)', stripped)
                if match:
                    func_name, params = match.groups()
                    knowledge["functions"].append({
                        "name": func_name,
                        "parameters": params,
                        "line": i,
                        "type": "javascript_function"
                    })
            
            # Extract variable declarations
            if stripped.startswith(('let ', 'const ', 'var ')):
                match = re.match(r'(let|const|var)\s+(\w+)', stripped)
                if match:
                    var_type, var_name = match.groups()
                    knowledge["variables"].append({
                        "name": var_name,
                        "line": i,
                        "type": f"javascript_{var_type}"
                    })
    
    def _extract_from_notebook(self, content: str, knowledge: Dict, filepath: str):
        """Extract knowledge from Jupyter notebooks."""
        try:
            notebook = json.loads(content)
            
            for cell_idx, cell in enumerate(notebook.get('cells', [])):
                cell_type = cell.get('cell_type')
                source = cell.get('source', [])
                
                if isinstance(source, list):
                    cell_content = ''.join(source)
                else:
                    cell_content = source
                
                if cell_type == 'code':
                    # Extract from code cells
                    self._extract_from_python(cell_content.split('\n'), knowledge, f"{filepath}:cell_{cell_idx}")
                elif cell_type == 'markdown':
                    # Extract from markdown cells
                    self._extract_from_markdown(cell_content.split('\n'), knowledge, f"{filepath}:cell_{cell_idx}")
        
        except (json.JSONDecodeError, KeyError):
            # If notebook parsing fails, treat as text
            self._extract_from_markdown(content.split('\n'), knowledge, filepath)
    
    def _enhance_mlops_knowledge(self, knowledge: Dict, lines: List[str], filepath: str):
        """Add MLOps-specific knowledge extraction."""
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Kubernetes resources
            if 'apiversion:' in line_lower or 'kind:' in line_lower:
                knowledge["configurations"].append({
                    "line": i,
                    "content": line.strip(),
                    "type": "kubernetes_resource",
                    "category": "mlops"
                })
            
            # Ansible tasks
            if '- name:' in line_lower:
                knowledge["concepts"].append({
                    "name": f"Ansible Task: {line.split(':', 1)[1].strip()}",
                    "line": i,
                    "type": "ansible_task",
                    "category": "mlops"
                })
            
            # Service definitions
            if any(service in line_lower for service in ['harbor', 'mlflow', 'seldon', 'istio', 'prometheus']):
                if ':' in line and not line.strip().startswith('#'):
                    knowledge["configurations"].append({
                        "line": i,
                        "content": line.strip(),
                        "type": "mlops_service_config",
                        "category": "mlops"
                    })
    
    def _enhance_ml_model_knowledge(self, knowledge: Dict, lines: List[str], filepath: str):
        """Add ML model-specific knowledge extraction."""
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Model training patterns
            if any(pattern in line_lower for pattern in ['fit(', 'train(', 'model.fit', '.train']):
                knowledge["concepts"].append({
                    "name": "Model Training",
                    "line": i,
                    "content": line.strip(),
                    "type": "ml_training",
                    "category": "ml_model"
                })
            
            # Feature engineering
            if any(pattern in line_lower for pattern in ['transform(', 'fit_transform(', 'feature']):
                knowledge["concepts"].append({
                    "name": "Feature Engineering",
                    "line": i,
                    "content": line.strip(),
                    "type": "ml_feature_engineering",
                    "category": "ml_model"
                })
            
            # Model evaluation
            if any(pattern in line_lower for pattern in ['score(', 'accuracy', 'precision', 'recall', 'f1']):
                knowledge["concepts"].append({
                    "name": "Model Evaluation",
                    "line": i,
                    "content": line.strip(),
                    "type": "ml_evaluation",
                    "category": "ml_model"
                })
    
    def _extract_commands_from_block(self, content: str, knowledge: Dict, filepath: str, line_offset: int):
        """Extract commands from code blocks."""
        for i, line in enumerate(content.split('\n')):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                knowledge["commands"].append({
                    "command": stripped,
                    "line": line_offset + i,
                    "file": filepath,
                    "type": self._classify_command(stripped),
                    "source": "code_block"
                })
    
    def _classify_command(self, command: str) -> str:
        """Classify command type."""
        cmd_lower = command.lower()
        if 'kubectl' in cmd_lower:
            return 'kubernetes'
        elif 'docker' in cmd_lower:
            return 'docker'
        elif 'ansible' in cmd_lower:
            return 'ansible'
        elif 'helm' in cmd_lower:
            return 'helm'
        elif 'git' in cmd_lower:
            return 'git'
        elif any(tool in cmd_lower for tool in ['pip', 'python', 'jupyter']):
            return 'python'
        else:
            return 'shell'
    
    def _classify_configuration(self, line: str) -> str:
        """Classify configuration type."""
        line_lower = line.lower()
        if 'namespace' in line_lower:
            return 'namespace'
        elif 'image' in line_lower:
            return 'container_image'
        elif 'port' in line_lower:
            return 'network'
        elif 'ip' in line_lower or 'loadbalancer' in line_lower:
            return 'network'
        else:
            return 'general'
    
    def _classify_yaml_config(self, key: str, value: str) -> str:
        """Classify YAML configuration type."""
        key_lower = key.lower()
        if 'namespace' in key_lower:
            return 'kubernetes_namespace'
        elif 'image' in key_lower:
            return 'container_image'
        elif 'port' in key_lower:
            return 'network_port'
        elif 'enabled' in key_lower:
            return 'feature_toggle'
        else:
            return 'yaml_config'
    
    def _classify_troubleshooting(self, line: str) -> str:
        """Classify troubleshooting entry type."""
        line_lower = line.lower()
        if 'error' in line_lower or 'failed' in line_lower:
            return 'error'
        elif 'fix' in line_lower or 'solution' in line_lower or 'resolved' in line_lower:
            return 'solution'
        else:
            return 'issue'
    
    def _classify_shell_command(self, command: str) -> str:
        """Classify shell command type."""
        return self._classify_command(command)
    
    def _extract_file_references(self, line: str) -> List[Dict]:
        """Extract file references from text."""
        refs = []
        patterns = [
            r'([a-zA-Z0-9_\-./]+\.md)',
            r'([a-zA-Z0-9_\-./]+\.ya?ml)',
            r'([a-zA-Z0-9_\-./]+\.sh)',
            r'([a-zA-Z0-9_\-./]+\.py)',
            r'([a-zA-Z0-9_\-./]+\.json)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                refs.append({
                    "file": match,
                    "context": line.strip()
                })
        
        return refs
    
    def _get_context(self, lines: List[str], index: int, window: int = 2) -> str:
        """Get context around a line."""
        start = max(0, index - window)
        end = min(len(lines), index + window + 1)
        return '\n'.join(lines[start:end])