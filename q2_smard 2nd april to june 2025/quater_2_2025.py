import marimo

__generated_with = "0.23.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import altair as alt
    alt.data_transformers.enable("vegafusion")
    return alt, mo, pd


@app.cell
def _(mo):
    mo.md(r"""
    # ⚡ Germany's Electricity: Can Renewables Power the Nation?
    ### STAGES Project · Bauhaus-Universität Weimar · SoSe 2026
    **Prof. Dr. Björn Rüffer & Dr. habil. Michael Schönlein** · Chair of Applied Mathematics

    ---

    > **What this analysis is about:** Germany has made a bold bet on renewable energy —
    > wind turbines, solar panels, hydropower, and biomass plants.
    > But can these sources actually *cover* what the country needs?
    > This dashboard explores 3 months of real grid data (April–June 2025)
    > to answer that question visually and honestly.

    **Data source:** [SMARD – Bundesnetzagentur](https://www.smard.de/en/downloadcenter/download-market-data/)
    · Hourly resolution · April 1 – June 30, 2025
    """)
    return


@app.cell
def _(pd):
    # ── Load & Clean ──────────────────────────────────────────────────────────
    def parse_mwh(s):
        return pd.to_numeric(
            s.astype(str)
            .str.replace(',', '', regex=False)
            .str.replace('-', '0', regex=False),
            errors='coerce'
        ).fillna(0)

    gen_raw = pd.read_csv(
        'data/Actual_generation_202504010000_202507010000_Hour.csv',
        sep=';', encoding='utf-8-sig'
    )
    con_raw = pd.read_csv(
        'data/Actual_consumption_202504010000_202507010000_Hour.csv',
        sep=';', encoding='utf-8-sig'
    )

    gen_raw['Date'] = pd.to_datetime(gen_raw['Start date'], format='%b %d, %Y %I:%M %p')
    con_raw['Date'] = pd.to_datetime(con_raw['Start date'], format='%b %d, %Y %I:%M %p')

    for col in gen_raw.columns[2:-1]:
        gen_raw[col] = parse_mwh(gen_raw[col])
    for col in con_raw.columns[2:-1]:
        con_raw[col] = parse_mwh(con_raw[col])

    gen = gen_raw.copy()
    gen['Solar']     = gen['Photovoltaics [MWh] Calculated resolutions']
    gen['Wind_Off']  = gen['Wind offshore [MWh] Calculated resolutions']
    gen['Wind_On']   = gen['Wind onshore [MWh] Calculated resolutions']
    gen['Wind']      = gen['Wind_Off'] + gen['Wind_On']
    gen['Biomass']   = gen['Biomass [MWh] Calculated resolutions']
    gen['Hydro']     = gen['Hydropower [MWh] Calculated resolutions']
    gen['Other_Ren'] = gen['Other renewable [MWh] Calculated resolutions']
    gen['Lignite']   = gen['Lignite [MWh] Calculated resolutions']
    gen['HardCoal']  = gen['Hard coal [MWh] Calculated resolutions']
    gen['Gas']       = gen['Fossil gas [MWh] Calculated resolutions']
    gen['OtherConv'] = gen['Other conventional [MWh] Calculated resolutions']
    gen['Pumped']    = gen['Hydro pumped storage [MWh] Calculated resolutions']

    gen['Total_Ren']   = gen[['Solar','Wind','Biomass','Hydro','Other_Ren']].sum(axis=1)
    gen['Total_Fossil']= gen[['Lignite','HardCoal','Gas','OtherConv']].sum(axis=1)
    gen['Total_Gen']   = gen['Total_Ren'] + gen['Total_Fossil'] + gen['Pumped']

    con = con_raw.copy()
    con['Grid_Load'] = con['grid load [MWh] Calculated resolutions']
    con['Residual']  = con['Residual load [MWh] Calculated resolutions']

    # Merge
    df = gen[['Date','Solar','Wind','Wind_Off','Wind_On','Biomass','Hydro',
              'Other_Ren','Lignite','HardCoal','Gas','OtherConv','Pumped',
              'Total_Ren','Total_Fossil','Total_Gen']].merge(
        con[['Date','Grid_Load','Residual']], on='Date'
    )
    df['Ren_Share'] = df['Total_Ren'] / df['Total_Gen'] * 100
    df['Coverage']  = df['Total_Gen'] / df['Grid_Load'] * 100
    df['Month']     = df['Date'].dt.strftime('%B')
    df['Hour']      = df['Date'].dt.hour
    df['day']       = df['Date'].dt.date

    # Daily aggregation
    daily = df.groupby('day').sum(numeric_only=True).reset_index()
    daily['Date']      = pd.to_datetime(daily['day'])
    daily['Ren_Share'] = daily['Total_Ren'] / daily['Total_Gen'] * 100
    daily['Coverage']  = daily['Total_Gen'] / daily['Grid_Load'] * 100
    daily['Month']     = daily['Date'].dt.strftime('%B')

    print("Data loaded:", len(df), "hourly rows,", len(daily), "daily rows")
    df, daily
    return daily, df


