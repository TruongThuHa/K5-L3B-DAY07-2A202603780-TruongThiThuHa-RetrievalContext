| Cấu hình | Phương pháp, top-k, budget | Hit@1 | Evidence Hit@3 | Context Evidence Rate | ms/câu |
|---|---|---|---|---|---|
| tfidf | tfidf, k=3, 800 ký tự | 7/15 (47%) | 12/15 (80%) | 5/15 (33%) | 1.0 |
| dense | dense, k=3, 800 ký tự | 9/15 (60%) | 12/15 (80%) | 7/15 (47%) | 43.4 |
| bm25 | bm25, k=3, 800 ký tự | 7/15 (47%) | 13/15 (87%) | 8/15 (53%) | 1.2 |
| hybrid | hybrid_rrf, k=3, 800 ký tự | 10/15 (67%) | 14/15 (93%) | 8/15 (53%) | 37.7 |
| hybrid_rerank | hybrid_rrf+rerank, k=3, 800 ký tự | 13/15 (87%) | 14/15 (93%) | 8/15 (53%) | 131.0 |
| hybrid_rerank_b2400 | hybrid_rrf+rerank, k=3, 2400 ký tự | 13/15 (87%) | 14/15 (93%) | 14/15 (93%) | 227.4 |
