import plotly.express as px


def generate_chart(df, chart_info):
    """Generates a plotly chart based on AI decision"""

    chart_type = chart_info.get("chart_type", "none")
    x_col = chart_info.get("x_column")
    y_col = chart_info.get("y_column")
    title = chart_info.get("title", "Chart")

    if x_col not in df.columns:
        x_col = df.columns[0]
    if y_col not in df.columns and len(df.columns) > 1:
        y_col = df.columns[1]
    elif y_col not in df.columns:
        y_col = df.columns[0]

    try:
        if chart_type == "bar":
            fig = px.bar(
                df, x=x_col, y=y_col,
                title=title,
                color=x_col,
                template="plotly_white"
            )
        elif chart_type == "line":
            fig = px.line(
                df, x=x_col, y=y_col,
                title=title,
                template="plotly_white",
                markers=True
            )
        elif chart_type == "pie":
            fig = px.pie(
                df,
                names=x_col,
                values=y_col,
                title=title,
                template="plotly_white"
            )
        elif chart_type == "scatter":
            fig = px.scatter(
                df, x=x_col, y=y_col,
                title=title,
                template="plotly_white"
            )
        else:
            return None

        fig.update_layout(
            title_font_size=18,
            title_x=0.5,
            showlegend=True,
            height=400
        )

        return fig

    except Exception:
        return None