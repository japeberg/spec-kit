#!/usr/bin/env python3
"""
Prolog MCP Server for opencode

This server exposes Prolog-based validation and test generation tools
through the Model Context Protocol (MCP) for use with opencode.

Tools provided:
- prolog.validate_spec: Validate domain constraints using Prolog rules
- prolog.generate_test_cases: Generate test cases based on Prolog scenarios
- prolog.query: Execute arbitrary Prolog queries (advanced)

Prerequisites:
- SWI-Prolog must be installed and available in PATH
- Install: apt-get install swi-prolog (Linux) or brew install swi-prolog (macOS)
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from typing import Any, Dict, Optional, List


def read_message() -> Dict[str, Any]:
    """Read a JSON-RPC message from stdin."""
    line = sys.stdin.readline()
    if not line:
        raise EOFError
    return json.loads(line)


def write_message(msg: Dict[str, Any]) -> None:
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def get_prolog_dir() -> Path:
    """Get the directory containing Prolog files."""
    # Server is in .opencode/mcp-prolog/, Prolog files are in prolog/ subdirectory
    server_dir = Path(__file__).parent
    return server_dir / "prolog"


def run_prolog(goal: str, prolog_files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Run a Prolog goal and return JSON output.
    
    Args:
        goal: Prolog goal to execute
        prolog_files: List of Prolog files to load (relative to prolog_dir)
    
    Returns:
        JSON output from Prolog or error information
    """
    prolog_dir = get_prolog_dir()
    
    # Build command - use -q for quiet mode
    cmd = ["swipl", "-q"]
    
    # Add file arguments
    if prolog_files:
        for pfile in prolog_files:
            file_path = prolog_dir / pfile
            if not file_path.exists():
                raise FileNotFoundError(f"Prolog file not found: {file_path}")
            cmd.extend(["-s", str(file_path)])
    
    # Add goal and halt on success
    cmd.extend(["-g", goal, "-t", "halt"])
    
    # Execute
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(prolog_dir),
            timeout=30,  # 30 second timeout
        )
        
        # Check if there was an error (non-zero exit that's not just Prolog failure)
        if proc.returncode != 0 and proc.stderr:
            error_msg = proc.stderr.strip()
            if error_msg:
                return {
                    "error": error_msg,
                    "returncode": proc.returncode
                }
        
        # Parse JSON output from stdout
        output_lines = proc.stdout.strip().splitlines()
        if not output_lines:
            return {"error": "No output from Prolog", "stderr": proc.stderr.strip()}
        
        # Try to parse the last line as JSON
        try:
            result = json.loads(output_lines[-1])
            return result
        except json.JSONDecodeError as e:
            # If we have multiple lines, try to parse all as a single JSON
            try:
                full_output = proc.stdout.strip()
                result = json.loads(full_output)
                return result
            except json.JSONDecodeError:
                return {
                    "error": f"Failed to parse Prolog output as JSON: {e}",
                    "raw_output": output_lines[-1] if output_lines else "",
                    "full_stdout": proc.stdout.strip()[:500]  # First 500 chars
                }
            
    except subprocess.TimeoutExpired:
        return {"error": "Prolog execution timed out (30s)"}
    except FileNotFoundError:
        return {
            "error": "SWI-Prolog not found. Please install: apt-get install swi-prolog (Linux) or brew install swi-prolog (macOS)"
        }
    except Exception as e:
        return {"error": f"Unexpected error running Prolog: {e}"}


def list_tools() -> Dict[str, Any]:
    """Return the list of available MCP tools."""
    return {
        "tools": [
            {
                "name": "prolog.validate_spec",
                "description": "Validate domain constraints using Prolog rules. Checks invariants defined in constraints.pl against the domain model.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "feature_dir": {
                            "type": "string",
                            "description": "Feature/spec directory for context (optional, not currently used)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "prolog.generate_test_cases",
                "description": "Generate test cases based on Prolog scenarios. Creates valid and invalid test vectors for the specified domain.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Domain area for which to generate test cases",
                            "enum": ["users"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of test cases to generate (optional)",
                            "default": 10
                        }
                    },
                    "required": ["domain"]
                }
            },
            {
                "name": "prolog.query",
                "description": "Execute an arbitrary Prolog query (advanced use only). Returns bindings or success/failure.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Prolog query string to execute (e.g., 'user(1, admin)')"
                        }
                    },
                    "required": ["query"]
                }
            }
        ]
    }


def handle_tool_call(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle a tool call and return the result."""
    
    if name == "prolog.validate_spec":
        # Run constraint validation
        result = run_prolog(
            "check_constraints_json",
            prolog_files=["queries.pl"]
        )
        return result
    
    elif name == "prolog.generate_test_cases":
        domain = args.get("domain")
        
        if domain == "users":
            result = run_prolog(
                "generate_user_cases",
                prolog_files=["queries.pl"]
            )
            return result
        else:
            return {"error": f"Unsupported domain: {domain}"}
    
    elif name == "prolog.query":
        query = args.get("query")
        if not query:
            return {"error": "Query parameter is required"}
        
        # Use execute_query predicate from queries.pl
        # Escape the query string for Prolog
        escaped_query = query.replace("'", "\\'")
        goal = f"execute_query('{escaped_query}')"
        
        result = run_prolog(
            goal,
            prolog_files=["queries.pl"]
        )
        return result
    
    else:
        return {"error": f"Unknown tool: {name}"}


def main():
    """Main MCP server loop."""
    # Check if SWI-Prolog is available
    try:
        subprocess.run(
            ["swipl", "--version"],
            capture_output=True,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        write_message({
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": "SWI-Prolog not found. Please install it to use this MCP server."
            }
        })
        sys.exit(1)
    
    # Main message loop
    while True:
        try:
            msg = read_message()
        except EOFError:
            break
        except json.JSONDecodeError as e:
            write_message({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                }
            })
            continue
        
        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})
        
        try:
            if method == "tools/list":
                result = list_tools()
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                
                if not tool_name:
                    raise ValueError("Tool name is required")
                
                tool_result = handle_tool_call(tool_name, tool_args)
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(tool_result, indent=2)
                            }
                        ]
                    }
                }
            
            elif method == "initialize":
                # Handle MCP initialization
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "prolog-spec-server",
                            "version": "0.1.0"
                        }
                    }
                }
            
            else:
                raise ValueError(f"Unknown method: {method}")
            
        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
        
        write_message(response)


if __name__ == "__main__":
    main()
