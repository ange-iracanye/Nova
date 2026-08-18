# Nova V1 Performance Architecture

## Main latency risks

Nova combines model inference, embeddings, retrieval, memory, and persistent user state. The expensive path should therefore be deliberately separated from request parsing and lightweight API work.

### Fast path

- health/readiness
- authentication validation
- settings reads
- metadata

These should not initialize NovaCore or embedding models.

### Expensive path

- chat generation
- retrieval with uncached embeddings
- memory extraction
- quiz generation
- large document processing

These should be bounded, observable, and streamed when possible.

## Rules

1. Initialize heavyweight models lazily and once per process.
2. Reuse embedding models rather than creating them per request.
3. Cache immutable knowledge indexes and metadata.
4. Keep request payload limits explicit.
5. Keep the NovaCore synchronization lock around only shared runtime mutation/inference, not authentication or file I/O.
6. Use background work for non-critical analytics where correctness permits it.
7. Stream model output to reduce perceived latency.
8. Avoid repeated JSON parsing/writing for the same request.
9. Add timing metrics for retrieval, prompt construction, inference, memory, and total request latency.
10. Keep production logging structured and sampled for high-volume chat traffic.

## Frontend

- Use Vite production builds.
- Keep route-level lazy loading.
- Avoid importing heavy visualization or editor libraries on the initial route.
- Use hashed assets and long-lived caching for static files.
- Avoid repeated backend health polling when the page is not visible.
- Abort stale requests when navigating away from a page.

## Capacity target for V1

Until NovaCore becomes request-isolated, prefer one backend process and scale vertically. Do not add multiple workers merely to increase concurrency because shared mutable runtime state is protected by an application lock.

The first scalable architecture milestone is to make model/runtime state immutable per request or isolate a runtime per worker, then load-test before increasing worker count.
