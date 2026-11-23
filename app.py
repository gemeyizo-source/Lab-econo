"""Laboratorio web: plan matemático de internacionalización empresarial.

Ejecutar: streamlit run app.py
Unidades monetarias: miles de COP, salvo indicación contraria.
"""
from __future__ import annotations

from io import BytesIO
from math import ceil

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

st.set_page_config(page_title="Laboratorio | Internacionalización", page_icon="🌐", layout="wide", initial_sidebar_state="expanded")

COLORS = {
    "green": "#22c55e", "purple": "#a78bfa", "orange": "#fb923c",
    "red": "#fb7185", "amber": "#facc15", "blue": "#38bdf8", "teal": "#2dd4bf",
}

BASE = {
    "A_R": 220.0, "g_R": 0.035, "beta": 0.02,
    "D0": 1800.0, "A_D": 350.0, "B_D": 120.0, "g_D": 0.025,
    "eta": 0.70, "c0": 80.0, "c1": 350.0, "c2": 15.0,
    "F0": 45.0, "A_F": 12.0,
    "I0": 3500.0, "B_I": 450.0, "g_I": 0.025,
    "T": 12,
}

SCENARIOS = {
    "Base": {},
    "Optimista": {"eta": 0.90, "g_R": 0.05, "beta": 0.03, "g_D": 0.04, "A_F": 6.0},
    "Pesimista": {"eta": 0.50, "g_R": 0.02, "beta": 0.01, "g_D": 0.01, "A_F": 20.0},
}

DEFS = [
    ("A_R", "Escala de ingreso marginal", 50., 500., 1., "miles COP/mes"),
    ("g_R", "Crecimiento de ingresos", 0., 0.10, 0.001, "1/mes"),
    ("beta", "Factor temporal de ingresos", 0., 0.10, 0.001, "1/mes"),
    ("D0", "Demanda base", 500., 3000., 10., "unidades/mes"),
    ("A_D", "Amplitud estacional", 0., 1000., 10., "unidades/mes"),
    ("B_D", "Tendencia de demanda", 0., 500., 5., "unidades/mes"),
    ("g_D", "Crecimiento de demanda", 0., 0.10, 0.001, "1/mes"),
    ("eta", "Conversión de demanda a ventas", 0., 1., 0.01, "fracción"),
    ("c0", "Costo marginal base", 0., 200., 1., "miles COP/unidad"),
    ("c1", "Componente logarítmica", 0., 1000., 10., "parámetro"),
    ("c2", "Ajuste de volumen", 1., 100., 1., "unidades"),
    ("F0", "Costo financiero base", 0., 150., 1., "miles COP/mes"),
    ("A_F", "Amplitud costo financiero", 0., 80., 1., "miles COP/mes"),
    ("I0", "Fondo inicial", 500., 8000., 50., "miles COP"),
    ("B_I", "Componente hiperbólica", 0., 2000., 10., "miles COP"),
    ("g_I", "Tasa del fondo", 0., 0.10, 0.001, "1/mes"),
]


def ensure_state():
    for name, value in BASE.items():
        st.session_state.setdefault(name, value)
    st.session_state.setdefault("scenario", "Base")


def apply_scenario(name: str):
    st.session_state.update(BASE)
    st.session_state.update(SCENARIOS[name])
    st.session_state["scenario"] = name


def reset():
    apply_scenario("Base")


