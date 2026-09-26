# EU Alignment Scorecard – Smart City Municipal AI Assistant

**Team Name:** UBM 
**Challenge:** SmartCity (Primăria Chișinău)  
**Primary Sector:** Public Administration / Smart Cities (Cross-sector Digital Europe)  
**TRL Estimate:** 4-5 (Prototype validated in relevant environment)  
**Mentor:** Liviu Maftuleac 
**Date:** 2026-09-26  

> **Summary:** This prototype is an evidence-grounded, bilingual (RO/RU) municipal AI assistant. It strictly answers based on a defined corpus of 40+ official City Hall documents. It features a deterministic safety workflow that explicitly flags `NOT_FOUND` or `CONFLICT` instead of hallucinating, provides exact verbatim citations, and operates fully offline on local hardware, ensuring maximum data privacy and zero API data exfiltration.

---

## A. Sustainability & Green Deal alignment

| ID | Criterion | Score | Notes / Evidence | EU Reference |
|---|---|---|---|---|
| **A1** | Green Deal problem fit | **3** | Digital transformation of public services reduces paper waste and citizen travel time. Aligns with "sustainable mobility" and "resource efficiency" by providing instant, accurate access to municipal regulations. | European Green Deal |
| **A2** | Eco-design & circularity | **2** | Software-only solution. Designed for longevity through modular architecture (separation of ingestion, retrieval, and LLM), allowing model swaps without rebuilding the system. | ESPR |
| **A3** | Footprint of the tech itself | **3** | **Evidence:** Uses quantized local open-weight models (e.g., Gemma 3 / Qwen3 4-bit) on consumer GPUs (RTX 5060/3060). No continuous cloud API calls. Explicit "offline mode" minimizes compute and network footprint. | Green & Digital Twin Transition |
| **A4** | Do no significant harm | **3** | **Evidence:** The deterministic `evidence gate` prevents hallucinations. If the corpus lacks info or contains contradictions, the system explicitly returns `NOT_FOUND` or `CONFLICT` rather than generating misleading legal/administrative advice. | EU Taxonomy (DNSH) |

## B. Digitalisation priorities (AI, HPC, cybersecurity)

| ID | Criterion | Score | Notes / Evidence | EU Reference |
|---|---|---|---|---|
| **B1** | Digital Europe capacity fit | **3** | Directly supports "wider deployment of digital technologies and support for digital transformation across the public sector" by modernizing citizen-municipality interaction. | Digital Europe Programme |
| **B2** | Trustworthy AI & AI Act awareness | **4** | **Evidence:** Designed for AI Act compliance. 1) **Transparency:** Every answer includes exact document + verbatim passage citations. 2) **Human oversight:** Feedback mechanism (👍/👎) and explicit uncertainty flags (`NOT_FOUND`). 3) **Risk mitigation:** No autonomous decision-making; purely informational. | EU AI Act, ALTAI |
| **B3** | Cybersecurity by design | **3** | **Evidence:** Local inference loopback only. No external data exfiltration. Input validation (max length, sanitization). Rate-limiting on API endpoints. Demo uses synthetic/public data only. | NIS2, Cyber Resilience Act |
| **B4** | Use of EU digital infrastructure | **3** | **Evidence:** Architecture is explicitly designed to be deployable and testable in **TEFs** (Testing and Experimentation Facilities) for Smart Cities, or supported by local **EDIHs** for municipal digital adoption. | EDIHs, TEFs |

## C. GDPR, data protection & ethics

