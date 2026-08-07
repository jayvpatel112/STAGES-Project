"""
utils.py — STAGES Project data utilities
Bauhaus-Universität Weimar · SoSe 2026
"""
import pandas as pd
import os


# ── I/O ──────────────────────────────────────────────────────────────────────

def load_smard_data(file_name: str, folder: str = 'data') -> pd.DataFrame:
    """Load a raw SMARD CSV from the data/ folder."""
    return pd.read_csv(os.path.join(folder, file_name), sep=';',
                       encoding='utf-8-sig', low_memory=False)


def save_cleaned_data(df: pd.DataFrame, file_name: str = "cleaned_smard_data.csv") -> str:
    folder_path = os.path.join('data', 'cleaned')
    os.makedirs(folder_path, exist_ok=True)
    path = os.path.join(folder_path, file_name)
    df.to_csv(path, index=False)
    return path


def load_cleaned_data(file_name: str = "cleaned_smard_data.csv") -> pd.DataFrame:
    df = pd.read_csv(os.path.join('data', 'cleaned', file_name), low_memory=False)
    df['Date'] = pd.to_datetime(df['Date'])
    return df


# ── Cleaning ─────────────────────────────────────────────────────────────────

def _parse_mwh(series: pd.Series) -> pd.Series:
    """Convert SMARD-formatted MWh strings to float."""
    return pd.to_numeric(
        series.astype(str)
            .str.replace(',', '', regex=False)
            .str.replace('-', '0', regex=False),
        errors='coerce'
    ).fillna(0)


def clean_generation_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the Actual_generation SMARD export.
    Returns a tidy DataFrame with one column per source and a 'Date' column.
    """
    col_map = {
        'Biomass [MWh] Calculated resolutions':          'Biomass',
        'Hydropower [MWh] Calculated resolutions':       'Hydro',
        'Wind offshore [MWh] Calculated resolutions':    'Wind_Offshore',
        'Wind onshore [MWh] Calculated resolutions':     'Wind_Onshore',
        'Photovoltaics [MWh] Calculated resolutions':    'Solar',
        'Other renewable [MWh] Calculated resolutions':  'Other_Renewable',
        'Nuclear [MWh] Calculated resolutions':          'Nuclear',
        'Lignite [MWh] Calculated resolutions':          'Lignite',
        'Hard coal [MWh] Calculated resolutions':        'Hard_Coal',
        'Fossil gas [MWh] Calculated resolutions':       'Gas',
        'Hydro pumped storage [MWh] Calculated resolutions': 'Pumped_Storage',
        'Other conventional [MWh] Calculated resolutions':   'Other_Conventional',
    }
    out = df.rename(columns=col_map).copy()
    out['Date'] = pd.to_datetime(out['Start date'], format='%b %d, %Y %I:%M %p')

    for col in col_map.values():
        if col in out.columns:
            out[col] = _parse_mwh(out[col])

    return out[['Date'] + list(col_map.values())]


def clean_consumption_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the Actual_consumption SMARD export.
    Returns a tidy DataFrame with consumption columns and a 'Date' column.

    Columns returned:
        Grid_Load      — total electricity drawn from the grid (MWh/h)
        Grid_Load_incl_Pumped — load including pumped storage demand
        Pumped_Demand  — electricity consumed by pumped-storage plants
        Residual_Load  — demand that renewables alone cannot cover
                         (= Grid_Load − renewable generation)
                         A low/negative value means renewables overproduce!
    """
    col_map = {
        'grid load [MWh] Calculated resolutions':
            'Grid_Load',
        'Grid load incl. hydro pumped storage [MWh] Calculated resolutions':
            'Grid_Load_incl_Pumped',
        'Hydro pumped storage [MWh] Calculated resolutions':
            'Pumped_Demand',
        'Residual load [MWh] Calculated resolutions':
            'Residual_Load',
    }
    out = df.rename(columns=col_map).copy()
    out['Date'] = pd.to_datetime(out['Start date'], format='%b %d, %Y %I:%M %p')

    for col in col_map.values():
        if col in out.columns:
            out[col] = _parse_mwh(out[col])

    return out[['Date'] + [c for c in col_map.values() if c in out.columns]]


# ── Feature Engineering ───────────────────────────────────────────────────────

