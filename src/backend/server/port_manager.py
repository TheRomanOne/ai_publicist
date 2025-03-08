import os
import signal
import subprocess
from typing import List

def find_process_ids_by_port(port: int) -> List[int]:
    """Find all process IDs using the specified port."""
    try:
        cmd = f"lsof -ti tcp:{port}"
        output = subprocess.check_output(cmd, shell=True)
        return [int(pid) for pid in output.decode().split('\n') if pid]
    except subprocess.CalledProcessError:
        return []

def kill_processes_by_port(port: int) -> None:
    """Kill all processes using the specified port."""
    pids = find_process_ids_by_port(port)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
            print(f"Killed process {pid} using port {port}")
        except ProcessLookupError:
            continue
    
    if find_process_ids_by_port(port):
        raise RuntimeError(f"Failed to free port {port}")
    else:
        print(f"Port {port} is now free") 