@app.cell
def _(daily, df, mo):
    # ── KPI Callouts ──────────────────────────────────────────────────────────
    total_twh     = round(df['Total_Gen'].sum() / 1e6, 1)
    ren_pct       = round(df['Total_Ren'].sum() / df['Total_Gen'].sum() * 100, 1)
    avg_load_gw   = round(df['Grid_Load'].mean() / 1000, 1)
    best_day      = daily.loc[daily['Ren_Share'].idxmax()]
    worst_day     = daily.loc[daily['Ren_Share'].idxmin()]
    low_ren_days  = len(daily[daily['Ren_Share'] < 40])
    coverage_avg  = round(daily['Coverage'].mean(), 1)

    mo.md(f"""
    ## 📊 The Big Picture: April – June 2025

    > Germany generated **{total_twh} TWh** of electricity over these 3 months,
    > with renewables covering **{ren_pct}%** of all generation.
    > On average, the grid demanded **{avg_load_gw} GW** every single hour.

    | Metric | Value | What it means |
    |--------|-------|--------------|
    | 🌱 Renewable share | **{ren_pct}%** | Of every 3 units of electricity, 2 came from renewables |
    | 📅 Best renewable day | **{best_day['Date'].strftime('%b %d')} ({round(best_day['Ren_Share'],1)}%)** | Almost entirely green electricity |
    | 📅 Lowest renewable day | **{worst_day['Date'].strftime('%b %d')} ({round(worst_day['Ren_Share'],1)}%)** | Still nearly half from renewables! |
    | ⚠️ Low-renewable days (<40%) | **{low_ren_days} days** | Days when fossils had to step in significantly |
    | 🔌 Avg. generation coverage | **{coverage_avg}%** | Germany generates roughly what it consumes |

    ---
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 🥧 Where Does Germany's Electricity Come From?

    > Think of Germany's electricity grid like a **pie being baked every hour**.
    > Different "ingredients" — solar, wind, gas, coal — are mixed in constantly changing proportions.
    > The chart below shows the *total contribution* of each source over the whole 3-month period.
    """)
    return


@app.cell
def _(alt, df):
    # ── Donut / Pie of total mix ──────────────────────────────────────────────
    source_totals = {
        'Solar':       df['Solar'].sum() / 1e6,
        'Wind':        df['Wind'].sum() / 1e6,
        'Biomass':     df['Biomass'].sum() / 1e6,
        'Hydro':       df['Hydro'].sum() / 1e6,
        'Other Ren.':  df['Other_Ren'].sum() / 1e6,
        'Lignite':     df['Lignite'].sum() / 1e6,
        'Hard Coal':   df['HardCoal'].sum() / 1e6,
        'Gas':         df['Gas'].sum() / 1e6,
        'Other Conv.': df['OtherConv'].sum() / 1e6,
    }
    import pandas as pd_inner
    pie_df = pd_inner.DataFrame([
        {'Source': k, 'TWh': round(v, 2),
         'Type': 'Renewable' if k in ['Solar','Wind','Biomass','Hydro','Other Ren.'] else 'Fossil/Conv.'}
        for k, v in source_totals.items()
    ])

    color_map = {
        'Solar': '#F59E0B', 'Wind': '#3B82F6', 'Biomass': '#22C55E',
        'Hydro': '#06B6D4', 'Other Ren.': '#A3E635',
        'Lignite': '#78350F', 'Hard Coal': '#44403C',
        'Gas': '#9CA3AF', 'Other Conv.': '#D4D4D8'
    }

    pie_chart = alt.Chart(pie_df).mark_arc(innerRadius=80, outerRadius=160).encode(
        theta=alt.Theta('TWh:Q'),
        color=alt.Color('Source:N',
            scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
            legend=alt.Legend(title='Energy Source', orient='right')
        ),
        tooltip=[
            alt.Tooltip('Source:N', title='Source'),
            alt.Tooltip('TWh:Q', title='Total (TWh)', format='.2f'),
            alt.Tooltip('Type:N', title='Category')
        ]
    ).properties(
        title='Total Electricity Mix — April to June 2025',
        width=500, height=380
    )
    pie_chart
    return


