# 🇧🇷 Brazil E-Commerce Logistics Analytics

> **End-to-end logistics delay analysis** on the Olist Brazilian E-Commerce public dataset.  
> From raw data to actionable business insights — with interactive dashboard & reproducible Python code.

[![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?logo=pandas)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.0+-3f4c6b?logo=plotly)](https://plotly.com/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter)](https://jupyter.org/)

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Key Findings](#key-findings)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Analysis Walkthrough](#analysis-walkthrough)
- [Interactive Dashboard](#interactive-dashboard)
- [Tech Stack](#tech-stack)
- [How to Run](#how-to-run)
- [Limitations & Future Work](#limitations--future-work)
- [About the Author](#about-the-author)

---

## Project Overview

Brazil's e-commerce market is booming, but **logistics remains a critical bottleneck**.  
This project analyzes **96,470 delivered orders** from Olist (Brazil's largest e-commerce platform) to answer:

1. How long do customers actually wait?
2. Which regions suffer most from delivery delays?
3. Does delay really hurt customer satisfaction?
4. When are delays most likely to happen?

**Approach:** Exploratory data analysis → data cleaning → hypothesis testing → interactive visualization → business recommendations.

---

## Key Findings

| # | Finding | Business Impact |
|---|---------|----------------|
| 1 | **Delayed orders score 1.72 pts lower** on reviews (avg 2.4 vs 4.1 / 5) | Delays have a measurable cost to customer retention |
| 2 | **Alagoas (AL) has a 23.9% delay rate** — nearly 3× the national average (8.1%) | Targeted logistics intervention needed in the Northeast |
| 3 | Delays spike in **Feb & Mar** (Carnival), **Nov & Dec** (Black Friday & Christmas) | Capacity should be pre-scaled before these periods |
| 4 | **Mon, Tue, Fri** have the highest delay rates; weekends are actually safer | Demand-smoothing promotions mid-week could reduce peak pressure |
| 5 | Electronics & garden tools have the **slowest delivery times** across all categories | Root cause: bulky items, specialized handling, or carrier routing |

> 💡 **Core insight:** 8% of orders are delayed, but when delays happen customers wait **3× longer** than average (25.2 days vs 8.9 days).

---

## Dataset

**Source:** [Olist Brazilian E-Commerce Dataset — Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

| File | Rows | Description |
|------|------|-------------|
| `olist_orders_dataset.csv` | 99,441 | Order status, timestamps, delivery dates |
| `olist_order_items_dataset.csv` | 112,650 | Items per order, seller info |
| `olist_customers_dataset.csv` | 99,441 | Customer location (state/city) |
| `olist_products_dataset.csv` | 32,951 | Product specs & categories |
| `olist_sellers_dataset.csv` | 3,095 | Seller location |
| `olist_order_reviews_dataset.csv` | 99,224 | Customer review scores (1–5) |
| `olist_order_payments_dataset.csv` | 103,886 | Payment method & installment info |
| `olist_geolocation_dataset.csv` | 1,000,163 | Zip-code-level lat/lon |
| `product_category_name_translation.csv` | 71 | Portuguese → English category names |

**Time span:** Sep 2016 – Oct 2018  
**Delivery success rate:** 97.0%

---

## Project Structure

```
brazil-logistics-analysis/
├── 01_data_overview.ipynb       # Data loading, schema check, missing value audit
├── 02_delivery_analysis.ipynb   # Delay rate analysis, geographic & seasonal patterns
├── 03_review_analysis.ipynb     # Delay vs. customer satisfaction correlation
├── generate_dashboard.py          # Generates dashboard.html (one-click dashboard)
├── dashboard.html                 # Interactive HTML dashboard (open in browser)
├── archive/                      # Raw CSV datasets (9 files)
└── README.md                     # ← You are here
```

---

## Analysis Walkthrough

### 📓 Notebook 1 — `01_data_overview.ipynb`

**Purpose:** Understand the data before analyzing it.

- Load all 9 CSV files into pandas DataFrames
- Audit missing values (key finding: `order_delivered_customer_date` has 3.0% nulls)
- Detect anomalies (negative delivery days → data entry errors)
- Profile each table: row count, column types, unique values

> ✅ **Why this matters:** Found that `product_category_name` has 1.9% missing values and review comments are 88% empty — both handled gracefully in downstream analysis.

---

### 📓 Notebook 2 — `02_delivery_analysis.ipynb`

**Purpose:** Quantify delivery performance and identify high-risk regions/periods.

**Key analyses:**
- Delivery days distribution (histogram)
- Delay rate by **customer state** (horizontal bar chart)
- Monthly delay rate trend (dual Y-axis: delay % + avg days)
- Delivery days by **product category** (boxplot)

**Code highlight — `groupby` + `first()` pattern:**
```python
# One order may have multiple items → assign the first item's category to the order
order_cat = (items_with_cat
              .groupby('order_id')
              .first()
              .reset_index()[['order_id', 'product_category_name_english']])
```

---

### 📓 Notebook 3 — `03_review_analysis.ipynb`

**Purpose:** Prove the business cost of delays.

**Key analyses:**
- Avg review score: on-time vs. delayed orders
- Review score vs. delay duration (line chart)
- Delay rate by **day of week**
- Delay rate by **month** (seasonal pattern)

**Statistical finding:**
```
On-time orders:  avg review = 4.12 / 5
Delayed orders:  avg review = 2.40 / 5
Gap:            −1.72 points  (p < 0.001, highly significant)
```

---

## Interactive Dashboard

Run one command to generate a self-contained HTML dashboard:

```bash
python generate_dashboard.py
```

Then open `dashboard.html` in any browser — **no server, no dependencies needed.**

### Dashboard Preview

The dashboard includes:

| Section | Charts |
|---------|--------|
| 🔢 **KPI Cards** | Total orders · Overall delay rate · Avg delivery days · Avg review score |
| 📊 **Distribution** | Delivery days histogram (on-time vs. delayed) |
| 🗺️ **Geography** | Delay rate by state (ranked, red = above avg) |
| 📈 **Time Series** | Monthly delay rate + avg days (dual axis) |
| ⭐ **Satisfaction** | On-time vs. delayed review score comparison |
| 📅 **Seasonality** | Day-of-week & monthly delay patterns |

> 💡 All charts are **Plotly interactive** — hover for exact values, zoom in, filter.

---

## Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| **Data wrangling** | `pandas` | Flexible handling of messy real-world data |
| **Visualization** | `plotly` | Interactive charts, publication-quality output |
| **Development** | Jupyter Notebook | Reproducible analysis + narrative |
| **Dashboard** | Plotly HTML export | Zero-dependency sharing (no server needed) |
| **(Alternative)** | SQL + Tableau | Faster for standard BI — but less flexible for custom logic |

---

## How to Run

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/brazil-logistics-analysis.git
cd brazil-logistics-analysis
```

### 2. Install dependencies
```bash
pip install pandas numpy plotly jupyter
```

### 3. Run the notebooks (in order)
```bash
jupyter notebook
# Open: 01_data_overview.ipynb → Run All
# Open: 02_delivery_analysis.ipynb → Run All
# Open: 03_review_analysis.ipynb → Run All
```

### 4. Generate the dashboard
```bash
python generate_dashboard.py
# → opens dashboard.html in your browser
```

---

## Limitations & Future Work

### Current Limitations
- **Geolocation:** `geolocation.csv` has 1M+ rows but is noisy (zip centroids, not exact addresses) — not used in this analysis.
- **Carrier data:** The dataset does not include which logistics carrier handled each order — a key variable for root-cause analysis.
- **Seller-side delay:** We measure customer-facing delay but cannot distinguish "seller processing delay" vs. "carrier transit delay".

### Future Work
- [ ] **Predictive model:** Random Forest / XGBoost to predict delay probability per order.
- [ ] **Seller clustering:** Segment sellers by on-time performance → targeted support programs.
- [ ] **Text mining:** Analyze 40,000+ review comments (non-null) for delay-related keywords.
- [ ] **SQL version:** Port the entire analysis to SQL (BigQuery) → compare Python vs. SQL workflows.

---

## About the Author

**Arwen** — Data Analyst @ Hubei RenFu Co., Ltd.

- 📍 Wuhan, China
- 🛠️ Stack: Python (pandas, Plotly), SQL, Excel, RPA (Shadowbot)
- 🌏 Seeking **remote data roles** (global / English-friendly)
- 💡 Interests: logistics analytics, customer behavior, data storytelling

> *This project was built to demonstrate end-to-end analytical thinking — from asking the right questions to delivering actionable business recommendations.*

---

## License

This project uses the **Olist public dataset** (CC0 public domain).  
Code in this repository is released under the [MIT License](LICENSE).

---

<p align="center">
  <i>⭐ If this project helped you, please consider starring the repo!</i>
</p>
