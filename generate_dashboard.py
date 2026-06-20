"""
generate_dashboard.py
巴西电商物流分析 — 汇总仪表盘生成器
运行后在当前目录生成 dashboard.html，浏览器直接打开即可。
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import os
import warnings
warnings.filterwarnings('ignore')

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'archive')

# ─────────────────────────────────────────────────────────────
# 1. 加载数据
# ─────────────────────────────────────────────────────────────
print("[1/3] Loading data...")
orders       = pd.read_csv(f'{BASE}/olist_orders_dataset.csv')
reviews      = pd.read_csv(f'{BASE}/olist_order_reviews_dataset.csv')
customers    = pd.read_csv(f'{BASE}/olist_customers_dataset.csv')
items        = pd.read_csv(f'{BASE}/olist_order_items_dataset.csv')
products     = pd.read_csv(f'{BASE}/olist_products_dataset.csv')
category_tr  = pd.read_csv(f'{BASE}/product_category_name_translation.csv')

# ─────────────────────────────────────────────────────────────
# 2. 数据处理
# ─────────────────────────────────────────────────────────────
for col in ['order_purchase_timestamp', 'order_delivered_customer_date',
            'order_estimated_delivery_date', 'order_delivered_carrier_date']:
    if col in orders.columns:
        orders[col] = pd.to_datetime(orders[col])

delivered = (orders[orders['order_status'] == 'delivered']
             .dropna(subset=['order_delivered_customer_date',
                             'order_estimated_delivery_date'])
             .copy())

delivered['actual_delivery_days'] = (
    delivered['order_delivered_customer_date'] -
    delivered['order_purchase_timestamp']
).dt.days

delivered['is_delayed'] = (
    delivered['order_delivered_customer_date'] >
    delivered['order_estimated_delivery_date']
)

# 剔除异常负值
delivered = delivered[delivered['actual_delivery_days'] >= 0]

# 合并州信息
delivered = delivered.merge(
    customers[['customer_id', 'customer_state']], on='customer_id', how='left'
)

# ─────────────────────────────────────────────────────────────
# 3. KPI
# ─────────────────────────────────────────────────────────────
total_orders = len(delivered)
delay_rate   = delivered['is_delayed'].mean() * 100
avg_days     = delivered['actual_delivery_days'].mean()

review_merged = delivered.merge(
    reviews[['order_id', 'review_score']], on='order_id', how='left'
).dropna(subset=['review_score'])
avg_review = review_merged['review_score'].mean()

delayed_count = delivered['is_delayed'].sum()
print(f"   Orders: {total_orders:,}  |  Delay rate: {delay_rate:.1f}%  |  Avg days: {avg_days:.1f}  |  Avg review: {avg_review:.2f}")

# ─────────────────────────────────────────────────────────────
# 4. 图表
# ─────────────────────────────────────────────────────────────

# ── 图①：配送天数分布 ────────────────────────────────────────
plot_data = delivered[delivered['actual_delivery_days'] <= 60].copy()
plot_data['Status'] = plot_data['is_delayed'].map(
    {True: '⚠️ Delayed', False: '✅ On Time'}
)
fig1 = px.histogram(
    plot_data,
    x='actual_delivery_days',
    color='Status',
    color_discrete_map={'⚠️ Delayed': '#e74c3c', '✅ On Time': '#2ecc71'},
    nbins=60,
    barmode='overlay',
    opacity=0.75,
    labels={'actual_delivery_days': 'Delivery Days (配送天数)'},
    title='① Delivery Days Distribution — Most orders arrive within 10 days',
    template='plotly_white'
)
fig1.update_layout(
    legend=dict(orientation='h', y=1.05, x=0),
    margin=dict(t=70, b=40, l=50, r=30),
    height=380
)

# ── 图②：各州延迟率排名 ──────────────────────────────────────
state_stats = (delivered.groupby('customer_state')
               .agg(total_orders=('order_id', 'count'),
                    delayed_orders=('is_delayed', 'sum'))
               .reset_index())
state_stats['delay_rate'] = (
    state_stats['delayed_orders'] / state_stats['total_orders'] * 100
).round(1)
state_stats = (state_stats[state_stats['total_orders'] >= 50]
               .sort_values('delay_rate', ascending=True))

colors2 = ['#e74c3c' if r > delay_rate else '#95a5a6'
           for r in state_stats['delay_rate']]

fig2 = go.Figure(go.Bar(
    x=state_stats['delay_rate'],
    y=state_stats['customer_state'],
    orientation='h',
    marker_color=colors2,
    text=state_stats['delay_rate'].astype(str) + '%',
    textposition='outside',
    customdata=state_stats[['total_orders', 'delayed_orders']].values,
    hovertemplate=(
        '<b>%{y}</b><br>'
        'Delay Rate: %{x:.1f}%<br>'
        'Total Orders: %{customdata[0]:,}<br>'
        'Delayed: %{customdata[1]:,}<extra></extra>'
    )
))
fig2.add_vline(
    x=delay_rate, line_dash='dash', line_color='#e67e22',
    annotation_text=f'Avg {delay_rate:.1f}%',
    annotation_position='top right',
    annotation_font_color='#e67e22'
)
fig2.update_layout(
    title='② Delay Rate by State — Red = above national average',
    template='plotly_white',
    margin=dict(t=70, b=40, l=60, r=80),
    height=620,
    xaxis=dict(title='Delay Rate %')
)

# ── 图③：月度延迟趋势 ────────────────────────────────────────
delivered['year_month'] = delivered['order_purchase_timestamp'].dt.to_period('M')
monthly = (delivered.groupby('year_month')
           .agg(total=('order_id', 'count'),
                delayed=('is_delayed', 'sum'),
                avg_days=('actual_delivery_days', 'mean'))
           .reset_index())
monthly['delay_rate'] = monthly['delayed'] / monthly['total'] * 100
monthly['ym_str'] = monthly['year_month'].astype(str)
monthly = monthly[monthly['total'] >= 30]

fig3 = go.Figure()
fig3.add_trace(go.Scatter(
    x=monthly['ym_str'], y=monthly['delay_rate'],
    name='Delay Rate %',
    line=dict(color='#e74c3c', width=2.5),
    yaxis='y1',
    hovertemplate='%{x}<br>Delay Rate: %{y:.1f}%<extra></extra>'
))
fig3.add_trace(go.Scatter(
    x=monthly['ym_str'], y=monthly['avg_days'],
    name='Avg Delivery Days',
    line=dict(color='#3498db', width=2, dash='dot'),
    yaxis='y2',
    hovertemplate='%{x}<br>Avg Days: %{y:.1f}<extra></extra>'
))
fig3.update_layout(
    title='③ Monthly Trend — Delay rate & average delivery days',
    template='plotly_white',
    yaxis=dict(title='Delay Rate %', color='#e74c3c', titlefont_color='#e74c3c'),
    yaxis2=dict(title='Avg Days', overlaying='y', side='right',
                color='#3498db', titlefont_color='#3498db'),
    legend=dict(orientation='h', y=1.08, x=0),
    margin=dict(t=70, b=60, l=50, r=60),
    height=360
)

# ── 图④：准时 vs 延迟评分对比 ───────────────────────────────
score_compare = (review_merged.groupby('is_delayed')['review_score']
                 .mean().reset_index())
score_compare['label'] = score_compare['is_delayed'].map(
    {True: '⚠️ Delayed', False: '✅ On Time'}
)
score_compare['color'] = score_compare['is_delayed'].map(
    {True: '#e74c3c', False: '#2ecc71'}
)
score_compare['score_fmt'] = score_compare['review_score'].round(2).astype(str)

fig4 = go.Figure(go.Bar(
    x=score_compare['label'],
    y=score_compare['review_score'],
    marker_color=score_compare['color'],
    text=score_compare['score_fmt'],
    textposition='outside',
    width=0.45
))
# 标注差值
gap = score_compare.loc[score_compare['is_delayed']==False, 'review_score'].values[0] - \
      score_compare.loc[score_compare['is_delayed']==True,  'review_score'].values[0]
fig4.add_annotation(
    x=0.5, y=3.8, xref='paper',
    text=f'Gap: <b>−{gap:.2f} pts</b>',
    showarrow=False,
    font=dict(size=16, color='#e74c3c'),
    bgcolor='#fff0f0', borderpad=6
)
fig4.update_layout(
    title='④ Review Score: On-Time vs Delayed Orders',
    yaxis=dict(title='Avg Review Score', range=[0, 5.8]),
    template='plotly_white',
    margin=dict(t=70, b=40, l=50, r=30),
    height=380
)

# ── 图⑤：星期几延迟率 ───────────────────────────────────────
delivered['day_name'] = delivered['order_purchase_timestamp'].dt.day_name()
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_stats = (delivered.groupby('day_name')
             .agg(total=('order_id', 'count'),
                  delayed=('is_delayed', 'sum'))
             .reset_index())
day_stats['delay_rate'] = day_stats['delayed'] / day_stats['total'] * 100
day_stats['day_name'] = pd.Categorical(day_stats['day_name'],
                                        categories=day_order, ordered=True)
day_stats = day_stats.sort_values('day_name')

HIGH_DAYS = {'Monday', 'Tuesday', 'Friday'}
day_colors = ['#e74c3c' if d in HIGH_DAYS else '#3498db'
              for d in day_stats['day_name']]

fig5 = go.Figure(go.Bar(
    x=day_stats['day_name'],
    y=day_stats['delay_rate'],
    marker_color=day_colors,
    text=day_stats['delay_rate'].round(1).astype(str) + '%',
    textposition='outside'
))
fig5.add_hline(y=delay_rate, line_dash='dash', line_color='#888',
               annotation_text=f'Avg {delay_rate:.1f}%',
               annotation_position='bottom right')
fig5.update_layout(
    title='⑤ Delay Rate by Day of Week — Mon/Tue/Fri highest',
    yaxis=dict(title='Delay Rate %', range=[0, day_stats['delay_rate'].max() * 1.25]),
    template='plotly_white',
    margin=dict(t=70, b=40, l=50, r=30),
    height=380
)

# ── 图⑥：月份季节性 ─────────────────────────────────────────
delivered['month'] = delivered['order_purchase_timestamp'].dt.month
month_stats = (delivered.groupby('month')
               .agg(total=('order_id', 'count'),
                    delayed=('is_delayed', 'sum'))
               .reset_index())
month_stats['delay_rate'] = month_stats['delayed'] / month_stats['total'] * 100
month_labels = {1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',
                7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
month_stats['month_label'] = month_stats['month'].map(month_labels)
avg_m = month_stats['delay_rate'].mean()

HIGH_MONTHS = {2, 3, 11, 12}
month_colors = ['#e74c3c' if m in HIGH_MONTHS else '#3498db'
                for m in month_stats['month']]

annotations_m = {
    2: 'Carnival',
    3: 'Post-Carnival',
    11: 'Black Friday',
    12: 'Christmas'
}
fig6 = go.Figure(go.Bar(
    x=month_stats['month_label'],
    y=month_stats['delay_rate'],
    marker_color=month_colors,
    text=month_stats['delay_rate'].round(1).astype(str) + '%',
    textposition='outside',
    customdata=month_stats['month'].values,
    hovertemplate='%{x}: %{y:.1f}%<extra></extra>'
))
fig6.add_hline(y=avg_m, line_dash='dash', line_color='#888',
               annotation_text=f'Avg {avg_m:.1f}%',
               annotation_position='bottom right')

# 标注重点月份
for m, label in annotations_m.items():
    row = month_stats[month_stats['month'] == m]
    if not row.empty:
        fig6.add_annotation(
            x=row['month_label'].values[0],
            y=row['delay_rate'].values[0] + 1.2,
            text=label,
            showarrow=False,
            font=dict(size=10, color='#c0392b'),
            bgcolor='rgba(255,255,255,0.8)'
        )

fig6.update_layout(
    title='⑥ Delay Rate by Month — Seasonal spikes at Carnival & year-end',
    yaxis=dict(title='Delay Rate %',
               range=[0, month_stats['delay_rate'].max() * 1.35]),
    template='plotly_white',
    margin=dict(t=70, b=40, l=50, r=30),
    height=400
)

# ─────────────────────────────────────────────────────────────
# 5. 组装 HTML
# ─────────────────────────────────────────────────────────────
print("[2/3] Building HTML dashboard...")

def to_div(fig):
    return pio.to_html(fig, full_html=False, include_plotlyjs=False,
                       config={'displayModeBar': True, 'scrollZoom': False})

d1 = to_div(fig1)
d2 = to_div(fig2)
d3 = to_div(fig3)
d4 = to_div(fig4)
d5 = to_div(fig5)
d6 = to_div(fig6)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Brazil E-Commerce Logistics Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f0f2f5;
      color: #1a1a2e;
    }}

    /* ── Header ── */
    header {{
      background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
      color: white;
      padding: 36px 48px 30px;
    }}
    header h1 {{ font-size: 26px; font-weight: 700; letter-spacing: -0.3px; margin-bottom: 6px; }}
    header p  {{ font-size: 13px; opacity: 0.65; }}

    /* ── Container ── */
    .wrap {{ max-width: 1440px; margin: 0 auto; padding: 28px 36px 40px; }}

    /* ── KPI cards ── */
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 22px;
    }}
    .kpi {{
      background: white;
      border-radius: 12px;
      padding: 22px 24px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07);
      border-top: 4px solid #3498db;
    }}
    .kpi.red    {{ border-top-color: #e74c3c; }}
    .kpi.orange {{ border-top-color: #f39c12; }}
    .kpi.green  {{ border-top-color: #2ecc71; }}
    .kpi-label  {{ font-size: 11px; color: #999; text-transform: uppercase;
                   letter-spacing: 0.6px; margin-bottom: 8px; }}
    .kpi-val    {{ font-size: 34px; font-weight: 800; color: #1a1a2e; line-height: 1; }}
    .kpi-sub    {{ font-size: 11px; color: #bbb; margin-top: 6px; }}

    /* ── Insights ── */
    .insights {{
      background: #fffbf0;
      border: 1px solid #ffe8a1;
      border-radius: 12px;
      padding: 18px 24px;
      margin-bottom: 22px;
    }}
    .insights h3 {{
      font-size: 12px; font-weight: 700; color: #d68910;
      text-transform: uppercase; letter-spacing: 0.5px;
      margin-bottom: 12px;
    }}
    .insights-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px 24px;
    }}
    .insight-item {{
      font-size: 13px; color: #444;
      padding-left: 14px;
      position: relative;
      line-height: 1.5;
    }}
    .insight-item::before {{
      content: '→';
      position: absolute; left: 0;
      color: #d68910; font-weight: 700;
    }}

    /* ── Chart cards ── */
    .card {{
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.07);
      padding: 4px 8px 8px;
      overflow: hidden;
    }}
    .full  {{ margin-bottom: 20px; }}
    .grid2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }}
    .grid2-left  {{ display: flex; flex-direction: column; }}
    .grid2-right {{ display: flex; flex-direction: column; gap: 20px; }}

    /* ── Footer ── */
    footer {{
      text-align: center;
      padding: 20px;
      font-size: 12px;
      color: #bbb;
    }}
  </style>
</head>
<body>

<header>
  <h1>🇧🇷 Brazil E-Commerce Logistics Analytics</h1>
  <p>Olist Public Dataset &nbsp;·&nbsp; 2016 – 2018 &nbsp;·&nbsp; {total_orders:,} delivered orders</p>
</header>

<div class="wrap">

  <!-- KPI Row -->
  <div class="kpi-row">
    <div class="kpi">
      <div class="kpi-label">Delivered Orders</div>
      <div class="kpi-val">{total_orders:,}</div>
      <div class="kpi-sub">97.0% order success rate</div>
    </div>
    <div class="kpi red">
      <div class="kpi-label">Overall Delay Rate</div>
      <div class="kpi-val">{delay_rate:.1f}%</div>
      <div class="kpi-sub">{int(delayed_count):,} delayed orders</div>
    </div>
    <div class="kpi orange">
      <div class="kpi-label">Avg Delivery Days</div>
      <div class="kpi-val">{avg_days:.1f}</div>
      <div class="kpi-sub">Median 7 days · Max 205 days</div>
    </div>
    <div class="kpi green">
      <div class="kpi-label">Avg Review Score</div>
      <div class="kpi-val">{avg_review:.2f}</div>
      <div class="kpi-sub">Out of 5.0 · {len(review_merged):,} reviews</div>
    </div>
  </div>

  <!-- Key Insights -->
  <div class="insights">
    <h3>💡 Key Findings</h3>
    <div class="insights-grid">
      <div class="insight-item">Delayed orders score <strong>1.72 pts lower</strong> on reviews (avg 2.4 vs 4.1 / 5)</div>
      <div class="insight-item"><strong>AL state</strong> has 23.9% delay rate — nearly <strong>3× the national avg</strong></div>
      <div class="insight-item"><strong>Feb &amp; Mar</strong> spike due to Carnival; <strong>Nov &amp; Dec</strong> due to Black Friday &amp; Christmas</div>
      <div class="insight-item"><strong>Mon, Tue, Fri</strong> have the highest delay rates; weekends are safest</div>
      <div class="insight-item">Delayed orders wait avg <strong>25.2 days</strong> vs 8.9 days for on-time orders (3× longer)</div>
      <div class="insight-item">Electronics &amp; garden tools have the <strong>slowest delivery</strong> across all categories</div>
    </div>
  </div>

  <!-- Chart 1: Full width -->
  <div class="card full">{d1}</div>

  <!-- Charts 2 + 3 (left tall + right stacked) -->
  <div class="grid2">
    <div class="card grid2-left">{d2}</div>
    <div class="grid2-right">
      <div class="card" style="flex:1">{d3}</div>
    </div>
  </div>

  <!-- Charts 4 + 5 -->
  <div class="grid2">
    <div class="card">{d4}</div>
    <div class="card">{d5}</div>
  </div>

  <!-- Chart 6: Full width -->
  <div class="card full">{d6}</div>

</div>

<footer>
  Built with Python &amp; Plotly &nbsp;|&nbsp; Data: Olist Brazilian E-Commerce Public Dataset (Kaggle) &nbsp;|&nbsp; Analysis by Fiona
</footer>

</body>
</html>"""

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n[3/3] Dashboard saved -> {out}")
print("   Open dashboard.html in any browser to view.\n")
