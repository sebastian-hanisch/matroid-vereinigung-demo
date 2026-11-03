"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import mvg_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _frame(fig, lo=-0.05, hi=1.05):
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)


def _lines(inst, edge_ids):
    xs, ys = [], []
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        xs += [inst.points[u][0], inst.points[v][0], None]
        ys += [inst.points[u][1], inst.points[v][1], None]
    return xs, ys


def build_graph(net, groups, unassigned=(), halo=(), edge_text=None, node_class=None, height=430):
    """Das Netz mit den Leitungen als Elementen. groups: Liste (Name, Leitungen, Farbe) in Zeichenreihenfolge, dick; unassigned: nicht untergebrachte Leitungen, rot gestrichelt;
    halo: Leitungen des Verbesserungswegs (orange unterlegt); übrige Leitungen dünn grau. edge_text: {Leitung: Text} an der Mitte der Leitung.
    node_class: Klassenindex je Standort (färbt die Standorte nach Klassen einer Partition), sonst Depot orange und die übrigen blau."""
    inst = net.inst
    fig = go.Figure()
    marked = {e for _, ids, _ in groups for e in ids} | set(unassigned) | set(halo)
    rest = [e for e in range(inst.m) if e not in marked]
    if rest:
        xs, ys = _lines(inst, rest)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OTHER, width=2), name="nicht gewählt", hoverinfo="skip"))
    if halo:
        xs, ys = _lines(inst, list(halo))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_PATH, width=13), opacity=0.55, name="Verbesserungsweg", hoverinfo="skip"))
    if unassigned:
        xs, ys = _lines(inst, list(unassigned))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_UNASSIGNED, width=4, dash="dash"), name="nicht untergebracht", hoverinfo="skip"))
    for name, ids, color in groups:
        if ids:
            xs, ys = _lines(inst, ids)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=6), name=name, hoverinfo="skip"))
    if edge_text:
        ids = sorted(edge_text)
        fig.add_trace(go.Scatter(
            x=[(inst.points[inst.edges[e][0]][0] + inst.points[inst.edges[e][1]][0]) / 2 for e in ids], y=[(inst.points[inst.edges[e][0]][1] + inst.points[inst.edges[e][1]][1]) / 2 for e in ids],
            mode="text", text=[edge_text[e] for e in ids], textfont=dict(size=13), hoverinfo="skip", showlegend=False))
    if node_class is None:
        colors = [C.COLOR_DEPOT if v == 0 else C.COLOR_NODE for v in range(inst.n)]
    else:
        colors = [C.COLOR_CLASS[c % len(C.COLOR_CLASS)] for c in node_class]
    fig.add_trace(go.Scatter(
        x=[p[0] for p in inst.points], y=[p[1] for p in inst.points], mode="markers+text", text=[inst.name(v) for v in range(inst.n)], textposition="top center", textfont=dict(size=14),
        marker=dict(size=16, color=colors, line=dict(color="white", width=1.5)), hovertemplate="%{text}<extra></extra>", showlegend=False))
    _frame(fig)
    return _base(fig, height)


def build_bar_chart(categories, values, colors, x_title, y_title, hover, height=300):
    """Balken; hover ist eine Formatzeichenfolge mit %{x} und %{y}."""
    fig = go.Figure(go.Bar(x=list(categories), y=list(values), marker_color=list(colors), hovertemplate=hover + "<extra></extra>"))
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)


def build_grouped_bars(categories, series, x_title, y_title, height=320):
    """Gruppierte Balken: series = [(Name, Werte, Farbe)]."""
    fig = go.Figure([go.Bar(name=name, x=list(categories), y=list(values), marker_color=color, hovertemplate=name + ": %{y:.0f}<extra></extra>") for name, values, color in series])
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)
