#!/usr/bin/env python3
"""
CLI Interface for Claude RAG Toolkit
Provides command-line tools for managing multi-repository documentation indexing.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.rag_engine import MultiRepoRAGEngine
from utils.repo_detector import RepositoryDetector


class CLIInterface:
    """Command line interface for Claude RAG Toolkit."""
    
    def __init__(self):
        self.engine = None
        self.project_root = Path.cwd()
    
    def init_engine(self, project_root: str = ".") -> MultiRepoRAGEngine:
        """Initialize RAG engine for project."""
        if self.engine is None:
            self.engine = MultiRepoRAGEngine(project_root)
        return self.engine
    
    def cmd_init(self, args):
        """Initialize RAG system in current project."""
        print(f"🔧 Initializing Claude RAG in {self.project_root}")
        
        # Check if already initialized
        rag_dir = self.project_root / ".claude-rag"
        if rag_dir.exists() and not args.force:
            print("✅ RAG system already initialized")
            print("Use --force to reinitialize")
            return
        
        # Initialize engine (will auto-detect and create config)
        engine = self.init_engine(str(self.project_root))
        
        print("\n📊 Project Analysis:")
        detector = RepositoryDetector(str(self.project_root))
        analysis = detector.analyze_project()
        
        detection = analysis["detection"]
        stats = analysis["statistics"]
        
        print(f"  Repository Type: {detection['repo_type']} (confidence: {detection['confidence']:.2f})")
        print(f"  Total Files: {stats['total_files']}")
        print(f"  Project Size: {stats['project_size']['total_size_mb']} MB")
        
        # Index project
        print("\n🔍 Building initial index...")
        result = engine.index_project(force_reindex=True)
        
        print(f"\n✅ RAG system initialized successfully!")
        print(f"📄 Configuration: {rag_dir}/config.json")
        print(f"📊 Index: {rag_dir}/index.json")
        print("\n📝 Next steps:")
        print("  1. Run 'claude-rag search <query>' to test search")
        print("  2. Configure Claude Code MCP integration")
        print("  3. Add .claude-rag/ to your .gitignore (except config.json)")
    
    def cmd_search(self, args):
        """Search project documentation."""
        engine = self.init_engine()
        
        results = engine.search(args.query, args.limit)
        
        if not results:
            print(f"❌ No results found for: '{args.query}'")
            return
        
        print(f"🔍 Search results for: '{args.query}'")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 {result['file']} (score: {result['score']})")
            print(f"   Repository: {result['repo_type']}")
            for match in result['matches']:
                print(f"   • {match}")
    
    def cmd_reindex(self, args):
        """Rebuild project index."""
        engine = self.init_engine()
        
        print("🔄 Rebuilding project index...")
        result = engine.index_project(force_reindex=True)
        
        print(f"✅ Reindexed {result['indexed_files']} files")
    
    def cmd_stats(self, args):
        """Show project statistics."""
        engine = self.init_engine()
        
        if not engine.index_file.exists():
            print("❌ No index found. Run 'claude-rag init' first.")
            return
        
        stats = engine.index.get("project_stats", {})
        
        print("📊 Project Statistics:")
        print("=" * 40)
        print(f"Repository Type: {stats.get('repo_type', 'unknown')}")
        print(f"Documents: {stats.get('total_documents', 0)}")
        print(f"Commands: {stats.get('total_commands', 0)}")
        print(f"Concepts: {stats.get('total_concepts', 0)}")
        print(f"Knowledge Graph Nodes: {len(engine.index.get('knowledge_graph', {}))}")
        print(f"Last Updated: {stats.get('last_updated', 'unknown')}")
        
        # Show file type breakdown
        print("\n📁 File Type Breakdown:")
        file_types = {}
        for doc_path in engine.index.get("documents", {}):
            ext = Path(doc_path).suffix or "no_ext"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        for ext, count in sorted(file_types.items()):
            print(f"  {ext}: {count}")
    
    def cmd_commands(self, args):
        """List commands for a specific technology."""
        engine = self.init_engine()
        
        command_index = engine.index.get("command_index", {})
        
        if args.technology.lower() in command_index:
            commands = command_index[args.technology.lower()]
        else:
            # Search for technology in all commands
            commands = []
            for cmd_type, cmd_list in command_index.items():
                for cmd in cmd_list:
                    if args.technology.lower() in cmd["command"].lower():
                        commands.append(cmd)
        
        if not commands:
            print(f"❌ No commands found for: {args.technology}")
            return
        
        print(f"⚡ Commands for '{args.technology}':")
        print("=" * 60)
        
        for i, cmd in enumerate(commands[:args.limit], 1):
            print(f"\n{i}. [{cmd['file']}:{cmd['line']}]")
            print(f"   {cmd['command']}")
    
    def cmd_context(self, args):
        """Get context for a specific file."""
        engine = self.init_engine()
        
        if args.filepath not in engine.index.get("documents", {}):
            print(f"❌ File not indexed: {args.filepath}")
            return
        
        doc = engine.index["documents"][args.filepath]
        knowledge = doc.get("knowledge", {})
        
        print(f"📄 Context for: {args.filepath}")
        print("=" * 60)
        
        # Show concepts
        concepts = knowledge.get("concepts", [])
        if concepts:
            print("\n📚 Key Concepts:")
            for concept in concepts[:5]:
                print(f"   • {concept['name']} (line {concept['line']})")
        
        # Show commands
        commands = knowledge.get("commands", [])
        if commands:
            print(f"\n⚡ Commands ({len(commands)}):")
            for cmd in commands[:3]:
                print(f"   • {cmd['command'][:80]}...")
        
        # Show cross-references
        refs = knowledge.get("cross_references", [])
        if refs:
            print("\n🔗 References:")
            seen = set()
            for ref in refs:
                target = ref.get("target_file", "")
                if target and target not in seen:
                    seen.add(target)
                    print(f"   • {target}")
                    if len(seen) >= 5:
                        break
        
        # Show file stats
        print(f"\n📊 File Stats:")
        print(f"   Size: {doc.get('size', 0)} characters")
        print(f"   Lines: {doc.get('lines', 0)}")
        print(f"   Last indexed: {doc.get('last_indexed', 'unknown')}")
    
    def cmd_troubleshoot(self, args):
        """Find troubleshooting information for errors."""
        engine = self.init_engine()
        
        keyword_lower = args.error.lower()
        solutions = []
        
        for doc_path, doc_info in engine.index.get("documents", {}).items():
            knowledge = doc_info.get("knowledge", {})
            
            for trouble in knowledge.get("troubleshooting", []):
                if keyword_lower in trouble["content"].lower():
                    solutions.append({
                        "file": doc_path,
                        "content": trouble["content"],
                        "type": trouble["type"],
                        "line": trouble["line"]
                    })
        
        if not solutions:
            print(f"❌ No troubleshooting information found for: {args.error}")
            return
        
        print(f"🔧 Troubleshooting: '{args.error}'")
        print("=" * 60)
        
        # Group by type
        errors = [s for s in solutions if s["type"] == "error"]
        fixes = [s for s in solutions if s["type"] == "solution"]
        issues = [s for s in solutions if s["type"] == "issue"]
        
        if errors:
            print("\n❌ Known Errors:")
            for err in errors[:3]:
                print(f"   [{err['file']}:{err['line']}]")
                print(f"   {err['content'][:100]}...")
        
        if fixes:
            print("\n✅ Solutions:")
            for fix in fixes[:5]:
                print(f"   [{fix['file']}:{fix['line']}]")
                print(f"   {fix['content'][:100]}...")
        
        if issues:
            print("\n⚠️ Related Issues:")
            for issue in issues[:3]:
                print(f"   [{issue['file']}:{issue['line']}]")
                print(f"   {issue['content'][:100]}...")
    
    def cmd_analyze(self, args):
        """Analyze project and suggest optimizations."""
        detector = RepositoryDetector(str(self.project_root))
        analysis = detector.analyze_project()
        
        print("🔍 Project Analysis Report")
        print("=" * 50)
        
        detection = analysis["detection"]
        config = analysis["config"]
        stats = analysis["statistics"]
        
        print(f"\n📋 Repository Detection:")
        print(f"  Type: {detection['repo_type']}")
        print(f"  Confidence: {detection['confidence']:.2f}")
        
        print(f"\n📊 Statistics:")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Project size: {stats['project_size']['total_size_mb']} MB")
        
        print(f"\n⚙️ Configuration:")
        print(f"  File patterns: {len(config['file_patterns'])}")
        print(f"  Keywords: {len(config['keywords'])}")
        print(f"  Exclusions: {len(config['exclude_paths'])}")
        
        print(f"\n📁 File Type Distribution:")
        for pattern, count in stats['file_counts'].items():
            print(f"  {pattern}: {count}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if detection['confidence'] < 0.7:
            print("  • Low confidence detection - consider manual configuration")
        if stats['total_files'] > 1000:
            print("  • Large project - consider adding more exclusion patterns")
        if stats['project_size']['total_size_mb'] > 100:
            print("  • Large files detected - indexing may be slow")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Claude RAG Toolkit - Multi-repository documentation management"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize RAG system")
    init_parser.add_argument("--repo-type", help="Force repository type")
    init_parser.add_argument("--force", action="store_true", help="Reinitialize if exists")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search documentation")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-l", "--limit", type=int, default=10, help="Result limit")
    
    # Reindex command
    reindex_parser = subparsers.add_parser("reindex", help="Rebuild index")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    # Commands command
    commands_parser = subparsers.add_parser("commands", help="List technology commands")
    commands_parser.add_argument("technology", help="Technology (kubectl, docker, etc.)")
    commands_parser.add_argument("-l", "--limit", type=int, default=10, help="Result limit")
    
    # Context command
    context_parser = subparsers.add_parser("context", help="Get file context")
    context_parser.add_argument("filepath", help="File path")
    
    # Troubleshoot command
    trouble_parser = subparsers.add_parser("troubleshoot", help="Find error solutions")
    trouble_parser.add_argument("error", help="Error keyword")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze project")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = CLIInterface()
    
    # Route to appropriate command
    command_methods = {
        "init": cli.cmd_init,
        "search": cli.cmd_search,
        "reindex": cli.cmd_reindex,
        "stats": cli.cmd_stats,
        "commands": cli.cmd_commands,
        "context": cli.cmd_context,
        "troubleshoot": cli.cmd_troubleshoot,
        "analyze": cli.cmd_analyze
    }
    
    if args.command in command_methods:
        try:
            command_methods[args.command](args)
        except KeyboardInterrupt:
            print("\n❌ Interrupted by user")
        except Exception as e:
            print(f"❌ Error: {e}")
            if "--debug" in sys.argv:
                import traceback
                traceback.print_exc()
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()