@app.cell
def _(mo):
    mo.md("""
    > 🟡 **Solar** and 🔵 **Wind** are the two giants of renewable electricity.
    > Brown tones (lignite, hard coal) represent fossil fuels —
    > these emit CO₂ and are being phased out under Germany's *Energiewende* policy.
    > Notice how renewables collectively dwarf the fossil sources in spring/summer.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 📈 Daily Generation: Renewables vs. Fossils Over Time

    > Each bar below represents **one day** of electricity production.
    > The green portion = renewable energy. The grey/brown portion = fossil fuels.
    > Watch how the green bar rises and falls — this is **weather at work**.
    > On sunny, windy days, green dominates. On calm, overcast days, fossils fill the gap.
    """)
    return


@app.cell
def _(alt, daily):
    # ── Stacked bar: daily ren vs fossil ─────────────────────────────────────
    import pandas as pd2
    stack_df = pd2.melt(
        daily[['Date','Total_Ren','Total_Fossil']],
        id_vars='Date',
        var_name='Type', value_name='MWh'
    )
    stack_df['GWh'] = stack_df['MWh'] / 1000
    stack_df['Label'] = stack_df['Type'].map({
        'Total_Ren': '🌱 Renewables', 'Total_Fossil': '🏭 Fossil Fuels'
    })

    bar = alt.Chart(stack_df).mark_bar(size=5).encode(
        x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %d', labelAngle=-45)),
        y=alt.Y('GWh:Q', title='Daily Generation (GWh)', stack='zero'),
        color=alt.Color('Label:N',
            scale=alt.Scale(
                domain=['🌱 Renewables', '🏭 Fossil Fuels'],
                range=['#22C55E', '#78350F']
            ),
            legend=alt.Legend(title='Source Type')
        ),
        tooltip=[
            alt.Tooltip('Date:T', format='%B %d, %Y'),
            alt.Tooltip('Label:N', title='Type'),
            alt.Tooltip('GWh:Q', title='Generation (GWh)', format='.0f')
        ]
    ).properties(
        title='Daily Electricity Generation: Renewable vs. Fossil (Apr–Jun 2025)',
        width=900, height=350
    ).interactive()
    bar
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 🔌 Supply vs. Demand: Is Generation Keeping Up?

    > **The most important question:** Does Germany produce *enough* electricity to meet its needs?
    >
    > The chart below compares **total generation** (what power plants produce)
    > against **grid load** (what households, factories, and businesses actually consume).
    > The gap between them tells us whether Germany needed to *import* electricity
    > or had *surplus* to export.

    > **Residual load** = the portion of demand that renewables *cannot* cover alone —
    > the gap that gas, coal, or imports must fill. When this goes to zero or negative,
    > renewables are producing *more* than the country needs!
    """)
    return


@app.cell
def _(alt, daily):
    # ── Supply vs Demand line chart ───────────────────────────────────────────
    import pandas as pd3
    sv_df = pd3.melt(
        daily[['Date','Total_Gen','Grid_Load','Residual']].assign(
            Total_Gen=daily['Total_Gen']/1000,
            Grid_Load=daily['Grid_Load']/1000,
            Residual=daily['Residual']/1000
        ),
        id_vars='Date', var_name='Metric', value_name='GWh'
    )
    label_map = {
        'Total_Gen': '⚡ Total Generation',
        'Grid_Load': '🏠 Grid Demand (Load)',
        'Residual':  '🔺 Residual Load (Fossils needed)'
    }
    sv_df['Label'] = sv_df['Metric'].map(label_map)

    supply_chart = alt.Chart(sv_df).mark_line(strokeWidth=2).encode(
        x=alt.X('Date:T', title='Date', axis=alt.Axis(format='%b %d', labelAngle=-45)),
        y=alt.Y('GWh:Q', title='Daily Total (GWh)'),
        color=alt.Color('Label:N',
            scale=alt.Scale(
                domain=list(label_map.values()),
                range=['#3B82F6', '#F59E0B', '#EF4444']
            ),
            legend=alt.Legend(title='')
        ),
        strokeDash=alt.StrokeDash('Label:N',
            scale=alt.Scale(
                domain=list(label_map.values()),
                range=[[1,0],[4,2],[6,3]]
            )
        ),
        tooltip=[
            alt.Tooltip('Date:T', format='%B %d, %Y'),
            alt.Tooltip('Label:N'),
            alt.Tooltip('GWh:Q', title='GWh', format='.0f')
        ]
    ).properties(
        title='Daily Supply vs. Demand — Germany, Apr–Jun 2025',
        width=900, height=350
    ).interactive()
    supply_chart
    return


@app.cell
def _(mo):
    mo.md("""
    > 🔵 **Blue line** = total electricity generated.
    > 🟡 **Yellow dashed** = actual demand (what's needed).
    > 🔴 **Red dotted** = the portion renewables *couldn't* cover (residual load).
    >
    > When the red line drops low, it means renewables were doing a great job.
    > When it spikes, fossil plants had to work hard to fill the gap.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## ☀️🌬️ A Closer Look: Solar vs. Wind — The Two Workhorses

    > Solar and wind together provide the majority of Germany's renewable electricity.
    > But they work very differently:
    > - **Solar** is predictable (peaks at noon, zero at night, stronger in summer)
    > - **Wind** is variable (can be strong any time, but unpredictable)
    >
    > Together, they *complement* each other — which is exactly what grid planners need.
    > The chart below shows their daily output side by side across the full period.
    """)
    return


@app.cell
def _(alt, daily):
    # ── Solar vs Wind dual-axis ───────────────────────────────────────────────
    import pandas as pd4
    sw_df = pd4.melt(
        daily[['Date','Solar','Wind']].assign(
            Solar=daily['Solar']/1000,
            Wind=daily['Wind']/1000
        ),
        id_vars='Date', var_name='Source', value_name='GWh'
    )

    solar_wind = alt.Chart(sw_df).mark_area(opacity=0.65).encode(
        x=alt.X('Date:T', axis=alt.Axis(format='%b %d', labelAngle=-45)),
        y=alt.Y('GWh:Q', title='Daily Generation (GWh)', stack=None),
        color=alt.Color('Source:N',
            scale=alt.Scale(
                domain=['Solar','Wind'],
                range=['#F59E0B','#3B82F6']
            )
        ),
        tooltip=[
            alt.Tooltip('Date:T', format='%B %d'),
            alt.Tooltip('Source:N'),
            alt.Tooltip('GWh:Q', title='GWh', format='.0f')
        ]
    ).properties(
        title='Solar ☀️ vs. Wind 🌬️ — Daily Generation (overlaid)',
        width=900, height=300
    ).interactive()
    solar_wind
    return


@app.cell
def _(mo):
    mo.md("""
    > Notice how **solar (orange)** ramps up from April to June as days get longer —
    > this is the seasonal effect of the sun's angle. Wind (blue) has no such pattern;
    > it comes in bursts and lulls independent of the month.
    > On days where wind is low AND solar is weak (cloudy, calm days),
    > the grid becomes more dependent on fossil fuels.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## ⏰ When Do We Use the Most Electricity? — Hourly Patterns

    > Electricity demand is not constant — it follows daily human rhythms.
    > The chart below shows the **average generation and consumption by hour of day**,
    > averaged across all 91 days. This reveals the **daily heartbeat** of Germany's grid.
    >
    > Key things to spot:
    > - ☀️ Solar peaks sharply around **noon**
    > - 🏠 Demand peaks in **morning and evening** (when people wake up and come home)
    > - 🌙 At night, everything quiets down — but wind keeps running!
    """)
    return


@app.cell
def _(alt, df):
    import pandas as pd5
    hourly_avg = df.groupby('Hour')[['Solar','Wind','Grid_Load','Total_Ren','Total_Fossil']].mean().reset_index()
    hourly_avg_gw = hourly_avg.copy()
    for c in ['Solar','Wind','Grid_Load','Total_Ren','Total_Fossil']:
        hourly_avg_gw[c] = hourly_avg_gw[c] / 1000

    h_melt = pd5.melt(
        hourly_avg_gw[['Hour','Solar','Wind','Grid_Load']],
        id_vars='Hour', var_name='Metric', value_name='GW'
    )
    hlabel = {'Solar':'☀️ Solar','Wind':'🌬️ Wind','Grid_Load':'🏠 Demand'}
    h_melt['Label'] = h_melt['Metric'].map(hlabel)

    hourly_chart = alt.Chart(h_melt).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X('Hour:O', title='Hour of Day (0=midnight, 12=noon)'),
        y=alt.Y('GW:Q', title='Average Power (GW)'),
        color=alt.Color('Label:N',
            scale=alt.Scale(
                domain=list(hlabel.values()),
                range=['#F59E0B','#3B82F6','#EF4444']
            )
        ),
        tooltip=[
            alt.Tooltip('Hour:O', title='Hour'),
            alt.Tooltip('Label:N'),
            alt.Tooltip('GW:Q', title='Avg GW', format='.2f')
        ]
    ).properties(
        title='Average Hourly Power — Solar, Wind, and Demand (Apr–Jun 2025)',
        width=700, height=320
    )
    hourly_chart
    return


@app.cell
def _(mo):
    mo.md("""
    > This chart exposes a critical challenge: **solar peaks when demand is lower** (midday),
    > while **demand peaks when solar is weak** (morning/evening).
    > This "duck curve" problem is why energy *storage* (like batteries or pumped hydro)
    > is crucial for a fully renewable grid.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 📅 Monthly Comparison: How Did Each Month Perform?

    > Spring transitions into summer between April and June.
    > How does this seasonal shift affect Germany's renewable performance?
    """)
    return


@app.cell
def _(alt, daily):
    import pandas as pd6
    month_order = ['April', 'May', 'June']
    monthly = daily.groupby('Month')[['Total_Ren','Total_Fossil','Grid_Load','Solar','Wind']].sum().reset_index()
    monthly['Ren_Share'] = monthly['Total_Ren'] / (monthly['Total_Ren'] + monthly['Total_Fossil']) * 100
    monthly['Solar_GWh'] = monthly['Solar'] / 1000
    monthly['Wind_GWh'] = monthly['Wind'] / 1000
    monthly['Month_order'] = monthly['Month'].map({'April':0,'May':1,'June':2})
    monthly = monthly.sort_values('Month_order')

    m_melt = pd6.melt(
        monthly[['Month','Solar_GWh','Wind_GWh']],
        id_vars='Month', var_name='Source', value_name='GWh'
    )
    mlabel = {'Solar_GWh':'☀️ Solar','Wind_GWh':'🌬️ Wind'}
    m_melt['Label'] = m_melt['Source'].map(mlabel)

    bars = alt.Chart(m_melt).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X('Month:N', sort=month_order, title=''),
        y=alt.Y('GWh:Q', title='Total Generation (GWh)'),
        color=alt.Color('Label:N',
            scale=alt.Scale(domain=list(mlabel.values()), range=['#F59E0B','#3B82F6'])
        ),
        column=alt.Column('Label:N', title=''),
        tooltip=[alt.Tooltip('Month:N'), alt.Tooltip('GWh:Q', format='.0f')]
    ).properties(width=200, height=280, title='Monthly Solar & Wind Generation')

    # Renewable share line
    ren_line = alt.Chart(monthly).mark_bar(color='#22C55E', cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X('Month:N', sort=month_order, title='Month'),
        y=alt.Y('Ren_Share:Q', title='Renewable Share (%)', scale=alt.Scale(domain=[0,100])),
        tooltip=[alt.Tooltip('Month:N'), alt.Tooltip('Ren_Share:Q', title='Ren. Share %', format='.1f')]
    ).properties(width=300, height=280, title='Monthly Renewable Share (%)')

    alt.hconcat(bars, ren_line).resolve_scale(y='independent')
    return


@app.cell
def _(mo):
    mo.md("""
    > **June is a standout month** — longer days mean more solar hours, pushing renewable
    > share to its highest point. May brings a mix of spring wind and growing solar.
    > April still relies more on wind due to fewer sunny hours.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 🌑 The *Dunkelflaute* Risk — When Renewables Fall Short

    > A *Dunkelflaute* (German: "dark doldrums") is a period of several days
    > with **both low wind AND low sunshine** — the worst-case scenario for a renewable grid.
    > During these periods, the residual load (what fossils must cover) spikes dramatically.
    >
    > The chart below highlights days where renewable share dropped below **50%**,
    > colored by how severe the shortfall was.
    """)
    return


@app.cell
def _(alt, daily):
    # Highlight low-renewable days
    dk = daily.copy()
    dk['Risk'] = 'Normal (≥60%)'
    dk.loc[dk['Ren_Share'] < 60, 'Risk'] = 'Watch zone (50–60%)'
    dk.loc[dk['Ren_Share'] < 50, 'Risk'] = '⚠️ Low renewable (<50%)'

    risk_colors = {
        'Normal (≥60%)': '#22C55E',
        'Watch zone (50–60%)': '#F59E0B',
        '⚠️ Low renewable (<50%)': '#EF4444'
    }

    risk_chart = alt.Chart(dk).mark_bar(size=6).encode(
        x=alt.X('Date:T', axis=alt.Axis(format='%b %d', labelAngle=-45)),
        y=alt.Y('Ren_Share:Q', title='Daily Renewable Share (%)',
                scale=alt.Scale(domain=[0,100])),
        color=alt.Color('Risk:N',
            scale=alt.Scale(domain=list(risk_colors.keys()), range=list(risk_colors.values())),
            legend=alt.Legend(title='Renewable Level')
        ),
        tooltip=[
            alt.Tooltip('Date:T', format='%B %d, %Y'),
            alt.Tooltip('Ren_Share:Q', title='Renewable Share %', format='.1f'),
            alt.Tooltip('Risk:N', title='Status')
        ]
    ).properties(
        title='Daily Renewable Share — Risk Assessment (Apr–Jun 2025)',
        width=900, height=320
    ).interactive()

    # Add 50% reference line
    rule = alt.Chart(alt.Data(values=[{'y': 50}])).mark_rule(
        color='red', strokeDash=[6,3], strokeWidth=1.5
    ).encode(y='y:Q')

    (risk_chart + rule)
    return


@app.cell
def _(daily, mo):
    low_days = len(daily[daily['Ren_Share'] < 50])
    watch_days = len(daily[(daily['Ren_Share'] >= 50) & (daily['Ren_Share'] < 60)])
    mo.md(f"""
    > In this period, there were **{low_days} days** where renewables covered less than 50% of generation,
    > and **{watch_days} days** in the "watch zone" (50–60%).
    > These are the days when gas and coal plants had to work hardest.
    > Understanding the *frequency and duration* of such periods is a core objective of the STAGES project.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## 🗺️ Project Planning: What Comes Next?

    > This initial analysis covers just **3 months**. The full STAGES project will extend this
    > to a multi-year view and add **weather data** to explain *why* renewables fluctuate.

    ### 🎯 Project Objectives

    | # | Objective | Key Question |
    |---|-----------|-------------|
    | 1 | **Analyze the energy transition** | How has Germany's renewable share evolved over the past decade? |
    | 2 | **Quantify weather dependency** | How strongly do wind speed & sunshine correlate with actual generation? |
    | 3 | **Identify vulnerability periods** | How often does *Dunkelflaute* occur, and how long does it last? |
    | 4 | **Build an interactive dashboard** | How can we make this data accessible to non-experts? |

    ### ❓ Research Questions to Explore

    1. Can renewables **fully replace** Germany's average electricity demand — and for how long?
    2. What is the **minimum backup capacity** (gas/storage) needed to guarantee supply?
    3. How does renewable generation vary **seasonally** (summer vs. winter)?
    4. What is the **typical duration** of a low-renewable period — hours, days, or weeks?
    5. Is Germany becoming **more or less reliant** on imports during low-renewable periods?
    6. How does the **residual load** (fossils + imports) trend over years? Is it declining?

    ### 📋 Action Items & Timeline

    | Week | Task | Owner |
    |------|------|-------|
    | Week 1–2 | Define project scope, download multi-year data | Whole team |
    | Week 2–3 | Clean & document data pipeline | Data team |
    | Week 3–4 | Extend analysis to 2015–2025 historical data | Analysis team |
    | Week 4–6 | Download & merge DWD weather data | Data team |
    | Week 5–7 | Correlation analysis (weather ↔ generation) | Analysis team |
    | Week 7–9 | Dunkelflaute detection & statistical analysis | Analysis team |
    | Week 8–10 | Dashboard development (Marimo/GitHub Pages) | Dev team |
    | Week 10–12 | Report writing (each section follows an objective) | Whole team |
    | **July 10** | **📬 Report submission (via email)** | **All** |

    ### 📦 Recommended Additional Data Sources

    - **[DWD Open Data (CDC)](https://opendata.dwd.de/climate_environment/CDC/)** — German weather service: wind speed, sunshine hours, temperature by station
    - **[Energy-Charts (Fraunhofer ISE)](https://energy-charts.info/)** — Great for validation and installed capacity data
    - **[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)** — Cross-border flows (imports/exports)
    - **[AGEB](https://ag-energiebilanzen.de/)** — Annual energy balances including heating/transport

    ---
    *STAGES Project · Bauhaus-Universität Weimar · SoSe 2026*
    """)
    return


if __name__ == "__main__":
    app.run()
