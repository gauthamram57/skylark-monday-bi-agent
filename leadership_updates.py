import os
import pandas as pd
from typing import Dict, List, Any
from fpdf import FPDF

class LeadershipUpdateGenerator:
    """
    Leadership Update Engine.
    Transforms raw Monday.com cross-board metrics into structured, deck-ready
    Executive Briefings, Board Update Bullets, and Exportable PDF/Markdown Reports.
    """
    def __init__(self, df_deals: pd.DataFrame, df_wo: pd.DataFrame, quality_report: Dict[str, Any]):
        self.df_deals = df_deals
        self.df_wo = df_wo
        self.quality_report = quality_report

    def generate_executive_briefing(self) -> Dict[str, Any]:
        """Generate complete executive briefing package."""
        # 1. Pipeline Metrics
        total_pipeline = self.df_deals["Deal Value Clean"].sum()
        weighted_pipeline = self.df_deals["Weighted Value"].sum()
        open_deals = self.df_deals[self.df_deals["Status Clean"] == "Open"]
        won_deals = self.df_deals[self.df_deals["Status Clean"] == "Won"]
        win_rate = (len(won_deals) / max(len(self.df_deals), 1)) * 100
        
        # 2. Operations & Revenue Metrics
        total_contracted = self.df_wo["Amount Excl GST Clean"].sum()
        total_billed = self.df_wo["Billed Excl GST Clean"].sum()
        total_collected = self.df_wo["Collected Incl GST Clean"].sum()
        unbilled_backlog = self.df_wo["Unbilled Excl GST Clean"].sum()
        total_receivable = self.df_wo["Receivable Clean"].sum()
        
        completed_wo = (self.df_wo["Execution Status Clean"] == "Completed").sum()
        paused_wo = (self.df_wo["Execution Status Clean"] == "Pause / struck").sum()
        
        # 3. Top Sector Analysis
        top_sector_deals = self.df_deals.groupby("Sector Clean")["Deal Value Clean"].sum().idxmax()
        top_sector_wo = self.df_wo.groupby("Sector Clean")["Amount Excl GST Clean"].sum().idxmax()
        
        # 4. Deck-Ready Summary Bullets
        deck_bullets = [
            f"• **Sales Funnel Velocity**: Gross sales pipeline stands at ₹{total_pipeline:,.2f} across {len(self.df_deals)} deals, with a weighted value of ₹{weighted_pipeline:,.2f}.",
            f"• **Revenue Realization**: Contracted work orders total ₹{total_contracted:,.2f}. Billed revenue stands at ₹{total_billed:,.2f} with ₹{total_collected:,.2f} in cash collected.",
            f"• **Operational Execution**: {completed_wo} of {len(self.df_wo)} work orders completed. {paused_wo} projects currently paused pending client inputs.",
            f"• **Sector Leader**: {top_sector_deals} dominates sales pipeline, while {top_sector_wo} leads active operational execution.",
            f"• **Receivables Risk**: ₹{total_receivable:,.2f} in accounts receivable pending collection, and ₹{unbilled_backlog:,.2f} in unbilled backlog."
        ]
        
        # 5. Strategic Decisions Required for Executive Team
        decisions_needed = [
            "Approval to reallocate 2 Senior KAMs to Mining & Powerline sectors to clear commercial negotiation backlog.",
            "Directive to Finance/AR team to institute strict payment follow-ups on accounts exceeding 45 days AR.",
            "Ops team alignment on resolving client blocker dependencies for paused work orders."
        ]
        
        briefing = {
            "title": "Skylark Drones - Executive Leadership Briefing",
            "subtitle": "Cross-Board Business Intelligence & Operational Performance Summary",
            "kpi_snapshot": {
                "Gross Pipeline": f"₹{total_pipeline:,.2f}",
                "Weighted Pipeline": f"₹{weighted_pipeline:,.2f}",
                "Contracted Revenue": f"₹{total_contracted:,.2f}",
                "Billed Value": f"₹{total_billed:,.2f}",
                "Cash Collected": f"₹{total_collected:,.2f}",
                "Unbilled Backlog": f"₹{unbilled_backlog:,.2f}",
                "Outstanding AR": f"₹{total_receivable:,.2f}"
            },
            "deck_bullets": deck_bullets,
            "decisions_needed": decisions_needed,
            "data_resilience_score": self.quality_report.get("overall_quality_score", 100),
            "data_warnings": self.quality_report.get("warnings", [])
        }
        return briefing

    def export_pdf_report(self, filepath: str) -> str:
        """Export executive briefing as a styled PDF report."""
        briefing = self.generate_executive_briefing()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Header
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(24, 43, 73)
        pdf.cell(0, 10, "SKYLARK DRONES", ln=True, align="L")
        
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(51, 51, 51)
        pdf.cell(0, 8, briefing["title"], ln=True, align="L")
        
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, briefing["subtitle"], ln=True, align="L")
        pdf.ln(5)
        
        # Divider Line
        pdf.set_draw_color(0, 102, 204)
        pdf.set_line_width(0.8)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # KPI Snapshot Table
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 8, "1. Executive KPI Snapshot", ln=True)
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(230, 240, 255)
        pdf.cell(95, 7, " Metric", border=1, fill=True)
        pdf.cell(95, 7, " Value (INR)", border=1, fill=True, ln=True)
        
        pdf.set_font("Helvetica", "", 10)
        for k, v in briefing["kpi_snapshot"].items():
            clean_v = str(v).replace("₹", "INR ")
            pdf.cell(95, 6, f" {k}", border=1)
            pdf.cell(95, 6, f" {clean_v}", border=1, ln=True)
            
        pdf.ln(6)
        
        # Deck Ready Bullets
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 8, "2. Key Highlights for Slide Deck / Board Briefing", ln=True)
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(40, 40, 40)
        for bullet in briefing["deck_bullets"]:
            clean_b = bullet.replace("**", "").replace("• ", "").replace("₹", "INR ")
            pdf.multi_cell(0, 5, f"- {clean_b}")
            pdf.ln(2)
            
        pdf.ln(4)
        
        # Decisions Needed
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(0, 102, 204)
        pdf.cell(0, 8, "3. Decisions Needed from Leadership", ln=True)
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(40, 40, 40)
        for dec in briefing["decisions_needed"]:
            pdf.multi_cell(0, 5, f"- {dec}")
            pdf.ln(2)
            
        pdf.ln(4)
        
        # Data Resilience Footnote
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, f"Data Quality Score: {briefing['data_resilience_score']}/100. Generated dynamically via Monday.com BI Agent.", ln=True)
        
        pdf.output(filepath)
        return filepath