def accumulated_trapezoid(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Integral acumulada con regla compuesta del trapecio."""
    return np.r_[0., np.cumsum(np.diff(x) * (y[1:] + y[:-1]) / 2.)]


@st.cache_data(show_spinner=False)
def calculate(p: dict) -> pd.DataFrame:
    t = np.linspace(0., float(p["T"]), max(1000, int(p["T"]) * 120 + 1))
    Rp = p["A_R"] * np.exp(p["g_R"] * t) * (1 + p["beta"] * t)
    R = accumulated_trapezoid(t, Rp)
    D = p["D0"] + p["A_D"] * np.sin(np.pi * t / 6.) + p["B_D"] * np.exp(p["g_D"] * t)
    q = accumulated_trapezoid(t, p["eta"] * D)
    # C(0)=0 como costo incremental. Es una hipótesis de simulación, no un dato observado.
    C = p["c0"] * q + p["c1"] * np.log1p(q / p["c2"])
    Fp = p["F0"] + p["A_F"] * np.cos(np.pi * t / 4.)
    F = accumulated_trapezoid(t, Fp)
    I = p["I0"] * np.cosh(p["g_I"] * t) - p["B_I"] * np.sinh(p["g_I"] * t)
    profit = R - C - F
    return pd.DataFrame({"Mes": t, "Ingreso marginal": Rp, "Ingresos": R,
                         "Demanda": D, "Ventas acumuladas": q, "Costos operativos": C,
                         "Costo financiero marginal": Fp, "Costos financieros": F,
                         "Fondo": I, "Beneficio ilustrativo": profit})


def get_monthly(df: pd.DataFrame, n_months: int) -> pd.DataFrame:
    x = df["Mes"].to_numpy()
    columns = [c for c in df.columns if c != "Mes"]
    rows = {"Mes": np.arange(0, n_months + 1, dtype=int)}
    for col in columns:
        rows[col] = np.interp(rows["Mes"], x, df[col].to_numpy())
    return pd.DataFrame(rows)


def format_cop_thousands(v: float) -> str:
    return f"{v:,.2f} mil COP"


def new_figure(title, yaxis):
    fig = go.Figure()
    fig.update_layout(title=title, template="plotly_dark", height=325,
                      margin=dict(l=35, r=18, t=50, b=35),
                      paper_bgcolor="#0f172a", plot_bgcolor="#111c33",
                      xaxis_title="Tiempo (meses)", yaxis_title=yaxis,
                      legend=dict(orientation="h", y=-0.27))
    return fig


def plots(df: pd.DataFrame, p: dict) -> list:
    t = df["Mes"].to_numpy()
    d = {c: df[c].to_numpy() for c in df.columns if c != "Mes"}
    result = []
    f = new_figure("Ingreso marginal y área acumulada", "miles COP/mes")
    f.add_trace(go.Scatter(x=t, y=d["Ingreso marginal"], mode="lines", fill="tozeroy", name="R'(t)", line_color=COLORS["green"]))
    result.append(f)

    f = new_figure("Demanda y valor promedio", "unidades/mes")
    avg = accumulated_trapezoid(t, d["Demanda"])[-1] / t[-1]
    f.add_trace(go.Scatter(x=t, y=d["Demanda"], mode="lines", name="D(t)", line_color=COLORS["purple"]))
    f.add_hline(y=avg, line_dash="dash", line_color=COLORS["amber"], annotation_text="Promedio")
    result.append(f)

    f = new_figure("Cantidad vendida acumulada", "unidades")
    f.add_trace(go.Scatter(x=t, y=d["Ventas acumuladas"], fill="tozeroy", mode="lines", name="q(t)", line_color=COLORS["blue"]))
    result.append(f)

    f = new_figure("Ingresos, costos y financiación", "miles COP")
    for key, color in [("Ingresos", COLORS["green"]), ("Costos operativos", COLORS["orange"]),
                       ("Costos financieros", COLORS["red"])]:
        f.add_trace(go.Scatter(x=t, y=d[key], name=key, line_color=color))
    result.append(f)

    f = new_figure("Fondo de inversión", "miles COP")
    f.add_trace(go.Scatter(x=t, y=d["Fondo"], name="I(t)", line_color=COLORS["amber"]))
    f.add_hline(y=p["I0"], line_dash="dash", line_color="#94a3b8", annotation_text="Fondo inicial")
    result.append(f)

    f = new_figure("Beneficio acumulado (supuesto ilustrativo)", "miles COP")
    f.add_trace(go.Scatter(x=t, y=d["Beneficio ilustrativo"], fill="tozeroy", mode="lines", name="Π(t)", line_color=COLORS["teal"]))
    f.add_hline(y=0, line_color="#94a3b8")
    if p["T"] > 12:
        f.add_vline(x=12, line_dash="dash", line_color=COLORS["amber"], annotation_text="Proyección")
    result.append(f)
    return result


def analysis(df: pd.DataFrame, p: dict) -> list[str]:
    final = df.iloc[-1]
    demand_integral = accumulated_trapezoid(df["Mes"].to_numpy(), df["Demanda"].to_numpy())[-1]
    mes_min = df.loc[df["Fondo"].idxmin(), "Mes"]
    mes_max_d = df.loc[df["Demanda"].idxmax(), "Mes"]
    mes_min_d = df.loc[df["Demanda"].idxmin(), "Mes"]
    msgs = [
        f"Ingreso acumulado estimado: {final['Ingresos']:,.2f} miles de COP.",
        f"Demanda potencial: {demand_integral:,.2f} unidades; promedio {demand_integral/p['T']:,.2f} unidades/mes.",
        f"Máximo de demanda: mes {mes_max_d:.2f}; mínimo: mes {mes_min_d:.2f}.",
        f"Mínimo del fondo: mes {mes_min:.2f}, {df['Fondo'].min():,.2f} miles de COP.",
        f"Costo incremental simulado: {final['Costos operativos']:,.2f} miles de COP; costo financiero acumulado: {final['Costos financieros']:,.2f} miles de COP.",
        f"Beneficio ilustrativo (con conversión η={p['eta']:.2f} y costo inicial C(0)=0): {final['Beneficio ilustrativo']:,.2f} miles de COP.",
    ]
    if final["Beneficio ilustrativo"] < 0:
        msgs.append("Bajo los supuestos elegidos, el beneficio ilustrativo es negativo; revise la escala del costo marginal y los supuestos de conversión.")
    else:
        msgs.append("Bajo los supuestos elegidos, el beneficio ilustrativo es positivo. Esto no acredita la viabilidad real del proyecto.")
    msgs.append("La viabilidad empresarial NO está demostrada: faltan calibración con ventas reales, costo inicial y evaluación integral de flujos de caja.")
    if p["T"] > 12:
        msgs.append("Los meses posteriores al 12 constituyen una extrapolación matemática, no una predicción validada.")
    return msgs


def pdf_report(monthly: pd.DataFrame, summary: list[str], p: dict) -> bytes:
    buf = BytesIO()
    pdf = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Heading1"], fontSize=15, spaceAfter=10))
    styles.add(ParagraphStyle(name="ReportBody", parent=styles["Normal"], fontSize=9, leading=13, spaceAfter=7))
    story = [Paragraph("Laboratorio de internacionalización empresarial", styles["ReportTitle"]),
             Paragraph("Caso de estudio: Karen Juliana Viancha Barragán · UPTC", styles["Normal"]),
             Spacer(1, 0.5*cm)]
    story.append(Paragraph("Resumen del escenario", styles["Heading2"]))
    for line in summary:
        story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;"), styles["ReportBody"]))
    story.append(Paragraph("Los resultados son ilustrativos y no constituyen una recomendación de inversión.", styles["ReportBody"]))
    story.append(PageBreak())
    story.append(Paragraph("Tabla mensual del modelo", styles["Heading2"]))
    fields = ["Mes", "Ingresos", "Costos operativos", "Costos financieros", "Demanda", "Ventas acumuladas", "Fondo", "Beneficio ilustrativo"]
    header = ["Mes", "Ingresos", "Costos", "Financiero", "Demanda", "Ventas", "Fondo", "Beneficio"]
    data = [header] + [[str(int(row["Mes"]))] + [f"{row[col]:,.1f}" for col in fields[1:]] for _, row in monthly.iterrows()]
    table = Table(data, repeatRows=1, colWidths=[1.35*cm] + [3.1*cm]*7)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), colors.HexColor("#143652")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#edf4fa")]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#bac6d2")),
        ("ALIGN",(0,0),(-1,-1),"RIGHT"),
        ("FONTSIZE",(0,0),(-1,-1),7),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("TOPPADDING",(0,0),(-1,-1),5),
    ]))
    story.append(table)
    pdf.build(story)
    return buf.getvalue()


ensure_state()
st.markdown("""<style>
.stApp {background: #0f172a; color:#e2e8f0}
[data-testid="stMetric"] {background:#1e293b; padding:14px; border-radius:12px; border-top:3px solid #38bdf8}
[data-testid="stSidebar"] {background:#18263b}
h1,h2,h3 {color:#e2e8f0}
</style>""", unsafe_allow_html=True)

st.title("🌐 Laboratorio de internacionalización empresarial")
st.caption("Modelación con cálculo diferencial e integral · Karen Juliana Viancha Barragán · UPTC")
st.info("**Modelo académico, no una evaluación de viabilidad real.** Valores monetarios en **miles de COP**. Los escenarios usan parámetros hipotéticos.")

with st.sidebar:
    st.header("⚙️ Parámetros")
    a, b = st.columns(2)
    a.button("↺ Restablecer", on_click=reset, use_container_width=True)
    b.button("12 ↔ 24 meses", on_click=lambda: st.session_state.update(T=24 if st.session_state["T"]==12 else 12), use_container_width=True)
    scenario = st.selectbox("Escenario", list(SCENARIOS), index=list(SCENARIOS).index(st.session_state["scenario"]))
    if st.button("Aplicar escenario", use_container_width=True):
        apply_scenario(scenario)
        st.rerun()
    st.slider("Horizonte temporal (meses)", 1, 36, key="T")
    groups = [
        ("💰 Ingresos", DEFS[:3]), ("📈 Demanda y ventas", DEFS[3:8]),
        ("🏭 Costos operativos", DEFS[8:11]), ("🏦 Costos financieros", DEFS[11:13]),
        ("🌐 Recursos de inversión", DEFS[13:]),
    ]
    for group, controls in groups:
        with st.expander(group, expanded=(group=="💰 Ingresos")):
            for key, label, lo, hi, step, unit in controls:
                st.slider(f"{label} ({unit})", min_value=lo, max_value=hi, step=step, key=key)

p = {name: st.session_state[name] for name in BASE}
df = calculate(p)
monthly = get_monthly(df, int(p["T"]))
final = df.iloc[-1]
demand_total = accumulated_trapezoid(df["Mes"].to_numpy(), df["Demanda"].to_numpy())[-1]

row1 = st.columns(3)
row2 = st.columns(3)
for dest, label, value in zip(row1 + row2,
        ["Ingresos acumulados", "Costos operativos", "Costos financieros", "Beneficio ilustrativo", "Demanda potencial", "Fondo final"],
        [format_cop_thousands(final["Ingresos"]), format_cop_thousands(final["Costos operativos"]),
         format_cop_thousands(final["Costos financieros"]), format_cop_thousands(final["Beneficio ilustrativo"]),
         f"{demand_total:,.1f} unidades", format_cop_thousands(final["Fondo"]) ]):
    dest.metric(label, value)

st.subheader("📊 Visualización dinámica")
all_figures = plots(df, p)
for i in range(0, len(all_figures), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        col.plotly_chart(all_figures[i+j], use_container_width=True, config={"displaylogo": False})

tab1, tab2, tab3 = st.tabs(["📋 Interpretación", "📅 Tabla mensual", "📐 Formulación y validación"])
summary = analysis(df, p)
with tab1:
    st.markdown("### Interpretación del escenario seleccionado")
    for msg in summary:
        st.write("• " + msg)
    st.warning("No usar la etiqueta 'viable/no viable' con los datos actuales. El costo inicial y la conversión real no están estimados.")
with tab2:
    st.dataframe(monthly.style.format({c: "{:,.2f}" for c in monthly.columns if c!="Mes"}), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Descargar tabla CSV", data=monthly.to_csv(index=False).encode("utf-8-sig"), file_name="tabla_internacionalizacion.csv", mime="text/csv")
with tab3:
    st.latex(r"R'(t)=A_R e^{g_R t}(1+\beta t),\qquad R(t)=\int_0^t R'(s)\,ds")
    st.latex(r"D(t)=D_0+A_D\sin(\pi t/6)+B_D e^{g_Dt}")
    st.latex(r"q(t)=\eta\int_0^t D(s)\,ds")
    st.latex(r"C(q)=c_0q+c_1\ln\!\left(\frac{q+c_2}{c_2}\right)")
    st.latex(r"F'(t)=F_0+A_F\cos(\pi t/4),\quad I(t)=I_0\cosh(g_It)-B_I\sinh(g_It)")
    st.latex(r"\Pi(t)=R(t)-C(q(t))-F(t)")
    st.caption("Convención del simulador: q(0)=0 y C(0)=0 para ilustrar costos incrementales. El artículo original deja sin calibrar ciertos parámetros.")
    if p["T"] == 12 and all(np.isclose(p[k], BASE[k]) for k in BASE if k != "T"):
        exact = 12*p["D0"] + p["B_D"] / p["g_D"] * np.expm1(p["g_D"]*12) if p["g_D"] else 12*(p["D0"]+p["B_D"])
        h = 1.0
        vals = p["D0"] + p["A_D"] * np.sin(np.pi*np.arange(13)/6) + p["B_D"] * np.exp(p["g_D"]*np.arange(13))
        trap = h*(vals[0]/2+vals[-1]/2+vals[1:-1].sum())
        simp = h/3*(vals[0]+vals[-1]+4*vals[1:-1:2].sum()+2*vals[2:-1:2].sum())
        validation = pd.DataFrame({"Método": ["Analítico", "Trapecio (n=12)", "Simpson (n=12)"],
                                   "Demanda acumulada": [exact, trap, simp],
                                   "Error absoluto": [0., abs(trap-exact), abs(simp-exact)]})
        st.dataframe(validation.style.format({"Demanda acumulada": "{:,.9f}", "Error absoluto": "{:.9f}"}), hide_index=True, use_container_width=True)
    else:
        st.caption("La tabla de verificación con valores de referencia se muestra al restablecer los parámetros base y 12 meses.")

st.download_button("📄 Descargar reporte PDF", data=pdf_report(monthly, summary, p),
                   file_name="reporte_internacionalizacion_web.pdf", mime="application/pdf", use_container_width=True)
st.caption("Las proyecciones y simulaciones son ilustrativas; no sustituyen la validación con datos de mercado.")
