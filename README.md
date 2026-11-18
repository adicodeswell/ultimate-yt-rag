# YouTube Knowledge Assistant — RAG Architecture

A Retrieval-Augmented Generation (RAG) application that uses knowledge extracted from YouTube playlists to answer technical questions with relevant explanations and video references.

The knowledge base contains content from multiple domains, including:

- Data Structures and Algorithms (DSA)
- Backend Engineering
- Artificial Intelligence
- SQL
- Other technical topics

The objective is to retrieve relevant information accurately and use an LLM to generate grounded answers with YouTube source links and timestamps.

---

# 1. What is RAG?

RAG stands for **Retrieval-Augmented Generation**.

A normal LLM generates answers using information learned during training. It doesn't automatically know the contents of your private YouTube knowledge base.

RAG solves this by retrieving relevant information from an external knowledge base before generating an answer.

It has three fundamental stages:

1. **Retrieval:** Find information relevant to the user's question.
2. **Augmentation:** Add the retrieved information to the LLM's prompt.
3. **Generation:** Generate an answer using the question and retrieved information.

### Example

User asks:

"Explain how Redis caching works."

The application:

1. Searches the YouTube knowledge base.
2. Finds relevant Redis explanations from backend videos.
3. Selects the most relevant passages.
4. Sends those passages to the LLM.
5. Generates an explanation with video references.

The LLM doesn't need to know the exact contents of your YouTube videos beforehand. It receives the relevant information at query time.

# 2. Data Ingestion Pipeline

Before retrieval can happen, YouTube content must be converted into searchable information.

Our ingestion pipeline:

YouTube Playlists → Video Metadata → Audio → Transcription → Chunking → Knowledge Base → Embeddings → Qdrant

## 2.1 Playlist Metadata Extraction

We collect information about each video:

- Video ID
- Video title
- YouTube URL
- Playlist ID
- Playlist title
- Category
- Difficulty level

A video can belong to multiple playlists, so playlist metadata is preserved rather than assigning each video to only one category.

## 2.2 Audio Extraction and Transcription

Audio is extracted from YouTube videos and converted into text using Whisper.

Why transcription?

Embedding models work with text. Converting video lectures into text allows us to search their actual explanations rather than just their titles.

We preserve timestamps so that retrieved information can be traced back to the original video.

## 2.3 Chunking

A transcript can contain thousands of words. Embedding an entire transcript as one document makes retrieval less precise.

Chunking divides the transcript into smaller passages.

Our current configuration:

| Parameter | Value |
|---|---:|
| Chunk duration | 75 seconds |
| Overlap | 15 seconds |
| Stride | 60 seconds |

### Why overlap?

Suppose one explanation begins near the end of a chunk and finishes in the next chunk.

Without overlap, the explanation might be split into two incomplete passages.

Overlap preserves some surrounding context between consecutive chunks.

Each chunk retains:

- Unique chunk ID
- Video ID
- Video title
- Playlist metadata
- Start and end timestamps
- YouTube URL
- Transcript text
- Domain labels

## 2.4 Domain Metadata

Each chunk contains a `domains` array.

Example:

```json
{
  "domains": ["backend", "sql"]
}
```

Why an array?

Some explanations belong to multiple technical domains.

We store each chunk only once instead of duplicating it across domain-specific files.

Current knowledge base:

| Domain | Chunks |
|---|---:|
| Backend | 10,088 |
| DSA | 11,402 |
| AI | 1,747 |
| SQL | 594 |
| Other | 1,895 |
| **Total unique chunks** | **25,301** |

Domain labels currently come from the earlier segregation process. Their semantic accuracy can be improved independently.

# 3. Embeddings and Vector Search

Computers cannot directly understand the meaning of text in the same way humans do.

An embedding model converts text into a numerical representation called a vector.

Example:

```text
"Redis is an in-memory data store."
             |
             v
      Embedding Model
             |
             v
[0.12, -0.45, 0.83, ...]
```

Texts with similar meanings generally have vectors that are close together in embedding space.

This makes semantic search possible.

## 3.1 Dense Embeddings

We use:

`BAAI/bge-small-en-v1.5`

Properties:

- Produces 384-dimensional vectors.
- Supports semantic similarity search.
- Useful for understanding meaning rather than exact word matches.

Example:

User query:

"How do applications store frequently accessed data?"

Relevant passage:

"Redis provides an in-memory caching layer for frequently requested application data."

The wording is different, but the underlying meaning is similar.

Dense retrieval can identify this relationship.

## 3.2 Cosine Similarity

We use cosine similarity to compare dense vectors.

It measures the angle between two vectors.

\[
\text{Similarity}(A,B)=
\frac{A\cdot B}{\|A\|\|B\|}
\]