| ID | Criterion | Score | Notes / Evidence | EU Reference |
|---|---|---|---|---|
| **C1** | Personal data mapping & minimisation | **4** | **Evidence:** The system processes **only public municipal documents**. It does not collect, store, or process any personal data (PII) from citizens beyond the transient query string, which is not logged with identifiers. | GDPR Art. 5 |
| **C2** | Lawful basis & consent | **4** | **Evidence:** Lawful basis is "public task" and "legitimate interest" for processing publicly available government data. No special category data is involved. | GDPR Art. 6 & 9 |
| **C3** | Privacy by design & by default | **4** | **Evidence:** "Offline-first" architecture. The LLM runs locally (Ollama). Even if the internet is disconnected, the system functions. No data is sent to third-party cloud providers. | GDPR Art. 25 |
| **C4** | Experimentation ethics | **4** | **Evidence:** The hackathon demo and golden evaluation dataset use strictly public, non-sensitive data or synthetically generated queries. No real citizen PII is used in testing or demos. | GDPR Art. 35 (DPIA) |

## D. Sectoral relevance (Smart Cities / Public Admin)

| ID | Criterion | Score | Notes / Evidence | EU Reference |
|---|---|---|---|---|
| **D1** | Sector policy priority fit | **3** | Aligns with the **New European Innovation Agenda** and **Digital Europe Programme** priorities for modernizing public administration and making government services more accessible and transparent. | Digital Europe, NEIA |
| **D2** | Stakeholder & value-chain fit | **3** | **Evidence:** Built directly for the challenge provider (Primăria Chișinău). End-users are citizens and municipal employees. The UI is designed for accessibility (RO/RU bilingual, clear citation links). | - |
| **D3** | Sector validation route | **3** | **Evidence:** Next credible step is a controlled pilot in one specific municipal department (e.g., Transparency or Urban Mobility) to measure deflection of routine inquiries, validated via the built-in feedback loop. | - |
| **D4** | Sector evidence & data standards | **3** | **Evidence:** The system is evaluated on a strict "Golden Dataset" using quantitative metrics (Recall@5, Citation Correctness, Status Accuracy) reported as N/M (e.g., 8/10), not vague percentages. | - |

## E. EU market scalability

| ID | Criterion | Score | Notes / Evidence | EU Reference |
|---|---|---|---|---|
| **E1** | EU market definition | **3** | **Evidence:** First market: Republic of Moldova (associated with Horizon Europe). Immediate scalability to Romania (shared language) and other EU municipalities with similar document-heavy structures (e.g., Italy, Spain). | EU Single Market |
| **E2** | EU value proposition & competition | **3** | **Evidence:** Differentiates from generic "chatbot wrappers" by guaranteeing **verifiable evidence** (no hallucinations), working offline, and providing transparent cost structures (self-hosted vs. API). | - |
| **E3** | Business model for EU scale | **3** | **Evidence:** Self-hosted GPU VPS or on-premise deployment model eliminates per-token API costs, making it highly predictable and scalable for public sector budgets across the EU. | EU Single Market |
| **E4** | Market-entry requirements & costs | **2** | Acknowledges that full production deployment would require adherence to local public procurement rules and potential CE marking / harmonized standards if packaged as a standalone software product. | CE Marking |
| **E5** | EU funding & growth pathway | **3** | **Evidence:** Targeting **Digital Europe Programme** (for public sector deployment) or **EIC Accelerator** (for scaling the underlying verifiable RAG technology to other regulated sectors like health or legal). | EIC, Digital Europe |

---

## Results (Automatic Calculation)

| Category | Average Score | Interpretation |
|---|---|---|
| **A. Sustainability & Green Deal** | 2.75 | Aligned |
| **B. Digitalisation priorities** | 3.25 | **EU-ready** |
| **C. GDPR, data protection & ethics** | 4.00 | **EU-ready** |
| **D. Sectoral relevance** | 3.00 | **EU-ready** |
| **E. EU market scalability** | 2.80 | Aligned |
| **OVERALL EU ALIGNMENT INDEX** | **3.16** | **EU-ready (for stage)** |

> **Conclusion for Mentor/Jury:** The prototype scores **>3.0**, placing it in the "EU-ready" band. Its strongest pillars are **GDPR/Privacy by Design (4.0)** and **Trustworthy AI (4.0)**, achieved through its strict evidence-grounded architecture, local processing, and explicit handling of uncertainty (`NOT_FOUND`/`CONFLICT`).
