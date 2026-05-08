import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(
    page_title="Walmart | BI Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Typography ── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', wf_segoe-ui_normal, helvetica, arial, sans-serif !important;
}

/* ── Canvas ── */
.main .block-container { background: #F3F3F3; padding-top: 0.6rem; max-width: 100%; }
.stApp { background: #F3F3F3; }

/* ── Column shadows escape parent ── */
[data-testid="stHorizontalBlock"] { overflow: visible !important; align-items: stretch !important; }

/* ── Power BI tile ── */
section.main div[data-testid="column"] {
    background: white !important;
    border-radius: 3px !important;
    box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.132), 0 0.3px 0.9px rgba(0,0,0,0.108) !important;
    overflow: hidden !important;
}

/* ── Sidebar — PBI Filter Pane ── */
[data-testid="stSidebar"] { background: #FAFAFA !important; border-right: 1px solid #EDEBE9 !important; }
[data-testid="stSidebar"] * { color: #323130 !important; }
[data-testid="stSidebar"] hr { border-color: #EDEBE9 !important; }
[data-testid="stSidebar"] [data-testid="stMultiSelect"] > div > div {
    background: white !important; border: 1px solid #8A8886 !important; border-radius: 2px !important;
}
[data-testid="stSidebar"] label { font-size: 11px !important; font-weight: 600 !important; }

/* ── Visual title bar ── */
.section-header {
    font-size: 11.5px; font-weight: 600; color: #252423;
    padding: 11px 14px 9px 14px; margin: 0;
    border-bottom: 1px solid #F0F0F0; display: block;
}

/* ── KPI internals ── */
.kpi-value  { font-size: 2rem; font-weight: 700; color: #252423; line-height: 1.2; padding: 6px 14px 2px 14px; }
.kpi-sub    { font-size: 11px; padding: 0 14px 4px 14px; color: #107C10; }
.kpi-sub.warn    { color: #D64550 !important; }
.kpi-sub.neutral { color: #605E5C !important; }

/* ── KPI goal progress bar ── */
.kpi-bar-track {
    height: 3px; background: #EDEBE9; border-radius: 2px;
    margin: 6px 14px 10px 14px; overflow: hidden;
}
.kpi-bar-fill { height: 3px; border-radius: 2px; }

/* ── Active-filter chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.filter-chip {
    background: #EEF3FB; color: #0F6CBD; border: 1px solid #B4D0F7;
    border-radius: 16px; padding: 3px 10px;
    font-size: 10.5px; font-weight: 600; display: inline-block;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    here = os.path.dirname(os.path.abspath(__file__))
    walmart_dir = os.path.join(here, 'walmart')
    
    # Load the three CSV files
    train_df = pd.read_csv(os.path.join(walmart_dir, 'train.csv'))
    stores_df = pd.read_csv(os.path.join(walmart_dir, 'stores.csv'))
    features_df = pd.read_csv(os.path.join(walmart_dir, 'features.csv'))
    
    # Convert Date columns to datetime
    train_df['Date'] = pd.to_datetime(train_df['Date'])
    features_df['Date'] = pd.to_datetime(features_df['Date'])
    
    # Merge train with stores info
    df = train_df.merge(stores_df[['Store', 'Type', 'Size']], on='Store', how='left')
    
    # Merge with features
    df = df.merge(
        features_df[['Store', 'Date', 'Temperature', 'Fuel_Price', 'CPI', 'Unemployment']],
        on=['Store', 'Date'],
        how='left'
    )
    
    # Extract year, month for grouping
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Month_Name'] = df['Date'].dt.strftime('%B')
    df['Week'] = df['Date'].dt.isocalendar().week
    
    # Create Department labels
    df['Dept_Label'] = 'Dept ' + df['Dept'].astype(str).str.zfill(2)
    df['Store_Label'] = 'Store ' + df['Store'].astype(str).str.zfill(2)
    
    # Fill NaN values in features
    df['Temperature'] = df['Temperature'].fillna(df['Temperature'].mean())
    df['Fuel_Price'] = df['Fuel_Price'].fillna(df['Fuel_Price'].mean())
    df['CPI'] = df['CPI'].fillna(df['CPI'].mean())
    df['Unemployment'] = df['Unemployment'].fillna(df['Unemployment'].mean())
    
    return df

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:#F3F2F1; margin:-1rem -1rem 1rem -1rem;
                padding:12px 16px; border-bottom:1px solid #EDEBE9;">
      <div style="display:flex; align-items:center; gap:8px;">
        <div style="background:#0071C5; color:white; font-weight:800; font-size:10px;
                    padding:2px 7px; border-radius:2px; font-family:Arial; letter-spacing:0.5px;">
          WALMART</div>
        <div style="font-size:12px; font-weight:600; color:#323130; font-family:'Segoe UI';">Filters</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    years_all   = sorted(df['Year'].unique())
    years_sel   = st.multiselect("Year",     years_all,                    default=years_all)
    stores_all  = sorted(df['Store'].unique())
    stores_sel  = st.multiselect("Store",    stores_all,                   default=stores_all)
    types_all   = sorted(df['Type'].unique())
    types_sel   = st.multiselect("Store Type", types_all,                   default=types_all)
    depts_all   = sorted(df['Dept'].unique())
    depts_sel   = st.multiselect("Department", depts_all,                  default=depts_all)

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:10px; color:#A19F9D; font-family:'Segoe UI';">
      Source: Kaggle Walmart Dataset<br/>{len(df):,} transactions · {df['Year'].min():.0f}–{df['Year'].max():.0f}
    </div>
    """, unsafe_allow_html=True)

# ── Filter ────────────────────────────────────────────────────────────────────
dff = df[
    df['Year'].isin(years_sel) &
    df['Store'].isin(stores_sel) &
    df['Type'].isin(types_sel) &
    df['Dept'].isin(depts_sel)
]

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_sales   = dff['Weekly_Sales'].sum()
total_holidays = dff['IsHoliday'].sum()
avg_weekly    = dff.groupby(['Store', 'Dept', 'Date'])['Weekly_Sales'].sum().mean()
avg_temp      = dff['Temperature'].mean()

all_sales  = df['Weekly_Sales'].sum()
all_holidays = df['IsHoliday'].sum()

sales_bar     = total_sales / all_sales * 100 if all_sales else 0
holiday_bar   = total_holidays / all_holidays * 100 if all_holidays else 0
temp_bar      = max(0, min(avg_temp / 80 * 100, 100))
dept_bar      = len(depts_sel) / len(depts_all) * 100

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#1B2A4A; padding:11px 18px; border-radius:3px; margin-bottom:10px;
            display:flex; align-items:center; justify-content:space-between;
            box-shadow:0 1.6px 3.6px rgba(0,0,0,0.18);">
  <div style="display:flex; align-items:center; gap:14px;">
    <div style="background:#0071C5; color:white; font-weight:800; font-size:11px;
                padding:3px 8px; border-radius:2px; font-family:Arial; letter-spacing:0.5px;">
      WALMART</div>
    <div>
      <div style="font-size:14px; font-weight:600; color:white; font-family:'Segoe UI'; line-height:1.3;">
        Store Performance Dashboard
      </div>
      <div style="font-size:10px; color:#9BA8B8; margin-top:2px; font-family:'Segoe UI';">
        Sales Intelligence · Store &amp; Department Analytics · Kaggle Walmart Dataset
      </div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:11px; color:#5BA4E5; font-weight:600; font-family:'Segoe UI';">{len(dff):,} records</div>
    <div style="font-size:10px; color:#9BA8B8; font-family:'Segoe UI';">{len(stores_sel)} store(s) · {len(depts_sel)} dept(s)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Active filter chips ───────────────────────────────────────────────────────
chips = []
if set(years_sel) != set(years_all):
    label = ", ".join(str(y) for y in years_sel) if len(years_sel) <= 2 else f"{len(years_sel)} of {len(years_all)} selected"
    chips.append(f'<span class="filter-chip">Year: {label}</span>')
if set(stores_sel) != set(stores_all):
    label = f"{len(stores_sel)} of {len(stores_all)} selected" if len(stores_sel) > 2 else ", ".join(str(s) for s in stores_sel)
    chips.append(f'<span class="filter-chip">Store: {label}</span>')
if set(types_sel) != set(types_all):
    chips.append(f'<span class="filter-chip">Type: {", ".join(types_sel)}</span>')
if chips:
    st.markdown(f'<div class="chip-row">{"".join(chips)}</div>', unsafe_allow_html=True)

# ── KPI row — 4 white tiles with goal progress bars ───────────────────────────
kc = st.columns(4, gap='small')

with kc[0]:
    st.markdown(f"""
    <div class="section-header">Total Sales</div>
    <div class="kpi-value">${total_sales / 1e6:.2f}M</div>
    <div class="kpi-sub neutral">All Stores & Depts</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{sales_bar:.0f}%; background:#0071C5;"></div>
    </div>
    """, unsafe_allow_html=True)

with kc[1]:
    st.markdown(f"""
    <div class="section-header">Avg Weekly Sales</div>
    <div class="kpi-value">${avg_weekly:,.0f}</div>
    <div class="kpi-sub neutral">Per Store-Dept-Week</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:100%; background:#107C10;"></div>
    </div>
    """, unsafe_allow_html=True)

with kc[2]:
    st.markdown(f"""
    <div class="section-header">Holiday Records</div>
    <div class="kpi-value">{total_holidays:,}</div>
    <div class="kpi-sub neutral">Peak Sales Weeks</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{holiday_bar:.0f}%; background:#FFB900;"></div>
    </div>
    """, unsafe_allow_html=True)

with kc[3]:
    st.markdown(f"""
    <div class="section-header">Avg Temperature</div>
    <div class="kpi-value">{avg_temp:.1f}°F</div>
    <div class="kpi-sub neutral">Regional Average</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{temp_bar:.0f}%; background:#E81123;"></div>
    </div>
    """, unsafe_allow_html=True)


# ── Chart helpers ─────────────────────────────────────────────────────────────
def pbi_layout(fig, h=300):
    fig.update_layout(
        paper_bgcolor='white', plot_bgcolor='white', height=h,
        font=dict(family='Segoe UI, wf_segoe-ui_normal, helvetica, arial', size=11, color='#252423'),
        margin=dict(l=10, r=10, t=8, b=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    font=dict(size=10), bgcolor='rgba(0,0,0,0)', borderwidth=0),
        hoverlabel=dict(bgcolor='white', bordercolor='#EDEBE9', font_size=11, font_family='Segoe UI'),
    )
    fig.update_xaxes(gridcolor='#F0F0F0', gridwidth=1, showline=False, zeroline=False,
                     tickfont=dict(size=10, color='#605E5C'), title_font=dict(size=10, color='#605E5C'))
    fig.update_yaxes(gridcolor='#F0F0F0', gridwidth=1, showline=False, zeroline=False,
                     tickfont=dict(size=10, color='#605E5C'), title_font=dict(size=10, color='#605E5C'))
    return fig


PBI_COLORS = ['#0071C5', '#107C10', '#FFB900', '#E81123',
              '#744EC2', '#E74856', '#008272', '#5B2D91', '#00B7C3', '#5B4B8A']


# ── ROW 1: Weekly Trend + Temperature Correlation ────────────────────────────
col1, col2 = st.columns([1.1, 1], gap='small')

with col1:
    st.markdown('<div class="section-header">Weekly Sales Trend by Holiday</div>',
                unsafe_allow_html=True)
    trend = dff.groupby('Date').agg(
        Sales_Holiday=('Weekly_Sales', lambda x: x[dff.loc[x.index, 'IsHoliday'] == True].sum()),
        Sales_Regular=('Weekly_Sales', lambda x: x[dff.loc[x.index, 'IsHoliday'] == False].sum())
    ).reset_index()
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=trend['Date'], y=trend['Sales_Regular'],
        name='Regular Week', fill='tozeroy', line=dict(color='#0071C5', width=2),
        fillcolor='rgba(0, 113, 197, 0.1)'))
    fig_trend.add_trace(go.Scatter(x=trend['Date'], y=trend['Sales_Holiday'],
        name='Holiday Week', line=dict(color='#FFB900', width=2.5)))
    
    pbi_layout(fig_trend, h=310)
    fig_trend.update_layout(
        xaxis_title='Date', yaxis_title='Total Sales ($)',
        yaxis=dict(tickprefix='$'))
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown('<div class="section-header">Temperature vs Sales</div>',
                unsafe_allow_html=True)
    temp_sales = dff.groupby('Date').agg(
        Temp=('Temperature', 'mean'),
        Sales=('Weekly_Sales', 'sum')
    ).reset_index()
    
    fig_temp = px.scatter(temp_sales, x='Temp', y='Sales',
        trendline='lowess', trendline_color_override='#E81123',
        labels={'Temp': 'Temperature (°F)', 'Sales': 'Weekly Sales ($)'})
    fig_temp.update_traces(marker=dict(color='#0071C5', size=5, opacity=0.6))
    pbi_layout(fig_temp, h=310)
    fig_temp.update_layout(yaxis=dict(tickprefix='$'))
    st.plotly_chart(fig_temp, use_container_width=True, config={'displayModeBar': False})


# ── ROW 2: Top Stores + Top Departments ───────────────────────────────────────
col3, col4 = st.columns(2, gap='small')

with col3:
    st.markdown('<div class="section-header">Top 10 Stores by Total Sales</div>',
                unsafe_allow_html=True)
    top_stores = dff.groupby(['Store', 'Store_Label'])['Weekly_Sales'].sum().nlargest(10).reset_index()
    top_stores = top_stores.sort_values('Weekly_Sales')
    
    fig_stores = go.Figure(go.Bar(
        x=top_stores['Weekly_Sales'], y=top_stores['Store_Label'],
        orientation='h', marker_color='#0071C5',
        text=[f'${v/1e6:.1f}M' for v in top_stores['Weekly_Sales']],
        textfont=dict(size=9), textposition='outside'))
    
    pbi_layout(fig_stores, h=310)
    fig_stores.update_layout(
        xaxis_title='Total Sales ($)',
        xaxis=dict(tickprefix='$'),
        yaxis=dict(tickfont=dict(size=10)),
        showlegend=False)
    st.plotly_chart(fig_stores, use_container_width=True, config={'displayModeBar': False})

with col4:
    st.markdown('<div class="section-header">Top 10 Departments by Avg Sales</div>',
                unsafe_allow_html=True)
    top_depts = dff.groupby(['Dept', 'Dept_Label'])['Weekly_Sales'].mean().nlargest(10).reset_index()
    top_depts = top_depts.sort_values('Weekly_Sales')
    
    fig_depts = go.Figure(go.Bar(
        x=top_depts['Weekly_Sales'], y=top_depts['Dept_Label'],
        orientation='h', marker_color='#107C10',
        text=[f'${v:,.0f}' for v in top_depts['Weekly_Sales']],
        textfont=dict(size=9), textposition='outside'))
    
    pbi_layout(fig_depts, h=310)
    fig_depts.update_layout(
        xaxis_title='Avg Weekly Sales ($)',
        xaxis=dict(tickprefix='$'),
        yaxis=dict(tickfont=dict(size=10)),
        showlegend=False)
    st.plotly_chart(fig_depts, use_container_width=True, config={'displayModeBar': False})


# ── ROW 3: Sales Distribution by Store Type + CPI vs Unemployment ──────────────
col5, col6 = st.columns(2, gap='small')

with col5:
    st.markdown('<div class="section-header">Sales Distribution by Store Type</div>',
                unsafe_allow_html=True)
    type_sales = dff.groupby('Type').agg(
        Total_Sales=('Weekly_Sales', 'sum'),
        Count=('Store', 'nunique')
    ).reset_index().sort_values('Total_Sales', ascending=False)
    
    colors = PBI_COLORS[:len(type_sales)]
    fig_types = go.Figure(go.Pie(
        labels=type_sales['Type'],
        values=type_sales['Total_Sales'],
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont=dict(size=10)))
    
    pbi_layout(fig_types, h=300)
    fig_types.update_layout(showlegend=True)
    st.plotly_chart(fig_types, use_container_width=True, config={'displayModeBar': False})

with col6:
    st.markdown('<div class="section-header">CPI vs Unemployment Correlation</div>',
                unsafe_allow_html=True)
    macro = dff.groupby('Date').agg(
        CPI=('CPI', 'mean'),
        Unemployment=('Unemployment', 'mean'),
        Sales=('Weekly_Sales', 'sum')
    ).reset_index()
    
    fig_macro = go.Figure()
    fig_macro.add_trace(go.Scatter(x=macro['Date'], y=macro['CPI'],
        name='CPI', line=dict(color='#0071C5', width=2), yaxis='y'))
    fig_macro.add_trace(go.Scatter(x=macro['Date'], y=macro['Unemployment'],
        name='Unemployment %', line=dict(color='#E81123', width=2), yaxis='y2'))
    
    fig_macro.update_layout(
        yaxis=dict(title='CPI', gridcolor='#F0F0F0'),
        yaxis2=dict(title='Unemployment %', overlaying='y', side='right'),
        paper_bgcolor='white', plot_bgcolor='white', height=300,
        font=dict(family='Segoe UI', size=11, color='#252423'),
        margin=dict(l=10, r=50, t=8, b=10),
        legend=dict(orientation='h', y=1.08, font=dict(size=10)),
        hovermode='x unified')
    pbi_layout(fig_macro, h=300)
    st.plotly_chart(fig_macro, use_container_width=True, config={'displayModeBar': False})


# ── ROW 4: Monthly Sales Heatmap + Fuel Price Trend ──────────────────────────
col7, col8 = st.columns([1.1, 1], gap='small')

with col7:
    st.markdown('<div class="section-header">Sales Heatmap: Month vs Year</div>',
                unsafe_allow_html=True)
    heatmap_data = dff.groupby(['Month_Name', 'Year'])['Weekly_Sales'].sum().reset_index()
    heatmap_pivot = heatmap_data.pivot(index='Month_Name', columns='Year', values='Weekly_Sales')
    
    # Order months correctly
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    heatmap_pivot = heatmap_pivot.reindex([m for m in month_order if m in heatmap_pivot.index])
    
    fig_heatmap = px.imshow(heatmap_pivot,
        color_continuous_scale='Blues',
        labels=dict(value='Total Sales ($)'),
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index)
    fig_heatmap.update_layout(
        xaxis_title='Year', yaxis_title='Month',
        coloraxis_colorbar_title='Sales ($)')
    pbi_layout(fig_heatmap, h=310)
    st.plotly_chart(fig_heatmap, use_container_width=True, config={'displayModeBar': False})

with col8:
    st.markdown('<div class="section-header">Fuel Price Trend</div>',
                unsafe_allow_html=True)
    fuel_trend = dff.groupby('Date')['Fuel_Price'].mean().reset_index()
    
    fig_fuel = go.Figure(go.Scatter(x=fuel_trend['Date'], y=fuel_trend['Fuel_Price'],
        fill='tozeroy', line=dict(color='#FFB900', width=2.5),
        fillcolor='rgba(255, 185, 0, 0.2)',
        name='Fuel Price'))
    
    pbi_layout(fig_fuel, h=310)
    fig_fuel.update_layout(
        yaxis_title='Fuel Price ($/gal)',
        xaxis_title='Date')
    st.plotly_chart(fig_fuel, use_container_width=True, config={'displayModeBar': False})


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#A19F9D; font-size:0.7rem; margin-top:8px; padding:8px;">
  Walmart Store Performance Dashboard · Sales & Operations Intelligence · Data: Kaggle Walmart Dataset
</div>
""", unsafe_allow_html=True)