A higher score generally indicates greater semantic similarity.

Our BGE embeddings are normalized, making cosine similarity efficient to use.

## 3.3 Qdrant

Qdrant is our vector database.

It stores:

- Dense vectors
- Sparse vectors
- Original chunk text
- Video metadata
- Playlist information
- Timestamps
- YouTube URLs

We use Qdrant because it supports vector search, metadata filtering, and hybrid retrieval.

Our new collection:

`youtube_knowledge_v3`

# 4. Sparse Retrieval and BM25

Dense retrieval is good at understanding meaning, but it can miss important exact keywords.

Consider:

User query:

"Explain TCP three-way handshake."

A passage containing the exact phrase "TCP three-way handshake" is highly relevant.

Keyword-based retrieval is useful here.

We use BM25, a ranking algorithm for lexical information retrieval.

BM25 considers factors such as:

- How frequently query terms appear in a document.
- How rare those terms are across the collection.
- The length of the document.

The intuition:

A rare, important term appearing in a passage can make that passage more relevant than a generic passage containing common words.

We use:

`Qdrant/bm25` through FastEmbed.

## Dense vs Sparse Retrieval

| Dense retrieval | Sparse retrieval |
|---|---|
| Understands semantic similarity | Matches important terms |
| Uses numerical embeddings | Uses sparse keyword vectors |
| Handles paraphrasing well | Handles exact terminology well |
| May miss exact technical terms | May miss conceptual relationships |

Neither approach is sufficient for every query.

This is why we combine them.

# 5. Hybrid Search

Hybrid search combines dense and sparse retrieval.

Instead of depending on one retrieval method, we search using both.

Example:

User query:

"How does a hash map resolve collisions?"

Dense search may retrieve passages discussing hash table implementation and collision handling.

Sparse search may retrieve passages containing the exact terms "hash map" and "collision resolution."

Combining both gives us a stronger candidate set.

Our architecture:

```text
                User Query
                     |
          +----------+----------+
          |                     |
          v                     v
     Dense Search          Sparse Search
       (BGE)                  (BM25)
          |                     |
          v                     v
    Dense Results          Sparse Results
          |                     |
          +----------+----------+
                     |
                     v
              Result Fusion
                     |
                     v
              Ranked Results
```

# 6. Reciprocal Rank Fusion (RRF)

RRF stands for Reciprocal Rank Fusion.

It combines ranked search results from multiple retrieval methods.

Why do we need it?

Dense and sparse retrieval produce different rankings and scores.

Their raw scores are not directly comparable.

RRF combines their rankings instead of comparing their raw scores.

The formula:

\[
RRF(d)=\sum_{r\in R}\frac{1}{k+rank_r(d)}
\]

Where:

- \(d\) is a retrieved document.
- \(R\) is the set of ranking systems.
- \(rank_r(d)\) is the position of document \(d\) in ranking \(r\).
- \(k\) is a constant, commonly 60.

### Example

Suppose both retrieval methods return these results:

| Document | Dense rank | Sparse rank |
|---|---:|---:|
| A | 1 | 4 |
| B | 2 | 1 |
| C | 5 | 2 |
| D | 3 | Not found |

RRF calculates a combined score for each document.

A document ranked highly by multiple retrieval methods receives a stronger combined ranking.

**Important:** RRF does not understand the meaning of the passages. It only combines rankings.

This leads to the next concept.

# 7. Reranking — Understanding the Most Relevant Results

Reranking is a second-stage retrieval process that improves the ordering of already retrieved documents.

This is different from the initial retrieval process.

### Why do we need it?

Imagine the user asks:

"Explain the optimal approach for Two Sum."

Hybrid retrieval returns 20 candidates.

| Initial rank | Retrieved passage |
|---|---|
| 1 | Array traversal |
| 2 | Hash map implementation |
| 3 | Two Sum problem explanation |
| 4 | Kadane's algorithm |
| 5 | Hash map collision handling |

The initial ranking might place a related but less useful passage above the actual Two Sum explanation.

We want to identify which passages most directly answer the question.

That is the purpose of reranking.

## 7.1 Bi-Encoder vs Cross-Encoder

Our initial BGE retrieval uses a bi-encoder approach.

A bi-encoder independently converts the query and documents into vectors.

```text
Query ----------------> Query Embedding
                              |
                              v
                        Similarity Search

Documents ------------> Document Embeddings
```

This is efficient because document embeddings can be generated and stored beforehand.

A cross-encoder works differently.

It receives the query and a document together.

```text
Query + Document
       |
       v
 Cross-Encoder
       |
       v
 Relevance Score
```

The model evaluates how relevant the passage is to the specific question.

