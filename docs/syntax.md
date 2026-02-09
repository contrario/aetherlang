# AetherLang Syntax Reference

Complete reference for the AetherLang Domain-Specific Language.

## Table of Contents

- [Flow Declaration](#flow-declaration)
- [Target Specification](#target-specification)
- [Inputs](#inputs)
- [Nodes](#nodes)
- [Connections](#connections)
- [Outputs](#outputs)
- [Comments](#comments)
- [Data Types](#data-types)
- [Keywords](#keywords)

---

## Flow Declaration

Every AetherLang program starts with a flow declaration:

```aetherlang
flow FlowName {
  // Flow contents
}
```

**Rules:**
- Flow names must start with uppercase letter
- Names can contain letters, numbers, underscores
- One flow per file

**Examples:**

```aetherlang
flow SimpleFlow { }
flow MyAIWorkflow { }
flow RAG_Pipeline_v2 { }
```

---

## Target Specification

Specify the execution platform and version:

```aetherlang
using target "platform_name" version "version_spec";
```

**Supported targets:**
- `"neuroaether"` - NeuroAether platform (recommended)

**Version specifications:**
- `">=0.2"` - Minimum version
- `"0.2.1"` - Exact version
- `">=0.2,<1.0"` - Range

**Example:**

```aetherlang
using target "neuroaether" version ">=0.2";
```

---

## Inputs

Define data coming into the flow:

```aetherlang
input type name;
```

**Supported types:**
- `text` - String/text data
- `number` - Numeric values
- `list` - List/array
- `dict` - Dictionary/object
- `bool` - Boolean (true/false)

**Examples:**

```aetherlang
input text query;
input number max_tokens;
input list keywords;
input dict context;
input bool debug_mode;
```

**Multiple inputs:**

```aetherlang
input text question;
input number temperature;
input list sources;
```

---

## Nodes

Nodes are processing units in the flow.

### Syntax

```aetherlang
node NodeAlias: node_type param1="value", param2=123;
```

**Rules:**
- Node aliases must start with uppercase
- Node types are lowercase
- Parameters are comma-separated
- String values use double quotes
- Numeric values are unquoted

### Node Declaration Examples

**Simple node:**

```aetherlang
node Guard: guard;
```

**With parameters:**

```aetherlang
node LLM: llm model="gpt-4o", temp=0.7;
```

**Multiple parameters:**

```aetherlang
node Analyzer: analyze depth="deep",
                       sentiment=true,
                       entities=["person", "org"];
```

### Available Node Types

See [nodes.md](nodes.md) for complete list of 28 node types.

---

## Connections

Define data flow between nodes:

### Syntax

```aetherlang
NodeA -> NodeB;
NodeA -> NodeB -> NodeC;
```

**Rules:**
- Use `->` for connections
- Chains are allowed
- Multiple paths supported

### Examples

**Sequential:**

```aetherlang
Guard -> Cache -> LLM -> Output;
```

**Parallel:**

```aetherlang
Start -> PathA -> End;
Start -> PathB -> End;
```

**Complex:**

```aetherlang
Input -> Splitter;
Splitter -> ProcessA -> Merger;
Splitter -> ProcessB -> Merger;
Merger -> Output;
```

---

## Outputs

Define results from the flow:

```aetherlang
output type name from NodeAlias;
```

**Examples:**

```aetherlang
output text summary from Summarizer;
output number confidence from Validator;
output list entities from Extractor;
```

**Multiple outputs:**

```aetherlang
output text analysis from Analyzer;
output text summary from Summarizer;
output number score from Scorer;
```

---

## Comments

### Single-line comments

```aetherlang
// This is a comment
```

### Multi-line comments

```aetherlang
/*
  This is a
  multi-line comment
*/
```

**Examples:**

```aetherlang
// Input for user query
input text query;

/*
  Main processing pipeline:
  1. Guard input
  2. Cache results
  3. Process with LLM
*/
node Guard: guard mode="STRICT";  // Strict validation
node Cache: cache ttl=3600;        // 1 hour cache
node LLM: llm model="gpt-4o";     // GPT-4 Optimized
```

---

## Data Types

### Primitives

| Type | Description | Example |
|------|-------------|---------|
| `text` | String data | `"Hello, world!"` |
| `number` | Numeric (int/float) | `42`, `3.14` |
| `bool` | Boolean | `true`, `false` |

### Collections

| Type | Description | Example |
|------|-------------|---------|
| `list` | Array/list | `["a", "b", "c"]` |
| `dict` | Dictionary/object | `{"key": "value"}` |

### Example usage:

```aetherlang
node Config: configure settings={
  "max_tokens": 1000,
  "temperature": 0.7,
  "models": ["gpt-4o", "gpt-4o-mini"]
};
```

---

## Keywords

Reserved keywords in AetherLang:

| Keyword | Purpose |
|---------|---------|
| `flow` | Flow declaration |
| `using` | Target specification |
| `target` | Platform target |
| `version` | Version requirement |
| `input` | Input declaration |
| `output` | Output declaration |
| `node` | Node declaration |
| `from` | Output source |
| `text` | Text type |
| `number` | Number type |
| `list` | List type |
| `dict` | Dict type |
| `bool` | Boolean type |
| `true` | Boolean true |
| `false` | Boolean false |

---

## Complete Example

```aetherlang
// Research Assistant Flow
// Performs multi-source research with caching and validation

flow ResearchAssistant {
  // Platform specification
  using target "neuroaether" version ">=0.2";

  // Inputs
  input text research_topic;
  input number max_sources;
  input bool include_academic;

  // Entry point with validation
  node Guard: guard mode="STRICT";

  // Caching layer (1 hour TTL)
  node Cache: cache ttl=3600;

  // Research paths
  node WebSearch: http method="GET",
                       endpoint="https://api.search.com";

  node RAGRetrieval: rag sources=["docs", "papers"],
                         top_k=10;

  node AcademicDB: http method="POST",
                        endpoint="https://scholar.api.com";

  // Merge research results
  node Merger: merge strategy="weighted",
                     weights=[0.4, 0.4, 0.2];

  // LLM synthesis
  node Synthesizer: llm model="gpt-4o",
                        temp=0.3,
                        max_tokens=2000,
                        system="Research synthesis expert";

  // Validation
  node Validator: validate schema="research_output",
                          required=["summary", "sources"];

  // Final summary
  node Reporter: summarize length="medium",
                          style="academic";

  // Flow connections
  Guard -> Cache;

  // Parallel research paths
  Cache -> WebSearch -> Merger;
  Cache -> RAGRetrieval -> Merger;
  Cache -> AcademicDB -> Merger;

  // Sequential processing
  Merger -> Synthesizer -> Validator -> Reporter;

  // Outputs
  output text research_summary from Reporter;
  output text detailed_analysis from Synthesizer;
  output list sources_used from Merger;
}
```

---

## Best Practices

### 1. Naming Conventions

```aetherlang
// ✅ Good: Descriptive names
node DocumentValidator: validate;
node PrimaryLLM: llm model="gpt-4o";

// ❌ Bad: Unclear names
node N1: validate;
node X: llm model="gpt-4o";
```

### 2. Comments

```aetherlang
// ✅ Good: Explain complex logic
node Merger: merge strategy="weighted",  // 60% web, 40% docs
                   weights=[0.6, 0.4];

// ❌ Bad: Obvious comments
node Guard: guard;  // This is a guard node
```

### 3. Formatting

```aetherlang
// ✅ Good: Readable spacing
node LLM: llm model="gpt-4o",
              temp=0.7,
              max_tokens=1000;

// ❌ Bad: Hard to read
node LLM: llm model="gpt-4o",temp=0.7,max_tokens=1000;
```

### 4. Error Handling

```aetherlang
// ✅ Good: Retry + fallback
node Retry: retry attempts=3;
node Fallback: fallback default="Error message";

Retry -> MainNode -> Fallback;

// ❌ Bad: No error handling
MainNode -> Output;
```

---

## Next Steps

- **[Node Reference](nodes.md)** - Learn about all 28 node types
- **[API Documentation](api.md)** - Python API reference
- **[Examples](../examples/)** - Sample flows

---

**Need help?** [Open an issue](https://github.com/contrario/aetherlang/issues)
