import os
import sys
import logging
import time
from colorama import init, Fore, Style, Back
from rag_system.rag_system import RAGSystem
from server.config_manager import ConfigManager
from collections import Counter, defaultdict
import re

# Initialize colorama for colored terminal output
init()

# Setup prettier logging with minimal timestamp
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s{Style.RESET_ALL} %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_info(msg):
    """Print a nicely formatted info message"""
    logger.info(f"{Fore.GREEN}→{Style.RESET_ALL} {msg}")

def log_warn(msg):
    """Print a nicely formatted warning message"""
    logger.warning(f"{Fore.YELLOW}⚠{Style.RESET_ALL} {msg}")

def log_success(msg):
    """Print a nicely formatted success message"""
    logger.info(f"{Fore.GREEN}✓{Style.RESET_ALL} {msg}")

def log_step(step, msg):
    """Print a nicely formatted step message"""
    logger.info(f"{Fore.BLUE}[{step}]{Style.RESET_ALL} {msg}")

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_terminal_width():
    """Get terminal width or use default of 80 columns"""
    try:
        return os.get_terminal_size().columns
    except:
        return 80

def count_tokens(text):
    """Approximate token count by counting words"""
    return len(re.findall(r'\S+', text))

def extract_project_name(file_path):
    """Extract project name from file path"""
    # Remove common prefixes
    path = file_path.replace('\\', '/')
    
    # Skip src/ or backend/ prefix if present
    parts = path.split('/')
    if len(parts) > 1:
        if parts[0] in ('src', 'backend', 'frontend'):
            return parts[1]
        return parts[0]
    return 'unknown'

def collect_statistics(chunks, metadata):
    """Collect comprehensive statistics about the RAG database"""
    stats = {
        'total_chunks': len(chunks),
        'total_tokens': 0,
        'by_project': defaultdict(lambda: {
            'chunks': 0,
            'tokens': 0,
            'files': set()
        }),
        'by_file': defaultdict(lambda: {
            'chunks': 0,
            'tokens': 0,
            'project': '',
            'lines': 0
        }),
        'file_extensions': Counter(),
        'line_stats': {
            'min': float('inf'),
            'max': 0,
            'avg': 0,
            'total': 0
        }
    }
    
    # Collect raw statistics
    for chunk, meta in zip(chunks, metadata):
        file_path = meta['file_path']
        project = extract_project_name(file_path)
        tokens = count_tokens(chunk)
        lines = len(chunk.split('\n'))
        
        # Update project stats
        stats['by_project'][project]['chunks'] += 1
        stats['by_project'][project]['tokens'] += tokens
        stats['by_project'][project]['files'].add(file_path)
        
        # Update file stats
        stats['by_file'][file_path]['chunks'] += 1
        stats['by_file'][file_path]['tokens'] += tokens
        stats['by_file'][file_path]['project'] = project
        stats['by_file'][file_path]['lines'] = max(
            stats['by_file'][file_path]['lines'],
            meta['end_line']
        )
        
        # Update total tokens
        stats['total_tokens'] += tokens
        
        # Update line stats
        line_count = meta['end_line'] - meta['start_line'] + 1
        stats['line_stats']['min'] = min(stats['line_stats']['min'], line_count)
        stats['line_stats']['max'] = max(stats['line_stats']['max'], line_count)
        stats['line_stats']['total'] += line_count
        
        # Update file extension stats
        ext = os.path.splitext(file_path)[1]
        if ext:
            stats['file_extensions'][ext] += 1
        else:
            stats['file_extensions']['no_extension'] += 1
    
    # Calculate average lines per chunk
    if stats['total_chunks'] > 0:
        stats['line_stats']['avg'] = stats['line_stats']['total'] / stats['total_chunks']
    
    # Replace defaultdicts with regular dicts for easier handling
    stats['by_project'] = dict(stats['by_project'])
    stats['by_file'] = dict(stats['by_file'])
    
    # Convert file sets to counts in project stats
    for project in stats['by_project']:
        stats['by_project'][project]['file_count'] = len(stats['by_project'][project]['files'])
        stats['by_project'][project]['files'] = list(stats['by_project'][project]['files'])
    
    return stats