It can consider the relationship between the words and concepts in the query and passage more directly.

## 7.2 Our Reranker

Proposed model:

`BAAI/bge-reranker-base`

Workflow:

1. Hybrid retrieval returns 20 candidate passages.
2. The cross-encoder evaluates each query-passage pair.
3. Every candidate receives a relevance score.
4. Candidates are sorted by that score.
5. The top 5 are passed to the context preparation stage.

### Why not use a cross-encoder for all 25,301 chunks?

Because it requires evaluating query-document pairs individually.

That is significantly more computationally expensive than searching precomputed vectors.

Instead, we use:

**First stage:** Fast retrieval over the entire knowledge base.

**Second stage:** More expensive relevance evaluation over a small candidate set.

This balances retrieval quality and computational cost.

Reranking scores are relevance scores, not probabilities. A score of 0.9 does not necessarily mean 90% relevance.

# 8. Context Preparation

After reranking, we need to prepare information for the LLM.

We should not blindly send every retrieved chunk.

Context preparation is responsible for:

- Selecting the best passages.
- Removing duplicate or highly redundant information.
- Preserving source metadata.
- Keeping timestamps and URLs.
- Managing the context size.
- Maintaining enough surrounding information for a useful answer.

Example context:

```text
Source 1:
Title: Two Sum - LeetCode
Timestamp: 04:20
URL: https://youtube.com/watch?v=VIDEO_ID&t=260s

Content:
The optimal solution uses a hash map to store
previously encountered values...
```

The LLM receives the actual passage and its source information.

It should never have to invent a source link or timestamp.

# 9. Prompt Engineering for RAG

Prompt engineering is the process of designing instructions that guide an LLM toward the desired behavior.

In our application, the prompt is especially important because the LLM must answer using retrieved YouTube content.

A weak prompt:

```text
Answer this question using the context.
```

This leaves too much room for hallucination and inconsistent behavior.

We need a structured prompt.

## 9.1 System Instructions

The system prompt defines the assistant's role and rules.

It should specify:

- The assistant is a technical knowledge assistant.
- Retrieved passages are the primary evidence.
- Retrieved content must be treated as reference data, not executable instructions.
- The assistant must not invent facts, sources, or timestamps.
- Unavailable information must be acknowledged.
- Conflicting sources must be handled transparently.

## 9.2 Context

The context contains the retrieved passages.

Every passage should include its source metadata.

The LLM should be able to distinguish one source from another.

## 9.3 User Question

The actual user question is passed separately.

This keeps the question distinct from the retrieved content.

## 9.4 Output Instructions

The prompt should encourage:

- Direct answers.
- Clear technical explanations.
- Useful examples when appropriate.
- Code examples when the question requires them.
- Source references for claims supported by the knowledge base.
- An explicit limitation when the retrieved information is insufficient.

We should avoid forcing every answer into a rigid template.

For example, a question asking for a definition should not receive a long tutorial, while a question asking for an implementation should receive a more detailed explanation.

# 10. LLM Generation

We use the Groq API for answer generation.

Current configured model:

`openai/gpt-oss-120b`

The generation stage receives:

1. System instructions.
2. User question.
3. Retrieved and reranked context.
4. Output requirements.

The model generates the final response.

### Important distinction

The LLM is responsible for generating an understandable answer.

The retrieval pipeline is responsible for finding the evidence.

A more capable LLM cannot compensate for consistently poor retrieval.

Likewise, excellent retrieval does not automatically guarantee a well-written answer.

Both stages must be evaluated.

# 11. Source Attribution

One of the most important features of this project is source traceability.

Every chunk already contains:

- Video title
- Video ID
- Start timestamp
- End timestamp
- YouTube URL

Example:

```text
Redis Caching Explained

Timestamp: 05:42

https://www.youtube.com/watch?v=VIDEO_ID&t=342s
```

The final answer should cite the sources that actually support its explanation.

We should not attach every retrieved source indiscriminately.

If a passage does not support a claim, it should not be cited for that claim.

This makes the assistant more useful as a learning tool because users can watch the original explanation.

# 12. Handling Missing Information

A RAG system should know when its knowledge base does not contain sufficient information.

Example:

User:

"Explain a specific algorithm that is not covered in my videos."

Possible behavior:

- Search the knowledge base.
- Evaluate the retrieved passages.
- Determine whether they contain sufficient evidence.
- Explain that the available sources do not adequately cover the topic.

The application should not fabricate a YouTube explanation or source.

A distinction is important:

The model may use general knowledge to explain concepts if the product explicitly allows it, but it must clearly distinguish general knowledge from information supported by the YouTube knowledge base.

# 13. Evaluation

A RAG system should not be considered complete simply because it generates fluent answers.

