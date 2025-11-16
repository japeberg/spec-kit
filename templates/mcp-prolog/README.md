# Prolog MCP Server for opencode

This directory contains a Model Context Protocol (MCP) server that integrates Prolog-based formal validation and test generation with opencode.

## Overview

The Prolog MCP server exposes three main tools to opencode:

1. **`prolog.validate_spec`** - Validate domain constraints using Prolog rules
2. **`prolog.generate_test_cases`** - Generate test cases based on Prolog scenarios
3. **`prolog.query`** - Execute arbitrary Prolog queries (advanced)

## Prerequisites

### SWI-Prolog

You must have SWI-Prolog installed and available in your PATH:

**Linux (Debian/Ubuntu):**

```bash
sudo apt-get update
sudo apt-get install swi-prolog
```

**macOS:**

```bash
brew install swi-prolog
```

**Windows:**

Download and install from: <https://www.swi-prolog.org/download/stable>

### Python 3

Python 3.7+ is required (usually already installed).

## Setup

### 1. Configure opencode MCP

The MCP configuration file (`mcp.json`) should be placed in your project's `.opencode/` directory or configured according to opencode's MCP documentation.

The default configuration in `mcp.json` looks like:

```json
{
  "mcpServers": {
    "prolog-spec": {
      "command": "python3",
      "args": [".opencode/mcp-prolog/server.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### 2. Verify Installation

Test that the server can start:

```bash
cd .opencode/mcp-prolog
python3 server.py
```

You should see no errors. Type `Ctrl+C` to exit.

Test that SWI-Prolog is accessible:

```bash
swipl --version
```

## Usage

### From opencode

When using opencode, the Prolog tools will be automatically available. You can invoke them in your prompts:

**Example prompts:**

> "Use the `prolog.validate_spec` tool to check if there are any constraint violations in the current domain model."

> "Use `prolog.generate_test_cases` for the 'users' domain to get boundary test cases."

> "Query the Prolog model to check if user 42 with role 'admin' can delete: use `prolog.query` with 'can_delete(42)'."

### Direct Testing (CLI)

You can also test the tools directly from the command line:

```bash
cd .opencode/mcp-prolog

# Test constraint validation
swipl -s prolog/queries.pl -g "check_constraints_json" -t halt

# Test test case generation
swipl -s prolog/queries.pl -g "generate_user_cases" -t halt
```

## Customizing the Prolog Model

The Prolog files in the `prolog/` directory define your domain model:

### `domain.pl`

Define your core domain concepts, entities, and business rules:

```prolog
% Example: Define a product entity
product(ProductId, Name, Price) :-
    integer(ProductId),
    atom(Name),
    number(Price),
    Price > 0.

% Example: Define ordering rules
can_order(UserId, ProductId) :-
    user(UserId, _),
    product(ProductId, _, Price),
    Price =< 1000.
```

### `constraints.pl`

Define invariants and validation rules:

```prolog
:- ['domain.pl'].

% Invariant: All products must have positive prices
check_product_prices(Violations) :-
    findall(ProductId,
        (product(ProductId, _, Price), Price =< 0),
        Violations).

% Update check_all_constraints to include new checks
check_all_constraints(Result) :-
    check_product_prices(PriceViolations),
    % ... other checks
    Result = _{
        invalid_prices: PriceViolations,
        % ... other results
    }.
```

### `scenarios.pl`

Define test case generators:

```prolog
:- ['domain.pl'].

% Generate valid product scenarios
valid_product(ProductId, Name, Price) :-
    between(1, 100, ProductId),
    atom(Name),
    between(1, 10000, Price).

% Generate invalid product scenarios
invalid_product(ProductId, Name, Price) :-
    (ProductId =< 0 ; Price =< 0).
```

### `queries.pl`

Add new query predicates for MCP tools:

```prolog
% Generate test cases for products
generate_product_cases :-
    findall(_{type: valid, product_id: P, name: N, price: Pr},
        (valid_product(P, N, Pr), P =< 10),
        Valids),
    findall(_{type: invalid, product_id: P2, name: N2, price: Pr2},
        (invalid_product(P2, N2, Pr2)),
        Invalids),
    append(Valids, Invalids, All),
    emit_json(_{test_cases: All}).
```

## Extending the MCP Server

To add new tools to the MCP server, edit `server.py`:

1. Add a new tool definition in `list_tools()`
2. Add a handler in `handle_tool_call()`
3. Create corresponding Prolog predicates in `queries.pl`

Example:

```python
# In list_tools()
{
    "name": "prolog.check_feature",
    "description": "Check a specific feature against constraints",
    "inputSchema": {
        "type": "object",
        "properties": {
            "feature_name": {
                "type": "string",
                "description": "Name of the feature to check"
            }
        },
        "required": ["feature_name"]
    }
}

# In handle_tool_call()
elif name == "prolog.check_feature":
    feature = args.get("feature_name")
    result = run_prolog(
        f"check_feature_json('{feature}')",
        prolog_files=["queries.pl"]
    )
    return result
```

## Troubleshooting

### "SWI-Prolog not found"

Ensure SWI-Prolog is installed and in your PATH:

```bash
which swipl  # Should show a path
swipl --version  # Should show version info
```

### "Parse error" or "Failed to parse Prolog output as JSON"

Check your Prolog files for syntax errors:

```bash
cd prolog
swipl -s queries.pl -g "check_constraints_json" -t halt
```

The output should be valid JSON.

### "Permission denied" when running server.py

Make the server executable:

```bash
chmod +x .opencode/mcp-prolog/server.py
```

### Server hangs or times out

Check for infinite loops in your Prolog predicates. The server has a 30-second timeout per query.

## Architecture

```
.opencode/
├── mcp-prolog/
│   ├── server.py           # MCP server (Python)
│   ├── prolog/
│   │   ├── domain.pl       # Domain model definitions
│   │   ├── constraints.pl  # Validation rules
│   │   ├── scenarios.pl    # Test case generators
│   │   └── queries.pl      # MCP query interface
│   └── README.md           # This file
└── mcp.json                # MCP configuration (or in project root)
```

## Resources

- [SWI-Prolog Documentation](https://www.swi-prolog.org/pldoc/doc_for?object=manual)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [opencode MCP Documentation](https://opencode.ai/docs/mcp-servers)
- [Spec Kit Documentation](https://github.com/github/spec-kit)

## License

This Prolog MCP server is part of the GitHub Spec Kit and is provided as-is for use with Spec-Driven Development workflows.
