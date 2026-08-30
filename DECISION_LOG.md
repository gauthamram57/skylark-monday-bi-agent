# Executive Decision Log & Architecture Briefing
**Project**: Monday.com Business Intelligence Agent for Skylark Drones  
**Author**: AI Systems Engineering & BI Architect Team  
**Date**: August 2026  

---

## 1. Problem Framing & Core Objective
Skylark Drones executives and founders require rapid, accurate, and multi-source business intelligence across two core operational vectors:
1. **Deals Funnel (Sales & Commercial Pipeline)**: Commercial stage tracking, deal value forecasting, sector distribution, win/loss rates.
2. **Work Order Tracker (Project Execution & Revenue Realization)**: Project delivery status, billed vs unbilled contract amounts, cash collections, outstanding Accounts Receivable (AR).

Currently, answering founder queries requires manual board consolidation, data cleaning, ad-hoc cross-table joining, and filtering incomplete or messy records. Our solution delivers an **AI-powered BI Agent** with dynamic Monday.com integration (via API v2 GraphQL and local board simulator), a Data Resilience Engine, natural language query understanding, and an automated Leadership Update generator.

---

## 2. Key Assumptions Made
1. **Dynamic Board Schema & Linking**:
   - Assumed `Deal Name` in Deals board corresponds to `Deal name masked` in Work Orders board, enabling cross-board relational joins.
   - Assumed `Client Code` in Deals corresponds to `Customer Name Code` in Work Orders.
2. **Fiscal Calendar Standard**:
   - Skylark Drones operates under standard quarterly business cycles (Q1: Apr–Jun, Q2: Jul–Sep, Q3: Oct–Dec, Q4: Jan–Mar).
3. **Probability & Pipeline Valuation**:
   - Text categorical probabilities (`High`, `Medium`, `Low`) map to 80%, 50%, and 20% weighting factors respectively. When missing, stage-based heuristic probabilities (e.g. Work Order Received = 100%, Lead Generated = 20%) are calculated to ensure no deal is omitted from weighted valuation.
4. **GST Tax Treatment**:
   - Revenue and contract values are evaluated using **Excl. GST** as the primary accounting metric for operating revenue, while cash collections and AR receivables track **Incl. GST** for exact cash flow matching.

---

## 3. Trade-offs Chosen & Technical Rationale

| Architectural Decision | Chosen Approach | Trade-off Rationale & Justification |
| :--- | :--- | :--- |
| **Monday.com Integration** | **Dual Engine (GraphQL API v2 + Dynamic Board Simulator)** | Choosing a pure API approach would fail if test evaluators lacked active Monday API keys. Choosing hardcoded CSVs violates assignment rules. The dual-engine seamlessly uses live GraphQL when credentials are provided, and falls back to a dynamic Monday.com item/column simulator when offline. |
| **User Interface** | **Streamlit Conversational Web App** | Selected Streamlit over static scripts or complex React frameworks for rapid execution, rich native Plotly charting, interactive data tables, session state chat, and instant web hosting capability. |
| **Data Resilience** | **Automated In-Memory Scrubbing & Audit Trail** | Rather than permanently mutating raw CSV/Excel data or silently dropping bad rows, the agent cleans data in memory on ingestion and appends explicit Data Resilience Warnings to every query output. |
| **NLP Query Parsing** | **Deterministic Intent Classification & Entity Extraction Engine** | Avoids fragile external LLM API rate limits or network latency by using a robust entity-intent matching engine paired with interactive clarification fallbacks when queries are ambiguous. |

---

## 4. Interpretation of "Leadership Updates" (Additional Requirement)
Founders and C-suite executives do not just consume raw numbers—they require **curated strategic updates** tailored for board meetings, weekly leadership syncs, and investor updates. We interpreted this requirement as an **Executive Briefing Engine** that:
1. **Synthesizes Key Performance Indicators**: Auto-compiles Gross Pipeline, Weighted Value, Billed Revenue, Cash Collected, and AR Receivables into executive metric cards.
2. **Generates Deck-Ready Bullet Points**: Formats key takeaways into concise, high-impact bullet points designed to be copied directly into presentation decks or investor emails.
3. **Flags Risks & Strategic Decisions**: Surfaces unbilled backlogs, overdue AR accounts, and paused projects alongside required executive decisions.
4. **Exports PDF Briefings**: Provides 1-click generation of styled, print-ready PDF executive briefings for leadership distribution.

---

## 5. What We Would Do Differently with More Time
1. **Bi-Directional Monday.com Sync & Webhooks**: Implement real-time Monday.com webhooks (`item_created`, `column_value_changed`) to auto-refresh BI cache instantly.
2. **Advanced Semantic Vector Search**: Integrate local vector embeddings (ChromaDB / FAISS) for complex unstructured query resolution (e.g., "Find all deals with scope creep risks").
3. **Automated Monday.com Dashboard Widgets**: Write custom Monday.com app widgets (using Monday Apps Framework) to render the agent directly inside Monday board views.
4. **Multi-Currency & Inflation Adjustment**: Support automatic currency conversion for multi-region drone execution projects.