def add_generation_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add aggregate columns to the cleaned generation DataFrame."""
    df = df.copy()
    df['Total_Wind']      = df['Wind_Onshore'] + df['Wind_Offshore']
    df['Total_Renewable'] = (
        df['Solar'] + df['Total_Wind'] +
        df['Biomass'] + df['Hydro'] + df['Other_Renewable']
    )
    df['Total_Fossil']    = (
        df['Lignite'] + df['Hard_Coal'] +
        df['Gas'] + df['Other_Conventional']
    )
    df['Total_Generation'] = (
        df['Total_Renewable'] + df['Total_Fossil'] + df['Pumped_Storage']
    )
    df['Renewable_Share_Pct'] = (
        df['Total_Renewable'] / df['Total_Generation'] * 100
    ).fillna(0)
    return df


def merge_generation_consumption(gen_df: pd.DataFrame,
                                  con_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge cleaned generation and consumption DataFrames on 'Date'.
    Adds coverage ratio: how much of demand is met by domestic generation.
    """
    df = gen_df.merge(con_df, on='Date', how='inner')
    df['Coverage_Pct'] = df['Total_Generation'] / df['Grid_Load'] * 100
    return df


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate hourly merged DataFrame to daily totals."""
    df = df.copy()
    df['day'] = df['Date'].dt.date
    daily = df.groupby('day').sum(numeric_only=True).reset_index()
    daily['Date'] = pd.to_datetime(daily['day'])
    daily['Renewable_Share_Pct'] = (
        daily['Total_Renewable'] / daily['Total_Generation'] * 100
    )
    daily['Coverage_Pct'] = daily['Total_Generation'] / daily['Grid_Load'] * 100
    daily['Month'] = daily['Date'].dt.strftime('%B')
    return daily


def compute_summary(df: pd.DataFrame) -> dict:
    """Return a dict of high-level KPIs from an hourly or daily DataFrame."""
    total_gen   = df['Total_Generation'].sum() / 1e6
    total_ren   = df['Total_Renewable'].sum() / 1e6
    total_load  = df['Grid_Load'].sum() / 1e6
    daily       = aggregate_daily(df) if 'day' not in df.columns else df

    return {
        'total_generation_twh':  total_gen,
        'total_load_twh':        total_load,
        'renewable_share_pct':   total_ren / total_gen * 100,
        'solar_twh':             df['Solar'].sum() / 1e6,
        'wind_twh':              (df.get('Total_Wind', df.get('Wind_Onshore', 0) +
                                          df.get('Wind_Offshore', 0))).sum() / 1e6,
        'avg_coverage_pct':      daily['Coverage_Pct'].mean(),
        'dunkelflaute_days':     len(daily[daily['Renewable_Share_Pct'] < 30]),
        'low_renewable_days':    len(daily[daily['Renewable_Share_Pct'] < 50]),
        'best_day':              daily.loc[daily['Renewable_Share_Pct'].idxmax()],
        'worst_day':             daily.loc[daily['Renewable_Share_Pct'].idxmin()],
    }


def generate_insights(summary: dict) -> str:
    return f"""
## 🎯 STAGES Project — Key Findings

### Summary Statistics
- **Total Generation:** {summary['total_generation_twh']:.2f} TWh
- **Total Demand (Grid Load):** {summary['total_load_twh']:.2f} TWh
- **Renewable Share:** {summary['renewable_share_pct']:.1f}%
- **Average Coverage:** {summary['avg_coverage_pct']:.1f}%
  *(how much of demand domestic generation covers)*

### Renewable Breakdown
- ☀️ Solar: **{summary['solar_twh']:.2f} TWh**
- 🌬️ Wind: **{summary['wind_twh']:.2f} TWh**

### Risk Assessment
- ⚠️ Days with <50% renewable share: **{summary['low_renewable_days']}**
- 🌑 Dunkelflaute days (<30%): **{summary['dunkelflaute_days']}**

### Record Days
- 🏆 Best renewable day: {summary['best_day']['Date'].date()} 
  ({summary['best_day']['Renewable_Share_Pct']:.1f}%)
- 📉 Worst renewable day: {summary['worst_day']['Date'].date()} 
  ({summary['worst_day']['Renewable_Share_Pct']:.1f}%)
"""