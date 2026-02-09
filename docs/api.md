# AetherLang Python API

Complete API reference for using AetherLang programmatically in Python.

## Table of Contents

- [AetherParser](#aetherparser)
- [AetherRuntime](#aetherruntime)
- [AetherValidator](#aethervalidator)
- [Data Structures](#data-structures)
- [Examples](#examples)

---

## AetherParser

Parse AetherLang code into Abstract Syntax Tree (AST).

### Class: `AetherParser`

```python
from aetherlang import AetherParser

parser = AetherParser()
```

### Methods

#### `parse(code: str) -> Flow`

Parse AetherLang code and return Flow object.

**Parameters:**
- `code` (str): AetherLang source code

**Returns:**
- `Flow`: Parsed flow object

**Raises:**
- `ParseError`: If syntax errors found

**Example:**

```python
parser = AetherParser()
flow = parser.parse("""
flow MyFlow {
    using target "neuroaether" version ">=0.2";
    input text query;
    node LLM: llm model="gpt-4o";
    output text result from LLM;
}
""")
```

#### `has_errors() -> bool`

Check if parsing encountered errors.

**Returns:**
- `bool`: True if errors exist

**Example:**

```python
if parser.has_errors():
    print("Parse errors found!")
```

#### `get_errors() -> list[str]`

Get list of parse errors.

**Returns:**
- `list[str]`: Error messages

**Example:**

```python
for error in parser.get_errors():
    print(f"Error: {error}")
```

---

## AetherRuntime

Execute parsed flows with async OpenAI integration.

### Class: `AetherRuntime`

```python
from aetherlang import AetherRuntime

runtime = AetherRuntime(openai_api_key="your-key")
```

### Constructor

#### `__init__(openai_api_key: str)`

**Parameters:**
- `openai_api_key` (str): OpenAI API key

**Example:**

```python
import os
runtime = AetherRuntime(openai_api_key=os.environ["OPENAI_API_KEY"])
```

### Methods

#### `execute(flow: Flow, inputs: dict) -> dict`

Execute a flow with given inputs (async).

**Parameters:**
- `flow` (Flow): Parsed flow object
- `inputs` (dict): Input values

**Returns:**
- `dict`: Execution result with structure:
  ```python
  {
      "status": "success" | "error",
      "outputs": {"output_name": value},
      "execution_log": [log_entries],
      "duration_seconds": float
  }
  ```

**Example:**

```python
import asyncio

async def main():
    result = await runtime.execute(flow, {
        "query": "What is AetherLang?"
    })

    if result["status"] == "success":
        print("Outputs:", result["outputs"])
        print(f"Duration: {result['duration_seconds']:.2f}s")
    else:
        print("Error:", result["error"])

asyncio.run(main())
```

#### `get_execution_history() -> list`

Get history of all executions.

**Returns:**
- `list`: Execution context objects

**Example:**

```python
history = runtime.get_execution_history()
for execution in history:
    print(f"Flow: {execution.flow.name}")
    print(f"Duration: {execution.duration_seconds}s")
```

---

## AetherValidator

Validate parsed flows for semantic correctness.

### Class: `AetherValidator`

```python
from aetherlang import AetherValidator

validator = AetherValidator()
```

### Methods

#### `validate(flow: Flow) -> bool`

Validate a flow for errors.

**Parameters:**
- `flow` (Flow): Parsed flow object

**Returns:**
- `bool`: True if valid

**Example:**

```python
validator = AetherValidator()
is_valid = validator.validate(flow)

if not is_valid:
    for error in validator.get_errors():
        print(f"Validation error: {error}")
```

#### `get_errors() -> list[str]`

Get validation errors.

**Returns:**
- `list[str]`: Error messages

**Example:**

```python
errors = validator.get_errors()
for error in errors:
    print(f"⚠️  {error}")
```

---

## Data Structures

### Flow

Represents a parsed AetherLang flow.

```python
@dataclass
class Flow:
    name: str
    target: str
    version: str
    inputs: dict[str, str]
    nodes: dict[str, Node]
    edges: list[Edge]
    outputs: dict[str, str]
```

**Example:**

```python
print(f"Flow: {flow.name}")
print(f"Nodes: {len(flow.nodes)}")
print(f"Edges: {len(flow.edges)}")
```

### Node

Represents a node in the flow.

```python
@dataclass
class Node:
    alias: str
    node_type: NodeType
    params: dict[str, any]
```

**Example:**

```python
for alias, node in flow.nodes.items():
    print(f"{alias}: {node.node_type.value}")
    print(f"  Params: {node.params}")
```

### Edge

Represents a connection between nodes.

```python
@dataclass
class Edge:
    source: str
    target: str
```

**Example:**

```python
for edge in flow.edges:
    print(f"{edge.source} -> {edge.target}")
```

### NodeType

Enum of all node types.

```python
class NodeType(Enum):
    GUARD = "guard"
    LLM = "llm"
    RAG = "rag"
    CACHE = "cache"
    # ... etc
```

### ExecutionContext

Runtime execution context.

```python
@dataclass
class ExecutionContext:
    flow: Flow
    inputs: dict
    node_outputs: dict
    execution_log: list
    start_time: datetime
```

---

## Examples

### Complete Example: Parse, Validate, Execute

```python
import asyncio
import os
from aetherlang import AetherParser, AetherValidator, AetherRuntime

async def main():
    # 1. Parse
    parser = AetherParser()
    code = """
    flow Greeting {
        using target "neuroaether" version ">=0.2";
        input text name;
        node Greeter: llm model="gpt-4o-mini",
                          system="Greet the user warmly";
        output text greeting from Greeter;
    }
    """

    flow = parser.parse(code)

    if parser.has_errors():
        print("Parse errors:")
        for error in parser.get_errors():
            print(f"  - {error}")
        return

    # 2. Validate
    validator = AetherValidator()
    if not validator.validate(flow):
        print("Validation errors:")
        for error in validator.get_errors():
            print(f"  - {error}")
        return

    # 3. Execute
    runtime = AetherRuntime(
        openai_api_key=os.environ["OPENAI_API_KEY"]
    )

    result = await runtime.execute(flow, {
        "name": "Alice"
    })

    # 4. Process results
    if result["status"] == "success":
        print("✅ Success!")
        print(f"Greeting: {result['outputs']['greeting']}")
        print(f"Duration: {result['duration_seconds']:.2f}s")

        # Show execution log
        print("\nExecution log:")
        for entry in result["execution_log"]:
            print(f"  [{entry['status']}] {entry['node']}: {entry['message']}")
    else:
        print("❌ Error!")
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Handling

```python
from aetherlang import AetherParser, ParseError

try:
    parser = AetherParser()
    flow = parser.parse(invalid_code)
except ParseError as e:
    print(f"Parse error: {e}")
    print(f"Line {e.line}, Column {e.column}")
```

### Batch Processing

```python
async def process_batch(flows: list, queries: list):
    runtime = AetherRuntime(openai_api_key=api_key)

    tasks = []
    for flow, query in zip(flows, queries):
        task = runtime.execute(flow, {"query": query})
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

### Custom Node Processing

```python
async def execute_with_monitoring(runtime, flow, inputs):
    start = time.time()

    result = await runtime.execute(flow, inputs)

    duration = time.time() - start
    print(f"Execution completed in {duration:.2f}s")

    # Log to monitoring system
    log_metrics({
        "flow": flow.name,
        "duration": duration,
        "status": result["status"],
        "nodes_executed": len(result["execution_log"])
    })

    return result
```

### Flow Inspection

```python
def analyze_flow(flow: Flow):
    """Analyze flow structure"""

    print(f"Flow: {flow.name}")
    print(f"Target: {flow.target} v{flow.version}")
    print(f"\nInputs: {len(flow.inputs)}")
    for name, type_ in flow.inputs.items():
        print(f"  - {name}: {type_}")

    print(f"\nNodes: {len(flow.nodes)}")
    for alias, node in flow.nodes.items():
        print(f"  - {alias} ({node.node_type.value})")
        if node.params:
            for key, value in node.params.items():
                print(f"      {key}={value}")

    print(f"\nConnections: {len(flow.edges)}")
    for edge in flow.edges:
        print(f"  - {edge.source} -> {edge.target}")

    print(f"\nOutputs: {len(flow.outputs)}")
    for name, source in flow.outputs.items():
        print(f"  - {name} from {source}")
```

### Loading from File

```python
def load_flow_from_file(filepath: str) -> Flow:
    """Load and parse flow from file"""

    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()

    parser = AetherParser()
    flow = parser.parse(code)

    if parser.has_errors():
        raise ValueError(f"Parse errors in {filepath}:\n" +
                        "\n".join(parser.get_errors()))

    return flow
```

---

## Type Hints

AetherLang uses Python type hints throughout:

```python
from aetherlang import AetherParser, AetherRuntime, Flow
from typing import Dict, List, Any

def process_flow(
    code: str,
    inputs: Dict[str, Any]
) -> Dict[str, Any]:
    parser: AetherParser = AetherParser()
    flow: Flow = parser.parse(code)

    runtime: AetherRuntime = AetherRuntime(openai_api_key=api_key)
    result: Dict[str, Any] = await runtime.execute(flow, inputs)

    return result
```

---

## Async/Await

AetherLang Runtime is fully async:

```python
import asyncio

# ✅ Correct: Using asyncio
async def main():
    result = await runtime.execute(flow, inputs)

asyncio.run(main())

# ❌ Wrong: Not awaiting
def main():
    result = runtime.execute(flow, inputs)  # Returns coroutine, not result!
```

---

## Next Steps

- **[Getting Started](getting-started.md)** - Quick start guide
- **[Syntax Guide](syntax.md)** - Language syntax
- **[Node Reference](nodes.md)** - All node types
- **[Examples](../examples/)** - Sample code

---

**Questions?** [Open an issue](https://github.com/contrario/aetherlang/issues)
