"""
Interactive Plotly visualisations for all analyses.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


PALETTE = px.colors.qualitative.Bold
BG = "#0f1117"
FONT_COLOR = "#e0e0e0"

BASE_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor="#1a1d2e",
    font=dict(color=FONT_COLOR, family="Inter, sans-serif"),
    margin=dict(t=60, b=40, l=60, r=40),
)


def fig_phase_success(df: pd.DataFrame) -> go.Figure:
    """Waterfall-style bar chart of completion rates by phase with CI."""
    df_plot = df[~df["suppressed"]].copy()
    df_plot["ci_range"] = df_plot["ci_upper"] - df_plot["ci_lower"]

    fig = go.Figure()
    for i, row in df_plot.iterrows():
        fig.add_trace(go.Bar(
            x=[row["phase_label"]],
            y=[row["completion_rate"]],
            error_y=dict(
                type="data",
                symmetric=False,
                array=[row["ci_upper"] - row["completion_rate"]],
                arrayminus=[row["completion_rate"] - row["ci_lower"]],
                color="#ffd700",
            ),
            marker_color=PALETTE[i % len(PALETTE)],
            name=row["phase_label"],
            text=f"{row['completion_rate']:.0%}<br>n={row['n_evaluable']}",
            textposition="auto",
            hovertemplate=(
                f"<b>{row['phase_label']}</b><br>"
                f"Completion rate: {row['completion_rate']:.1%}<br>"
                f"95% CI: [{row['ci_lower']:.1%}, {row['ci_upper']:.1%}]<br>"
                f"Evaluable: {row['n_evaluable']}<br>"
                f"Total: {row['n_total']}<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="<b>Trial Completion Rate by Phase</b><br>"
              "<sup>Error bars = 95% Wilson CI | Excludes censored trials</sup>",
        yaxis=dict(title="Completion Rate", tickformat=".0%", range=[0, 1.05]),
        xaxis_title="Trial Phase",
        showlegend=False,
        **BASE_LAYOUT,
    )
    return fig


def fig_technology_heatmap(df: pd.DataFrame) -> go.Figure:
    """Heatmap of completion rate by technology × phase."""
    pivot = df.pivot_table(
        index="technology_group",
        columns="phase_label",
        values="completion_rate",
        aggfunc="first",
    )
    n_pivot = df.pivot_table(
        index="technology_group",
        columns="phase_label",
        values="n_evaluable",
        aggfunc="first",
    )

    z = pivot.values
    text = []
    for i in range(pivot.shape[0]):
        row_text = []
        for j in range(pivot.shape[1]):
            val = z[i, j]
            n = n_pivot.values[i, j]
            if pd.notna(val) and pd.notna(n):
                row_text.append(f"{val:.0%}<br>n={int(n)}")
            else:
                row_text.append("")
        text.append(row_text)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        text=text,
        texttemplate="%{text}",
        colorscale="RdYlGn",
        zmin=0, zmax=1,
        colorbar=dict(title="Completion Rate", tickformat=".0%"),
        hoverongaps=False,
    ))

    fig.update_layout(
        title="<b>Completion Rate: Technology Group × Phase</b>",
        xaxis_title="Phase",
        yaxis_title="Technology Group",
        **BASE_LAYOUT,
    )
    return fig


def fig_indication_bars(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """Horizontal bars of completion rate by indication, sorted."""
    df_plot = (
        df[~df["suppressed"]]
        .nlargest(top_n, "n_evaluable")
        .sort_values("completion_rate")
    )

    fig = go.Figure(go.Bar(
        x=df_plot["completion_rate"],
        y=df_plot["indication"],
        orientation="h",
        error_x=dict(
            type="data",
            symmetric=False,
            array=(df_plot["ci_upper"] - df_plot["completion_rate"]).tolist(),
            arrayminus=(df_plot["completion_rate"] - df_plot["ci_lower"]).tolist(),
            color="#ffd700",
        ),
        marker=dict(
            color=df_plot["completion_rate"],
            colorscale="RdYlGn",
            cmin=0, cmax=1,
        ),
        text=[f"{v:.0%}" for v in df_plot["completion_rate"]],
        textposition="auto",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Completion rate: %{x:.1%}<br>"
            "n evaluable: %{customdata}<extra></extra>"
        ),
        customdata=df_plot["n_evaluable"],
    ))

    fig.update_layout(
        title="<b>Completion Rate by Indication</b><br><sup>Top 15 by trial count</sup>",
        xaxis=dict(title="Completion Rate", tickformat=".0%", range=[0, 1.1]),
        yaxis_title="",
        height=600,
        **BASE_LAYOUT,
    )
    return fig


def fig_temporal_trend(df: pd.DataFrame) -> go.Figure:
    """Line chart: completion rate over start year, by phase."""
    df = df[~df["suppressed"] & df["start_year"].notna()].copy()
    df["start_year"] = df["start_year"].astype(int)

    fig = go.Figure()
    for i, phase in enumerate(df["phase_label"].unique()):
        sub = df[df["phase_label"] == phase].sort_values("start_year")
        fig.add_trace(go.Scatter(
            x=sub["start_year"],
            y=sub["completion_rate"],
            mode="lines+markers",
            name=phase,
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            marker=dict(size=8),
            hovertemplate=(
                f"<b>{phase}</b><br>"
                "Year: %{x}<br>"
                "Rate: %{y:.1%}<extra></extra>"
            ),
        ))

    fig.update_layout(
        title="<b>Completion Rate Trend by Phase and Start Year</b>",
        xaxis_title="Trial Start Year",
        yaxis=dict(title="Completion Rate", tickformat=".0%"),
        **BASE_LAYOUT,
    )
    return fig


def save_all_figures(figures: dict[str, go.Figure],
                     output_dir: str = "reports/") -> None:
    """Save all figures as interactive HTML and static PNG."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    for name, fig in figures.items():
        html_path = f"{output_dir}/{name}.html"
        fig.write_html(html_path, include_plotlyjs="cdn")
        print(f"  ✓ {html_path}")
        
        