def print_summary(chunk, width=70):
    """Print a summary of the chunk with proper formatting"""
    # Get first paragraph or line for summary
    first_paragraph = chunk.split('\n\n')[0] if '\n\n' in chunk else chunk.split('\n')[0]
    
    # Truncate if too long
    if len(first_paragraph) > width - 12:
        first_paragraph = first_paragraph[:width-15] + "..."
    
    print(f"{Fore.WHITE}{Back.GREEN} SUMMARY {Style.RESET_ALL} {first_paragraph}")

def print_file_list(file_stats, current_page=0, items_per_page=20):
    """Print a list of files with chunk counts"""
    total_files = len(file_stats)
    total_pages = max(1, (total_files + items_per_page - 1) // items_per_page)
    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_files)
    
    # Print header
    print(f"{Fore.CYAN}╔{'═' * 68}╗{Style.RESET_ALL}")
    header = f"FILE LIST (Page {current_page + 1}/{total_pages})"
    padding = (68 - len(header)) // 2
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.WHITE}{Back.BLUE}{header}{Style.RESET_ALL}{Fore.CYAN}{' ' * (68 - padding - len(header))}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
    
    # Print file list items
    for i in range(start_idx, end_idx):
        file_path, count = file_stats[i]
        # Truncate file path if too long
        display_path = file_path
        if len(display_path) > 55:
            display_path = "..." + display_path[-52:]
        
        # Format: [count] path
        line = f" [{count:3d}] {display_path}"
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {line}{' ' * (67 - len(line))}{Fore.CYAN}║{Style.RESET_ALL}")
    
    # Fill empty rows if needed
    for _ in range(items_per_page - (end_idx - start_idx)):
        print(f"{Fore.CYAN}║{' ' * 68}║{Style.RESET_ALL}")
    
    # Print footer with navigation help
    print(f"{Fore.CYAN}╠{'═' * 68}╣{Style.RESET_ALL}")
    nav_help = "[ PAGE UP (<) | PAGE DOWN (>) | BACK (b) | STATS (t) ]"
    padding = (68 - len(nav_help)) // 2
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.YELLOW}{nav_help}{Style.RESET_ALL}{Fore.CYAN}{' ' * (68 - padding - len(nav_help))}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚{'═' * 68}╝{Style.RESET_ALL}")

