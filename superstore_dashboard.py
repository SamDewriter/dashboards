import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

st.set_page_config(
    page_title="Superstore | BI Dashboard",
    page_icon="🏪",
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

/* ── KPI goal bar ── */
.kpi-bar-track { height: 3px; background: #EDEBE9; border-radius: 2px; margin: 6px 14px 10px 14px; overflow: hidden; }
.kpi-bar-fill  { height: 3px; border-radius: 2px; }

/* ── Filter chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.filter-chip {
    background: #EEF3FB; color: #0F6CBD; border: 1px solid #B4D0F7;
    border-radius: 16px; padding: 3px 10px; font-size: 10.5px; font-weight: 600; display: inline-block;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────
US_STATES = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','District of Columbia':'DC',
    'Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL',
    'Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
    'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN',
    'Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
    'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY',
    'North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR',
    'Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',
    'Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA',
    'Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
}

CAT_COLORS = {
    'Technology':      '#118DFF',
    'Furniture':       '#D64550',
    'Office Supplies': '#107C10',
}

PBI_COLORS = ['#118DFF','#E66C37','#107C10','#D64550',
              '#744EC2','#D9B300','#E044A7','#12239E','#00B7C3','#8764B8']


@st.cache_data
def load_data():
    here = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(here, 'Sample - Superstore.csv'), encoding='latin-1')

    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%m/%d/%Y')
    df['Year']  = df['Order Date'].dt.year
    df['Month'] = df['Order Date'].dt.to_period('M').astype(str)

    df['Discount_Pct']  = (df['Discount'] * 100).round(1)
    df['Profit_Margin'] = np.where(df['Sales'] > 0, df['Profit'] / df['Sales'] * 100, 0)

    def disc_band(d):
        if d <= 0:    return 'No Discount'
        elif d <= 10: return '1–10%'
        elif d <= 20: return '11–20%'
        elif d <= 40: return '21–40%'
        return '41%+'
    df['Discount_Band'] = df['Discount_Pct'].apply(disc_band)
    return df


df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:#F3F2F1; margin:-1rem -1rem 1rem -1rem;
                padding:12px 16px; border-bottom:1px solid #EDEBE9;">
      <div style="display:flex; align-items:center; gap:8px;">
        <div style="background:#1B2A4A; color:white; font-weight:800; font-size:10px;
                    padding:2px 7px; border-radius:2px; font-family:Arial; letter-spacing:0.5px;">
          SUPERSTORE</div>
        <div style="font-size:12px; font-weight:600; color:#323130; font-family:'Segoe UI';">Filters</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    years_all   = sorted(df['Year'].unique())
    years_sel   = st.multiselect("Year",     years_all,                    default=years_all)
    regions_all = sorted(df['Region'].unique())
    regions_sel = st.multiselect("Region",   regions_all,                  default=regions_all)
    segs_all    = sorted(df['Segment'].unique())
    segs_sel    = st.multiselect("Segment",  segs_all,                     default=segs_all)
    cats_all    = sorted(df['Category'].unique())
    cats_sel    = st.multiselect("Category", cats_all,                     default=cats_all)

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:10px; color:#A19F9D; font-family:'Segoe UI';">
      Source: Kaggle Superstore Dataset<br/>{len(df):,} transactions · 2014–2017
    </div>
    """, unsafe_allow_html=True)

# ── Filter ────────────────────────────────────────────────────────────────────
dff = df[
    df['Year'].isin(years_sel) &
    df['Region'].isin(regions_sel) &
    df['Segment'].isin(segs_sel) &
    df['Category'].isin(cats_sel)
]

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_sales   = dff['Sales'].sum()
total_profit  = dff['Profit'].sum()
margin_pct    = total_profit / total_sales * 100 if total_sales else 0
total_orders  = len(dff)
avg_order_val = total_sales / total_orders if total_orders else 0

all_sales  = df['Sales'].sum()
all_profit = df['Profit'].sum()

sales_bar   = total_sales  / all_sales  * 100 if all_sales  else 0
profit_bar  = max(0, min(total_profit / all_profit * 100, 100)) if all_profit > 0 else 0
margin_bar  = max(0, min(margin_pct / 15.0 * 100, 100))
orders_bar  = total_orders / len(df) * 100

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#1B2A4A; padding:11px 18px; border-radius:3px; margin-bottom:10px;
            display:flex; align-items:center; justify-content:space-between;
            box-shadow:0 1.6px 3.6px rgba(0,0,0,0.18);">
  <div style="display:flex; align-items:center; gap:14px;">
    <div style="background:#2E75B6; color:white; font-weight:800; font-size:11px;
                padding:3px 8px; border-radius:2px; font-family:Arial; letter-spacing:0.5px;">
      SUPERSTORE</div>
    <div>
      <div style="font-size:14px; font-weight:600; color:white; font-family:'Segoe UI'; line-height:1.3;">
        Global Performance Dashboard
      </div>
      <div style="font-size:10px; color:#9BA8B8; margin-top:2px; font-family:'Segoe UI';">
        Commercial Health · Geographic &amp; Category Intelligence · Kaggle Superstore Dataset
      </div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:11px; color:#5BA4E5; font-weight:600; font-family:'Segoe UI';">{total_orders:,} orders</div>
    <div style="font-size:10px; color:#9BA8B8; font-family:'Segoe UI';">{len(years_sel)} year(s) · {len(regions_sel)} region(s)</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Active filter chips ───────────────────────────────────────────────────────
chips = []
if set(years_sel)   != set(years_all):
    chips.append(f'<span class="filter-chip">Year: {", ".join(map(str, sorted(years_sel)))}</span>')
if set(regions_sel) != set(regions_all):
    chips.append(f'<span class="filter-chip">Region: {", ".join(sorted(regions_sel))}</span>')
if set(segs_sel)    != set(segs_all):
    chips.append(f'<span class="filter-chip">Segment: {", ".join(sorted(segs_sel))}</span>')
if set(cats_sel)    != set(cats_all):
    chips.append(f'<span class="filter-chip">Category: {", ".join(sorted(cats_sel))}</span>')
if chips:
    st.markdown(f'<div class="chip-row">{"".join(chips)}</div>', unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
kc = st.columns(4, gap='small')

with kc[0]:
    st.markdown(f"""
    <div class="section-header">Total Sales</div>
    <div class="kpi-value">${total_sales:,.0f}</div>
    <div class="kpi-sub neutral">Avg ${avg_order_val:,.0f} / order</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{sales_bar:.0f}%; background:#118DFF;"></div>
    </div>""", unsafe_allow_html=True)

with kc[1]:
    p_cls = '' if total_profit >= 0 else 'warn'
    st.markdown(f"""
    <div class="section-header">Total Profit</div>
    <div class="kpi-value">${total_profit:,.0f}</div>
    <div class="kpi-sub {p_cls}">{'▲' if total_profit >= 0 else '▼'} {abs(margin_pct):.1f}% margin</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{profit_bar:.0f}%; background:#107C10;"></div>
    </div>""", unsafe_allow_html=True)

with kc[2]:
    m_cls = 'warn' if margin_pct < 12 else ''
    m_txt = '▼ Below 12% threshold' if margin_pct < 12 else '▲ Above 12% threshold'
    st.markdown(f"""
    <div class="section-header">Profit Margin</div>
    <div class="kpi-value">{margin_pct:.1f}%</div>
    <div class="kpi-sub {m_cls}">{m_txt}</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{margin_bar:.0f}%; background:#E66C37;"></div>
    </div>""", unsafe_allow_html=True)

with kc[3]:
    st.markdown(f"""
    <div class="section-header">Total Orders</div>
    <div class="kpi-value">{total_orders:,}</div>
    <div class="kpi-sub neutral">of {len(df):,} total transactions</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{orders_bar:.0f}%; background:#744EC2;"></div>
    </div>""", unsafe_allow_html=True)


# ── Chart helper ──────────────────────────────────────────────────────────────
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


# ── ROW 1: Choropleth map + Sub-Category Sales vs Profit ──────────────────────
col1, col2 = st.columns([1.25, 1], gap='small')

with col1:
    st.markdown('<div class="section-header">Sales by US State</div>', unsafe_allow_html=True)
    state_df = dff.groupby('State', as_index=False).agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum'), Orders=('Sales', 'count')
    )
    state_df['Code']   = state_df['State'].map(US_STATES)
    state_df['Margin'] = (state_df['Profit'] / state_df['Sales'] * 100).round(1)
    fig_map = px.choropleth(
        state_df.dropna(subset=['Code']),
        locations='Code', locationmode='USA-states',
        color='Sales',
        color_continuous_scale=[[0, '#D6E8F7'], [0.5, '#2E75B6'], [1, '#1B2A4A']],
        scope='usa', hover_name='State',
        hover_data={'Sales': ':$,.0f', 'Profit': ':$,.0f', 'Margin': ':.1f', 'Code': False},
    )
    fig_map.update_layout(
        paper_bgcolor='white', geo_bgcolor='white',
        geo=dict(showlakes=False, showframe=False, bgcolor='white', lakecolor='white'),
        coloraxis_colorbar=dict(title='Sales ($)', tickprefix='$', tickfont=dict(size=9), thickness=10),
        height=295, margin=dict(l=0, r=0, t=4, b=0),
        font=dict(family='Segoe UI'),
    )
    st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown('<div class="section-header">Sub-Category Sales vs Profit</div>', unsafe_allow_html=True)
    sc = dff.groupby(['Sub-Category', 'Category'], as_index=False).agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum'), Orders=('Sales', 'count')
    )
    fig_sc = px.scatter(
        sc, x='Sales', y='Profit', color='Category', text='Sub-Category',
        color_discrete_map=CAT_COLORS, size='Orders', size_max=26,
        hover_data={'Sales': ':$,.0f', 'Profit': ':$,.0f', 'Orders': True},
        labels={'Sales': 'Total Sales ($)', 'Profit': 'Total Profit ($)'},
    )
    fig_sc.update_traces(textposition='top center', textfont=dict(size=8, color='#252423'),
                         marker=dict(opacity=0.85, line=dict(width=1, color='white')))
    fig_sc.add_hline(y=0, line_dash='dot', line_color='#D64550', line_width=1.5,
                     annotation_text='Break-even', annotation_font_size=9,
                     annotation_font_color='#D64550')
    fig_sc.add_vline(x=sc['Sales'].median(), line_dash='dot', line_color='#605E5C',
                     line_width=1, opacity=0.5)
    pbi_layout(fig_sc, h=295)
    fig_sc.update_layout(
        xaxis=dict(tickprefix='$', tickformat=',.0f'),
        yaxis=dict(tickprefix='$', tickformat=',.0f'),
    )
    st.plotly_chart(fig_sc, use_container_width=True, config={'displayModeBar': False})

# ── ROW 2: Waterfall + Discount vs Profit Margin ──────────────────────────────
col3, col4 = st.columns(2, gap='small')

with col3:
    st.markdown('<div class="section-header">Profit Contribution by Category</div>', unsafe_allow_html=True)
    cat_p = dff.groupby('Category')['Profit'].sum().sort_values(ascending=False)
    wf_x   = list(cat_p.index) + ['Net Total']
    wf_y   = list(cat_p.values) + [cat_p.sum()]
    wf_m   = ['relative'] * len(cat_p) + ['total']
    wf_txt = [f'${v:,.0f}' for v in wf_y]
    fig_wf = go.Figure(go.Waterfall(
        measure=wf_m, x=wf_x, y=wf_y,
        connector=dict(line=dict(color='#E0E0E0', width=1, dash='dot')),
        increasing=dict(marker=dict(color='#107C10')),
        decreasing=dict(marker=dict(color='#D64550')),
        totals=dict(marker=dict(color='#118DFF')),
        text=wf_txt, textposition='outside', textfont=dict(size=10),
        hovertemplate='<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>',
    ))
    pbi_layout(fig_wf, h=295)
    fig_wf.update_layout(
        showlegend=False,
        yaxis=dict(tickprefix='$', tickformat=',.0f', title='Profit ($)'),
    )
    st.plotly_chart(fig_wf, use_container_width=True, config={'displayModeBar': False})

with col4:
    st.markdown('<div class="section-header">Discount Rate vs Profit Margin</div>', unsafe_allow_html=True)
    sample = dff.sample(min(1500, len(dff)), random_state=42).copy()
    sample = sample[sample['Sales'] > 0].copy()
    sample['PM'] = sample['Profit'] / sample['Sales'] * 100
    fig_disc = px.scatter(
        sample, x='Discount_Pct', y='PM', color='Category',
        color_discrete_map=CAT_COLORS, opacity=0.45, trendline='lowess',
        labels={'Discount_Pct': 'Discount (%)', 'PM': 'Profit Margin (%)'},
        hover_data={'Sales': ':$,.0f'},
    )
    fig_disc.add_hline(y=0, line_dash='solid', line_color='#D64550', line_width=1.5,
                       annotation_text='Break-even', annotation_font_size=9,
                       annotation_font_color='#D64550')
    pbi_layout(fig_disc, h=295)
    fig_disc.update_layout(yaxis=dict(title='Profit Margin (%)'))
    st.plotly_chart(fig_disc, use_container_width=True, config={'displayModeBar': False})

# ── ROW 3: Key Influencers + Decomposition Tree (Icicle) ─────────────────────
col5, col6 = st.columns(2, gap='small')

with col5:
    st.markdown('<div class="section-header">Key Influencers — Predictors of High Profit</div>',
                unsafe_allow_html=True)
    global_mean_p = dff['Profit'].mean() if len(dff) else 0
    records = []
    dim_cfg = {
        'Category':      ('■', cats_all,     'Category',     'Cat'),
        'Region':        ('▲', regions_all,  'Region',       'Region'),
        'Segment':       ('●', segs_all,     'Segment',      'Segment'),
        'Discount Band': ('◆', ['No Discount','1–10%','11–20%','21–40%','41%+'],
                          'Discount_Band', 'Disc'),
    }
    for dim, (sym, vals, col_name, prefix) in dim_cfg.items():
        for val in vals:
            sub = dff[dff[col_name] == val]
            if len(sub) >= 5:
                records.append({
                    'Label': f'{sym} {prefix}: {val}',
                    'Avg':   sub['Profit'].mean(),
                    'Count': len(sub),
                    'Delta': sub['Profit'].mean() - global_mean_p,
                })

    if records:
        inf_df = pd.DataFrame(records).sort_values('Delta')
        inf_df = pd.concat([inf_df.head(5), inf_df.tail(5)]).drop_duplicates().sort_values('Delta')
        inf_colors = ['#107C10' if d >= 0 else '#D64550' for d in inf_df['Delta']]
        fig_inf = go.Figure(go.Bar(
            x=inf_df['Delta'], y=inf_df['Label'], orientation='h',
            marker_color=inf_colors,
            text=[f'${d:+,.0f}' for d in inf_df['Delta']],
            textfont=dict(size=9.5), textposition='outside',
            customdata=np.stack([inf_df['Avg'], inf_df['Count']], axis=1),
            hovertemplate=(
                '<b>%{y}</b><br>Avg Profit/order: $%{customdata[0]:,.0f}<br>'
                'Orders: %{customdata[1]:,}<br>vs mean: $%{x:+,.0f}<extra></extra>'
            ),
        ))
        fig_inf.add_vline(x=0, line_color='#323130', line_width=1.2)
        pbi_layout(fig_inf, h=295)
        fig_inf.update_layout(
            showlegend=False,
            xaxis=dict(tickprefix='$', tickformat='+,.0f', title='Profit delta vs global mean ($/order)'),
            yaxis=dict(tickfont=dict(size=9.5)),
        )
        st.plotly_chart(fig_inf, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("No data for selected filters.")

with col6:
    st.markdown('<div class="section-header">Profit Decomposition — Region › Category › Sub-Category</div>',
                unsafe_allow_html=True)
    tree_df = dff.groupby(['Region', 'Category', 'Sub-Category'], as_index=False).agg(
        Sales=('Sales', 'sum'), Profit=('Profit', 'sum')
    )
    try:
        fig_tree = px.icicle(
            tree_df,
            path=[px.Constant('All'), 'Region', 'Category', 'Sub-Category'],
            values='Sales',
            color='Profit',
            color_continuous_scale=[[0,'#D64550'],[0.45,'#FADADD'],[0.5,'#F3F2F1'],[0.55,'#D4EDDA'],[1,'#107C10']],
            color_continuous_midpoint=0,
        )
    except Exception:
        fig_tree = px.sunburst(
            tree_df,
            path=['Region', 'Category', 'Sub-Category'],
            values='Sales',
            color='Profit',
            color_continuous_scale=[[0,'#D64550'],[0.5,'#F3F2F1'],[1,'#107C10']],
            color_continuous_midpoint=0,
        )
    fig_tree.update_traces(
        textfont=dict(size=10, family='Segoe UI'),
        hovertemplate='<b>%{label}</b><br>Sales: $%{value:,.0f}<extra></extra>',
    )
    fig_tree.update_layout(
        paper_bgcolor='white', height=295,
        margin=dict(l=2, r=2, t=2, b=2),
        coloraxis_colorbar=dict(title='Profit ($)', tickprefix='$', tickfont=dict(size=9), thickness=10),
        font=dict(family='Segoe UI'),
    )
    st.plotly_chart(fig_tree, use_container_width=True, config={'displayModeBar': False})

# ── ROW 4: Sub-Category Performance Matrix (full-width) ───────────────────────
(mat_col,) = st.columns([1])
with mat_col:
    st.markdown('<div class="section-header">Sub-Category Performance Matrix</div>',
                unsafe_allow_html=True)

    mx = dff.groupby(['Sub-Category', 'Category'], as_index=False).agg(
        Sales     =('Sales',   'sum'),
        Profit    =('Profit',  'sum'),
        Orders    =('Sales',   'count'),
        Avg_Disc  =('Discount_Pct', 'mean'),
    ).sort_values('Sales', ascending=False)

    mx['Margin']  = (mx['Profit'] / mx['Sales'] * 100).round(1)
    mx['Status']  = mx['Profit'].apply(lambda p: '▲  Profitable' if p > 0 else '▼  Loss-making')

    def _fill(p):
        if p > 0:  return '#F1FAF1'
        return '#FFF0F0'

    n = len(mx)
    profit_fills = [_fill(p) for p in mx['Profit']]
    white_col    = ['white'] * n

    fig_mx = go.Figure(data=[go.Table(
        columnwidth=[160, 140, 100, 100, 100, 110, 110],
        header=dict(
            values=['<b>Sub-Category</b>', '<b>Category</b>', '<b>Sales</b>',
                    '<b>Profit</b>', '<b>Margin %</b>', '<b>Avg Discount</b>', '<b>Status</b>'],
            fill_color='#F3F2F1',
            align=['left', 'left', 'right', 'right', 'center', 'center', 'left'],
            font=dict(size=11, color='#252423', family='Segoe UI'),
            height=34, line_color='#EDEBE9',
        ),
        cells=dict(
            values=[
                mx['Sub-Category'],
                mx['Category'],
                [f'${v:,.0f}' for v in mx['Sales']],
                [f'${v:,.0f}' for v in mx['Profit']],
                [f'{m:.1f}%'  for m in mx['Margin']],
                [f'{d:.1f}%'  for d in mx['Avg_Disc']],
                mx['Status'],
            ],
            fill_color=[
                white_col, white_col, white_col,
                profit_fills, profit_fills,
                white_col, profit_fills,
            ],
            align=['left','left','right','right','center','center','left'],
            font=dict(size=10.5, color='#252423', family='Segoe UI'),
            height=30, line_color='#F0F0F0',
        ),
    )])
    fig_mx.update_layout(
        paper_bgcolor='white',
        height=34 + n * 30 + 20,
        margin=dict(l=0, r=0, t=0, b=0),
    )
    st.plotly_chart(fig_mx, use_container_width=True, config={'displayModeBar': False})

st.markdown("""
<div style="text-align:center; color:#A19F9D; font-size:10px; margin-top:6px; padding:6px;
            font-family:'Segoe UI';">
  Global Superstore BI Dashboard · External Consultant Report · Kaggle Superstore Dataset
</div>
""", unsafe_allow_html=True)
