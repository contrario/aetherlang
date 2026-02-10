"""
AetherLang Example Flows
"""

EXAMPLES = {
    "intro": {
        "name": "Εισαγωγικό Flow",
        "description": "Βασικό flow με Guard -> Plan -> LLM",
        "code": """
flow Intro {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guardian: guard mode="STRICT";
  node Planner: plan steps=4;
  node RAG: rag topk=3;
  node LLM: llm model="gpt-4o", temp=0.4;

  Guardian -> Planner -> LLM;
  RAG -> LLM;

  output text report from LLM;
}
"""
    },

    "analysis": {
        "name": "Πλήρης Ανάλυση",
        "description": "Flow με ανάλυση και περίληψη",
        "code": """
flow DeepAnalysis {
  using target "neuroaether" version ">=0.2";

  input text query;

  node Guard: guard mode="NORMAL";
  node Analyzer: analyze depth="deep";
  node RAG: rag topk=5;
  node LLM: llm model="gpt-4o", temp=0.5;
  node Summarizer: summarize length="short";

  Guard -> Analyzer;
  Analyzer -> LLM;
  RAG -> LLM;
  LLM -> Summarizer;

  output text analysis from LLM;
  output text summary from Summarizer;
}
"""
    },

    "extract": {
        "name": "Εξαγωγή Δεδομένων",
        "description": "Flow για structured data extraction",
        "code": """
flow DataExtraction {
  using target "neuroaether" version ">=0.2";

  input text document;

  node Processor: llm model="gpt-4o-mini", temp=0.2;
  node Extractor: extract type="entities";
  node Transform: transform type="json";

  Processor -> Extractor;
  Extractor -> Transform;

  output text structured_data from Transform;
}
"""
    },

    "research": {
        "name": "Ερευνητικό Flow",
        "description": "Πολύπλοκο flow με πολλαπλά στάδια",
        "code": """
flow ResearchFlow {
  using target "neuroaether" version ">=0.2";

  input text topic;

  node Guard: guard mode="STRICT";
  node Planner: plan steps=6;
  node RAG1: rag topk=5;
  node RAG2: rag topk=3;
  node Analyzer: analyze depth="comprehensive";
  node LLM1: llm model="gpt-4o", temp=0.6;
  node LLM2: llm model="gpt-4o", temp=0.3;
  node Merger: merge strategy="smart";
  node Summarizer: summarize length="detailed";

  Guard -> Planner;
  Planner -> RAG1;
  Planner -> RAG2;
  RAG1 -> Analyzer;
  RAG2 -> Analyzer;
  Analyzer -> LLM1;
  Analyzer -> LLM2;
  LLM1 -> Merger;
  LLM2 -> Merger;
  Merger -> Summarizer;

  output text full_report from Merger;
  output text summary from Summarizer;
}
"""
    },

    "greek_education": {
        "name": "Ελληνικό Εκπαιδευτικό Flow",
        "description": "Ειδικό flow για ελληνικό εκπαιδευτικό υλικό",
        "code": """
flow GreekEducation {
  using target "neuroaether" version ">=0.2";

  input text educational_content;
  input text grade_level;

  node Analyzer: analyze type="educational";
  node SimplifyLLM: llm model="gpt-4o", temp=0.4;
  node QuizGen: llm model="gpt-4o-mini", temp=0.7;
  node FlashcardGen: llm model="gpt-4o-mini", temp=0.5;

  Analyzer -> SimplifyLLM;
  SimplifyLLM -> QuizGen;
  SimplifyLLM -> FlashcardGen;

  output text simplified from SimplifyLLM;
  output text quiz from QuizGen;
  output text flashcards from FlashcardGen;
}
"""
    },

    "enterprise": {
        "name": "Enterprise Document Processing",
        "description": "Flow για επεξεργασία εταιρικών εγγράφων",
        "code": """
flow EnterpriseDoc {
  using target "neuroaether" version ">=0.2";

  input text document;

  node Classifier: llm model="gpt-4o-mini", temp=0.1;
  node Extractor: extract type="structured";
  node Validator: filter criteria="business_rules";
  node Transformer: transform type="excel";

  Classifier -> Extractor;
  Extractor -> Validator;
  Validator -> Transformer;

  output text classification from Classifier;
  output text extracted_data from Transformer;
}
"""
    },

    "chef_recipe": {
        "name": "AI Chef - Συνταγή",
        "description": "Culinary flow: Guard -> Plan -> Chef -> Summarize",
        "code": """
flow RecipeCreator {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="MODERATE";
  node Planner: plan steps=3;
  node Chef: chef cuisine="greek", difficulty="medium", servings=4;
  node Summary: summarize length="detailed";
  Guard -> Planner -> Chef -> Summary;
  output text recipe from Summary;
}
"""
    },

    "safe_chat": {
        "name": "Ασφαλής Συνομιλία",
        "description": "Απλό flow με Guard και LLM για safe chat",
        "code": """
flow SafeChat {
  using target "neuroaether" version ">=0.2";
  input text message;
  node Shield: guard mode="STRICT";
  node Responder: llm model="gpt-4o", temp=0.7;
  Shield -> Responder;
  output text reply from Responder;
}
"""
    },

    "market_research": {
        "name": "Market Analysis",
        "description": "Research + Consult + Market analysis pipeline",
        "code": """
flow MarketResearch {
  using target "neuroaether" version ">=0.2";
  input text query;
  node Guard: guard mode="STRICT";
  node Research: research depth="comprehensive";
  node Consult: consult domain="business", framework="swot";
  node Market: market scope="global", timeframe="6months";
  node Summary: summarize length="detailed";
  Guard -> Research -> Consult -> Market -> Summary;
  output text report from Summary;
}
"""
    }
}


def get_example(name: str) -> dict:
    """Get example flow by name"""
    return EXAMPLES.get(name)


def list_examples() -> list:
    """List all available examples"""
    return [
        {
            "id": key,
            "name": value["name"],
            "description": value["description"]
        }
        for key, value in EXAMPLES.items()
    ]