def print_stats(stats, view="overview", width=70):
    """Print statistics about the RAG database"""
    # Ensure width is at least 70
    width = max(70, width)
    
    # Print header
    print(f"{Fore.CYAN}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    header = f"DATABASE STATISTICS - {view.upper()}"
    padding = (width - 2 - len(header)) // 2
    right_padding = width - 2 - padding - len(header)
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.WHITE}{Back.BLUE}{header}{Style.RESET_ALL}{Fore.CYAN}{' ' * right_padding}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╠{'═' * (width - 2)}╣{Style.RESET_ALL}")
    
    if view == "overview":
        # Print overview statistics
        overview_items = [
            ("Total chunks", f"{stats['total_chunks']} chunks"),
            ("Total tokens", f"{stats['total_tokens']:,} tokens"),
            ("Total projects", f"{len(stats['by_project'])} projects"),
            ("Total files", f"{len(stats['by_file'])} files"),
            ("Lines per chunk", f"{stats['line_stats']['avg']:.1f} avg ({stats['line_stats']['min']} min, {stats['line_stats']['max']} max)"),
            ("File extensions", ', '.join(f"{ext[1:]}({count})" for ext, count in stats['file_extensions'].most_common(5)))
        ]
        
        for label, value in overview_items:
            line = f" {Fore.YELLOW}{label}:{Style.RESET_ALL} {value}"
            print(f"{Fore.CYAN}║{Style.RESET_ALL}{line}{' ' * (width - 1 - len(label) - len(value))}║")
        
        print(f"{Fore.CYAN}╠{'═' * (width - 2)}╣{Style.RESET_ALL}")
        
        # Project statistics header
        print(f"{Fore.CYAN}║{Fore.YELLOW} PROJECT STATISTICS{' ' * (width - 21)}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{' ' * (width - 2)}║{Style.RESET_ALL}")
        
        # Sort projects by chunk count
        sorted_projects = sorted(stats['by_project'].items(), key=lambda x: x[1]['chunks'], reverse=True)
        
        # Print top projects
        for project, project_stats in sorted_projects[:5]:
            line = f" {Fore.GREEN}{project}{Style.RESET_ALL}: {project_stats['chunks']} chunks, {project_stats['file_count']} files, {project_stats['tokens']:,} tokens"
            if len(line) > width - 5:
                line = line[:width-8] + "..."
            print(f"{Fore.CYAN}║{Style.RESET_ALL}{line}{' ' * max(0, width - 2 - len(line))}║")
    
    elif view == "projects":
        # Print detailed project statistics
        sorted_projects = sorted(stats['by_project'].items(), key=lambda x: x[1]['chunks'], reverse=True)
        
        for project, project_stats in sorted_projects:
            project_line = f" {Fore.GREEN}{project}{Style.RESET_ALL}"
            print(f"{Fore.CYAN}║{Style.RESET_ALL}{project_line}{' ' * (width - 2 - len(project))}║")
            
            stats_line = f"   {project_stats['chunks']} chunks, {project_stats['file_count']} files, {project_stats['tokens']:,} tokens"
            print(f"{Fore.CYAN}║{Style.RESET_ALL}{stats_line}{' ' * (width - 2 - len(stats_line))}║")
            
            # Add a separator line
            print(f"{Fore.CYAN}║{' ' * (width - 2)}║{Style.RESET_ALL}")
    
    elif view == "files":
        # Print top files by chunk count
        sorted_files = sorted(stats['by_file'].items(), key=lambda x: x[1]['chunks'], reverse=True)
        
        for i, (file_path, file_stats) in enumerate(sorted_files[:15]):
            # Truncate file path if too long
            display_path = file_path
            if len(display_path) > width - 25:
                display_path = "..." + display_path[-(width-28):]
            
            # Print file info
            path_line = f" {i+1}. {Fore.YELLOW}{display_path}{Style.RESET_ALL}"
            print(f"{Fore.CYAN}║{Style.RESET_ALL}{path_line}{' ' * max(0, width - 2 - len(display_path) - 5)}║")
            
            stats_line = f"    Project: {file_stats['project']}, Chunks: {file_stats['chunks']}, Lines: {file_stats['lines']}, Tokens: {file_stats['tokens']:,}"
            if len(stats_line) > width - 5:
                stats_line = stats_line[:width-8] + "..."
            print(f"{Fore.CYAN}║{Style.RESET_ALL}{stats_line}{' ' * max(0, width - 2 - len(stats_line))}║")
            
            # Add a separator line
            print(f"{Fore.CYAN}║{' ' * (width - 2)}║{Style.RESET_ALL}")
    
    # Print footer with navigation help
    print(f"{Fore.CYAN}╠{'═' * (width - 2)}╣{Style.RESET_ALL}")
    nav_help = "[ OVERVIEW (o) | PROJECTS (p) | FILES (f) | BACK (b) ]"
    padding = (width - 2 - len(nav_help)) // 2
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.YELLOW}{nav_help}{Style.RESET_ALL}{Fore.CYAN}{' ' * max(0, width - 2 - padding - len(nav_help))}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

