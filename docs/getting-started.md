# Getting Started with AetherLang

Welcome to AetherLang! This guide will help you create your first AI workflow in minutes.

## Installation

### Using pip

```bash
pip install aetherlang
```

### From source

```bash
git clone https://github.com/contrario/aetherlang.git
cd aetherlang
pip install -e .
```

## Prerequisites

- Python 3.10 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Your First Flow

### Step 1: Create a flow file

Create a file named `hello.ae`:

```aetherlang
flow HelloWorld {
  using target "neuroaether" version ">=0.2";

  input text message;

  node Greeter: llm model="gpt-4o-mini",
                    system="You are a friendly assistant";

  output text response from Greeter;
}
```

### Step 2: Parse and execute

Create `run.py`:

```python
import asyncio
import os
from aetherlang import AetherParser, AetherRuntime

async def main():
    # Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"

    # Parse the flow
    parser = AetherParser()
    with open("hello.ae", "r") as f:
        flow = parser.parse(f.read())

    # Check for errors
    if parser.has_errors():
        for error in parser.get_errors():
            print(f"Error: {error}")
        return

    # Execute the flow
    runtime = AetherRuntime(openai_api_key=os.environ["OPENAI_API_KEY"])
    result = await runtime.execute(flow, {
        "message": "Hello, AetherLang!"
    })

    # Print results
    if result["status"] == "success":
        print("Response:", result["outputs"]["response"])
    else:
        print("Error:", result["error"])

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Run it

```bash
python run.py
```

## Understanding the Flow

Let's break down the `hello.ae` flow:

```aetherlang
flow HelloWorld {                        // Flow declaration
  using target "neuroaether" version ">=0.2";  // Target platform

  input text message;                    // Define input

  node Greeter: llm model="gpt-4o-mini", // Node definition
                    system="You are a friendly assistant";

  output text response from Greeter;     // Define output
}
```

### Key Components:

1. **Flow Declaration**: `flow FlowName { ... }`
2. **Target**: Specifies the execution platform
3. **Inputs**: Data coming into the flow
4. **Nodes**: Processing units (LLM, cache, etc.)
5. **Connections**: Data flow between nodes
6. **Outputs**: Results from the flow

## Next Steps

### Add More Nodes

```aetherlang
flow EnhancedFlow {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="STRICT";
  node Cache: cache ttl=3600;
  node LLM: llm model="gpt-4o-mini";
  node Summarizer: summarize length="short";

  // Connect nodes
  Guard -> Cache -> LLM -> Summarizer;

  output text summary from Summarizer;
}
```

### Try Examples

Explore the [examples](../examples/) directory:
- `01-simple.ae` - Basic flow
- `02-analysis.ae` - Document analysis with retry
- `03-research.ae` - Complex multi-path flow
- `04-education.ae` - Greek education assistant

### Visual Designer

Try the interactive visual designer:
👉 [neurodoc.app/aether-nexus-omega-dsl](https://neurodoc.app/aether-nexus-omega-dsl)

Features:
- Real-time visualization
- Live execution tracking
- Drag & drop physics layout
- Export to SVG/PNG

## Common Patterns

### Sequential Processing

```aetherlang
A -> B -> C -> D;
```

### Parallel Paths

```aetherlang
Start -> PathA -> End;
Start -> PathB -> End;
Start -> PathC -> End;
```

### With Caching

```aetherlang
Cache -> ExpensiveNode -> Output;
```

### With Retry Logic

```aetherlang
Retry -> UnreliableNode -> Validator;
```

## Troubleshooting

### Parse Errors

```python
if parser.has_errors():
    for error in parser.get_errors():
        print(f"Line {error.line}: {error.message}")
```

### Validation Errors

```python
from aetherlang import AetherValidator

validator = AetherValidator()
is_valid = validator.validate(flow)

if not is_valid:
    for error in validator.get_errors():
        print(f"Validation error: {error}")
```

### Runtime Errors

```python
result = await runtime.execute(flow, inputs)

if result["status"] == "error":
    print("Error:", result["error"])
    print("Execution log:", result["execution_log"])
```

## Resources

- **[Syntax Guide](syntax.md)** - Complete language reference
- **[Node Reference](nodes.md)** - All available nodes
- **[API Documentation](api.md)** - Python API
- **[GitHub](https://github.com/contrario/aetherlang)** - Source code

## Need Help?

- 📖 [Documentation](https://github.com/contrario/aetherlang/tree/main/docs)
- 🐛 [Report Issues](https://github.com/contrario/aetherlang/issues)
- 💬 [Discussions](https://github.com/contrario/aetherlang/discussions)

Happy coding! 🚀
