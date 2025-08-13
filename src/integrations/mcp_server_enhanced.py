#!/usr/bin/env python3
"""
Enhanced MCP Server for Claude RAG Toolkit
Implements the Model Context Protocol with JSON-RPC 2.0 support.
"""

import asyncio
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.rag_engine import MultiRepoRAGEngine


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Enhanced MCP Server with JSON-RPC 2.0 protocol support."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.engine = None
        self.server_info = {
            "name": "claude-rag-toolkit",
            "version": "1.0.0",
            "description": "Multi-repository documentation RAG system for Claude Code",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False
            }
        }
        self.session_id = None
        
    def _get_engine(self) -> MultiRepoRAGEngine:
        """Get or initialize RAG engine."""
        if self.engine is None:
            self.engine = MultiRepoRAGEngine(str(self.project_root))
        return self.engine
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization request."""
        self.session_id = params.get("sessionId", datetime.now().isoformat())
        
        return {
            "serverInfo": self.server_info,
            "capabilities": {
                "tools": {
                    "listTools": True,
                    "callTool": True
                }
            },
            "instructions": "Use the search_documentation tool to search project knowledge base. "
                          "Use troubleshoot_error for finding solutions. "
                          "Use get_file_context for understanding file relationships."
        }
    
    async def handle_list_tools(self) -> Dict[str, Any]:
        """List available MCP tools."""
        tools = [
            {
                "name": "search_documentation",
                "description": "Search project documentation and knowledge base",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or keywords"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["all", "concepts", "commands", "configurations", "troubleshooting"],
                            "description": "Category to search in",
                            "default": "all"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "troubleshoot_error",
                "description": "Find solutions for specific errors or issues",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string",
                            "description": "Error message or keyword to search for"
                        }
                    },
                    "required": ["error"]
                }
            },
            {
                "name": "get_file_context",
                "description": "Get detailed context and relationships for a specific file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filepath": {
                            "type": "string",
                            "description": "Path to file relative to project root"
                        }
                    },
                    "required": ["filepath"]
                }
            },
            {
                "name": "get_related_commands",
                "description": "Find commands related to a specific technology or tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "technology": {
                            "type": "string",
                            "description": "Technology name (kubectl, docker, ansible, etc.)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of commands to return",
                            "default": 15,
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["technology"]
                }
            },
            {
                "name": "get_project_stats",
                "description": "Get project statistics and index health information",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "reindex_project",
                "description": "Rebuild the project documentation index",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force reindex all files even if unchanged",
                            "default": False
                        }
                    }
                }
            }
        ]
        
        return {"tools": tools}
    
    async def handle_call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool invocation."""
        try:
            engine = self._get_engine()
            
            if tool_name == "search_documentation":
                query = arguments.get("query", "")
                category = arguments.get("category", "all")
                limit = arguments.get("limit", 10)
                
                results = engine.search(query, limit)
                
                # Filter by category if specified
                if category != "all":
                    category_map = {
                        "concepts": "concept_matches",
                        "commands": "command_matches",
                        "configurations": "configuration_matches",
                        "troubleshooting": "troubleshooting_matches"
                    }
                    if category in category_map:
                        filtered_results = {category_map[category]: results.get(category_map[category], [])}
                        results = filtered_results
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": self._format_search_results(results, query)
                        }
                    ]
                }
            
            elif tool_name == "troubleshoot_error":
                error = arguments.get("error", "")
                results = engine.search(error, limit=20)
                
                # Focus on troubleshooting matches
                troubleshooting = results.get("troubleshooting_matches", [])
                
                # Also check other matches for error-related content
                for category in ["concept_matches", "command_matches", "configuration_matches"]:
                    for match in results.get(category, []):
                        if any(keyword in str(match).lower() for keyword in ["error", "fix", "solution", "troubleshoot"]):
                            troubleshooting.append(match)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": self._format_troubleshooting_results(troubleshooting, error)
                        }
                    ]
                }
            
            elif tool_name == "get_file_context":
                filepath = arguments.get("filepath", "")
                context = engine.get_file_context(filepath)
                
                if context and "error" not in context:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": self._format_file_context(context, filepath)
                            }
                        ]
                    }
                else:
                    error_msg = context.get("error", "File not found") if context else "File not found"
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"❌ {error_msg}"
                            }
                        ]
                    }
            
            elif tool_name == "get_related_commands":
                technology = arguments.get("technology", "")
                limit = arguments.get("limit", 15)
                
                results = engine.search(technology, limit=50)
                commands = []
                
                # Extract commands from all categories
                for category in results:
                    for match in results[category]:
                        if "command" in str(match).lower() or technology.lower() in str(match).lower():
                            commands.append(match)
                            if len(commands) >= limit:
                                break
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": self._format_command_results(commands[:limit], technology)
                        }
                    ]
                }
            
            elif tool_name == "get_project_stats":
                stats = engine.index.get("project_stats", {})
                index_info = {
                    "version": engine.index.get("version"),
                    "repo_type": engine.index.get("repo_type"),
                    "last_updated": engine.index.get("last_updated"),
                    "total_documents": len(engine.index.get("documents", {}))
                }
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": self._format_project_stats(stats, index_info)
                        }
                    ]
                }
            
            elif tool_name == "reindex_project":
                force = arguments.get("force", False)
                
                # Call index_project method
                results = engine.index_project()
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": self._format_reindex_results(results, force)
                        }
                    ]
                }
            
            else:
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        
        except Exception as e:
            logger.error(f"Error in tool execution: {e}", exc_info=True)
            return {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def _format_search_results(self, results: Dict, query: str) -> str:
        """Format search results for display."""
        output = [f"🔍 Search Results for: '{query}'\n"]
        
        total_results = sum(len(matches) for matches in results.values())
        output.append(f"Found {total_results} matches across categories:\n")
        
        for category, matches in results.items():
            if matches:
                category_name = category.replace("_", " ").title()
                output.append(f"\n### {category_name} ({len(matches)} matches)")
                
                for i, match in enumerate(matches[:5], 1):  # Show first 5 per category
                    if isinstance(match, dict):
                        title = match.get("title", "Unknown")
                        score = match.get("score", 0)
                        file = match.get("file", "")
                        output.append(f"{i}. **{title}** (score: {score:.2f})")
                        if file:
                            output.append(f"   File: {file}")
                    else:
                        output.append(f"{i}. {match}")
        
        if total_results == 0:
            output.append("No matches found. Try different keywords or run 'reindex_project' to update the index.")
        
        return "\n".join(output)
    
    def _format_troubleshooting_results(self, results: List, error: str) -> str:
        """Format troubleshooting results."""
        output = [f"🔧 Troubleshooting Results for: '{error}'\n"]
        
        if results:
            output.append(f"Found {len(results)} potential solutions:\n")
            
            for i, solution in enumerate(results[:10], 1):  # Show first 10
                if isinstance(solution, dict):
                    title = solution.get("title", "Solution")
                    content = solution.get("content", "")
                    file = solution.get("file", "")
                    
                    output.append(f"\n{i}. **{title}**")
                    if file:
                        output.append(f"   Source: {file}")
                    if content:
                        output.append(f"   {content[:200]}...")
                else:
                    output.append(f"\n{i}. {solution}")
        else:
            output.append("No specific troubleshooting information found.")
            output.append("\nSuggestions:")
            output.append("- Try searching with different error keywords")
            output.append("- Check the project documentation")
            output.append("- Run 'reindex_project' to ensure index is up-to-date")
        
        return "\n".join(output)
    
    def _format_file_context(self, context: Dict, filepath: str) -> str:
        """Format file context information."""
        output = [f"📄 File Context: {filepath}\n"]
        
        if "last_modified" in context:
            output.append(f"Last Modified: {context['last_modified']}")
        
        if "knowledge" in context:
            knowledge = context["knowledge"]
            if knowledge.get("functions"):
                output.append(f"\nFunctions: {', '.join(knowledge['functions'][:5])}")
            if knowledge.get("dependencies"):
                output.append(f"Dependencies: {', '.join(knowledge['dependencies'][:5])}")
            if knowledge.get("concepts"):
                output.append(f"Concepts: {', '.join(str(c) for c in knowledge['concepts'][:5])}")
        
        if "related_files" in context:
            output.append(f"\nRelated Files:")
            for file in context["related_files"][:5]:
                output.append(f"  - {file}")
        
        return "\n".join(output)
    
    def _format_command_results(self, commands: List, technology: str) -> str:
        """Format command results."""
        output = [f"💻 Commands for: {technology}\n"]
        
        if commands:
            output.append(f"Found {len(commands)} related commands:\n")
            
            for i, cmd in enumerate(commands, 1):
                if isinstance(cmd, dict):
                    command = cmd.get("command", cmd.get("title", ""))
                    file = cmd.get("file", "")
                    output.append(f"{i}. `{command}`")
                    if file:
                        output.append(f"   Source: {file}")
                else:
                    output.append(f"{i}. {cmd}")
        else:
            output.append(f"No commands found for '{technology}'")
        
        return "\n".join(output)
    
    def _format_project_stats(self, stats: Dict, index_info: Dict) -> str:
        """Format project statistics."""
        output = ["📊 Project Statistics\n"]
        
        output.append(f"Repository Type: {index_info.get('repo_type', 'Unknown')}")
        output.append(f"Index Version: {index_info.get('version', 'Unknown')}")
        output.append(f"Last Updated: {index_info.get('last_updated', 'Never')}")
        output.append(f"Total Documents: {index_info.get('total_documents', 0)}")
        
        if stats:
            output.append("\nDetailed Statistics:")
            for key, value in stats.items():
                output.append(f"  {key}: {value}")
        
        return "\n".join(output)
    
    def _format_reindex_results(self, results: Dict, force: bool) -> str:
        """Format reindex results."""
        output = ["🔄 Reindex Results\n"]
        
        if force:
            output.append("Force reindex: All files processed")
        
        if results:
            indexed = results.get("indexed_files", 0)
            output.append(f"Files Indexed: {indexed}")
            
            if "total_concepts" in results:
                output.append(f"Concepts Found: {results['total_concepts']}")
            if "total_commands" in results:
                output.append(f"Commands Extracted: {results['total_commands']}")
        
        output.append("\n✅ Index successfully updated")
        
        return "\n".join(output)
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC 2.0 request."""
        # Validate request structure
        if "jsonrpc" not in request or request["jsonrpc"] != "2.0":
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "Invalid Request: Not a JSON-RPC 2.0 request"
                },
                "id": request.get("id")
            }
        
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        # Route to appropriate handler
        result = None
        error = None
        
        try:
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools()
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await self.handle_call_tool(tool_name, arguments)
            else:
                error = {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            error = {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        
        # Build response
        response = {"jsonrpc": "2.0"}
        
        if error:
            response["error"] = error
        else:
            response["result"] = result
        
        if request_id is not None:
            response["id"] = request_id
        
        return response
    
    async def run_stdio_server(self):
        """Run MCP server using stdio transport."""
        logger.info(f"Starting MCP server for project: {self.project_root}")
        
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        writer = sys.stdout
        
        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break
                
                # Parse JSON-RPC request
                try:
                    request = json.loads(line.decode())
                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        },
                        "id": None
                    }
                    writer.write(json.dumps(error_response).encode() + b'\n')
                    writer.flush()
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response
                writer.write(json.dumps(response).encode() + b'\n')
                writer.flush()
                
            except KeyboardInterrupt:
                logger.info("Server stopped by user")
                break
            except Exception as e:
                logger.error(f"Server error: {e}", exc_info=True)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Claude RAG Toolkit MCP Server")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    parser.add_argument("--list-tools", action="store_true", help="List available tools and exit")
    
    args = parser.parse_args()
    
    server = MCPServer(args.project_root)
    
    if args.list_tools:
        tools = await server.handle_list_tools()
        print(json.dumps(tools, indent=2))
        return
    
    if args.test:
        # Test mode - run a sample request
        test_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        response = await server.handle_request(test_request)
        print(json.dumps(response, indent=2))
        return
    
    # Run the server
    await server.run_stdio_server()


if __name__ == "__main__":
    asyncio.run(main())