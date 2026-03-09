import sys
import os
import logging
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from snowflake.snowpark import Session
from openai import AzureOpenAI
from streamlit_option_menu import option_menu
from streamlit_extras.stylable_container import stylable_container

# ───────────────────────── Page Config & Branding ─────────────────────────
try:
    jade_logo = Image.open("logo/jadeglobalsmall.png")
except:
    jade_logo = None

st.set_page_config(
    page_title="FailGuardAI | Jade Global",
    page_icon=jade_logo,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Jade Global Standard Colors
JADE_BLUE = "#175388"  # Sidebar Inactive / Headers
JADE_GOLD = "#ecb713"  # Sidebar Active / Metrics

# ───────────────────────── Custom UI Styling ─────────────────────────
CUSTOM_CSS = f"""
<style>
    /* Global Container */
    .block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem !important; }}
    .stAppHeader {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}

    /* Sidebar Logo: Forced to 60% Width */
    [data-testid="stSidebar"] {{ background-color: #ffffff; }}
    [data-testid=stSidebar] [data-testid=stImage] img {{
        text-align: center; display: block; margin-left: auto; margin-right: auto; 
        width: 60% !important; height: auto;
    }}

    /* Sidebar Branding Text */
    .app-title {{
        text-align: center; color: {JADE_BLUE}; font-weight: bold;
        font-size: 22px; margin-top: -10px; margin-bottom: 0px;
    }}
    .app-subtitle {{
        text-align: center; color: {JADE_BLUE}; font-size: 14px; margin-bottom: 20px;
    }}

    /* Jade Standard Buttons */
    .stButton > button {{
        border-radius: 8px !important;
        border: 2px solid #144774 !important;
        background-color: {JADE_BLUE} !important;
        color: white !important;
        width: 100%;
        font-weight: 600;
        transition: 0.3s;
    }}
    .stButton > button:hover {{
        background-color: {JADE_GOLD} !important;
        border-color: #c49e10 !important;
        color: {JADE_BLUE} !important;
    }}

    /* AI Report styling */
    .report-view {{
        background-color: #ffffff; padding: 35px; border: 1px solid #e0e0e0;
        font-family: 'Georgia', serif; line-height: 1.6; color: #333;
        box-shadow: 2px 2px 15px rgba(0,0,0,0.05);
    }}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ───────────────────────── System Logic & Helpers ─────────────────────────

def get_snowflake_session():
    """Returns the Snowflake session from state or creates a new one."""
    try:
        if "snowflake_session" not in st.session_state:
            st.session_state.snowflake_session = Session.builder.configs(st.secrets["snowflake"]).create()
        return st.session_state.snowflake_session
    except Exception as e:
        st.error(f"Snowflake Connection Failed: Check secrets.toml")
        return None

@st.cache_data(ttl=600)
def fetch_data(query):
    """Queries Snowflake and caches results for 10 minutes."""
    session = get_snowflake_session()
    if session:
        try:
            return session.sql(query).to_pandas()
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def get_azure_ai_response(prompt):
    """Direct Azure OpenAI gpt-5-mini connection."""
    try:
        endpoint="https://elevaite-2026.cognitiveservices.azure.com/"
        model_name = "gpt-5-mini"
        deployment = "hackathon-model-grp-04"
        subscription_key = st.secrets["azure_openai_key"]
        api_version = "2024-02-01"

        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a Quality Engineering & Compliance AI for FailGuardAI."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=16384,
            model=deployment

        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI Connection Error: {str(e)}"

def run_system_check():
    """Diagnostic function to test connections."""
    status = {"snowflake": False, "azure": False}
    try:
        session = get_snowflake_session()
        if session and session.sql("SELECT 1").collect():
            status["snowflake"] = True
    except: pass
    try:
        client = AzureOpenAI(api_version="2024-02-01", 
                             azure_endpoint="https://elevaite-2026.cognitiveservices.azure.com/", 
                             api_key=st.secrets["azure_openai_key"])
        res = client.chat.completions.create(messages=[{"role":"user","content":"hi"}], 
                                            model="hackathon-model-grp-04", max_tokens=5)
        if res: status["azure"] = True
    except: pass
    return status

# ───────────────────────── UI Components ─────────────────────────

def render_banner(title, subtitle):
    banner_html = f"""
    <div style="padding: 25px; border-radius: 15px; background: linear-gradient(135deg, {JADE_BLUE} 0%, #2A7B9B 100%); text-align: center; margin-bottom: 2rem;">
        <div style="font-size: 32px; font-weight: bold; color: white;">{title}</div>
        <div style="font-size: 16px; color: #E0F7FA; margin-top: 8px;">{subtitle}</div>
    </div>
    """
    st.markdown(banner_html, unsafe_allow_html=True)

def render_metric(key, label, value):
    with stylable_container(key=key, css_styles="{background-color: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid #e6e6e6; text-align: left;}"):
        st.markdown(f"<p style='color: {JADE_BLUE}; font-size: 14px; text-transform: uppercase; font-weight: bold;'>{label}</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color: {JADE_GOLD}; margin: 0;'>{value}</h2>", unsafe_allow_html=True)

# ───────────────────────── Page Controllers ─────────────────────────

def page_dashboard(df_claims, df_batches, df_alerts):
    render_banner("FailGuardAI Operations Dashboard", "Real-time analytics and AI-powered insights across product reliability and warranty operations.")
    m1, m2, m3, m4 = st.columns(4)
    with m1: render_metric("m1", "Total Claims", f"{len(df_claims):,}")
    with m2: render_metric("m2", "Liability Exposure", f"${df_claims['REPAIR_COST'].sum()/1e6:.1f}M")
    with m3: render_metric("m3", "Critical Alerts", len(df_alerts))
    with m4: render_metric("m4", "Avg Field Life", f"{df_claims['DAYS_IN_FIELD'].mean():.0f} Days")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(df_claims, names='FAILURE_TYPE', title="Claims by Failure Category", hole=0.5, color_discrete_sequence=[JADE_BLUE, JADE_GOLD, "#2A7B9B"]), width='stretch')
    with c2:
        merged = df_claims.merge(df_batches, on='BATCH_ID')
        st.plotly_chart(px.bar(merged.groupby('PLANT_LOCATION')['REPAIR_COST'].sum().reset_index(), x='REPAIR_COST', y='PLANT_LOCATION', orientation='h', title="Liability by Manufacturing Plant", color_discrete_sequence=[JADE_BLUE]), width='stretch')

def page_risk_analysis(df_batches):
    render_banner("AI Root Cause Analysis", "Connecting manufacturing variances to field failure probability.")
    batch_id = st.selectbox("Select Batch ID for Technical Audit", df_batches['BATCH_ID'].unique())
    batch_data = df_batches[df_batches['BATCH_ID'] == batch_id].iloc[0]
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.subheader("Batch Profile")
        st.info(f"**Supplier:** {batch_data['SUPPLIER_NAME']}\n\n**QC Score:** {batch_data['QC_SENSITIVITY_SCORE']}")
        if st.button("Generate Technical Hypothesis"):
            with st.spinner("Azure gpt-5-mini analyzing patterns..."):
                prompt = f"Analyze Batch {batch_id} with QC score {batch_data['QC_SENSITIVITY_SCORE']}. Suggest specific engineering root causes."
                st.markdown(f'<div class="report-view">{get_azure_ai_response(prompt)}</div>', unsafe_allow_html=True)
    with col_b:
        risk = min(batch_data['QC_SENSITIVITY_SCORE'] * 20, 100)
        fig = go.Figure(go.Indicator(mode="gauge+number", value=risk, title={'text': "Predicted Failure Prob (%)"}, gauge={'bar': {'color': JADE_BLUE}, 'steps': [{'range': [0, 50], 'color': "lightgreen"}, {'range': [50, 100], 'color': JADE_GOLD}]}))
        st.plotly_chart(fig, width='stretch')

def page_recall_planner(df_alerts):
    render_banner("Recall Documentation AI", "Automated generation of safety notifications and customer compliance letters.")
    if df_alerts.empty:
        st.success("System Scan: No active critical alerts.")
    else:
        target = st.selectbox("Select Alert for Action", df_alerts['BATCH_ID'])
        if st.button("Draft Recall Notification"):
            with st.spinner("Drafting via Azure AI..."):
                doc = get_azure_ai_response(f"Draft a formal customer recall letter for Batch {target}.")
                st.markdown(f'<div class="report-view">{doc}</div>', unsafe_allow_html=True)

def page_supplier_scorecard(df_batches, df_alerts):
    render_banner("Supplier Quality Scorecard", "Ranking vendor reliability based on AI-predicted failure alerts and QC variances.")
    sup_risk = df_batches.merge(df_alerts, on='BATCH_ID', how='left').fillna(0)
    scorecard = sup_risk.groupby('SUPPLIER_NAME').agg({'BATCH_ID': 'count', 'PREDICTED_FAILURE_PROBABILITY': 'mean'}).reset_index()
    scorecard.columns = ['Supplier Name', 'Total Batches', 'Avg Risk Score']
    st.plotly_chart(px.bar(scorecard.sort_values('Avg Risk Score', ascending=False), x='Supplier Name', y='Avg Risk Score', color='Avg Risk Score', color_continuous_scale='Reds', title="Supplier Risk Ranking Index"), width='stretch')
    st.dataframe(scorecard, width='stretch', hide_index=True)

def page_compliance_checker(df_claims):
    render_banner("Regulatory Compliance AI", "Automated monitoring against mandatory 5% reporting thresholds.")
    stats = df_claims.groupby('BATCH_ID').size().reset_index(name='count')
    stats['rate'] = (stats['count'] / 1000) * 100
    st.plotly_chart(px.bar(stats, x='BATCH_ID', y='rate', color='rate', color_continuous_scale='Reds', title="Failure Rate (%) per Batch"), width='stretch')
    violations = stats[stats['rate'] > 5.0]
    if not violations.empty:
        st.error(f"🚨 Mandatory Reporting: {len(violations)} batches have exceeded the 5% threshold.")
        if st.button("Draft Government Safety Filing"):
            with st.spinner("Drafting Section 15 report..."):
                doc = get_azure_ai_response(f"Draft a Section 15 safety filing for Batch {violations.iloc[0]['BATCH_ID']}.")
                st.markdown(f'<div class="report-view">{doc}</div>', unsafe_allow_html=True)

# ───────────────────────── Main Execution ─────────────────────────
def main():
    with st.sidebar:
        try: st.image('logo/jadeglobal.png')
        except: st.markdown(f"<h2 style='text-align: center; color: {JADE_BLUE};'>JADE</h2>", unsafe_allow_html=True)
        
        st.markdown("<p class='app-title'>FailGuardAI</p>", unsafe_allow_html=True)
        st.markdown("<p class='app-subtitle'>Predictive Quality Platform</p>", unsafe_allow_html=True)
        
        page = option_menu(
            menu_title=None,
            options=['Dashboard', 'Risk Analysis', 'Recall Planner', 'Supplier Scorecard', 'Compliance Checker', 'Settings'],
            icons=['speedometer2', 'search', 'file-text', 'people', 'shield-check', 'gear'],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "nav-link": {"font-size": "15px", "text-align": "left", "color": "#ffffff", "background-color": JADE_BLUE, "margin": "5px 0", "border-radius": "8px"},
                "nav-link-selected": {"background-color": JADE_GOLD, "color": JADE_BLUE, "font-weight": "bold"}
            }
        )
        st.divider()
        st.caption("Infrastructure: Snowflake | Azure OpenAI")

    try:
        df_batches = fetch_data("SELECT * FROM MANUFACTURING_DATA")
        df_claims = fetch_data("SELECT * FROM FIELD_CLAIMS")
        df_alerts = fetch_data("SELECT * FROM RISK_ALERTS")

        if page == 'Dashboard': page_dashboard(df_claims, df_batches, df_alerts)
        elif page == 'Risk Analysis': page_risk_analysis(df_batches)
        elif page == 'Recall Planner': page_recall_planner(df_alerts)
        elif page == 'Supplier Scorecard': page_supplier_scorecard(df_batches, df_alerts)
        elif page == 'Compliance Checker': page_compliance_checker(df_claims)
        elif page == 'Settings':
            render_banner("⚙️ System Health Check", "Verify connectivity to Snowflake and Azure AI services.")
            if st.button("Run Connection Diagnostics"):
                results = run_system_check()
                st.success("Snowflake: CONNECTED") if results['snowflake'] else st.error("Snowflake: DISCONNECTED")
                st.success("Azure AI: CONNECTED") if results['azure'] else st.error("Azure AI: DISCONNECTED")
            
    except Exception as e:
        st.error(f"Critical System Error: {e}")

if __name__ == "__main__":
    main()