import plotly.graph_objects as go

def fig_attrition_sankey(df_phases):
    """
    Generates a Sankey diagram showing Phase Attrition.
    df_phases must have columns: phase, count_completed, count_failed, count_censored
    """
    # Define Nodes
    nodes = ["Phase 1", "Phase 2", "Phase 3", "Completed", "Failed/Terminated", "Ongoing (Censored)"]
    
    # Map node names to indices for Plotly
    node_indices = {name: i for i, name in enumerate(nodes)}
    
    # Initialize links
    source = []
    target = []
    value = []
    
    # Helper to safely extract counts
    def get_counts(phase_name):
        row = df_phases[df_phases['phase_label'] == phase_name]
        if row.empty: return 0, 0, 0
        return int(row['n_success'].iloc[0]), int(row['n_evaluable'].iloc[0] - row['n_success'].iloc[0]), int(row['n_total'].iloc[0] - row['n_evaluable'].iloc[0])
    
    p1_comp, p1_fail, p1_cens = get_counts('PHASE1')
    p2_comp, p2_fail, p2_cens = get_counts('PHASE2')
    p3_comp, p3_fail, p3_cens = get_counts('PHASE3')
    
    # Phase 1 to Outcomes
    source.extend([0, 0, 0])
    target.extend([node_indices["Completed"], node_indices["Failed/Terminated"], node_indices["Ongoing (Censored)"]])
    value.extend([p1_comp, p1_fail, p1_cens])
    
    # Phase 2 to Outcomes
    source.extend([1, 1, 1])
    target.extend([node_indices["Completed"], node_indices["Failed/Terminated"], node_indices["Ongoing (Censored)"]])
    value.extend([p2_comp, p2_fail, p2_cens])
    
    # Phase 3 to Outcomes
    source.extend([2, 2, 2])
    target.extend([node_indices["Completed"], node_indices["Failed/Terminated"], node_indices["Ongoing (Censored)"]])
    value.extend([p3_comp, p3_fail, p3_cens])
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 15,
          thickness = 20,
          line = dict(color = "black", width = 0.5),
          label = nodes,
          color = ["blue", "purple", "orange", "green", "red", "gray"]
        ),
        link = dict(
          source = source,
          target = target,
          value = value
      ))])
    
    fig.update_layout(title_text="Clinical Trial Attrition by Phase", font_size=12, height=600)
    return fig
