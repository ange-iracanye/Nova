# Nova Architecture

Nova is designed as a modular AI tutoring system.

The main architectural goal is to separate **student context, memory, knowledge retrieval, tutoring logic, prompt construction, and model inference**.

This makes individual systems easier to test, replace, and improve.

---

## High-Level Architecture

```text
Student
   │
   ▼
Conversation
   │
   ▼
Intent Detection
   │
   ├───────────────┐
   │               │
   ▼               ▼
Memory          Knowledge
System          Retrieval
   │               │
   └───────┬───────┘
           │
           ▼
      Student Context
           │
           ▼
       TutorEngine
           │
           ▼
      PromptBuilder
           │
           ▼
        LocalLLM
           │
           ▼
        Response
           │
           ▼
   Memory / Learning Update
```

---

# 1. Intent Detection

The intent detection layer determines what the student is trying to accomplish.

Possible categories can include:

* asking a question
* requesting an explanation
* requesting practice
* requesting a quiz
* requesting calculations
* requesting information
* using a specific skill

The goal is to prevent every request from being processed identically.

---

# 2. Student Context

Nova can combine information about the current student with the current request.

Student context can include:

* student profile
* subject
* previous interactions
* confidence
* learning history
* relevant memories

This context can influence how Nova responds.

---

# 3. Memory System

The memory system extracts and stores potentially useful information from conversations.

Memory is intended to provide continuity between interactions.

It can contain information such as:

```text
type
text
subject
conversation
importance
confidence
```

Memory is later available to other parts of the tutoring pipeline.

---

# 4. Knowledge Retrieval

Nova uses retrieval to find relevant information from its knowledge base.

The retrieval system uses embeddings and similarity search to identify potentially relevant knowledge.

A relevance threshold is used to determine whether retrieved information is sufficiently related to the current request.

---

# 5. TutorEngine

The TutorEngine coordinates the tutoring process.

It receives information such as:

* student
* subject
* message
* mode
* tutoring strategy

and coordinates the generation process.

The TutorEngine acts as the bridge between tutoring logic and model inference.

---

# 6. PromptBuilder

PromptBuilder separates prompt construction from the TutorEngine.

Conceptually:

```text
Student
Subject
Question
Mode
Strategy
   │
   ▼
PromptBuilder
   │
   ├── System Prompt
   └── User Prompt
```

This makes it possible to modify tutoring instructions without rewriting the entire inference layer.

---

# 7. Local LLM

Nova uses local language-model inference.

The model layer is responsible for:

1. Receiving the constructed prompt
2. Generating tokens
3. Extracting only the newly generated tokens
4. Decoding the generated text
5. Returning the response

Keeping model inference separate allows the rest of Nova's architecture to remain relatively independent of the specific model being used.

---

# 8. Tools

Nova can use specialized capabilities instead of relying on the language model for every operation.

Examples include:

* calculator
* internet-related functionality
* skills

This follows the principle:

```text
If a specialized tool is better suited to a task,
use the tool instead of asking the language model
to perform everything itself.
```

---

# 9. Learning Update

After a response, relevant information can be stored or updated.

This creates a longer-term loop:

```text
Question
   ↓
Context
   ↓
Tutoring
   ↓
Answer
   ↓
Learning Information
   ↓
Memory / Student State
   ↓
Future Tutoring
```

This feedback loop is one of the central ideas behind Nova.

---

# Architectural Goals

Nova's architecture is being developed around:

* modularity
* testability
* separation of responsibilities
* student personalization
* replaceable AI components
* local inference
* continuous experimentation

The architecture will continue evolving as Nova becomes more sophisticated.
