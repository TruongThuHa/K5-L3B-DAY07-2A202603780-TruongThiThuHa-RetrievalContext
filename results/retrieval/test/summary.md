| Cấu hình | Phương pháp, top-k, budget | Hit@1 | Evidence Hit@3 | Context Evidence Rate | ms/câu |
|---|---|---|---|---|---|
| tfidf | tfidf, k=3, 800 ký tự | 4/5 (80%) | 5/5 (100%) | 3/5 (60%) | 1.1 |
| dense | dense, k=3, 800 ký tự | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 38.2 |
| bm25 | bm25, k=3, 800 ký tự | 4/5 (80%) | 5/5 (100%) | 3/5 (60%) | 1.3 |
| hybrid | hybrid_rrf, k=3, 800 ký tự | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 30.7 |
| hybrid_rerank | hybrid_rrf+rerank, k=3, 800 ký tự | 5/5 (100%) | 5/5 (100%) | 4/5 (80%) | 95.0 |
| hybrid_rerank_b2400 | hybrid_rrf+rerank, k=3, 2400 ký tự | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 102.2 |
