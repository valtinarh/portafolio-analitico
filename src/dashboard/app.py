import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import psycopg2
from datetime import date

def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="inversiones_clientes",
        user="postgres",
        password="1234"
    )

def query_to_df(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

app = dash.Dash(__name__)

# ─── Estilos globales ───────────────────────────────────────────────────────
COLORS = {
    "bg":        "#0f172a",
    "card":      "#1e293b",
    "accent":    "#38bdf8",
    "accent2":   "#818cf8",
    "accent3":   "#34d399",
    "text":      "#f1f5f9",
    "subtext":   "#94a3b8",
    "border":    "#334155",
}

card_style = {
    "background":   COLORS["card"],
    "borderRadius": "12px",
    "padding":      "20px 24px",
    "border":       f"1px solid {COLORS['border']}",
    "flex":         "1",
    "minWidth":     "160px",
    "textAlign":    "center",
}

graph_style = {
    "background":   COLORS["card"],
    "borderRadius": "12px",
    "padding":      "16px",
    "border":       f"1px solid {COLORS['border']}",
    "flex":         "1",
    "minWidth":     "300px",
}

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"], family="Inter, sans-serif"),
    margin=dict(t=50, b=20, l=20, r=20),
)

# ─── Carga inicial de clientes (portafolio total) ────────────────────────────
clientes_df = query_to_df("""
    SELECT DISTINCT id_sistema_cliente
    FROM views.vw_portafolio_total
    ORDER BY id_sistema_cliente
""")

fechas_df = query_to_df("""
    SELECT DISTINCT
        TO_DATE(
            ingestion_year || '-' ||
            LPAD(SPLIT_PART(ingestion_month::text, '.', 1), 2, '0') || '-' ||
            LPAD(SPLIT_PART(ingestion_day::text,   '.', 1), 2, '0'),
            'YYYY-MM-DD'
        ) AS fecha
    FROM views.vw_portafolio_total
    ORDER BY fecha
""")
min_fecha = fechas_df["fecha"].min()
max_fecha = fechas_df["fecha"].max()

# ─── Layout ─────────────────────────────────────────────────────────────────
app.layout = html.Div(style={
    "backgroundColor": COLORS["bg"],
    "minHeight":       "100vh",
    "padding":         "32px 40px",
    "fontFamily":      "Inter, sans-serif",
    "color":           COLORS["text"],
}, children=[

    # Título
    html.H1("Dashboard · Portafolio de Clientes",
            style={"color": COLORS["accent"], "marginBottom": "8px", "fontSize": "26px"}),
    html.P("Visualización consolidada de inversiones locales e internacionales",
           style={"color": COLORS["subtext"], "marginBottom": "28px", "fontSize": "14px"}),

    # ── Filtros ──────────────────────────────────────────────────────────────
    html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "28px",
                    "flexWrap": "wrap"}, children=[

        html.Div([
            html.Label("Cliente", style={"color": COLORS["subtext"],
                                         "fontSize": "12px", "marginBottom": "6px"}),
            dcc.Dropdown(
                id="cliente-dropdown",
                options=[{"label": str(c), "value": c}
                         for c in clientes_df["id_sistema_cliente"]],
                placeholder="Selecciona un cliente",
                style={"minWidth": "220px", "color": "#000000"},
            ),
        ]),

        html.Div([
            html.Label("Rango de fechas", style={"color": COLORS["subtext"],
                                                  "fontSize": "12px", "marginBottom": "6px"}),
            dcc.DatePickerRange(
                id="date-picker",
                min_date_allowed=str(min_fecha),
                max_date_allowed=str(max_fecha),
                start_date=str(min_fecha),
                end_date=str(max_fecha),
                display_format="YYYY-MM-DD",
                style={"fontSize": "13px"},
            ),
        ]),
    ]),

    # ── KPI Cards ────────────────────────────────────────────────────────────
    html.Div(id="kpi-cards",
             style={"display": "flex", "gap": "16px",
                    "flexWrap": "wrap", "marginBottom": "28px"}),

    # ── Gráficos ─────────────────────────────────────────────────────────────
    html.Div(style={"display": "flex", "gap": "20px", "flexWrap": "wrap",
                    "marginBottom": "28px"}, children=[

        html.Div(dcc.Graph(id="donut-local"),  style=graph_style),
        html.Div(dcc.Graph(id="bar-inter"),    style=graph_style),
    ]),

    # ── Top 5 activos ─────────────────────────────────────────────────────────
    html.Div(id="top5-tabla"),
])


