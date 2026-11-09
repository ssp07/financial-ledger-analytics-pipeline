import os
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
import re

# ==========================================
# 1. DATABASE CONNECTIVITY & NORMALIZATION
# ==========================================
DB_FILE = "financial_ledger.db"

def initialize_ledger():
    if os.path.exists("dataset.csv"):
        try:
            df = pd.read_csv("dataset.csv")
            # Strip trailing spaces, enforce lowercase, and remove special formatting symbols safely
            df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_").replace("(", "").replace(")", "") for c in df.columns]
            conn = sqlite3.connect(DB_FILE)
            df.to_sql("ledger_table", conn, if_exists="replace", index=False)
            conn.close()
            return "ledger_table"
        except Exception as pipeline_err:
            st.error(f"Ingestion Pipeline Processing Error: {pipeline_err}")
            return None
    return None

active_table = initialize_ledger()

# ==========================================
# 2. STREAMLIT DYNAMIC INTERFACE PORTAL
# ==========================================
st.set_page_config(page_title="Financial Analytics Engine", layout="wide")
st.title("💼 Financial Ledger Data Pipeline & Analytics Engine")
st.markdown("---")

if not active_table:
    st.error("⚠️ System Check Failure: 'dataset.csv' financial data sheet not detected.")
else:
    conn = sqlite3.connect(DB_FILE)
    df_schema = pd.read_sql_query(f"SELECT * FROM {active_table} LIMIT 1", conn)
    conn.close()

    all_cols = df_schema.columns.tolist()
    numeric_cols = df_schema.select_dtypes(include=[np.number]).columns.tolist()
    text_cols = df_schema.select_dtypes(include=[object]).columns.tolist()

    # Dynamic schema introspector identifies key columns by scanning common matching text patterns
    val_col = next((c for c in numeric_cols if any(k in c for k in ["amount", "value", "fee", "cost", "revenue", "expenditure", "outlay", "price"])), None)
    if not val_col:
        val_col = numeric_cols[-1] if numeric_cols else "amount"

    cat_col = next((c for c in text_cols if any(k in c for k in ["category", "description", "region", "status", "tier", "item", "name", "state"])), None)
    if not cat_col:
        cat_col = text_cols[0] if text_cols else "category"

    date_col = next((c for c in all_cols if any(k in c for k in ["date", "time", "year", "fiscal"])), None)

    # Wrap column expressions securely in square brackets to fully handle messy embedded dot symbols
    safe_val_col = f"[{val_col}]"
    safe_cat_col = f"[{cat_col}]"
    safe_date_col = f"[{date_col}]" if date_col else None
    safe_all_cols_str = ", ".join([f"[{c}]" for c in all_cols])

    # ==========================================
    # 3. SELF-MUTATING FINANCIAL FAQ ENGINE
    # ==========================================
    faq_registry = {"Select a pre-verified query...": None}
    
    faq_registry["Q1: Display complete master transaction ledger logs"] = f"SELECT {safe_all_cols_str} FROM {active_table};"
    faq_registry[f"Q2: Isolate highest value transactions sorted by `{val_col.upper()}` descending"] = f"SELECT {safe_all_cols_str} FROM {active_table} ORDER BY {safe_val_col} DESC;"
    faq_registry[f"Q3: Isolate smallest metric allocations sorted by `{val_col.upper()}` ascending"] = f"SELECT {safe_all_cols_str} FROM {active_table} ORDER BY {safe_val_col} ASC;"
    faq_registry[f"Q4: Filter high-impact transactions exceeding 400 threshold units inside `{val_col.upper()}`"] = f"SELECT {safe_all_cols_str} FROM {active_table} WHERE abs({safe_val_col}) > 400.00;"
    
    if safe_date_col:
        faq_registry[f"Q5: Sort ledger chronologically to evaluate cash flow timing based on `{date_col.upper()}`"] = f"SELECT {safe_all_cols_str} FROM {active_table} ORDER BY {safe_date_col} ASC;"
    else:
        faq_registry["Q5: Display sequentially formatted database rows by standard index order"] = f"SELECT {safe_all_cols_str} FROM {active_table};"

    col_left, col_right = st.columns(2)
    with col_left:
        selected_faq = st.selectbox("Execute a pre-verified audit query:", list(faq_registry.keys()))
    with col_right:
        user_input = st.text_input("Ask a manual financial question (e.g., 'show everything ordered by amount'):", "")

    sql_query = faq_registry[selected_faq] if selected_faq != "Select a pre-verified query..." else None

    # ==========================================
    # 4. NATURAL INTENT PARSER MATRIX
    # ==========================================
    if user_input:
        clean_input = user_input.lower().strip()
        if any(col in clean_input for col in all_cols) or any(word in clean_input for word in ["everything", "all", "show", "select", "ledger", "logs", "rows", "table"]):
            where_clauses = []
            if any(w in clean_input for w in ["debit", "expense", "burn", "loss", "spending", "outflow"]):
                if "type" in all_cols: where_clauses.append("[type] LIKE '%debit%'")
                elif numeric_cols: where_clauses.append(f"{safe_val_col} < 0")
            elif any(w in clean_input for w in ["credit", "revenue", "income", "profit", "inflow"]):
                if "type" in all_cols: where_clauses.append("[type] LIKE '%credit%'")
                elif numeric_cols: where_clauses.append(f"{safe_val_col} > 0")
                
            num_match = re.search(r"(?:over|greater\s+than|>)\s*(\d+(?:\.\d+)?)", clean_input)
            if num_match:
                extracted_limit = float(num_match.group(1))
                where_clauses.append(f"abs({safe_val_col}) > {extracted_limit}")
                
            order_clause = ""
            if "date" in clean_input and safe_date_col:
                order_clause = f" ORDER BY {safe_date_col} ASC"
            elif any(s in clean_input for s in ["amount", "value", "highest", "rank", "sort"]):
                order_clause = f" ORDER BY abs({safe_val_col}) DESC"
                
            sql_query = f"SELECT {safe_all_cols_str} FROM {active_table}"
            if where_clauses:
                sql_query += " WHERE " + " AND ".join(where_clauses)
            sql_query += order_clause + ";"

    # ==========================================
    # 5. DATA PRESENTATION & STATISTICAL ANALYSIS
    # ==========================================
    if sql_query:
        try:
            conn = sqlite3.connect(DB_FILE)
            df_results = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            if not df_results.empty:
                st.success(f"Executed Financial SQL Statement: `{sql_query}`")
                total_records = len(df_results)
                df_results[val_col] = pd.to_numeric(df_results[val_col], errors='coerce').fillna(0)
                
                total_credits = df_results[df_results[val_col] > 0][val_col].sum()
                total_debits = df_results[df_results[val_col] < 0][val_col].sum()
                net_burn_rate = total_credits + total_debits
                
                if "type" in df_results.columns:
                    total_credits = df_results[df_results["type"].astype(str).str.lower().str.contains("credit|income|revenue")][val_col].abs().sum()
                    total_debits = df_results[df_results["type"].astype(str).str.lower().str.contains("debit|expense|outlay")][val_col].abs().sum()
                    net_profit_loss = total_credits - total_debits
                else:
                    net_profit_loss = net_burn_rate
                
                st.markdown("### 🎯 Executive Data Trend Summary")
                st.info(f"""
*   **📊 Transaction Density:** Found **{total_records} journal ledger rows** matching this audit selection.
*   **🟢 Gross Inflow Baseline:** Total identified pipeline revenue stands at **${total_credits:,.2f}**.
*   **🔴 Operational Overhead Burn Rate:** Total identified ledger expenses stand at **${abs(total_debits):,.2f}**.
*   **💎 Net Net Liquidity Allocation:** The net margin yield for this cluster tracks explicitly at **${net_profit_loss:,.2f}**.
                """)
                
                g_col1, g_col2 = st.columns(2)
                with g_col1:
                    st.markdown(f"**Chart A: Categorical Expenditure Burn Densities (Volume in `{val_col.upper()}`)**")
                    df_bar = df_results.copy()
                    df_bar[val_col] = df_bar[val_col].abs()
                    st.bar_chart(df_bar.groupby(cat_col)[[val_col]].sum(), height=350)
                    
                with g_col2:
                    st.markdown("**Chart B: Cumulative Cash Flow Trajectory**")
                    if date_col and date_col in df_results.columns:
                        df_line = df_results.copy()
                        df_line[date_col] = pd.to_datetime(df_line[date_col], errors='coerce')
                        df_line = df_line.sort_values(date_col)
                        df_line["rolling_balance"] = df_line[val_col].cumsum()
                        st.area_chart(df_line.groupby(date_col)[["rolling_balance"]].last(), height=350)
                    else:
                        df_results["rolling_balance"] = df_results[val_col].cumsum()
                        st.line_chart(df_results[["rolling_balance"]], height=350)
                
                st.markdown("### 📋 Filtered Ledger Transaction Grid Table")
                st.dataframe(df_results, use_container_width=True, hide_index=True, height=250)
            else:
                st.warning("⚠️ Relational query compiled successfully, but returned exactly 0 matching dataset records.")
        except Exception as e:
            st.error(f"Ledger Pipeline Processing Error: {e}")
