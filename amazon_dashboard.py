import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="Amazon | BI Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── Typography — Segoe UI (Power BI default) ── */
html, body, [class*="css"] {
    font-family: 'Segoe UI', wf_segoe-ui_normal, helvetica, arial, sans-serif !important;
}

/* ── Canvas ── */
.main .block-container { background: #F3F3F3; padding-top: 0.6rem; max-width: 100%; }
.stApp { background: #F3F3F3; }

/* ── Allow column box-shadows to escape their parent ── */
[data-testid="stHorizontalBlock"] { overflow: visible !important; align-items: stretch !important; }

/* ── Power BI tile ── */
section.main div[data-testid="column"] {
    background: white !important;
    border-radius: 3px !important;
    box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.132), 0 0.3px 0.9px rgba(0,0,0,0.108) !important;
    overflow: hidden !important;
}

/* ── Sidebar — Power BI Filter Pane ── */
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
    df = pd.read_csv(os.path.join(here, 'amazon.csv'))

    def clean_money(s):
        return pd.to_numeric(
            s.astype(str).str.replace('₹', '', regex=False)
                         .str.replace(',', '', regex=False).str.strip(),
            errors='coerce'
        )

    df['Actual_Price']     = clean_money(df['actual_price'])
    df['Discounted_Price'] = clean_money(df['discounted_price'])
    df['Discount_Pct']     = pd.to_numeric(
        df['discount_percentage'].astype(str).str.replace('%', '', regex=False).str.strip(),
        errors='coerce'
    )
    df['Rating']       = pd.to_numeric(df['rating'], errors='coerce')
    df['Rating_Count'] = pd.to_numeric(
        df['rating_count'].astype(str).str.replace(',', '', regex=False).str.strip(),
        errors='coerce'
    )
    df['Category']     = df['category'].apply(lambda s: str(s).split('|')[0].replace('&', ' & ').strip())
    df['Sub_Category'] = df['category'].apply(
        lambda s: (str(s).split('|')[-1] if '|' in str(s) else str(s)).replace('&', ' & ').strip()
    )
    df['Product_Name'] = df['product_name'].str[:60]

    df = df.dropna(subset=['Rating', 'Discount_Pct', 'Actual_Price', 'Rating_Count'])
    df = df[(df['Actual_Price'] > 0) & (df['Discount_Pct'] >= 0) & (df['Rating'].between(1, 5))]

    band_labels = ['0–10%', '11–25%', '26–40%', '41–60%', '60%+']
    df['Discount_Band'] = pd.cut(
        df['Discount_Pct'], bins=[0, 10, 25, 40, 60, 100],
        labels=band_labels, include_lowest=True
    ).astype(str)

    tier_labels = ['Budget (<₹500)', 'Mid (₹500–2K)', 'Premium (₹2K–10K)', 'Luxury (₹10K+)']
    df['Price_Tier'] = pd.cut(
        df['Actual_Price'], bins=[0, 500, 2000, 10000, np.inf], labels=tier_labels
    ).astype(str)

    def rat_tier(r):
        if r >= 4.5: return '⭐⭐⭐⭐⭐ (4.5+)'
        if r >= 4.0: return '⭐⭐⭐⭐ (4.0–4.4)'
        if r >= 3.5: return '⭐⭐⭐ (3.5–3.9)'
        return '⭐⭐ (Below 3.5)'
    df['Rating_Tier'] = df['Rating'].apply(rat_tier)
    return df


df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="background:#F3F2F1; margin:-1rem -1rem 1rem -1rem;
                padding:12px 16px; border-bottom:1px solid #EDEBE9;">
      <div style="display:flex; align-items:center; gap:8px;">
        <div style="background:#FF9900; color:#232F3E; font-weight:800; font-size:10px;
                    padding:2px 6px; border-radius:2px; font-family:Arial; letter-spacing:0.5px;">amazon</div>
        <div style="font-size:12px; font-weight:600; color:#323130; font-family:'Segoe UI';">Filters</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    all_cats   = sorted(df['Category'].unique())
    cats_sel   = st.multiselect("Category", all_cats, default=all_cats)
    band_order = ['0–10%', '11–25%', '26–40%', '41–60%', '60%+']
    bands_sel  = st.multiselect("Discount Band", band_order, default=band_order)
    min_rating = st.slider("Min. Rating", 1.0, 5.0, 1.0, 0.1)

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:10px; color:#A19F9D; font-family:'Segoe UI';">
      Source: Kaggle Amazon Sales Dataset<br/>{len(df):,} product listings
    </div>
    """, unsafe_allow_html=True)

# ── Filter ────────────────────────────────────────────────────────────────────
dff = df[
    df['Category'].isin(cats_sel) &
    df['Discount_Band'].isin(bands_sel) &
    (df['Rating'] >= min_rating)
]

# ── KPI values ────────────────────────────────────────────────────────────────
total_prods      = len(dff)
avg_rating       = dff['Rating'].mean()      if total_prods else 0.0
avg_discount     = dff['Discount_Pct'].mean() if total_prods else 0.0
total_reviews    = dff['Rating_Count'].sum()
total_reviews_all = df['Rating_Count'].sum()

# ── Report header ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#232F3E; padding:11px 18px; border-radius:3px; margin-bottom:10px;
            display:flex; align-items:center; justify-content:space-between;
            box-shadow:0 1.6px 3.6px rgba(0,0,0,0.18);">
  <div style="display:flex; align-items:center; gap:14px;">
    <div style="background:#FF9900; color:#232F3E; font-weight:800; font-size:11px;
                padding:3px 8px; border-radius:2px; font-family:Arial; letter-spacing:0.5px;">amazon</div>
    <div>
      <div style="font-size:14px; font-weight:600; color:white; font-family:'Segoe UI'; line-height:1.3;">
        Product Performance Dashboard
      </div>
      <div style="font-size:10px; color:#9BA8B8; margin-top:2px; font-family:'Segoe UI';">
        Pricing &amp; Sentiment Intelligence &nbsp;·&nbsp; Kaggle Amazon Sales Dataset
      </div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:11px; color:#FF9900; font-weight:600; font-family:'Segoe UI';">{total_prods:,} products</div>
    <div style="font-size:10px; color:#9BA8B8; font-family:'Segoe UI';">{dff['Category'].nunique()} categories</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Active filter chips ───────────────────────────────────────────────────────
chips = []
if set(cats_sel) != set(all_cats):
    label = ", ".join(cats_sel) if len(cats_sel) <= 2 else f"{len(cats_sel)} of {len(all_cats)} selected"
    chips.append(f'<span class="filter-chip">Category: {label}</span>')
if set(bands_sel) != set(band_order):
    chips.append(f'<span class="filter-chip">Discount: {", ".join(bands_sel)}</span>')
if min_rating > 1.0:
    chips.append(f'<span class="filter-chip">Rating ≥ {min_rating:.1f} ★</span>')
if chips:
    st.markdown(f'<div class="chip-row">{"".join(chips)}</div>', unsafe_allow_html=True)

# ── KPI row — 4 white tiles with goal progress bars ───────────────────────────
kc = st.columns(4, gap='small')

prod_pct   = total_prods / len(df) * 100 if len(df) else 0
rating_pct = avg_rating / 5.0 * 100
disc_pct   = min(avg_discount / 70.0 * 100, 100)
review_pct = total_reviews / total_reviews_all * 100 if total_reviews_all else 0

with kc[0]:
    trend_r = 'warn' if avg_rating < 4.0 else ''
    trend_t = '▼ Below 4.0 target' if avg_rating < 4.0 else '▲ Above 4.0 target'
    st.markdown(f"""
    <div class="section-header">Avg Customer Rating</div>
    <div class="kpi-value">{avg_rating:.2f} ★</div>
    <div class="kpi-sub {trend_r}">{trend_t}</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{rating_pct:.0f}%; background:#E66C37;"></div>
    </div>
    """, unsafe_allow_html=True)

with kc[1]:
    st.markdown(f"""
    <div class="section-header">Products Analysed</div>
    <div class="kpi-value">{total_prods:,}</div>
    <div class="kpi-sub neutral">{dff['Category'].nunique()} categories visible</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{prod_pct:.0f}%; background:#118DFF;"></div>
    </div>
    """, unsafe_allow_html=True)

with kc[2]:
    margin_txt = '⚠ High — margin risk' if avg_discount > 30 else '✓ Moderate'
    st.markdown(f"""
    <div class="section-header">Avg Discount</div>
    <div class="kpi-value">{avg_discount:.1f}%</div>
    <div class="kpi-sub warn">{margin_txt}</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{disc_pct:.0f}%; background:#D64550;"></div>
    </div>
    """, unsafe_allow_html=True)

with kc[3]:
    st.markdown(f"""
    <div class="section-header">Total Reviews</div>
    <div class="kpi-value">{total_reviews / 1e6:.2f}M</div>
    <div class="kpi-sub neutral">of {total_reviews_all / 1e6:.2f}M catalogue total</div>
    <div class="kpi-bar-track">
      <div class="kpi-bar-fill" style="width:{review_pct:.0f}%; background:#107C10;"></div>
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


PBI_COLORS = ['#118DFF', '#E66C37', '#107C10', '#D64550',
              '#744EC2', '#D9B300', '#E044A7', '#12239E', '#00B7C3', '#8764B8']


# ── ROW 1: Treemap + Discount vs Rating ───────────────────────────────────────
col1, col2 = st.columns([1, 1.1], gap='small')

with col1:
    st.markdown('<div class="section-header">Product Distribution by Category</div>',
                unsafe_allow_html=True)
    tm = dff.groupby(['Category', 'Sub_Category'], as_index=False).agg(
        Count=('Rating', 'count'), Avg_Rating=('Rating', 'mean')
    )
    fig_tm = px.treemap(
        tm, path=['Category', 'Sub_Category'], values='Count',
        color='Avg_Rating',
        color_continuous_scale=[[0, '#D64550'], [0.5, '#E66C37'], [1, '#107C10']],
        range_color=[3.0, 5.0], color_continuous_midpoint=4.0,
    )
    fig_tm.update_traces(
        textfont=dict(size=10, family='Segoe UI'),
        marker=dict(cornerradius=2),
        hovertemplate='<b>%{label}</b><br>Products: %{value}<br>Avg Rating: %{color:.2f}★<extra></extra>',
    )
    fig_tm.update_layout(
        paper_bgcolor='white', height=300,
        margin=dict(l=2, r=2, t=2, b=2),
        coloraxis_colorbar=dict(title='Avg Rating', tickfont=dict(size=9), thickness=10),
        font=dict(family='Segoe UI'),
    )
    st.plotly_chart(fig_tm, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown('<div class="section-header">Discount % vs Customer Rating</div>',
                unsafe_allow_html=True)
    fig_disc = px.scatter(
        dff, x='Discount_Pct', y='Rating', color='Category',
        color_discrete_sequence=PBI_COLORS,
        opacity=0.5, trendline='lowess',
        labels={'Discount_Pct': 'Discount (%)', 'Rating': 'Customer Rating (★)'},
        hover_data={'Actual_Price': ':₹,.0f', 'Product_Name': True},
    )
    fig_disc.add_hline(y=4.0, line_dash='dot', line_color='#605E5C', line_width=1.2,
                       annotation_text='4.0 target', annotation_font_size=9,
                       annotation_font_color='#605E5C')
    pbi_layout(fig_disc, h=300)
    st.plotly_chart(fig_disc, use_container_width=True, config={'displayModeBar': False})

# ── ROW 2: Bar + Review scatter ───────────────────────────────────────────────
col3, col4 = st.columns(2, gap='small')

with col3:
    st.markdown('<div class="section-header">Avg Rating by Category</div>',
                unsafe_allow_html=True)
    cat_rating = dff.groupby('Category', as_index=False)['Rating'].mean().sort_values('Rating')
    bar_colors = ['#107C10' if r >= 4.0 else '#E66C37' if r >= 3.5 else '#D64550'
                  for r in cat_rating['Rating']]
    fig_bar = go.Figure(go.Bar(
        x=cat_rating['Rating'], y=cat_rating['Category'],
        orientation='h', marker_color=bar_colors,
        text=[f'{r:.2f}★' for r in cat_rating['Rating']],
        textfont=dict(size=10), textposition='outside',
    ))
    fig_bar.add_vline(x=4.0, line_dash='dot', line_color='#605E5C', line_width=1.2,
                      annotation_text='4.0 target', annotation_font_size=9,
                      annotation_font_color='#605E5C')
    pbi_layout(fig_bar, h=300)
    fig_bar.update_layout(
        showlegend=False,
        xaxis=dict(range=[0, 5.6], title='Average Rating (★)'),
        yaxis=dict(tickfont=dict(size=10)),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

with col4:
    st.markdown('<div class="section-header">Review Volume vs Avg Rating</div>',
                unsafe_allow_html=True)
    fig_rev = px.scatter(
        dff, x='Rating_Count', y='Rating', color='Category',
        color_discrete_sequence=PBI_COLORS,
        opacity=0.55, size='Actual_Price', size_max=16,
        labels={'Rating_Count': 'Review Count', 'Rating': 'Avg Rating (★)'},
        hover_data={'Product_Name': True, 'Discount_Pct': ':.1f'},
        log_x=True,
    )
    fig_rev.add_hrect(y0=4.0, y1=5.1, fillcolor='rgba(16,124,16,0.05)', line_width=0,
                      annotation_text='Star Quadrant', annotation_position='top right',
                      annotation_font_size=9, annotation_font_color='#605E5C')
    fig_rev.add_hrect(y0=1.0, y1=3.5, fillcolor='rgba(214,69,80,0.05)', line_width=0,
                      annotation_text='Risk Quadrant', annotation_position='bottom right',
                      annotation_font_size=9, annotation_font_color='#605E5C')
    fig_rev.add_hline(y=4.0, line_dash='dot', line_color='#605E5C', line_width=1, opacity=0.7)
    pbi_layout(fig_rev, h=300)
    st.plotly_chart(fig_rev, use_container_width=True, config={'displayModeBar': False})

# ── ROW 3: Funnel (count + rating quality) + Key Influencers ─────────────────
col5, col6 = st.columns(2, gap='small')

with col5:
    st.markdown('<div class="section-header">Products by Discount Band</div>',
                unsafe_allow_html=True)
    band_data = (
        dff.groupby('Discount_Band')
           .agg(Count=('Rating', 'count'), Avg_Rating=('Rating', 'mean'))
           .reindex(band_order).dropna().reset_index()
    )
    # Colour each band by its avg-rating quality; label shows both count and rating
    funnel_colors = ['#107C10' if r >= 4.0 else '#E66C37' if r >= 3.5 else '#D64550'
                     for r in band_data['Avg_Rating']]
    fig_funnel = go.Figure(go.Funnel(
        y=band_data['Discount_Band'],
        x=band_data['Count'],
        text=[f"{int(c):,}  ·  {r:.2f} ★"
              for c, r in zip(band_data['Count'], band_data['Avg_Rating'])],
        textinfo='text',
        textfont=dict(size=10.5, family='Segoe UI'),
        marker=dict(color=funnel_colors, line=dict(width=1.5, color='white')),
        connector=dict(line=dict(color='#F0F0F0', width=1)),
        customdata=np.stack([band_data['Avg_Rating'], band_data['Count']], axis=1),
        hovertemplate=(
            '<b>%{y}</b><br>'
            'Products: %{customdata[1]:,}<br>'
            'Avg Rating: %{customdata[0]:.2f} ★<extra></extra>'
        ),
    ))
    pbi_layout(fig_funnel, h=285)
    fig_funnel.update_layout(showlegend=False, xaxis_title='Number of Products')
    st.plotly_chart(fig_funnel, use_container_width=True, config={'displayModeBar': False})

with col6:
    st.markdown('<div class="section-header">Key Influencers — Drivers of High Rating</div>',
                unsafe_allow_html=True)
    global_mean = dff['Rating'].mean() if total_prods else 4.0
    records = []
    dim_cfg = {
        'Category':      ('■', dff['Category'].unique(),                                              'Category',     'Category'),
        'Discount Band': ('●', band_order,                                                            'Discount_Band','Disc'),
        'Price Tier':    ('▲', ['Budget (<₹500)', 'Mid (₹500–2K)', 'Premium (₹2K–10K)', 'Luxury (₹10K+)'], 'Price_Tier',   'Price'),
    }
    for dim, (sym, vals, col_name, prefix) in dim_cfg.items():
        for val in vals:
            sub = dff[dff[col_name] == val]
            if len(sub) >= 5:
                records.append({
                    'Label':      f'{sym} {prefix}: {val}',
                    'Avg_Rating': sub['Rating'].mean(),
                    'Count':      len(sub),
                    'Delta':      sub['Rating'].mean() - global_mean,
                })

    if records:
        inf_df = pd.DataFrame(records).sort_values('Delta')
        inf_df = pd.concat([inf_df.head(5), inf_df.tail(5)]).drop_duplicates().sort_values('Delta')
        inf_colors = ['#107C10' if d >= 0 else '#D64550' for d in inf_df['Delta']]

        fig_inf = go.Figure(go.Bar(
            x=inf_df['Delta'], y=inf_df['Label'], orientation='h',
            marker_color=inf_colors,
            text=[f'{d:+.3f}' for d in inf_df['Delta']],
            textfont=dict(size=9.5), textposition='outside',
            customdata=np.stack([inf_df['Avg_Rating'], inf_df['Count']], axis=1),
            hovertemplate=(
                '<b>%{y}</b><br>Avg Rating: %{customdata[0]:.2f}★<br>'
                'Products: %{customdata[1]:,}<br>vs mean: %{x:+.3f}<extra></extra>'
            ),
        ))
        fig_inf.add_vline(x=0, line_color='#323130', line_width=1.2)
        pbi_layout(fig_inf, h=285)
        fig_inf.update_layout(
            showlegend=False,
            xaxis=dict(tickformat='+.3f', title='Rating delta vs global mean'),
            yaxis=dict(tickfont=dict(size=9.5)),
        )
        st.plotly_chart(fig_inf, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Apply filters to see key influencers.")

# ── ROW 4: Category performance matrix (full-width) ───────────────────────────
(mat_col,) = st.columns([1])
with mat_col:
    st.markdown('<div class="section-header">Category Performance Matrix</div>',
                unsafe_allow_html=True)

    cat_mx = dff.groupby('Category', as_index=False).agg(
        Products    =('Rating',       'count'),
        Avg_Rating  =('Rating',       'mean'),
        Avg_Discount=('Discount_Pct', 'mean'),
        Total_Reviews=('Rating_Count','sum'),
        High_Rated  =('Rating',       lambda x: (x >= 4.0).sum()),
    ).sort_values('Avg_Rating', ascending=False)

    cat_mx['Pct_High'] = (cat_mx['High_Rated'] / cat_mx['Products'] * 100).round(0).astype(int)
    cat_mx['Status']   = cat_mx['Avg_Rating'].apply(
        lambda r: '▲  On target' if r >= 4.0 else '▼  Off target'
    )

    def _cell_fill(r):
        if r >= 4.0: return '#F1FAF1'
        if r >= 3.5: return '#FFF8EC'
        return '#FFF0F0'

    n = len(cat_mx)
    rating_fills  = [_cell_fill(r) for r in cat_mx['Avg_Rating']]
    white_col     = ['white'] * n

    fig_mx = go.Figure(data=[go.Table(
        columnwidth=[190, 75, 100, 110, 140, 110, 110],
        header=dict(
            values=[
                '<b>Category</b>', '<b>Products</b>', '<b>Avg Rating</b>',
                '<b>Avg Discount</b>', '<b>Total Reviews</b>',
                '<b>% ≥ 4 ★</b>', '<b>Status</b>',
            ],
            fill_color='#F3F2F1',
            align=['left', 'center', 'center', 'center', 'right', 'center', 'left'],
            font=dict(size=11, color='#252423', family='Segoe UI'),
            height=34,
            line_color='#EDEBE9',
        ),
        cells=dict(
            values=[
                cat_mx['Category'],
                cat_mx['Products'],
                [f'{r:.2f} ★' for r in cat_mx['Avg_Rating']],
                [f'{d:.1f}%'  for d in cat_mx['Avg_Discount']],
                [f'{int(v):,}' for v in cat_mx['Total_Reviews']],
                [f'{p}%'       for p in cat_mx['Pct_High']],
                cat_mx['Status'],
            ],
            fill_color=[
                white_col, white_col,
                rating_fills,
                white_col, white_col,
                rating_fills, rating_fills,
            ],
            align=['left', 'center', 'center', 'center', 'right', 'center', 'left'],
            font=dict(size=10.5, color='#252423', family='Segoe UI'),
            height=30,
            line_color='#F0F0F0',
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
  Amazon Product Analytics · External Consultant Report · Kaggle Amazon Sales Dataset
</div>
""", unsafe_allow_html=True)
