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

# Handle both relative and absolute imports
try:
    # When imported as a module (installed package)
    from core.rag_engine import MultiRepoRAGEngine
    from utils.repo_detector import RepositoryDetector
    from utils.session_manager import SessionManager
except ImportError:
    try:
        # When run from within the package structure
        from .core.rag_engine import MultiRepoRAGEngine
        from .utils.repo_detector import RepositoryDetector
        from .utils.session_manager import SessionManager
    except ImportError:
        # When run directly as a script - add src to path
        import sys
        from pathlib import Path
        src_path = Path(__file__).parent
        sys.path.insert(0, str(src_path))
        
        from core.rag_engine import MultiRepoRAGEngine
        from utils.repo_detector import RepositoryDetector
        from utils.session_manager import SessionManager


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
        reindex_parser.add_argument('--verbose', action='store_true', help='Show detailed indexing information')
        
        # Info command
        subparsers.add_parser('info', help='Show repository information')
        
        # Setup command
        setup_parser = subparsers.add_parser('setup-mcp', help='Setup MCP server configuration')
        setup_parser.add_argument('--claude-config-dir', help='Path to Claude Code configuration directory')
        
        # Session management commands
        session_parser = subparsers.add_parser('session', help='Session management commands')
        session_subparsers = session_parser.add_subparsers(dest='session_command', help='Session operations')
        
        # session start
        start_parser = session_subparsers.add_parser('start', help='Start a new development session')
        start_parser.add_argument('name', help='Session name')
        start_parser.add_argument('-d', '--description', help='Session description')
        start_parser.add_argument('-o', '--objectives', nargs='*', help='Session objectives')
        
        # session update
        update_parser = session_subparsers.add_parser('update', help='Update current session with progress')
        update_parser.add_argument('notes', help='Progress notes')
        update_parser.add_argument('-b', '--blocker', help='Record a blocker')
        update_parser.add_argument('--decision', help='Record a decision')
        
        # session end
        end_parser = session_subparsers.add_parser('end', help='End the current session')
        end_parser.add_argument('-s', '--summary', help='Session summary')
        
        # session pause
        pause_parser = session_subparsers.add_parser('pause', help='Pause the current session')
        pause_parser.add_argument('-r', '--reason', help='Reason for pausing')
        
        # session resume
        resume_parser = session_subparsers.add_parser('resume', help='Resume a paused session')
        resume_parser.add_argument('session_id', help='Session ID to resume')
        
        # session list
        list_parser = session_subparsers.add_parser('list', help='List all sessions')
        list_parser.add_argument('--status', choices=['active', 'paused', 'completed', 'cancelled'], help='Filter by status')
        
        # session show
        show_parser = session_subparsers.add_parser('show', help='Show session details')
        show_parser.add_argument('session_id', help='Session ID to show')
        
        # session current
        session_subparsers.add_parser('current', help='Show current session status')
        
        # session report
        report_parser = session_subparsers.add_parser('report', help='Generate session report')
        report_parser.add_argument('session_id', help='Session ID for report')
        report_parser.add_argument('-o', '--output', help='Output file (default: stdout)')
        
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
        elif args.command == 'session':
            return self._cmd_session(args)
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
        print(f"📊 Indexed {results['indexed_files']} files")
        
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
        
        # Show patterns being used if verbose
        if args.verbose:
            print(f"📋 Repository type: {engine.config.get('repo_type', 'unknown')}")
            print(f"📁 File patterns:")
            for pattern in engine.config.get('file_patterns', []):
                print(f"   - {pattern}")
            print(f"🚫 Exclude patterns:")
            for exclude in engine.config.get('exclude_paths', []):
                print(f"   - {exclude}")
            print()
        
        results = engine.index_project(force_reindex=args.force, verbose=args.verbose)
        
        print(f"✅ Reindexing complete!")
        print(f"📊 Processed: {results['indexed_files']} files")
        print(f"📁 Total files: {results['total_files']} files")
        
        if args.verbose and 'skipped_files' in results:
            print(f"⏭️  Skipped: {results['skipped_files']} files")
        
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
        import json
        import os
        from pathlib import Path
        
        print("🔧 Setting up MCP server configuration...")
        
        # Get Claude config directory
        if args.claude_config_dir:
            config_dir = Path(args.claude_config_dir)
        else:
            # Try common locations
            home = Path.home()
            possible_dirs = [
                home / ".config" / "claude",
                home / ".claude",
                home / "Library" / "Application Support" / "Claude",
            ]
            
            config_dir = None
            for dir_path in possible_dirs:
                if dir_path.exists():
                    config_dir = dir_path
                    break
            
            if not config_dir:
                print("❌ Could not find Claude configuration directory")
                print("💡 Please specify with --claude-config-dir")
                return 1
        
        # Ensure MCP config file exists
        mcp_config_file = config_dir / "mcp.json"
        
        if mcp_config_file.exists():
            print(f"📄 Found existing MCP config: {mcp_config_file}")
            with open(mcp_config_file, 'r') as f:
                mcp_config = json.load(f)
        else:
            print(f"📝 Creating new MCP config: {mcp_config_file}")
            mcp_config = {"servers": {}}
        
        # Get project and toolkit paths
        project_root = Path.cwd().resolve()
        toolkit_path = Path(__file__).parent.parent.resolve()
        
        # Create server configuration
        server_config = {
            "command": "python3",
            "args": [
                str(toolkit_path / "src" / "integrations" / "mcp_server_enhanced.py"),
                "--project-root", str(project_root)
            ],
            "env": {
                "PYTHONPATH": str(toolkit_path / "src")
            }
        }
        
        # Add to MCP config
        project_name = project_root.name
        server_key = f"claude-rag-{project_name}"
        
        mcp_config["servers"][server_key] = server_config
        
        # Save config
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(mcp_config_file, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        
        print(f"✅ MCP server configured: {server_key}")
        print(f"📁 Project root: {project_root}")
        print(f"🔧 Toolkit path: {toolkit_path}")
        print()
        print("📋 Configuration added to:", mcp_config_file)
        print()
        print("🚀 Next steps:")
        print("1. Restart Claude Code to load the new configuration")
        print("2. The RAG tools will be available in your conversation")
        print()
        print("💡 Available tools:")
        print("  - search_documentation: Search project knowledge base")
        print("  - troubleshoot_error: Find error solutions")
        print("  - get_file_context: Get file relationships")
        print("  - get_related_commands: Find technology commands")
        print("  - get_project_stats: View index statistics")
        print("  - reindex_project: Update documentation index")
        
        return 0
    
    def _get_engine(self) -> Optional[MultiRepoRAGEngine]:
        """Get initialized RAG engine."""
        try:
            return MultiRepoRAGEngine('.')
        except Exception as e:
            print(f"❌ RAG system not initialized: {e}")
            print("💡 Run 'claude-rag init' to initialize")
            return None
    
    def _cmd_session(self, args) -> int:
        """Handle session management commands."""
        session_manager = SessionManager('.')
        
        if not args.session_command:
            print("❌ Session command required")
            print("💡 Use 'claude-rag session --help' for available commands")
            return 1
        
        if args.session_command == 'start':
            return self._session_start(session_manager, args)
        elif args.session_command == 'update':
            return self._session_update(session_manager, args)
        elif args.session_command == 'end':
            return self._session_end(session_manager, args)
        elif args.session_command == 'pause':
            return self._session_pause(session_manager, args)
        elif args.session_command == 'resume':
            return self._session_resume(session_manager, args)
        elif args.session_command == 'list':
            return self._session_list(session_manager, args)
        elif args.session_command == 'show':
            return self._session_show(session_manager, args)
        elif args.session_command == 'current':
            return self._session_current(session_manager, args)
        elif args.session_command == 'report':
            return self._session_report(session_manager, args)
        else:
            print(f"❌ Unknown session command: {args.session_command}")
            return 1
    
    def _session_start(self, session_manager: SessionManager, args) -> int:
        """Start a new development session."""
        try:
            session = session_manager.start_session(
                name=args.name,
                description=args.description or "",
                objectives=args.objectives or []
            )
            
            print(f"🚀 Started session: {session.name}")
            print(f"📅 Session ID: {session.session_id}")
            print(f"🌿 Git branch: {session.initial_branch}")
            print(f"📝 Initial commit: {session.initial_commit[:8]}")
            
            if session.objectives:
                print(f"🎯 Objectives:")
                for i, obj in enumerate(session.objectives, 1):
                    print(f"  {i}. {obj}")
            
            print("\n💡 Use 'claude-rag session update \"progress notes\"' to log progress")
            return 0
            
        except Exception as e:
            print(f"❌ Failed to start session: {e}")
            return 1
    
    def _session_update(self, session_manager: SessionManager, args) -> int:
        """Update current session with progress."""
        if not session_manager.update_session(
            notes=args.notes,
            blocker=args.blocker,
            decision=args.decision
        ):
            print("❌ No active session found")
            print("💡 Start a session with 'claude-rag session start <name>'")
            return 1
        
        print(f"✅ Session updated: {args.notes}")
        
        if args.blocker:
            print(f"🚫 Blocker recorded: {args.blocker}")
        
        if args.decision:
            print(f"🎯 Decision recorded: {args.decision}")
        
        return 0
    
    def _session_end(self, session_manager: SessionManager, args) -> int:
        """End the current session."""
        session = session_manager.end_session(summary=args.summary or "")
        
        if not session:
            print("❌ No active session found")
            return 1
        
        print(f"🏁 Session ended: {session.name}")
        print(f"⏱️  Duration: {session.start_time} → {session.end_time}")
        
        if session.lines_added or session.lines_removed:
            print(f"📊 Code changes: +{session.lines_added} -{session.lines_removed} lines")
        
        if args.summary:
            print(f"📋 Summary: {args.summary}")
        
        print(f"\n📄 Session report available: claude-rag session report {session.session_id}")
        return 0
    
    def _session_pause(self, session_manager: SessionManager, args) -> int:
        """Pause the current session."""
        if not session_manager.pause_session(reason=args.reason or ""):
            print("❌ No active session found")
            return 1
        
        print("⏸️  Session paused")
        if args.reason:
            print(f"📝 Reason: {args.reason}")
        
        return 0
    
    def _session_resume(self, session_manager: SessionManager, args) -> int:
        """Resume a paused session."""
        if not session_manager.resume_session(args.session_id):
            print(f"❌ Failed to resume session: {args.session_id}")
            print("💡 Use 'claude-rag session list --status paused' to see paused sessions")
            return 1
        
        session = session_manager.get_current_session()
        print(f"▶️  Resumed session: {session.name}")
        print(f"📅 Session ID: {session.session_id}")
        
        return 0
    
    def _session_list(self, session_manager: SessionManager, args) -> int:
        """List all sessions."""
        sessions = session_manager.list_sessions()
        
        # Filter by status if requested
        if args.status:
            sessions = [s for s in sessions if s.get('status') == args.status]
        
        if not sessions:
            status_msg = f" with status '{args.status}'" if args.status else ""
            print(f"📭 No sessions found{status_msg}")
            return 0
        
        print(f"📋 Sessions ({len(sessions)}):")
        print("=" * 60)
        
        # Group by status
        status_order = ['active', 'paused', 'completed', 'cancelled']
        status_icons = {
            'active': '🟢',
            'paused': '🟡', 
            'completed': '✅',
            'cancelled': '❌'
        }
        
        for status in status_order:
            status_sessions = [s for s in sessions if s.get('status') == status]
            if not status_sessions:
                continue
                
            icon = status_icons.get(status, '❓')
            print(f"\n{icon} {status.title()} ({len(status_sessions)}):")
            
            for session in status_sessions:
                session_id = session['session_id'][:8]
                name = session['name']
                start_time = session['start_time'][:19].replace('T', ' ')
                print(f"  • {session_id} - {name} ({start_time})")
        
        return 0
    
    def _session_show(self, session_manager: SessionManager, args) -> int:
        """Show detailed session information."""
        session = session_manager.get_session_details(args.session_id)
        
        if not session:
            print(f"❌ Session not found: {args.session_id}")
            return 1
        
        print(f"📄 Session: {session.name}")
        print("=" * 60)
        print(f"ID: {session.session_id}")
        print(f"Status: {session.status}")
        print(f"Started: {session.start_time}")
        
        if session.end_time:
            print(f"Ended: {session.end_time}")
        
        if session.description:
            print(f"Description: {session.description}")
        
        if session.objectives:
            print(f"\nObjectives:")
            for i, obj in enumerate(session.objectives, 1):
                print(f"  {i}. {obj}")
        
        print(f"\nGit Info:")
        print(f"  Branch: {session.initial_branch}")
        print(f"  Initial: {session.initial_commit[:8]}")
        if session.final_commit:
            print(f"  Final: {session.final_commit[:8]}")
        
        if session.lines_added or session.lines_removed:
            print(f"  Changes: +{session.lines_added} -{session.lines_removed} lines")
        
        if session.progress_log:
            print(f"\nProgress ({len(session.progress_log)} entries):")
            for entry in session.progress_log[-5:]:  # Show last 5 entries
                timestamp = entry['timestamp'][:19].replace('T', ' ')
                print(f"  • {timestamp}: {entry['notes']}")
        
        if session.blockers:
            open_blockers = [b for b in session.blockers if b.get('status') == 'open']
            if open_blockers:
                print(f"\nOpen Blockers ({len(open_blockers)}):")
                for blocker in open_blockers:
                    timestamp = blocker['timestamp'][:19].replace('T', ' ')
                    print(f"  🚫 {timestamp}: {blocker['description']}")
        
        return 0
    
    def _session_current(self, session_manager: SessionManager, args) -> int:
        """Show current session status."""
        session = session_manager.get_current_session()
        
        if not session:
            print("📭 No active session")
            print("💡 Start a session with 'claude-rag session start <name>'")
            return 0
        
        print(f"🟢 Current Session: {session.name}")
        print(f"📅 ID: {session.session_id}")
        print(f"⏱️  Started: {session.start_time}")
        print(f"🌿 Branch: {session.initial_branch}")
        
        if session.progress_log:
            latest = session.progress_log[-1]
            latest_time = latest['timestamp'][:19].replace('T', ' ')
            print(f"📝 Latest: {latest_time} - {latest['notes']}")
        
        # Show any open blockers
        open_blockers = [b for b in session.blockers if b.get('status') == 'open']
        if open_blockers:
            print(f"🚫 Open blockers: {len(open_blockers)}")
        
        return 0
    
    def _session_report(self, session_manager: SessionManager, args) -> int:
        """Generate a detailed session report."""
        report = session_manager.generate_session_report(args.session_id)
        
        if report == "Session not found.":
            print(f"❌ Session not found: {args.session_id}")
            return 1
        
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(report)
                print(f"📄 Report saved to: {args.output}")
            except Exception as e:
                print(f"❌ Failed to save report: {e}")
                return 1
        else:
            print(report)
        
        return 0


def main():
    """Main entry point."""
    cli = RAGToolkitCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())