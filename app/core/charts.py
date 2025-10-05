# app/core/charts.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def radar_chart(skill_avgs: dict):
    """Plotly radar chart for average skill ratings."""
    df = pd.DataFrame({
        "Skill": list(skill_avgs.keys()),
        "Average": list(skill_avgs.values())
    })
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=df["Average"],
            theta=df["Skill"],
            fill="toself",
            name="Performance"
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False,
        title="Skill Averages (Accepted Feedback)"
    )
    return fig


def performance_line_chart(df: pd.DataFrame, skill_cols: list, mode: str = "Time (by Date)"):
    """Line chart showing performance evolution by date or case index."""
    # Defensive copy
    df = df.copy()
    df = df[["Date"] + skill_cols]

    # Adjust x-axis
    if mode == "Number of Cases Practiced":
        df["Cases"] = range(1, len(df) + 1)
        x_col = "Cases"
    else:
        x_col = "Date"

    # Build long format for Plotly
    long_df = df.melt(id_vars=x_col, var_name="Skill", value_name="Rating")
    long_df["Rating"] = pd.to_numeric(long_df["Rating"], errors="coerce")

    fig = px.line(
        long_df,
        x=x_col,
        y="Rating",
        color="Skill",
        title=f"Performance Over {('Time' if mode == 'Time (by Date)' else 'Number of Cases')}",
    )
    fig.update_yaxes(range=[0, 5], title="Rating (1–5)")
    fig.update_xaxes(
        tickformat="%Y-%m-%d" if x_col == "Date" else None,
        title=x_col
    )
    return fig
