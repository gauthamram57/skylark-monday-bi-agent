import os
import time
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from monday_client import MondayDataManager, MondayGraphQLClient
from data_resilience import DataResilienceEngine
from bi_agent import BusinessIntelligenceAgent
from leadership_updates import LeadershipUpdateGenerator
from monday_seeder import MondayBoardSeeder

# Page Configuration
st.set_page_config(
    page_title="Skylark Drones - Business Intelligence Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File Paths
DEALS_EXCEL = "/home/gt/Projects/skylark_project/Deal funnel Data.xlsx"
WO_EXCEL = "/home/gt/Projects/skylark_project/Work_Order_Tracker Data.xlsx"

# Executive CSS Styling & Button Alignment
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .metric-card {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 8px;
        padding: 1.2rem;
        text-align: left;
    }
    
    .resilience-alert {
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-left: 4px solid #3b82f6;
        padding: 1rem 1.2rem;
        border-radius: 6px;
        margin: 1.2rem 0;
    }
    
    /* Clean Equal Button Styling for Suggested Queries */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
        width: 100%;
        text-align: center;
        padding: 0.5rem 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "api_key" not in st.session_state:
    st.session_state["api_key"] = os.getenv("MONDAY_API_KEY", "")
if "deals_board_id" not in st.session_state:
    st.session_state["deals_board_id"] = ""
if "wo_board_id" not in st.session_state:
    st.session_state["wo_board_id"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Cached Data Manager Initialization
@st.cache_resource(show_spinner="Loading and verifying Monday.com datasets...")
def get_data_manager(api_key, deals_id, wo_id):
    return MondayDataManager(DEALS_EXCEL, WO_EXCEL, api_key, deals_id, wo_id)

dm = get_data_manager(
    st.session_state["api_key"],
    st.session_state["deals_board_id"],
    st.session_state["wo_board_id"]
)
agent = BusinessIntelligenceAgent(dm)
leadership_gen = LeadershipUpdateGenerator(dm.df_deals, dm.df_wo, dm.quality_report)

# Sidebar Setup with Top-Left Drone Logo Only
with st.sidebar:
    st.image("https://img.icons8.com/color/96/drone.png", width=60)
    st.title("Skylark BI Control Panel")
    st.markdown("---")
    
    st.subheader("Monday.com Connection")
    conn_type = st.radio(
        "Data Source Mode:",
        ["Simulated Monday Data Engine", "Live Monday.com API v2"],
        index=1 if st.session_state["api_key"] else 0
    )
    
    if conn_type == "Live Monday.com API v2":
        api_key_input = st.text_input("Monday API Key:", value=st.session_state["api_key"], type="password")
        deals_id_input = st.text_input("Deals Board ID:", value=st.session_state["deals_board_id"])
        wo_id_input = st.text_input("Work Orders Board ID:", value=st.session_state["wo_board_id"])
        
        if st.button("Connect & Sync Live Boards", type="primary"):
            st.session_state["api_key"] = api_key_input
            st.session_state["deals_board_id"] = deals_id_input
            st.session_state["wo_board_id"] = wo_id_input
            st.cache_resource.clear()
            st.rerun()
            
        st.markdown("---")
        st.subheader("Automated Board Seeder")
        if st.button("Seed Boards to Monday.com"):
            if not api_key_input:
                st.error("Please enter a valid Monday API Key first.")
            else:
                with st.spinner("Creating & importing boards into Monday.com..."):
                    seeder = MondayBoardSeeder(api_key_input)
                    d_id = seeder.seed_deals_board(dm.df_deals, max_rows=25)
                    w_id = seeder.seed_work_orders_board(dm.df_wo, max_rows=25)
                    st.success(f"Boards created successfully!\nDeals ID: {d_id}\nWork Orders ID: {w_id}")
                    st.session_state["deals_board_id"] = d_id
                    st.session_state["wo_board_id"] = w_id
                    st.cache_resource.clear()
                    st.rerun()
    else:
        st.info("Operating in high-performance simulated Monday.com board engine mode.")
        
    st.markdown("---")
    st.subheader("Data Resilience Audit")
    score = dm.quality_report["overall_quality_score"]
    st.metric("Dataset Quality Score", f"{score} / 100")
    
    with st.expander("View Quality Audit Breakdown"):
        st.write(f"**Total Deals Loaded**: {dm.quality_report['deals_total']}")
        st.write(f"**Total Work Orders Loaded**: {dm.quality_report['wo_total']}")
        st.write("**Active Data Resilience Warnings:**")
        for w in dm.quality_report["warnings"]:
            clean_w = w.replace("⚠️ ", "").replace("ℹ️ ", "").replace("📊 ", "").replace("💵 ", "").replace("📌 ", "").replace("🚨 ", "")
            st.caption(f"- {clean_w}")

# Native Theme-Adaptive Header
st.title("Skylark Drones — Monday.com BI Agent")
st.caption("Executive Decision Intelligence across Sales Pipeline & Operational Execution")
st.markdown("---")

# Application Tabs
tab_chat, tab_explorer, tab_leadership, tab_docs = st.tabs([
    "Conversational BI Agent",
    "Board Data Explorer",
    "Leadership Updates Builder",
    "Decision Log & Architecture"
])

# ---------------------------------------------------------
# TAB 1: CONVERSATIONAL BI AGENT (Clean Layout, Aligned Grid, Auto-Scroll)
# ---------------------------------------------------------
with tab_chat:
    # 1. Perfectly Aligned Suggested Queries Grid (1 Row, 5 Equal Columns)
    st.markdown("##### Suggested Founder Queries:")
    s_cols = st.columns(5)
    
    p1 = s_cols[0].button("Energy Pipeline", use_container_width=True)
    p2 = s_cols[1].button("Revenue & AR", use_container_width=True)
    p3 = s_cols[2].button("Work Order Status", use_container_width=True)
    p4 = s_cols[3].button("Sector Comparison", use_container_width=True)
    p5 = s_cols[4].button("Executive Summary", use_container_width=True)

    selected_prompt = ""
    if p1: selected_prompt = "How's our pipeline looking for energy sector this quarter?"
    elif p2: selected_prompt = "What is our total revenue, billed value, and uncollected AR?"
    elif p3: selected_prompt = "Show operational execution status of work orders by sector"
    elif p4: selected_prompt = "Compare deal win rate and revenue execution across all sectors"
    elif p5: selected_prompt = "Show complete executive cross-board overview"

    st.markdown("---")

    # 2. Render Existing Chat Messages (Only if messages exist, no empty grey box!)
    if st.session_state["messages"]:
        for idx, msg in enumerate(st.session_state["messages"]):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "table" in msg and msg["table"]:
                    st.dataframe(pd.DataFrame(msg["table"]), use_container_width=True)
                if "chart" in msg and msg["chart"]:
                    cdata = msg["chart"]
                    if cdata.get("x") and cdata.get("y"):
                        fig = px.bar(x=cdata["x"], y=cdata["y"], title=cdata.get("title", ""))
                        st.plotly_chart(fig, use_container_width=True, key=f"hist_bar_{idx}")
                    elif cdata.get("labels") and cdata.get("values"):
                        fig = px.pie(names=cdata["labels"], values=cdata["values"], title=cdata.get("title", ""))
                        st.plotly_chart(fig, use_container_width=True, key=f"hist_pie_{idx}")
    else:
        st.info("Welcome to Skylark Drones BI Agent. Click one of the suggested query buttons above or type any custom business question in the chat input below to begin.")

    # 3. Process New Query & Stream Line-by-Line
    user_input = st.chat_input("Ask a founder-level business question...")
    query_to_run = selected_prompt or user_input
    
    if query_to_run:
        st.session_state["messages"].append({"role": "user", "content": query_to_run})
        st.rerun()

    # 4. Generate Pending Assistant Response
    if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
        latest_query = st.session_state["messages"][-1]["content"]
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Monday.com boards and querying Business Intelligence..."):
                res = agent.answer_query(latest_query)
                
                headline_text = res.get("headline", res.get("response_text", ""))
                clean_headline = headline_text.replace("📊 ", "").replace("💰 ", "").replace("🛠️ ", "").replace("🌐 ", "").replace("🏢 ", "").replace("💡 ", "").replace("🎯 ", "").replace("⚠️ ", "").replace("💵 ", "").replace("📌 ", "").replace("🚨 ", "").replace("✅ ", "").replace("🏆 ", "").replace("🔄 ", "").replace("📈 ", "").replace("⚙️ ", "").replace("🛡️ ", "")
                
                if res.get("status") == "clarification_needed":
                    st.warning(res["response_text"])
                    st.write("**Recommended Options:**")
                    for opt in res["options"]:
                        st.caption(f"- {opt}")
                else:
                    # Stream line-by-line / word-by-word typing animation
                    def stream_text():
                        lines = clean_headline.split("\n")
                        for line_idx, line in enumerate(lines):
                            words = line.split(" ")
                            for w_idx, word in enumerate(words):
                                yield word + (" " if w_idx < len(words) - 1 else "")
                                time.sleep(0.008)
                            if line_idx < len(lines) - 1:
                                yield "\n"
                                time.sleep(0.02)
                                
                    st.write_stream(stream_text)
                    
                    # Interactive Chart
                    if "chart_data" in res and res["chart_data"]:
                        cdata = res["chart_data"]
                        chart_key = f"live_chart_{len(st.session_state['messages'])}"
                        if res.get("chart_type") == "pie":
                            fig = px.pie(names=cdata["labels"], values=cdata["values"], title=cdata["title"])
                            st.plotly_chart(fig, use_container_width=True, key=chart_key)
                        else:
                            fig = px.bar(x=cdata["x"], y=cdata["y"], title=cdata["title"])
                            st.plotly_chart(fig, use_container_width=True, key=chart_key)
                            
                    # Data Table Breakdown
                    if "table_data" in res and res["table_data"]:
                        st.markdown("##### Data Breakdown:")
                        df_table = pd.DataFrame(res["table_data"])
                        st.dataframe(df_table, use_container_width=True)
                        
                    # Strategic Insights & Recommendations
                    st.markdown("##### Strategic Insights:")
                    for insight in res.get("insights", []):
                        clean_insight = insight.replace("💡 ", "").replace("🎯 ", "").replace("⚠️ ", "").replace("💵 ", "").replace("📌 ", "").replace("🚨 ", "").replace("✅ ", "").replace("🏆 ", "").replace("🔄 ", "").replace("📈 ", "").replace("⚙️ ", "").replace("🛡️ ", "")
                        st.write(f"- {clean_insight}")
                        
                    st.markdown("##### Recommended Actions:")
                    for rec in res.get("recommendations", []):
                        st.write(f"- {rec}")
                        
                    # Resilience Caveats
                    if res.get("data_warnings"):
                        st.markdown('<div class="resilience-alert">', unsafe_allow_html=True)
                        st.markdown("**Data Resilience Caveats & Quality Notes:**")
                        for w in res["data_warnings"]:
                            clean_w = w.replace("⚠️ ", "").replace("ℹ️ ", "").replace("📊 ", "").replace("💵 ", "").replace("📌 ", "").replace("🚨 ", "")
                            st.caption(f"- {clean_w}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Dynamic Follow-Up Prompt Suggestions for Next Question
                    if res.get("followup_suggestions"):
                        st.markdown("##### Suggested Follow-Up Prompts:")
                        f_cols = st.columns(len(res["followup_suggestions"]))
                        for f_idx, f_text in enumerate(res["followup_suggestions"]):
                            btn_key = f"followup_btn_{len(st.session_state['messages'])}_{f_idx}"
                            if f_cols[f_idx].button(f_text, key=btn_key, use_container_width=True):
                                st.session_state["messages"].append({"role": "user", "content": f_text})
                                st.rerun()
                        
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": clean_headline,
                    "table": res.get("table_data"),
                    "chart": res.get("chart_data"),
                    "followups": res.get("followup_suggestions")
                })
                
        # Target Anchor & Multi-Timeout Auto-Scroll JavaScript
        st.markdown('<div id="end-of-chat"></div>', unsafe_allow_html=True)
        components.html("""
        <script>
            function scrollToBottom() {
                try {
                    var mainContainer = window.parent.document.querySelector('.main');
                    if (mainContainer) {
                        mainContainer.scrollTo({ top: mainContainer.scrollHeight, behavior: 'smooth' });
                    }
                    var target = window.parent.document.getElementById('end-of-chat');
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'end' });
                    }
                } catch (e) {
                    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
                }
            }
            setTimeout(scrollToBottom, 50);
            setTimeout(scrollToBottom, 300);
            setTimeout(scrollToBottom, 800);
        </script>
        """, height=0)
        st.rerun()

# ---------------------------------------------------------
# TAB 2: BOARD DATA EXPLORER
# ---------------------------------------------------------
with tab_explorer:
    st.subheader("Monday.com Board Data Explorer")
    board_choice = st.radio("Select Board to Inspect:", ["Deals Board (Sales Funnel)", "Work Orders Board (Execution)"], horizontal=True)
    
    if board_choice == "Deals Board (Sales Funnel)":
        st.markdown(f"**Total Deals**: {len(dm.df_deals)}")
        sec_filter = st.multiselect("Filter by Sector:", options=dm.df_deals["Sector Clean"].unique().tolist())
        df_show = dm.df_deals
        if sec_filter:
            df_show = df_show[df_show["Sector Clean"].isin(sec_filter)]
            
        st.dataframe(df_show[[
            "Deal Name Clean", "Owner Code Clean", "Client Code Clean", "Status Clean",
            "Deal Stage Clean", "Deal Value Clean", "Probability Clean", "Weighted Value",
            "Sector Clean", "Fiscal Quarter"
        ]], use_container_width=True)
    else:
        st.markdown(f"**Total Work Orders**: {len(dm.df_wo)}")
        sec_filter = st.multiselect("Filter by Sector:", options=dm.df_wo["Sector Clean"].unique().tolist())
        df_show = dm.df_wo
        if sec_filter:
            df_show = df_show[df_show["Sector Clean"].isin(sec_filter)]
            
        st.dataframe(df_show[[
            "Deal Name Clean", "Customer Code Clean", "Serial Clean", "Execution Status Clean",
            "Sector Clean", "Amount Excl GST Clean", "Billed Excl GST Clean",
            "Collected Incl GST Clean", "Receivable Clean", "Billing Status Clean"
        ]], use_container_width=True)

# ---------------------------------------------------------
# TAB 3: LEADERSHIP UPDATES BUILDER
# ---------------------------------------------------------
with tab_leadership:
    st.subheader("Leadership Briefing & Executive Update Generator")
    st.write("Generates deck-ready bullet points, KPI summaries, and exportable PDF reports for leadership syncs.")
    
    briefing = leadership_gen.generate_executive_briefing()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### {briefing['title']}")
        st.caption(briefing['subtitle'])
        
        st.markdown("#### 1. Executive KPI Snapshot")
        df_kpi = pd.DataFrame(list(briefing["kpi_snapshot"].items()), columns=["Metric", "Value"])
        st.table(df_kpi)
        
        st.markdown("#### 2. Slide Deck Ready Bullet Points")
        for bullet in briefing["deck_bullets"]:
            clean_b = bullet.replace("**", "").replace("• ", "")
            st.markdown(f"- {clean_b}")
            
        st.markdown("#### 3. Key Decisions Needed from Executive Team")
        for dec in briefing["decisions_needed"]:
            st.markdown(f"- {dec}")
            
    with col2:
        st.markdown("### Export Options")
        st.write("Download styled PDF report for leadership distribution.")
        
        if st.button("Generate & Download PDF Report", type="primary"):
            pdf_path = "/home/gt/Projects/skylark_project/Skylark_Executive_Briefing.pdf"
            leadership_gen.export_pdf_report(pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF Report",
                    data=f,
                    file_name="Skylark_Executive_Briefing.pdf",
                    mime="application/pdf"
                )
            st.success("PDF Report generated successfully!")

# ---------------------------------------------------------
# TAB 4: DECISION LOG & ARCHITECTURE
# ---------------------------------------------------------
with tab_docs:
    st.subheader("Decision Log & Architectural Overview")
    doc_path = "/home/gt/Projects/skylark_project/DECISION_LOG.md"
    if os.path.exists(doc_path):
        with open(doc_path, "r") as f:
            st.markdown(f.read())
