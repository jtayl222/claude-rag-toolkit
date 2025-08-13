"""
Unit tests for the MCP Server implementation.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from integrations.mcp_server_enhanced import MCPServer


class TestMCPServer:
    """Test cases for MCP Server."""

    def test_init(self, temp_dir):
        """Test MCP server initialization."""
        server = MCPServer(str(temp_dir))
        
        assert server.project_root == temp_dir
        assert server.engine is None
        assert server.server_info["name"] == "claude-rag-toolkit"
        assert server.server_info["capabilities"]["tools"] is True

    @pytest.mark.asyncio
    async def test_handle_initialize(self, temp_dir):
        """Test initialization handler."""
        server = MCPServer(str(temp_dir))
        
        params = {"sessionId": "test-session-123"}
        result = await server.handle_initialize(params)
        
        assert "serverInfo" in result
        assert "capabilities" in result
        assert "instructions" in result
        assert result["serverInfo"]["name"] == "claude-rag-toolkit"
        assert result["capabilities"]["tools"]["listTools"] is True
        assert result["capabilities"]["tools"]["callTool"] is True
        assert server.session_id == "test-session-123"

    @pytest.mark.asyncio
    async def test_handle_list_tools(self, temp_dir):
        """Test listing available tools."""
        server = MCPServer(str(temp_dir))
        
        result = await server.handle_list_tools()
        
        assert "tools" in result
        tools = result["tools"]
        assert len(tools) == 6
        
        # Check tool names
        tool_names = [tool["name"] for tool in tools]
        assert "search_documentation" in tool_names
        assert "troubleshoot_error" in tool_names
        assert "get_file_context" in tool_names
        assert "get_related_commands" in tool_names
        assert "get_project_stats" in tool_names
        assert "reindex_project" in tool_names
        
        # Check tool has required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool

    @pytest.mark.asyncio
    async def test_handle_call_tool_search(self, temp_dir):
        """Test search_documentation tool call."""
        server = MCPServer(str(temp_dir))
        
        # Mock the engine
        with patch.object(server, '_get_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.search.return_value = {
                "concept_matches": [
                    {"title": "Test Concept", "score": 0.9, "file": "test.md"}
                ],
                "command_matches": [],
                "configuration_matches": [],
                "troubleshooting_matches": []
            }
            mock_get_engine.return_value = mock_engine
            
            result = await server.handle_call_tool(
                "search_documentation",
                {"query": "test query", "limit": 5}
            )
            
            assert "content" in result
            assert len(result["content"]) > 0
            assert result["content"][0]["type"] == "text"
            assert "Search Results for: 'test query'" in result["content"][0]["text"]
            assert "Test Concept" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown(self, temp_dir):
        """Test handling unknown tool."""
        server = MCPServer(str(temp_dir))
        
        result = await server.handle_call_tool("unknown_tool", {})
        
        assert "error" in result
        assert result["error"]["code"] == -32601
        assert "Unknown tool" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_call_tool_error(self, temp_dir):
        """Test error handling in tool call."""
        server = MCPServer(str(temp_dir))
        
        # Mock engine to raise exception
        with patch.object(server, '_get_engine') as mock_get_engine:
            mock_get_engine.side_effect = Exception("Test error")
            
            result = await server.handle_call_tool(
                "search_documentation",
                {"query": "test"}
            )
            
            assert "error" in result
            assert result["error"]["code"] == -32603
            assert "Test error" in result["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_request_jsonrpc(self, temp_dir):
        """Test JSON-RPC 2.0 request handling."""
        server = MCPServer(str(temp_dir))
        
        # Test valid request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert response["id"] == 1
        assert "tools" in response["result"]

    @pytest.mark.asyncio
    async def test_handle_request_invalid_jsonrpc(self, temp_dir):
        """Test handling invalid JSON-RPC version."""
        server = MCPServer(str(temp_dir))
        
        request = {
            "jsonrpc": "1.0",  # Invalid version
            "method": "tools/list",
            "id": 1
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32600
        assert "Not a JSON-RPC 2.0 request" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_request_method_not_found(self, temp_dir):
        """Test handling unknown method."""
        server = MCPServer(str(temp_dir))
        
        request = {
            "jsonrpc": "2.0",
            "method": "unknown/method",
            "id": 2
        }
        
        response = await server.handle_request(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "error" in response
        assert response["error"]["code"] == -32601
        assert "Method not found" in response["error"]["message"]

    @pytest.mark.asyncio
    async def test_handle_troubleshoot_error(self, temp_dir):
        """Test troubleshoot_error tool."""
        server = MCPServer(str(temp_dir))
        
        with patch.object(server, '_get_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.search.return_value = {
                "troubleshooting_matches": [
                    {"title": "Fix for error", "content": "Solution here", "file": "troubleshoot.md"}
                ],
                "concept_matches": [],
                "command_matches": [],
                "configuration_matches": []
            }
            mock_get_engine.return_value = mock_engine
            
            result = await server.handle_call_tool(
                "troubleshoot_error",
                {"error": "connection refused"}
            )
            
            assert "content" in result
            text = result["content"][0]["text"]
            assert "Troubleshooting Results" in text
            assert "connection refused" in text

    @pytest.mark.asyncio
    async def test_handle_get_file_context(self, temp_dir):
        """Test get_file_context tool."""
        server = MCPServer(str(temp_dir))
        
        with patch.object(server, '_get_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.get_file_context.return_value = {
                "file_path": "test.py",
                "last_modified": "2024-01-01",
                "knowledge": {
                    "functions": ["main", "helper"],
                    "dependencies": ["os", "sys"],
                    "concepts": ["testing"]
                },
                "related_files": ["test2.py", "README.md"]
            }
            mock_get_engine.return_value = mock_engine
            
            result = await server.handle_call_tool(
                "get_file_context",
                {"filepath": "test.py"}
            )
            
            assert "content" in result
            text = result["content"][0]["text"]
            assert "File Context: test.py" in text
            assert "Functions: main, helper" in text
            assert "Dependencies: os, sys" in text

    @pytest.mark.asyncio
    async def test_handle_get_project_stats(self, temp_dir):
        """Test get_project_stats tool."""
        server = MCPServer(str(temp_dir))
        
        with patch.object(server, '_get_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.index = {
                "version": "1.0",
                "repo_type": "python",
                "last_updated": "2024-01-01T10:00:00",
                "documents": {"file1.py": {}, "file2.py": {}},
                "project_stats": {
                    "total_files": 100,
                    "total_lines": 5000
                }
            }
            mock_get_engine.return_value = mock_engine
            
            result = await server.handle_call_tool(
                "get_project_stats",
                {}
            )
            
            assert "content" in result
            text = result["content"][0]["text"]
            assert "Project Statistics" in text
            assert "Repository Type: python" in text
            assert "Total Documents: 2" in text

    @pytest.mark.asyncio
    async def test_handle_reindex_project(self, temp_dir):
        """Test reindex_project tool."""
        server = MCPServer(str(temp_dir))
        
        with patch.object(server, '_get_engine') as mock_get_engine:
            mock_engine = Mock()
            mock_engine.index_project.return_value = {
                "indexed_files": 50,
                "total_concepts": 100,
                "total_commands": 25
            }
            mock_get_engine.return_value = mock_engine
            
            result = await server.handle_call_tool(
                "reindex_project",
                {"force": True}
            )
            
            assert "content" in result
            text = result["content"][0]["text"]
            assert "Reindex Results" in text
            assert "Files Indexed: 50" in text
            assert "Index successfully updated" in text

    @pytest.mark.asyncio
    async def test_format_search_results_empty(self, temp_dir):
        """Test formatting empty search results."""
        server = MCPServer(str(temp_dir))
        
        results = {
            "concept_matches": [],
            "command_matches": [],
            "configuration_matches": [],
            "troubleshooting_matches": []
        }
        
        text = server._format_search_results(results, "test query")
        
        assert "Search Results for: 'test query'" in text
        assert "No matches found" in text
        assert "Try different keywords" in text

    @pytest.mark.asyncio
    async def test_format_troubleshooting_empty(self, temp_dir):
        """Test formatting empty troubleshooting results."""
        server = MCPServer(str(temp_dir))
        
        text = server._format_troubleshooting_results([], "error message")
        
        assert "Troubleshooting Results for: 'error message'" in text
        assert "No specific troubleshooting information found" in text
        assert "Suggestions:" in text

    def test_get_engine_lazy_initialization(self, temp_dir):
        """Test lazy initialization of RAG engine."""
        server = MCPServer(str(temp_dir))
        
        assert server.engine is None
        
        engine1 = server._get_engine()
        assert engine1 is not None
        assert server.engine is engine1
        
        # Should return same instance
        engine2 = server._get_engine()
        assert engine2 is engine1