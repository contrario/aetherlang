# AetherLang Node Reference

Complete reference for all 28 node types available in AetherLang.

## Node Categories

- [Control Flow](#control-flow) (6 nodes)
- [AI & LLM](#ai--llm) (6 nodes)
- [Data Processing](#data-processing) (6 nodes)
- [System](#system) (8 nodes)
- [Other](#other) (2 nodes)

---

## Control Flow

### guard
**Purpose:** Input validation and filtering

**Parameters:**
- `mode` (text): Validation mode - "STRICT" or "RELAXED"

**Example:**
```aetherlang
node Guard: guard mode="STRICT";
```

---

### plan
**Purpose:** Creates execution plan/strategy

**Parameters:**
- `steps` (number): Number of planning steps

**Example:**
```aetherlang
node Planner: plan steps=5;
```

---

### switch
**Purpose:** Conditional routing based on conditions

**Parameters:**
- `condition` (text): Routing condition

**Example:**
```aetherlang
node Router: switch condition="sentiment";
```

---

### conditional
**Purpose:** If-then-else logic

**Parameters:**
- `condition` (text): Boolean condition
- `true_path` (text): Path if true
- `false_path` (text): Path if false

**Example:**
```aetherlang
node Decision: conditional condition="score > 0.8";
```

---

### loop
**Purpose:** Iterative processing

**Parameters:**
- `max_iterations` (number): Maximum loop count
- `condition` (text): Continue condition

**Example:**
```aetherlang
node Iterator: loop max_iterations=10;
```

---

### parallel
**Purpose:** Parallel execution coordinator

**Parameters:**
- `max_concurrent` (number): Max parallel tasks

**Example:**
```aetherlang
node Parallel: parallel max_concurrent=5;
```

---

## AI & LLM

### llm
**Purpose:** Large Language Model inference

**Parameters:**
- `model` (text): Model name (e.g., "gpt-4o", "gpt-4o-mini")
- `temp` (number): Temperature (0.0-2.0)
- `max_tokens` (number): Max output tokens
- `system` (text): System prompt

**Example:**
```aetherlang
node GPT: llm model="gpt-4o",
              temp=0.7,
              max_tokens=2000,
              system="You are a helpful assistant";
```

---

### rag
**Purpose:** Retrieval-Augmented Generation

**Parameters:**
- `sources` (list): Data sources
- `top_k` (number): Number of results
- `threshold` (number): Relevance threshold

**Example:**
```aetherlang
node Retriever: rag sources=["docs", "web"],
                    top_k=10,
                    threshold=0.7;
```

---

### summarize
**Purpose:** Text summarization

**Parameters:**
- `length` (text): "short", "medium", "long"
- `style` (text): Summary style
- `language` (text): Output language

**Example:**
```aetherlang
node Summarizer: summarize length="short",
                           style="academic";
```

---

### analyze
**Purpose:** Deep content analysis

**Parameters:**
- `depth` (text): "shallow", "deep", "comprehensive"
- `sentiment` (bool): Include sentiment analysis
- `entities` (bool): Extract entities

**Example:**
```aetherlang
node Analyzer: analyze depth="deep",
                       sentiment=true,
                       entities=true;
```

---

### extract
**Purpose:** Entity and data extraction

**Parameters:**
- `entities` (list): Entity types to extract
- `format` (text): Output format

**Example:**
```aetherlang
node Extractor: extract entities=["person", "org", "date"];
```

---

### transform
**Purpose:** Data transformation

**Parameters:**
- `type` (text): Transformation type
- `format` (text): Output format

**Example:**
```aetherlang
node Transformer: transform type="json_to_xml";
```

---

## Data Processing

### filter
**Purpose:** Filter data based on criteria

**Parameters:**
- `condition` (text): Filter condition
- `keep` (text): "matches" or "non_matches"

**Example:**
```aetherlang
node Filter: filter condition="score > 0.5";
```

---

### map
**Purpose:** Apply function to each element

**Parameters:**
- `operation` (text): Operation to apply

**Example:**
```aetherlang
node Mapper: map operation="lowercase";
```

---

### reduce
**Purpose:** Aggregate data

**Parameters:**
- `operation` (text): Reduction operation
- `initial_value`: Starting value

**Example:**
```aetherlang
node Reducer: reduce operation="sum";
```

---

### split
**Purpose:** Split data into multiple streams

**Parameters:**
- `by` (text): Split criteria
- `count` (number): Number of splits

**Example:**
```aetherlang
node Splitter: split by="category", count=3;
```

---

### merge
**Purpose:** Combine multiple inputs

**Parameters:**
- `strategy` (text): "concat", "weighted", "prioritized"
- `weights` (list): Weight for each input

**Example:**
```aetherlang
node Merger: merge strategy="weighted",
                   weights=[0.6, 0.4];
```

---

### join
**Purpose:** SQL-like join operation

**Parameters:**
- `type` (text): "inner", "left", "right", "outer"
- `on` (text): Join key

**Example:**
```aetherlang
node Joiner: join type="inner", on="id";
```

---

## System

### cache
**Purpose:** Cache results

**Parameters:**
- `ttl` (number): Time-to-live in seconds
- `key` (text): Cache key

**Example:**
```aetherlang
node Cache: cache ttl=3600;  // 1 hour
```

---

### retry
**Purpose:** Retry failed operations

**Parameters:**
- `attempts` (number): Max retry attempts
- `delay` (number): Delay between retries (seconds)
- `backoff` (text): "linear", "exponential"

**Example:**
```aetherlang
node Retry: retry attempts=3,
                  delay=1.0,
                  backoff="exponential";
```

---

### timeout
**Purpose:** Timeout for operations

**Parameters:**
- `seconds` (number): Timeout duration

**Example:**
```aetherlang
node Timeout: timeout seconds=30;
```

---

### fallback
**Purpose:** Fallback value on error

**Parameters:**
- `default`: Default value
- `on_error` (text): Error handling strategy

**Example:**
```aetherlang
node Fallback: fallback default="No result";
```

---

### validate
**Purpose:** Data validation

**Parameters:**
- `schema` (text): Validation schema
- `required` (list): Required fields

**Example:**
```aetherlang
node Validator: validate schema="output_format",
                        required=["summary", "score"];
```

---

### http
**Purpose:** HTTP request

**Parameters:**
- `method` (text): "GET", "POST", "PUT", "DELETE"
- `endpoint` (text): URL endpoint
- `headers` (dict): HTTP headers

**Example:**
```aetherlang
node API: http method="POST",
               endpoint="https://api.example.com/data";
```

---

### webhook
**Purpose:** Webhook trigger/listener

**Parameters:**
- `url` (text): Webhook URL
- `events` (list): Events to listen for

**Example:**
```aetherlang
node Hook: webhook url="https://example.com/hook",
                   events=["complete", "error"];
```

---

### rate_limit
**Purpose:** Rate limiting

**Parameters:**
- `max_requests` (number): Max requests per period
- `period` (number): Time period (seconds)

**Example:**
```aetherlang
node RateLimit: rate_limit max_requests=100,
                            period=60;  // 100 req/min
```

---

## Other

### sleep
**Purpose:** Delay execution

**Parameters:**
- `seconds` (number): Sleep duration

**Example:**
```aetherlang
node Delay: sleep seconds=2;
```

---

### enrich
**Purpose:** Enrich data with additional information

**Parameters:**
- `source` (text): Enrichment source
- `fields` (list): Fields to enrich

**Example:**
```aetherlang
node Enricher: enrich source="database",
                      fields=["metadata", "tags"];
```

---

## Node Patterns

### Sequential Processing

```aetherlang
node A: guard;
node B: llm model="gpt-4o";
node C: summarize;

A -> B -> C;
```

### Parallel Paths

```aetherlang
node Start: guard;
node PathA: llm model="gpt-4o";
node PathB: rag sources=["docs"];
node End: merge;

Start -> PathA -> End;
Start -> PathB -> End;
```

### Error Handling

```aetherlang
node Retry: retry attempts=3;
node Timeout: timeout seconds=30;
node Fallback: fallback default="Error";

Retry -> Timeout -> MainNode -> Fallback;
```

### Caching Pattern

```aetherlang
node Cache: cache ttl=3600;
node Expensive: llm model="gpt-4o";

Cache -> Expensive;
```

### Validation Pattern

```aetherlang
node Guard: guard mode="STRICT";
node Process: llm model="gpt-4o";
node Validate: validate schema="output";

Guard -> Process -> Validate;
```

---

## Best Practices

### 1. Use Guards

Always validate input:

```aetherlang
node Guard: guard mode="STRICT";
Guard -> FirstProcessingNode;
```

### 2. Add Caching

Cache expensive operations:

```aetherlang
node Cache: cache ttl=3600;
Cache -> ExpensiveLLM;
```

### 3. Handle Errors

Use retry + fallback:

```aetherlang
node Retry: retry attempts=3;
node Fallback: fallback default="Error";

Retry -> RiskyNode -> Fallback;
```

### 4. Validate Outputs

Validate before final output:

```aetherlang
node Validator: validate schema="output";
ProcessingNode -> Validator -> Output;
```

### 5. Use Timeouts

Prevent hanging:

```aetherlang
node Timeout: timeout seconds=30;
Timeout -> LongRunningNode;
```

---

## Next Steps

- **[Getting Started](getting-started.md)** - Create your first flow
- **[Syntax Guide](syntax.md)** - Language syntax
- **[API Documentation](api.md)** - Python API
- **[Examples](../examples/)** - Sample flows

---

**Need a specific node?** [Request a feature](https://github.com/contrario/aetherlang/issues)
