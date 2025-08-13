#!/usr/bin/env python3
"""
Claude RAG Toolkit CLI
Command-line interface for multi-repository documentation management.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional

from .core.rag_engine import MultiRepoRAGEngine
from .utils.repo_detector import RepositoryDetector


class RAGToolkitCLI:
    """Command-line interface for the RAG toolkit."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description="Claude RAG Toolkit - Multi-repository documentation management",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  claude-rag init --repo-type mlops-platform    Initialize RAG system for MLOps platform
  claude-rag search "harbor registry"           Search for harbor registry information
  claude-rag troubleshoot "port 6443"           Find solutions for port 6443 issues
  claude-rag context README.md                  Get context for README.md file
  claude-rag commands kubectl                   List kubectl commands
  claude-rag reindex                            Rebuild the documentation index
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Init command
        init_parser = subparsers.add_parser('init', help='Initialize RAG system in current project')
        init_parser.add_argument('--repo-type', choices=['mlops-platform', 'ml-model', 'kubernetes', 'ansible', 'python', 'documentation', 'generic'], 
                               help='Specify repository type (auto-detected if not provided)')
        init_parser.add_argument('--force', action='store_true', help='Overwrite existing configuration')
        
        # Search command
        search_parser = subparsers.add_parser('search', help='Search documentation')
        search_parser.add_argument('query', help='Search query')
        search_parser.add_argument('-l', '--limit', type=int, default=10, help='Maximum results per category')
        search_parser.add_argument('--category', choices=['concepts', 'commands', 'configurations', 'troubleshooting'], 
                                 help='Limit search to specific category')
        
        # Context command
        context_parser = subparsers.add_parser('context', help='Get file context and relationships')
        context_parser.add_argument('filepath', help='File path (relative to project root)')
        
        # Troubleshoot command
        trouble_parser = subparsers.add_parser('troubleshoot', help='Find error solutions')
        trouble_parser.add_argument('error', help='Error keyword or message')
        
        # Commands command
        commands_parser = subparsers.add_parser('commands', help='List commands for specific technology')
        commands_parser.add_argument('technology', help='Technology (kubectl, docker, ansible, etc.)')
        commands_parser.add_argument('-l', '--limit', type=int, default=15, help='Maximum number of commands')
        
        # Recent command
        subparsers.add_parser('recent', help='Show recent documentation changes')
        
        # Stats command
        subparsers.add_parser('stats', help='Show index statistics')
        
        # Reindex command
        reindex_parser = subparsers.add_parser('reindex', help='Rebuild documentation index')
        reindex_parser.add_argument('--force', action='store_true', help='Force reindex all files')
        
        # Info command
        subparsers.add_parser('info', help='Show repository information')
        
        # Setup command
        setup_parser = subparsers.add_parser('setup-mcp', help='Setup MCP server configuration')
        setup_parser.add_argument('--claude-config-dir', help='Path to Claude Code configuration directory')
        
        return parser
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI with given arguments."""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        try:
            return self._execute_command(parsed_args)
        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            print(f"❌ Error: {e}")
            if '--debug' in (args or sys.argv):
                import traceback
                traceback.print_exc()
            return 1
    
    def _execute_command(self, args) -> int:
        """Execute the parsed command."""
        if args.command == 'init':
            return self._cmd_init(args)
        elif args.command == 'search':
            return self._cmd_search(args)
        elif args.command == 'context':
            return self._cmd_context(args)
        elif args.command == 'troubleshoot':
            return self._cmd_troubleshoot(args)
        elif args.command == 'commands':
            return self._cmd_commands(args)
        elif args.command == 'recent':
            return self._cmd_recent(args)
        elif args.command == 'stats':
            return self._cmd_stats(args)
        elif args.command == 'reindex':
            return self._cmd_reindex(args)
        elif args.command == 'info':
            return self._cmd_info(args)
        elif args.command == 'setup-mcp':
            return self._cmd_setup_mcp(args)
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
    
    def _cmd_init(self, args) -> int:
        """Initialize RAG system in current project."""
        project_root = Path.cwd()
        rag_dir = project_root / '.claude-rag'
        config_path = rag_dir / 'config.json'
        
        # Check if already initialized
        if config_path.exists() and not args.force:
            print(f"✅ RAG system already initialized in {project_root}")
            print(f"📄 Configuration: {config_path}")
            print("💡 Use --force to reinitialize")
            return 0
        
        print(f"🚀 Initializing RAG system in: {project_root}")
        
        # Initialize RAG engine (will auto-detect repo type and create config)
        engine = MultiRepoRAGEngine(str(project_root))
        
        # Override repo type if specified
        if args.repo_type:
            config = engine.config
            config['repo_type'] = args.repo_type
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"🔧 Repository type set to: {args.repo_type}")
        
        # Run initial indexing
        print("📚 Running initial indexing...")
        results = engine.index_project()
        
        print(f"✅ RAG system initialized successfully!")
        print(f"📁 Configuration: {config_path}")
        print(f"📊 Indexed {results['processed']} files")
        
        # Add gitignore entry for generated files
        gitignore_path = project_root / '.gitignore'
        gitignore_entry = ".claude-rag/index.json\n.claude-rag/cache.json\n.claude-rag/*.tmp\n"
        
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            if '.claude-rag/' not in content:
                with open(gitignore_path, 'a') as f:
                    f.write(f"\n# Claude RAG generated files\n{gitignore_entry}")
                print("📝 Added .claude-rag/ entries to .gitignore")
        else:
            with open(gitignore_path, 'w') as f:
                f.write(f"# Claude RAG generated files\n{gitignore_entry}")
            print("📝 Created .gitignore with RAG entries")
        
        return 0
    
    def _cmd_search(self, args) -> int:
        """Search documentation."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        results = engine.search(args.query, args.limit)
        
        print(f"🔍 Search results for: '{args.query}'")
        print("=" * 60)
        
        categories = ['concept_matches', 'command_matches', 'configuration_matches', 'troubleshooting_matches']
        category_icons = {
            'concept_matches': '💡',
            'command_matches': '⚡',
            'configuration_matches': '⚙️',
            'troubleshooting_matches': '🔧'
        }
        
        if args.category:
            categories = [f"{args.category}_matches"]
        
        total_results = 0
        for category in categories:
            matches = results.get(category, [])
            if matches:
                icon = category_icons.get(category, '📄')
                category_name = category.replace('_matches', '').replace('_', ' ').title()
                print(f"\n{icon} {category_name}:")
                
                for i, match in enumerate(matches, 1):
                    file = match.get('file', 'Unknown')
                    line = match.get('line', '?')
                    
                    if category == 'concept_matches':
                        print(f"  {i}. [{file}:{line}] {match.get('concept', '')}")
                    elif category == 'command_matches':
                        print(f"  {i}. [{file}:{line}] {match.get('command', '')}")
                    elif category == 'configuration_matches':
                        print(f"  {i}. [{file}:{line}] {match.get('content', '')[:80]}...")
                    elif category == 'troubleshooting_matches':
                        print(f"  {i}. [{file}:{line}] ({match.get('type', '')}) {match.get('content', '')[:80]}...")
                
                total_results += len(matches)
        
        if total_results == 0:
            print("❌ No results found")
            print("💡 Try different keywords or run 'claude-rag reindex' to update the index")
        else:
            print(f"\n📊 Total results: {total_results}")
        
        return 0
    
    def _cmd_context(self, args) -> int:
        """Get file context and relationships."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        context = engine.get_file_context(args.filepath)
        
        if 'error' in context:
            print(f"❌ {context['error']}")
            return 1
        
        print(f"📄 Context for: {args.filepath}")
        print("=" * 60)
        
        # File info
        file_info = context['file_info']
        print(f"📊 File Info:")
        print(f"  Size: {file_info['size']} bytes")
        print(f"  Lines: {file_info['lines']}")
        print(f"  Type: {file_info['type']}")
        print(f"  Last indexed: {file_info.get('last_indexed', 'Unknown')}")
        
        # Concepts
        concepts = context.get('concepts', [])
        if concepts:
            print(f"\n💡 Key Concepts:")
            for concept in concepts[:5]:
                print(f"  • {concept.get('name', 'Unknown')} (line {concept.get('line', '?')})")
        
        # Commands
        commands = context.get('commands', [])
        if commands:
            print(f"\n⚡ Commands Found:")
            for cmd in commands[:5]:
                print(f"  • [{cmd.get('type', 'shell')}] {cmd.get('command', '')[:60]}...")
        
        # Related files
        related = context.get('related_files', [])
        if related:
            print(f"\n🔗 Related Files:")
            for related_file in related:
                print(f"  • {related_file}")
        
        return 0
    
    def _cmd_troubleshoot(self, args) -> int:
        """Find troubleshooting information."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        results = engine.search(args.error, limit=20)
        troubleshooting = results.get('troubleshooting_matches', [])
        
        print(f"🔧 Troubleshooting: '{args.error}'")
        print("=" * 60)
        
        if not troubleshooting:
            print("❌ No troubleshooting information found")
            print("💡 Try different keywords or check if the issue is documented")
            return 0
        
        # Group by type
        errors = [t for t in troubleshooting if t.get('type') == 'error']
        solutions = [t for t in troubleshooting if t.get('type') == 'solution']
        issues = [t for t in troubleshooting if t.get('type') == 'issue']
        
        if errors:
            print("\n❌ Known Errors:")
            for i, error in enumerate(errors[:3], 1):
                print(f"  {i}. [{error.get('file', '')}:{error.get('line', '?')}]")
                print(f"     {error.get('content', '')[:100]}...")
        
        if solutions:
            print("\n✅ Solutions:")
            for i, solution in enumerate(solutions[:5], 1):
                print(f"  {i}. [{solution.get('file', '')}:{solution.get('line', '?')}]")
                print(f"     {solution.get('content', '')[:100]}...")
        
        if issues:
            print("\n⚠️  Related Issues:")
            for i, issue in enumerate(issues[:3], 1):
                print(f"  {i}. [{issue.get('file', '')}:{issue.get('line', '?')}]")
                print(f"     {issue.get('content', '')[:100]}...")
        
        return 0
    
    def _cmd_commands(self, args) -> int:
        """List commands for specific technology."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        results = engine.search(args.technology, limit=50)
        commands = results.get('command_matches', [])
        
        # Filter by technology
        tech_commands = [cmd for cmd in commands 
                        if args.technology.lower() in cmd.get('command', '').lower() 
                        or args.technology.lower() in cmd.get('type', '').lower()]
        
        print(f"⚡ Commands for '{args.technology}':")
        print("=" * 60)
        
        if not tech_commands:
            print("❌ No commands found")
            return 0
        
        # Limit results
        tech_commands = tech_commands[:args.limit]
        
        for i, cmd in enumerate(tech_commands, 1):
            cmd_type = cmd.get('type', 'shell')
            file = cmd.get('file', 'Unknown')
            line = cmd.get('line', '?')
            command = cmd.get('command', '')
            
            print(f"  {i}. [{file}:{line}] ({cmd_type})")
            print(f"     {command}")
        
        print(f"\n📊 Found {len(tech_commands)} commands")
        return 0
    
    def _cmd_recent(self, args) -> int:
        """Show recent documentation changes."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        changes = engine.index.get('recent_changes', [])
        
        print("📝 Recent Documentation Changes:")
        print("=" * 60)
        
        if not changes:
            print("❌ No recent changes tracked")
            print("💡 Changes are tracked via git history")
            return 0
        
        for change in changes:
            status = change.get('status', '?')
            file = change.get('file', 'Unknown')
            timestamp = change.get('timestamp', '')
            
            status_icon = "➕" if status == "A" else "✏️" if status == "M" else "➖" if status == "D" else "❓"
            print(f"{status_icon} {file} ({timestamp[:10]})")
        
        return 0
    
    def _cmd_stats(self, args) -> int:
        """Show index statistics."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        stats = engine.index.get('statistics', {})
        repo_type = engine.index.get('repo_type', 'unknown')
        last_indexed = engine.index.get('last_indexed', 'Never')
        
        print("📊 Documentation Index Statistics:")
        print("=" * 60)
        print(f"Repository Type: {repo_type}")
        print(f"Last Indexed: {last_indexed}")
        print(f"Files Indexed: {stats.get('total_files', 0)}")
        print(f"Commands Extracted: {stats.get('total_commands', 0)}")
        print(f"Concepts Identified: {stats.get('total_concepts', 0)}")
        print(f"Configurations Found: {stats.get('total_configurations', 0)}")
        print(f"Troubleshooting Entries: {stats.get('total_troubleshooting', 0)}")
        print(f"Knowledge Graph Nodes: {stats.get('knowledge_graph_nodes', 0)}")
        print(f"Recent Changes: {len(engine.index.get('recent_changes', []))}")
        
        return 0
    
    def _cmd_reindex(self, args) -> int:
        """Rebuild documentation index."""
        engine = self._get_engine()
        if not engine:
            return 1
        
        print("🔄 Rebuilding documentation index...")
        results = engine.index_project(force_reindex=args.force)
        
        print(f"✅ Reindexing complete!")
        print(f"📊 Processed: {results['processed']} files")
        print(f"🔄 Updated: {results['updated']} files")
        
        return 0
    
    def _cmd_info(self, args) -> int:
        """Show repository information."""
        detector = RepositoryDetector('.')
        info = detector.get_repository_info()
        
        print("📋 Repository Information:")
        print("=" * 60)
        print(f"Project Root: {info['project_root']}")
        print(f"Detected Type: {info['detected_type']}")
        
        if info['git_info'].get('remote'):
            print(f"Git Remote: {info['git_info']['remote']}")
        
        print(f"\n📁 Directory Structure:")
        for directory in info['directory_structure']:
            print(f"  • {directory}/")
        
        print(f"\n📄 File Types:")
        for ext, count in list(info['file_counts'].items())[:5]:
            print(f"  • {ext}: {count} files")
        
        return 0
    
    def _cmd_setup_mcp(self, args) -> int:
        """Setup MCP server configuration."""
        # This would set up MCP configuration for Claude Code
        print("🔧 Setting up MCP server configuration...")
        print("⚠️  This feature is not yet implemented")
        print("💡 Manually configure MCP server using documentation in README_MCP.md")
        return 0
    
    def _get_engine(self) -> Optional[MultiRepoRAGEngine]:
        """Get initialized RAG engine."""
        try:
            return MultiRepoRAGEngine('.')
        except Exception as e:
            print(f"❌ RAG system not initialized: {e}")
            print("💡 Run 'claude-rag init' to initialize")
            return None


def main():
    """Main entry point."""
    cli = RAGToolkitCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())