We need to evaluate retrieval and generation separately.

## 13.1 Retrieval Evaluation

Create a test dataset of questions with expected relevant chunks or video sources.

Useful metrics:

**Recall@K**

Measures how many relevant documents are retrieved within the top K results.

**Precision@K**

Measures what proportion of the top K retrieved documents are relevant.

**Mean Reciprocal Rank (MRR)**

Measures how highly the first relevant result appears.

For example, if the first relevant result is ranked second:

\[
RR=\frac{1}{2}
\]

MRR averages reciprocal ranks across multiple queries.

## 13.2 Generation Evaluation

Evaluate:

- Answer correctness.
- Relevance to the question.
- Faithfulness to retrieved evidence.
- Completeness.
- Hallucinated information.
- Source correctness.
- Timestamp correctness.

## 13.3 Example Evaluation Dataset

| Question | Expected topic |
|---|---|
| Explain Two Sum using a hash map | DSA |
| What is Redis caching? | Backend |
| Explain TCP three-way handshake | Networking |
| What is a SQL index? | SQL |
| What are embeddings? | AI |

Start with 50–100 carefully selected questions.

Evaluate the same questions against different retrieval configurations:

1. Dense retrieval only.
2. Sparse retrieval only.
3. Hybrid retrieval with RRF.
4. Hybrid retrieval with RRF and reranking.

This tells us whether each additional component actually improves performance.

# 14. Current Architecture

```text
                  YOUTUBE PLAYLISTS
                         |
                         v
                  Video Metadata
                         |
                         v
                   Audio Extraction
                         |
                         v
                    Transcription
                         |
                         v
                      Chunking
                         |
                         v
                Single-Copy Knowledge Base
                         |
                         v
                   Embedding Pipeline
                         |
                 +-------+-------+
                 |               |
                 v               v
           Dense BGE         Sparse BM25
                 |               |
                 +-------+-------+
                         |
                         v
                       Qdrant
                         |
                    User Query
                         |
                 +-------+-------+
                 |               |
                 v               v
            Dense Search     Sparse Search
                 |               |
                 +-------+-------+
                         |
                         v
                  Reciprocal Rank
                     Fusion
                         |
                         v
                     Reranking
                         |
                         v
                 Context Preparation
                         |
                         v
                  Groq LLM Prompt
                         |
                         v
                  Final Generation
                         |
                         v
                Answer + Video Sources
```

# 15. Current Project Status

| Component | Status |
|---|---|
| Playlist metadata extraction | Completed |
| Audio extraction | Completed |
| Whisper transcription | Completed |
| Chunk generation | Completed |
| Domain segregation | Completed |
| Single-copy knowledge base | Completed |
| Knowledge base validation | Passed |
| Dense embeddings | Completed |
| Sparse BM25 embeddings | Completed |
| Qdrant v3 collection | Created |
| Hybrid retrieval | Implemented and tested |
| Cross-encoder reranking | Next to implement and benchmark |
| Context preparation | Pending |
| Groq generation | Pending |
| Prompt engineering | Pending |
| Evaluation dataset | Pending |
| Retrieval and generation evaluation | Pending |

# 16. Important Design Principles

1. **Keep ingestion separate from retrieval.** We should not need to transcribe videos again when changing retrieval strategies.

2. **Store each chunk once.** Use metadata arrays for multi-domain membership.

3. **Avoid hardcoded query routers.** Search the full collection by default and introduce metadata filters only when they genuinely help.

4. **Use hybrid retrieval.** Semantic and lexical retrieval complement each other.

5. **Rerank only a limited candidate set.** Avoid expensive cross-encoder inference over the entire database.

6. **Keep prompts separate from application logic.** Prompt versions should be independently editable and testable.

7. **Preserve source metadata.** Every answer should be traceable to the original video and timestamp.

8. **Evaluate before optimizing.** Do not assume an additional model or technique improves quality without testing.

9. **Handle uncertainty explicitly.** The assistant should acknowledge when the knowledge base does not contain sufficient evidence.

10. **Keep the architecture modular.** Each component should be independently testable and replaceable.

---

# 17. Final Objective

The goal is not simply to build a chatbot that searches YouTube transcripts.

The goal is to build a reliable technical learning assistant that can:

- Understand questions across multiple technical domains.
- Retrieve relevant explanations from a large video knowledge base.
- Find exact technical concepts even when wording differs.
- Rank the most useful passages.
- Generate structured, understandable explanations.
- Provide accurate video references and timestamps.
- Acknowledge missing information instead of inventing answers.
- Improve through measurable retrieval and generation evaluation.

The quality of the application will depend on the entire pipeline: ingestion, retrieval, ranking, context construction, prompting, and evaluation.