def print_chunk_info(idx, total, metadata, width=70):
    """Print chunk metadata in a nice header"""
    # Ensure width is at least 70
    width = max(70, width)
    
    # Chunk number and navigation
    nav_text = f"CHUNK {idx + 1} OF {total}"
    print(f"{Fore.CYAN}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    
    # Center the navigation text
    padding = (width - 2 - len(nav_text)) // 2
    right_padding = width - 2 - padding - len(nav_text)
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.WHITE}{Back.BLUE}{nav_text}{Style.RESET_ALL}{Fore.CYAN}{' ' * right_padding}║{Style.RESET_ALL}")
    
    # File path
    file_path = metadata['file_path']
    if len(file_path) > width - 10:
        file_path = "..." + file_path[-(width-13):]
    print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.YELLOW}File:{Style.RESET_ALL} {file_path}{' ' * max(0, width - 9 - len(file_path))}{Fore.CYAN}║{Style.RESET_ALL}")
    
    # Project
    project = extract_project_name(file_path)
    print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.YELLOW}Project:{Style.RESET_ALL} {project}{' ' * max(0, width - 12 - len(project))}{Fore.CYAN}║{Style.RESET_ALL}")
    
    # Function name (if available)
    if 'function_name' in metadata and metadata['function_name']:
        fn_name = metadata['function_name']
        if len(fn_name) > width - 14:
            fn_name = fn_name[:width-17] + "..."
        print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.YELLOW}Function:{Style.RESET_ALL} {fn_name}{' ' * max(0, width - 13 - len(fn_name))}{Fore.CYAN}║{Style.RESET_ALL}")
    
    # Line numbers
    line_text = f"{metadata['start_line']}-{metadata['end_line']} ({metadata['end_line'] - metadata['start_line'] + 1} lines)"
    print(f"{Fore.CYAN}║{Style.RESET_ALL} {Fore.YELLOW}Lines:{Style.RESET_ALL} {line_text}{' ' * max(0, width - 10 - len(line_text))}{Fore.CYAN}║{Style.RESET_ALL}")
    
    # Bottom border
    print(f"{Fore.CYAN}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

def print_chunk_content(chunk, width=70):
    """Print chunk content with syntax highlighting"""
    # Ensure width is at least 70
    width = max(70, width)
    content_width = width - 4  # Account for borders and spacing
    
    # Split the chunk by newlines to get individual lines
    lines = chunk.split('\n')
    
    # Print code with Python syntax highlighting simulation
    print(f"{Fore.GREEN}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    
    # Show up to 20 lines of the chunk
    display_lines = lines[:20]
    for line in display_lines:
        # Truncate line if too long
        display_line = line
        if len(display_line) > content_width:
            display_line = display_line[:content_width-3] + "..."
        
        # Basic syntax highlighting (very simplified)
        highlighted = display_line
        if display_line.strip().startswith(('def ', 'class ')):
            highlighted = f"{Fore.MAGENTA}{display_line}{Style.RESET_ALL}"
        elif "import " in display_line or "from " in display_line:
            highlighted = f"{Fore.GREEN}{display_line}{Style.RESET_ALL}"
        elif "#" in display_line:
            comment_idx = display_line.index('#')
            highlighted = f"{display_line[:comment_idx]}{Fore.CYAN}{display_line[comment_idx:]}{Style.RESET_ALL}"
        elif "=" in display_line:
            highlighted = f"{Fore.YELLOW}{display_line}{Style.RESET_ALL}"
        elif any(kw in display_line for kw in ['return', 'if', 'else', 'elif', 'for', 'while', 'try', 'except']):
            highlighted = f"{Fore.RED}{display_line}{Style.RESET_ALL}"
            
        # Print line with proper padding
        padding = max(0, content_width - len(display_line))
        print(f"{Fore.GREEN}│{Style.RESET_ALL} {highlighted}{' ' * padding} {Fore.GREEN}│{Style.RESET_ALL}")
    
    # Show ellipsis if chunk is longer than visible area
    if len(lines) > 20:
        ellipsis = f"... ({len(lines) - 20} more lines)"
        print(f"{Fore.GREEN}│{Style.RESET_ALL} {Fore.YELLOW}{ellipsis}{Style.RESET_ALL}{' ' * (content_width - len(ellipsis))} {Fore.GREEN}│{Style.RESET_ALL}")
    
    # Fill empty space if chunk is shorter than 20 lines
    for _ in range(20 - min(20, len(lines))):
        print(f"{Fore.GREEN}│{' ' * (width - 2)}│{Style.RESET_ALL}")
    
    # Bottom border
    print(f"{Fore.GREEN}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

def print_navigation_bar(width=70):
    """Print the navigation bar at the bottom"""
    # Ensure width is at least 70
    width = max(70, width)
    
    nav_text = "[ ← PREV (p) | NEXT (n) → | QUIT (q) | SEARCH (s) | VIEW FILES (v) | STATS (t) ]"
    
    print(f"{Fore.CYAN}╔{'═' * (width - 2)}╗{Style.RESET_ALL}")
    
    # Center the navigation text
    padding = (width - 2 - len(nav_text)) // 2
    right_padding = width - 2 - padding - len(nav_text)
    print(f"{Fore.CYAN}║{' ' * padding}{Fore.WHITE}{Back.BLUE}{nav_text}{Style.RESET_ALL}{Fore.CYAN}{' ' * right_padding}║{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}╚{'═' * (width - 2)}╝{Style.RESET_ALL}")

def search_chunks(chunks, metadata, search_term):
    """Search for a term in all chunks and return matching indices"""
    results = []
    for idx, (chunk, meta) in enumerate(zip(chunks, metadata)):
        # Search in code and metadata
        if (search_term.lower() in chunk.lower() or 
            search_term.lower() in meta.get('file_path', '').lower() or
            search_term.lower() in meta.get('function_name', '').lower()):
            results.append(idx)
    return results

def get_file_statistics(metadata):
    """Get file statistics from metadata"""
    # Count chunks per file
    file_counter = Counter(meta['file_path'] for meta in metadata)
    
    # Convert to sorted list of (file_path, count) tuples
    file_stats = sorted(file_counter.items(), key=lambda x: x[1], reverse=True)
    return file_stats

def visualize_rag_system(config_path=None):
    """Visualize the RAG system's database with an interactive UI."""
    # Load configuration
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(parent_dir))
    config_manager = ConfigManager(project_root)
    config = config_manager.get_config()

    # Initialize RAG system
    rag_system = RAGSystem(
        code_directories=config["rag"]["code_directories"],
        embeddings_cache=config["rag"]["embeddings_cache"],
        chunk_size=config["backend"]["chunk_size"]
    )

    # Welcome message
    clear_screen()
    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'📊 RAG System Database Visualization 📊':^70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    # Check if there are any chunks
    chunks_count = len(rag_system.code_chunks)
    if chunks_count == 0:
        log_warn("No code chunks found in the database.")
        return

    log_info(f"Found {chunks_count} code chunks in the database.")
    print("Loading interactive viewer...\n")
    time.sleep(1)  # Brief pause for effect
    
    # Get file statistics
    file_stats = get_file_statistics(rag_system.code_metadata)
    
    # Collect comprehensive statistics
    log_info("Collecting database statistics...")
    db_stats = collect_statistics(rag_system.code_chunks, rag_system.code_metadata)
    log_success(f"Statistics collected for {len(db_stats['by_file'])} files across {len(db_stats['by_project'])} projects.")

    # Interactive navigation
    current_idx = 0
    search_results = []
    search_index = -1
    file_list_page = 0
    items_per_page = 20
    view_mode = "chunks"  # Can be "chunks", "files", or "stats"
    stats_view = "overview"  # Can be "overview", "projects", or "files"
    
    while True:
        clear_screen()
        terminal_width = get_terminal_width()
        display_width = min(terminal_width, 100)
        
        if view_mode == "chunks":
            # Get current chunk and metadata
            current_chunk = rag_system.code_chunks[current_idx]
            current_metadata = rag_system.code_metadata[current_idx]
            
            # Print the first line of the chunk as a summary
            print_summary(current_chunk, width=display_width)
            
            # Print chunk info, content, and navigation bar
            print_chunk_info(current_idx, chunks_count, current_metadata, width=display_width)
            print_chunk_content(current_chunk, width=display_width)
            print_navigation_bar(width=display_width)
            
            # Get user input for navigation
            command = input(f"{Fore.YELLOW}Enter command:{Style.RESET_ALL} ").lower().strip()
            
            if command == 'q':
                # Quit
                break
            elif command == 'n' or command == '':
                # Next chunk
                current_idx = (current_idx + 1) % chunks_count
            elif command == 'p':
                # Previous chunk
                current_idx = (current_idx - 1) % chunks_count
            elif command == 's':
                # Search
                search_term = input(f"{Fore.YELLOW}Search term:{Style.RESET_ALL} ").strip()
                if search_term:
                    search_results = search_chunks(rag_system.code_chunks, rag_system.code_metadata, search_term)
                    if search_results:
                        search_index = 0
                        current_idx = search_results[search_index]
                        print(f"Found {len(search_results)} matches. Showing result 1/{len(search_results)}")
                        time.sleep(1)
                    else:
                        print(f"No matches found for '{search_term}'")
                        time.sleep(1)
            elif command == 'next' and search_results:
                # Next search result
                search_index = (search_index + 1) % len(search_results)
                current_idx = search_results[search_index]
                print(f"Showing result {search_index + 1}/{len(search_results)}")
                time.sleep(0.5)
            elif command == 'v':
                # Switch to file list view
                view_mode = "files"
                file_list_page = 0
            elif command == 't':
                # Switch to stats view
                view_mode = "stats"
                stats_view = "overview"
        
        elif view_mode == "files":
            # Display file list
            print_file_list(file_stats, file_list_page, items_per_page)
            
            # Get user input for navigation
            command = input(f"{Fore.YELLOW}Enter command:{Style.RESET_ALL} ").lower().strip()
            
            if command == 'q':
                # Quit
                break
            elif command == '<' or command == 'p':
                # Previous page
                file_list_page = (file_list_page - 1) % ((len(file_stats) + items_per_page - 1) // items_per_page)
            elif command == '>' or command == 'n' or command == '':
                # Next page
                file_list_page = (file_list_page + 1) % ((len(file_stats) + items_per_page - 1) // items_per_page)
            elif command == 'b' or command == 'v':
                # Back to chunk view
                view_mode = "chunks"
            elif command == 't':
                # Switch to stats view
                view_mode = "stats"
                stats_view = "overview"
            elif command.isdigit():
                # If user enters a number, try to find chunk with that index
                try:
                    idx = int(command)
                    if 1 <= idx <= chunks_count:
                        current_idx = idx - 1
                        view_mode = "chunks"
                    else:
                        print(f"Invalid chunk number. Range is 1-{chunks_count}")
                        time.sleep(1)
                except ValueError:
                    pass
        
        elif view_mode == "stats":
            # Display statistics
            print_stats(db_stats, stats_view, width=display_width)
            
            # Get user input for navigation
            command = input(f"{Fore.YELLOW}Enter command:{Style.RESET_ALL} ").lower().strip()
            
            if command == 'q':
                # Quit
                break
            elif command == 'o':
                # Overview stats
                stats_view = "overview"
            elif command == 'p':
                # Project stats
                stats_view = "projects"
            elif command == 'f':
                # File stats
                stats_view = "files"
            elif command == 'b':
                # Back to chunk view
                view_mode = "chunks"
            elif command == 'v':
                # Switch to file list view
                view_mode = "files"
                file_list_page = 0
    
    clear_screen()
    log_success("Visualization complete.")

if __name__ == "__main__":
    try:
        visualize_rag_system()
    except KeyboardInterrupt:
        clear_screen()
        print(f"{Fore.YELLOW}Visualization interrupted by user.{Style.RESET_ALL}")
        sys.exit(0) 