# ─── Helper: tarjeta KPI ─────────────────────────────────────────────────────
def kpi_card(label, value, color=COLORS["accent"]):
    return html.Div(style=card_style, children=[
        html.P(label, style={"color": COLORS["subtext"], "fontSize": "12px",
                              "margin": "0 0 6px 0", "textTransform": "uppercase",
                              "letterSpacing": "0.5px"}),
        html.P(value, style={"color": color, "fontSize": "22px",
                              "fontWeight": "700", "margin": "0"}),
    ])


# ─── Callback principal ───────────────────────────────────────────────────────
@app.callback(
    [Output("kpi-cards",   "children"),
     Output("donut-local", "figure"),
     Output("bar-inter",   "figure"),
     Output("top5-tabla",  "children")],
    [Input("cliente-dropdown", "value"),
     Input("date-picker",      "start_date"),
     Input("date-picker",      "end_date")]
)
def update_dashboard(cliente, start_date, end_date):

    empty_fig = go.Figure().update_layout(**PLOT_LAYOUT)

    if cliente is None:
        return [], empty_fig, empty_fig, []

    # ── Filtro de fechas en SQL ───────────────────────────────────────────────
    date_filter = f"""
        TO_DATE(
            ingestion_year || '-' ||
            LPAD(SPLIT_PART(ingestion_month::text, '.', 1), 2, '0') || '-' ||
            LPAD(SPLIT_PART(ingestion_day::text,   '.', 1), 2, '0'),
            'YYYY-MM-DD'
        ) BETWEEN '{start_date}' AND '{end_date}'
    """

    # ── Portafolio con filtro de fecha ────────────────────────────────────────
    port_df = query_to_df(f"""
        SELECT nombre_activo, macroactivo, valor, moneda
        FROM views.vw_portafolio_total
        WHERE id_sistema_cliente = '{cliente}'
          AND {date_filter}
    """)

    if port_df.empty:
        msg = html.P("Sin datos para el rango seleccionado.",
                     style={"color": COLORS["subtext"]})
        return [msg], empty_fig, empty_fig, []

    local_df = port_df[port_df["moneda"] == "COP"].copy()
    inter_df = port_df[port_df["moneda"] == "USD"].copy()

    aum_cop   = local_df["valor"].sum()
    aum_usd   = inter_df["valor"].sum()
    aum_total = port_df["valor"].sum()
    n_activos = port_df["nombre_activo"].nunique()

    # Métricas adicionales
    metrics_df = query_to_df(f"""
        SELECT
            MAX(valor) / NULLIF(SUM(valor), 0) * 100 AS pct_mayor_posicion,
            SUM(CASE WHEN moneda='USD' THEN valor ELSE 0 END)
                / NULLIF(SUM(valor), 0) * 100         AS pct_usd,
            MODE() WITHIN GROUP (ORDER BY perfil_riesgo) AS perfil_riesgo,
            MODE() WITHIN GROUP (ORDER BY banca)          AS banca
        FROM views.vw_portafolio_total
        WHERE id_sistema_cliente = '{cliente}'
          AND {date_filter}
    """)

    pct_top    = metrics_df["pct_mayor_posicion"].values[0] or 0
    pct_usd    = metrics_df["pct_usd"].values[0] or 0
    perfil     = metrics_df["perfil_riesgo"].values[0] or "—"
    banca      = metrics_df["banca"].values[0] or "—"

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    cards = [
        kpi_card("AUM COP",          f"$ {aum_cop:,.0f}",    COLORS["accent3"]),
        kpi_card("AUM USD",          f"$ {aum_usd:,.0f}",    COLORS["accent2"]),
        kpi_card("# Activos",        str(n_activos),          COLORS["text"]),
        kpi_card("Perfil de riesgo", perfil,                   COLORS["text"]),
        kpi_card("Banca",            banca,                    COLORS["text"]),
    ]

    # ── Donut — Portafolio Local (COP) ────────────────────────────────────────
    if not local_df.empty:
        macro_agg = local_df.groupby("macroactivo", as_index=False)["valor"].sum()
        macro_agg["macroactivo"] = macro_agg["macroactivo"].fillna("Sin clasificar")
        donut_fig = px.pie(
            macro_agg,
            names="macroactivo",
            values="valor",
            hole=0.55,
            title="Composicion por Macroactivo (COP)",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        donut_fig.update_traces(textposition="outside", textinfo="percent+label")
        donut_fig.update_layout(**PLOT_LAYOUT, title_font_size=15)
    else:
        donut_fig = go.Figure().update_layout(
            **PLOT_LAYOUT,
            title=dict(text="Composicion por Macroactivo (COP) - sin datos", font=dict(size=15)),
        )

    # ── Barras horizontales — Portafolio Internacional (USD) ──────────────────
    if not inter_df.empty:
        inter_agg = (inter_df.groupby("nombre_activo", as_index=False)["valor"]
                     .sum().sort_values("valor", ascending=True))
        bar_fig = px.bar(
            inter_agg,
            x="valor",
            y="nombre_activo",
            orientation="h",
            title="Portafolio Internacional (USD)",
            color="valor",
            color_continuous_scale="Blues",
            labels={"valor": "Valor (USD)", "nombre_activo": "Activo"},
        )
        bar_fig.update_layout(
            **PLOT_LAYOUT,
            title_font_size=15,
            coloraxis_showscale=False,
            yaxis=dict(tickfont=dict(size=11)),
        )
        bar_fig.update_traces(marker_line_width=0)
    else:
        bar_fig = go.Figure().update_layout(
            **PLOT_LAYOUT,
            title=dict(text="Portafolio Internacional (USD) — sin datos",
                       font=dict(size=15)),
        )

    # ── Top 5 activos por valor ───────────────────────────────────────────────
    top5_df = query_to_df(f"""
        SELECT
            cod_activo,
            nombre_activo,
            macroactivo,
            SUM(valor) AS valor_total
        FROM views.vw_portafolio_local
        WHERE id_sistema_cliente = '{cliente}'
          AND {date_filter}
        GROUP BY cod_activo, nombre_activo, macroactivo
        ORDER BY valor_total DESC
        LIMIT 5
    """)

    if not top5_df.empty:
        top5_df["valor_total"] = top5_df["valor_total"].apply(lambda x: f"$ {x:,.2f}")
        top5_df["macroactivo"] = top5_df["macroactivo"].fillna("—")

        col_labels = {
            "cod_activo":   "Codigo",
            "nombre_activo":"Activo",
            "macroactivo":  "Macroactivo",
            "valor_total":  "Valor total",
        }

        th_style = {
            "padding":         "10px 16px",
            "textAlign":       "left",
            "color":           COLORS["subtext"],
            "fontSize":        "12px",
            "textTransform":   "uppercase",
            "letterSpacing":   "0.5px",
            "borderBottom":    f"1px solid {COLORS['border']}",
            "whiteSpace":      "nowrap",
        }
        td_style = {
            "padding":      "10px 16px",
            "fontSize":     "13px",
            "color":        COLORS["text"],
            "borderBottom": f"1px solid {COLORS['border']}",
        }
        td_rank_style = {**td_style, "color": COLORS["accent"],
                         "fontWeight": "700", "textAlign": "center"}

        medal = {1: "🥇", 2: "🥈", 3: "🥉"}

        header = html.Tr(
            [html.Th("#", style={**th_style, "textAlign": "center"})] +
            [html.Th(col_labels[c], style=th_style) for c in top5_df.columns]
        )
        rows = [
            html.Tr(
                [html.Td(medal.get(i + 1, str(i + 1)), style=td_rank_style)] +
                [html.Td(str(top5_df.iloc[i][c]), style=td_style)
                 for c in top5_df.columns]
            )
            for i in range(len(top5_df))
        ]

        tabla_top5 = html.Div(style={
            "background":   COLORS["card"],
            "borderRadius": "12px",
            "border":       f"1px solid {COLORS['border']}",
            "padding":      "20px 24px",
            "marginBottom": "32px",
        }, children=[
            html.H3("🏆 Top 5 Activos Locales (COP)",
                    style={"color": COLORS["accent"], "fontSize": "15px",
                           "marginBottom": "16px", "marginTop": "0"}),
            html.Div(style={"overflowX": "auto"}, children=[
                html.Table(style={"width": "100%", "borderCollapse": "collapse"},
                           children=[html.Thead(header), html.Tbody(rows)])
            ])
        ])
    else:
        tabla_top5 = []

    return cards, donut_fig, bar_fig, tabla_top5


if __name__ == "__main__":
    app.run(debug=True)
