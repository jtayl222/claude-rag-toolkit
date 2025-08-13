#!/usr/bin/env python3
"""
MCP Server for Claude RAG Toolkit
Provides Model Context Protocol integration for Claude Code.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.rag_engine import MultiRepoRAGEngine


class ClaudeRAGMCPServer:
    """MCP Server for Claude RAG Toolkit."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.engine = None
    
    def _get_engine(self) -> MultiRepoRAGEngine:
        """Get or initialize RAG engine."""
        if self.engine is None:
            self.engine = MultiRepoRAGEngine(str(self.project_root))
        return self.engine
    
    async def search_documentation(self, query: str, category: str = "all", limit: int = 10) -> Dict[str, Any]:
        """Search project documentation."""
        try:
            engine = self._get_engine()
            results = engine.search(query, limit)
            
            return {
                "success": True,
                "results": results,
                "total_results": len(results),
                "query": query,
                "category": category
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def troubleshoot_error(self, error: str) -> Dict[str, Any]:
        """Find troubleshooting information for errors."""
        try:
            engine = self._get_engine()
            results = engine.search(error, limit=20)
            
            # Filter for troubleshooting content
            troubleshooting = []
            for result in results:
                if "troubleshoot" in result.get("file", "").lower() or \
                   any("error" in match.lower() or "fix" in match.lower() or "solution" in match.lower() 
                       for match in result.get("matches", [])):
                    troubleshooting.append(result)
            
            return {
                "success": True,
                "troubleshooting_results": troubleshooting,
                "total_results": len(troubleshooting),
                "error_query": error
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_query": error
            }
    
    async def get_file_context(self, filepath: str) -> Dict[str, Any]:
        """Get context for a specific file."""
        try:
            engine = self._get_engine()
            context = engine.get_file_context(filepath)
            
            return {
                "success": True,
                "file_context": context,
                "filepath": filepath
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filepath": filepath
            }
    
    async def get_related_commands(self, technology: str, limit: int = 15) -> Dict[str, Any]:
        """Find commands related to a technology."""
        try:
            engine = self._get_engine()
            results = engine.search(technology, limit=50)
            
            # Filter for commands
            commands = []
            for result in results:
                for match in result.get("matches", []):
                    if "Command:" in match and technology.lower() in match.lower():
                        commands.append({
                            "file": result.get("file"),
                            "command": match.replace("Command: ", ""),
                            "score": result.get("score", 0)
                        })
            
            return {
                "success": True,
                "commands": commands[:limit],
                "technology": technology,
                "total_found": len(commands)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "technology": technology
            }
    
    async def get_project_stats(self) -> Dict[str, Any]:
        """Get project statistics."""
        try:
            engine = self._get_engine()
            stats = engine.index.get("project_stats", {})
            
            return {
                "success": True,
                "stats": stats,
                "index_info": {
                    "version": engine.index.get("version"),
                    "last_updated": engine.index.get("last_updated"),
                    "total_documents": len(engine.index.get("documents", {})),
                    "repo_type": engine.index.get("repo_type")
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reindex_project(self, force: bool = False) -> Dict[str, Any]:
        """Reindex the project."""
        try:
            engine = self._get_engine()
            results = engine.index_project(force_reindex=force)
            
            return {
                "success": True,
                "indexing_results": results,
                "force_reindex": force
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "force_reindex": force
            }
    
    def get_tool_definitions(self) -> Dict[str, Any]:
        """Get MCP tool definitions."""
        return {
            "search_documentation": {
                "description": "Search project documentation and knowledge base",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "category": {"type": "string", "enum": ["all", "concepts", "commands", "configurations", "troubleshooting"], "default": "all"},
                        "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50}
                    },
                    "required": ["query"]
                }
            },
            "troubleshoot_error": {
                "description": "Find solutions for errors and issues",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string", "description": "Error message or keyword"}
                    },
                    "required": ["error"]
                }
            },
            "get_file_context": {
                "description": "Get detailed context for a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filepath": {"type": "string", "description": "File path relative to project root"}
                    },
                    "required": ["filepath"]
                }
            },
            "get_related_commands": {
                "description": "Find commands for a specific technology",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "technology": {"type": "string", "description": "Technology name"},
                        "limit": {"type": "integer", "default": 15, "minimum": 1, "maximum": 50}
                    },
                    "required": ["technology"]
                }
            },
            "get_project_stats": {
                "description": "Get project statistics and health",
                "parameters": {"type": "object", "properties": {}}
            },
            "reindex_project": {
                "description": "Rebuild project documentation index",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "force": {"type": "boolean", "default": False, "description": "Force reindex all files"}
                    }
                }
            }
        }
    
    async def handle_tool_call(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls."""
        handlers = {
            "search_documentation": self.search_documentation,
            "troubleshoot_error": self.troubleshoot_error,
            "get_file_context": self.get_file_context,
            "get_related_commands": self.get_related_commands,
            "get_project_stats": self.get_project_stats,
            "reindex_project": self.reindex_project
        }
        
        if tool_name not in handlers:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(handlers.keys())
            }
        
        try:
            return await handlers[tool_name](**parameters)
        except TypeError as e:
            return {
                "success": False,
                "error": f"Invalid parameters for {tool_name}: {e}",
                "tool": tool_name,
                "parameters": parameters
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution error: {e}",
                "tool": tool_name
            }


async def run_mcp_server(project_root: str, port: int = 8000):
    """Run the MCP server."""
    server = ClaudeRAGMCPServer(project_root)
    
    print(f"🚀 Claude RAG MCP Server starting...")
    print(f"📁 Project root: {project_root}")
    print(f"🔌 Port: {port}")
    print(f"🛠️ Available tools: {list(server.get_tool_definitions().keys())}")
    
    # For now, this is a basic implementation
    # In a full MCP implementation, this would handle the MCP protocol
    print("⚠️ This is a development server. Full MCP protocol support coming soon.")
    print("💡 For now, use the CLI interface: claude-rag <command>")
    
    # Keep server running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Claude RAG MCP Server")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--test-tools", action="store_true", help="Test tool definitions")
    
    args = parser.parse_args()
    
    if args.test_tools:
        server = ClaudeRAGMCPServer(args.project_root)
        tools = server.get_tool_definitions()
        print(json.dumps(tools, indent=2))
        return
    
    asyncio.run(run_mcp_server(args.project_root, args.port))


if __name__ == "__main__":
    main()