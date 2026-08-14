# Nova Memory System

Nova's memory system is designed to give the tutor continuity between conversations.

The goal is not to remember everything.

The goal is to remember information that can improve future tutoring.

---

## Why Memory?

Without memory:

```text
Student
   ↓
Question
   ↓
Answer
   ↓
Conversation ends
```

With memory:

```text
Student
   ↓
Question
   ↓
Answer
   ↓
Useful information extracted
   ↓
Memory
   ↓
Future conversation
   ↓
Personalized tutoring
```

---

# Memory Extraction

Nova includes a `MemoryExtractor` responsible for identifying potentially useful information from natural-language conversations.

For example:

```text
"My goal is to study artificial intelligence."
```

could represent a student goal.

Similarly:

```text
"I prefer detailed explanations."
```

could represent a learning preference.

---

# Memory Metadata

Nova's memory system can associate information with metadata such as:

```text
type
text
subject
conversation_id
importance
confidence
```

This allows memories to eventually be filtered and ranked rather than treated as identical pieces of text.

---

# Memory Pipeline

```text
Conversation
     │
     ▼
MemoryExtractor
     │
     ▼
Potential Fact
     │
     ▼
Metadata
     │
     ▼
Storage
     │
     ▼
Retrieval
     │
     ▼
Student Context
     │
     ▼
TutorEngine
```

---

# Current Development Challenge

Natural-language fact extraction is still imperfect.

For example, a sentence such as:

```text
"My name is Michael."
```

should ideally produce a structured representation such as:

```text
Type: identity
Field: name
Value: Michael
```

rather than simply extracting:

```text
"Michael."
```

Improving this behavior is an active development task.

---

# Memory Quality

Memory should eventually be evaluated according to:

### Relevance

Is this information actually useful?

### Accuracy

Was the information extracted correctly?

### Confidence

How confident is Nova that the extracted fact is correct?

### Importance

How valuable is the information for future tutoring?

### Persistence

Should the information remain available in future sessions?

---

# Future Improvements

Planned improvements include:

* better structured fact extraction
* duplicate detection
* memory updating
* contradiction handling
* memory ranking
* better retrieval
* memory expiration where appropriate
* automated memory tests
* stronger personalization

---

# Design Principle

Nova should not remember information simply because it can.

The objective is:

> **Remember what helps the student learn better.**
