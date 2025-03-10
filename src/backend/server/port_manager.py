import os
import signal
import subprocess
import time
from typing import List, Tuple

def is_port_in_use(port: int) -> bool:
    """Check if the specified port is in use."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_ids_by_port(port: int) -> List[int]:
    """Find all process IDs using the specified port."""
    try:
        cmd = f"lsof -ti tcp:{port}"
        output = subprocess.check_output(cmd, shell=True)
        return [int(pid) for pid in output.decode().split('\n') if pid]
    except subprocess.CalledProcessError:
        return []

def kill_processes_by_port(port: int) -> bool:
    """Kill processes using the specified port one by one until the port is free.
    
    Returns:
        bool: True if port was successfully freed, False otherwise
    """
    # First check if the port is even in use
    if not is_port_in_use(port):
        print(f"Port {port} is already free")
        return True
    
    # Get all process IDs using this port
    pids = find_process_ids_by_port(port)
    if not pids:
        print(f"No processes found using port {port}, but port appears to be in use")
        return False
    
    print(f"Found {len(pids)} process(es) using port {port}: {pids}")
    
    # Try to kill processes one by one
    for pid in pids:
        try:
            # Get process name for better logging
            cmd = f"ps -p {pid} -o comm="
            process_name = subprocess.check_output(cmd, shell=True).decode().strip()
            
            print(f"Attempting to kill process {pid} ({process_name}) using port {port}")
            os.kill(pid, signal.SIGTERM)  # Try SIGTERM first (graceful)
            
            # Give the process a moment to terminate
            for _ in range(5):  # Wait up to 0.5 seconds
                time.sleep(0.1)
                if not is_port_in_use(port):
                    print(f"Successfully freed port {port} by terminating process {pid} ({process_name})")
                    return True
            
            # If SIGTERM didn't work, try SIGKILL
            print(f"Process {pid} didn't release port {port}, trying SIGKILL")
            os.kill(pid, signal.SIGKILL)
            
            # Check if port is now free
            for _ in range(5):  # Wait up to 0.5 seconds
                time.sleep(0.1)
                if not is_port_in_use(port):
                    print(f"Successfully freed port {port} by killing process {pid} ({process_name})")
                    return True
                
        except ProcessLookupError:
            print(f"Process {pid} no longer exists")
        except Exception as e:
            print(f"Error killing process {pid}: {e}")
    
    # Final check to see if port is free
    if not is_port_in_use(port):
        print(f"Port {port} is now free")
        return True
    else:
        print(f"Failed to free port {port} after killing all identified processes")
        return False 