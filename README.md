# 🛸 Skylark Drones — Monday.com Business Intelligence Agent

> **Technical Assignment**: AI Business Intelligence Agent connecting sales pipeline data (Deals) and operational project execution data (Work Orders) from **monday.com** to deliver founder-level decision insights.

---

## 🌟 Architecture Overview

```
                      +-----------------------------------+
                      |   Founder / Executive Interface   |
                      |  (Streamlit Conversational Web)   |
                      +-----------------+-----------------+
                                        |
                   +--------------------+--------------------+
                   |                                         |
         +---------v----------+                   +----------v---------+
         |  BI Query Agent    |                   | Leadership Briefing|
         |  Intent & Metrics  |                   | PDF/Deck Generator |
         +---------+----------+                   +----------+---------+
                   |                                         |
                   +--------------------+--------------------+
                                        |
                          +-------------v-------------+
                          |   Data Resilience Engine  |
                          | (Header Scrubbing, Sector |
                          |  Normalization, Audit)    |
                          +-------------+-------------+
                                        |
              +-------------------------+-------------------------+
              |                                                   |
    +---------v-----------------+                       +---------v-----------------+
    |   MondayGraphQLClient     |                       |    MondayMockEngine       |
    | (Live monday.com API v2)  |                       | (Dynamic Board Simulator) |
    +---------------------------+                       +---------------------------+
```

---

## ✨ Core Features

1. **Monday.com GraphQL API Integration (`monday_client.py`)**:
   - Direct integration with Monday.com API v2 (`https://api.monday.com/v2`).
   - Dynamic GraphQL querying for items, columns, and custom schema values.
   - Dual-mode support: seamlessly connects live when an API Key and Board IDs are provided, and falls back to a dynamic Monday.com Board Simulator when offline.

2. **Automated Monday.com Board Seeder (`monday_seeder.py`)**:
   - Automated script and UI button to automatically create `Skylark Deals Funnel` and `Skylark Work Order Tracker` boards on Monday.com via GraphQL mutations, configuring column types and populating initial item records.

3. **Data Resilience Engine (`data_resilience.py`)**:
   - **Header Scrubbing**: Strips out leaked header rows present in raw exports.
   - **Sector Normalization**: Standardizes sector taxonomy across Mining, Powerline, Renewables, Railways, Construction, Security, DSP, and Aviation.
   - **Probability Heuristics**: Converts qualitative strings (`High`, `Medium`, `Low`) into percentage probabilities, applying stage-based fallbacks for missing values.
   - **Data Quality Audit**: Displays a live Dataset Integrity Score (e.g. `87/100`) and appends explicit Data Resilience Warnings to every query response.

4. **Founder Query Understanding & BI Agent (`bi_agent.py`)**:
   - Natural language query parser categorizing intent across Pipeline Health, Revenue & Collections, Operational Metrics, Sector Performance, and Cross-Board Syntheses.
   - Interactive clarification generator for ambiguous queries.
   - Cross-board joins matching Sales Funnel deals with Work Order execution records.

5. **Leadership Updates Engine (`leadership_updates.py`)**:
   - Generates 1-page executive summaries, deck-ready bullet points, quarterly board updates, and downloadable PDF reports (`Skylark_Executive_Briefing.pdf`).

---

## 🛠️ Setup & Installation Instructions

### 1. Prerequisites
- Python 3.10+
- `pip` package manager

### 2. Quickstart Installation
```bash
# Clone or extract repository
cd skylark_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Launching the Web Application
```bash
# Launch Streamlit app
streamlit run app.py --server.port 8501
```
Open your browser at `http://localhost:8501`.

---

## 🔌 Monday.com Setup & Configuration Guide

### Option A: Using the Automated Seeder Script (Recommended)
If you have a Monday.com API Key, you can auto-create and populate the boards with one command:

```bash
python monday_seeder.py <YOUR_MONDAY_API_KEY>
```
The script will output your new **Deals Board ID** and **Work Orders Board ID**. Enter these IDs in the application sidebar settings to connect live!

### Option B: Manual Monday.com Board Setup
1. Log in to your [Monday.com](https://monday.com) account.
2. **Deals Board**: Create a new board named `Skylark Deals Funnel`.
   - Add columns: `Owner Code` (Text), `Client Code` (Text), `Deal Status` (Status), `Deal Stage` (Status), `Masked Deal Value` (Numbers), `Closure Probability` (Text), `Sector` (Text), `Tentative Close Date` (Date).
   - Import `Deal funnel Data.xlsx`.
3. **Work Orders Board**: Create a new board named `Skylark Work Order Tracker`.
   - Add columns: `Customer Name Code` (Text), `Serial #` (Text), `Execution Status` (Status), `Sector` (Text), `Amount Excl GST` (Numbers), `Billed Value` (Numbers), `Collected Amount` (Numbers), `Amount Receivable` (Numbers), `Billing Status` (Status).
   - Import `Work_Order_Tracker Data.xlsx`.
4. Obtain your API Key from **Admin > Developers > API**.
5. Input the API Key and Board IDs into the app's sidebar settings drawer.

---

## 💡 Sample Queries to Try

- 📈 *"How's our pipeline looking for energy sector this quarter?"*
- 💰 *"What is our total revenue, billed value, and uncollected AR?"*
- 🛠️ *"Show operational execution status of work orders by sector"*
- 🌐 *"Compare deal win rate and revenue execution across all sectors"*
- 🏢 *"Show complete executive cross-board overview"*
- 📄 *"Prepare an executive briefing for leadership updates"*

---

## 📁 Repository Structure

```
skylark_project/
├── app.py                   # Streamlit Web Application Interface
├── bi_agent.py              # BI Query Understanding & Cross-Board Agent
├── data_resilience.py       # Data Cleaning, Normalization & Audit Engine
├── monday_client.py         # Monday.com GraphQL API Client & Board Simulator
├── monday_seeder.py         # Automated Monday.com Board Creator & Importer
├── leadership_updates.py    # Executive Briefing & PDF Report Generator
├── DECISION_LOG.md          # 2-Page Executive Decision Log
├── requirements.txt         # Python Package Dependencies
├── Deal funnel Data.xlsx    # Sample Sales Funnel Dataset
└── Work_Order_Tracker Data.xlsx # Sample Work Order Dataset
```
