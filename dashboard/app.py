import ast
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"

st.set_page_config(page_title="RTBF Coverage Intelligence", page_icon="🇧🇪", layout="wide")

# Manual names {topic_id: "Readable name"}. They take priority over everything else.
# Topics not listed use the "Label" column of topic_info.csv (written by topic_modeling.py),
# or an automatic 3-keyword name. Ids must match the "Topic" column in outputs/topic_info.csv.
TOPIC_NAMES: dict[int, str] = {
    0: "Cinéma & séries",
    1: "Musique & concerts",
    2: "Cyclisme",
    3: "Écoles & jeunesse",
    4: "Diables Rouges (football)",
    5: "Procès & justice",
    6: "Guerre en Ukraine",
    7: "Jeux vidéo",
    8: "Budget & gouvernement",
    9: "Météo",
    10: "Événements & festivals (Namur)",
    11: "Football : Ronaldo & Messi",
    12: "IA & technologie",
    # Check these two ids on the Topic Explorer page before enabling them:
    # 13: "Santé & cancer",
    # 14: "Formule 1",
}

# ---------------------------------------------------------------- look & feel
BLACK, YELLOW, RED = "#1F1F1F", "#FAE042", "#ED2939"
PAPER, LINE = "#FBF8F1", "#E6DFCC"
PALETTE = [
    "#C8102E", "#1F1F1F", "#F2B705", "#2E6F9E", "#5B8C5A", "#8E5A9B",
    "#E07B39", "#3AA6A0", "#A63D40", "#7A7A7A", "#B8860B", "#4C6EF5",
]
GREY = {
    "Unassigned (outliers)": "#DCD7CA",
    "Not selected": "#DCD7CA",
    "Other topics": "#B9B2A0",
    "Other": "#B9B2A0",
}

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Source+Sans+3:wght@400;600&display=swap');

html, body, .stApp {{ font-family: 'Source Sans 3', sans-serif; }}
.stApp {{ background: {PAPER}; }}
header[data-testid="stHeader"] {{ background: transparent; }}

/* thin Belgian tricolour stripe across the top of the page */
.stApp::before {{
    content: ""; position: fixed; top: 0; left: 0; right: 0; height: 5px; z-index: 999999;
    background: linear-gradient(90deg, {BLACK} 0 33.33%, {YELLOW} 33.33% 66.66%, {RED} 66.66% 100%);
}}

h1, h2, h3, h4 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 700 !important; letter-spacing: -0.01em; color: {BLACK};
}}
h1 {{ font-size: 2.4rem !important; }}

/* small flag drawn with CSS so it renders the same on every OS */
.flag {{
    display: inline-flex; width: 30px; height: 20px; border-radius: 2px; overflow: hidden;
    box-shadow: 0 0 0 1px rgba(0,0,0,.18); vertical-align: middle; margin-right: 10px;
}}
.flag i {{ flex: 1; display: block; }}
.flag i:nth-child(1) {{ background: {BLACK}; }}
.flag i:nth-child(2) {{ background: {YELLOW}; }}
.flag i:nth-child(3) {{ background: {RED}; }}
.kicker {{
    font-size: .78rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
    color: #6B6358; margin-bottom: .2rem;
}}

/* metric cards */
[data-testid="stMetric"] {{
    background: #fff; border: 1px solid {LINE}; border-left: 4px solid {RED};
    padding: 14px 16px; border-radius: 6px;
}}
[data-testid="stMetricLabel"] p {{
    text-transform: uppercase; font-size: .72rem; letter-spacing: .08em; color: #6B6358;
}}
[data-testid="stMetricValue"] {{ font-family: 'Fraunces', Georgia, serif; }}

/* bordered containers (Topic Explorer, insights box) */
[data-testid="stVerticalBlockBorderWrapper"] {{ background: #fff; border-color: {LINE}; border-radius: 6px; }}

/* sidebar */
[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}
.sb-brand {{ font-family: 'Fraunces', Georgia, serif; font-weight: 700; font-size: 1.15rem; line-height: 1.2; }}
</style>
""",
    unsafe_allow_html=True,
)

FLAG = '<span class="flag"><i></i><i></i><i></i></span>'


def style(fig, height: int | None = None):
    """Apply the same look to every Plotly chart."""
    fig.update_layout(
        font=dict(family="Source Sans 3, sans-serif", color=BLACK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(title_text="", font=dict(size=11)),
        colorway=PALETTE,
    )
    fig.update_xaxes(gridcolor=LINE, zeroline=False)
    fig.update_yaxes(gridcolor=LINE, zeroline=False, automargin=True)
    if height:
        fig.update_layout(height=height)
    return fig


def hbar(data: pd.DataFrame, x: str, y: str):
    """Horizontal bars in charcoal, largest bar in red. Data must be sorted ascending."""
    fig = px.bar(data, x=x, y=y, orientation="h", labels={y: "", x: "Articles"})
    fig.update_traces(marker_color=[BLACK] * (len(data) - 1) + [RED])
    return style(fig, height=480)


# ---------------------------------------------------------------- helpers
def find_col(df: pd.DataFrame, *names: str) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def auto_label(raw_name: str) -> str:
    """'12_ia_apple_intelligence_x' -> 'Ia / Apple / Intelligence'"""
    parts = re.sub(r"^-?\d+_", "", str(raw_name)).split("_")
    return " / ".join(p.capitalize() for p in parts[:3])


def parse_keywords(value) -> list[str]:
    try:
        kw = ast.literal_eval(value) if isinstance(value, str) else list(value)
        return [str(k) for k in kw if str(k).strip()]
    except (ValueError, SyntaxError):
        return []


@st.cache_data
def load_topic_info() -> pd.DataFrame:
    ti = pd.read_csv(OUT / "topic_info.csv")
    c_id = find_col(ti, "Topic")
    c_count = find_col(ti, "Count")
    c_name = find_col(ti, "Name")
    c_kw = find_col(ti, "Representation", "keywords")
    c_label = find_col(ti, "Label")
    out = pd.DataFrame({
        "topic": ti[c_id],
        "articles": ti[c_count],
        "keywords": ti[c_kw].apply(parse_keywords) if c_kw else [[]] * len(ti),
    })
    out["label"] = [
        TOPIC_NAMES.get(t) or (ti[c_label].iloc[i] if c_label else None) or auto_label(ti[c_name].iloc[i])
        for i, t in enumerate(out["topic"])
    ]
    return out


@st.cache_data
def load_articles() -> pd.DataFrame:
    df = pd.read_csv(OUT / "articles_with_topics.csv")
    df = df.rename(columns={find_col(df, "topic"): "topic"})

    cl_path = OUT / "articles_with_clusters.csv"
    if cl_path.exists() and "url" in df.columns:
        cl = pd.read_csv(cl_path)[["url", "cluster"]].drop_duplicates("url")
        df = df.merge(cl, on="url", how="left")

    df["published_date"] = pd.to_datetime(
        df["published_date"], errors="coerce", utc=True
    ).dt.tz_localize(None)

    labels = load_topic_info().set_index("topic")["label"]
    df["topic_name"] = df["topic"].map(labels).fillna("Unassigned")
    df.loc[df["topic"] == -1, "topic_name"] = "Unassigned (outliers)"
    return df


@st.cache_data
def load_cluster_summary() -> pd.DataFrame | None:
    p = OUT / "cluster_summary.csv"
    return pd.read_csv(p) if p.exists() else None


def time_buckets(df: pd.DataFrame) -> tuple[str, str]:
    """Pick a sensible bucket size from the date span."""
    span = (df["published_date"].max() - df["published_date"].min()).days
    if span > 120:
        return "MS", "month"
    if span > 28:
        return "W", "week"
    return "D", "day"


def page_header(title: str, subtitle: str | None = None):
    st.markdown(f'<div class="kicker">{FLAG}RTBF Coverage Intelligence</div>', unsafe_allow_html=True)
    st.title(title)
    if subtitle:
        st.caption(subtitle)


# ---------------------------------------------------------------- data
df = load_articles()
topics = load_topic_info()
real_topics = topics[topics["topic"] != -1].sort_values("articles", ascending=False)
has_cluster = "cluster" in df.columns
all_dated = df.dropna(subset=["published_date"])
d1 = all_dated["published_date"].max()
# A few articles carry much older dates (2020-2025). Time analysis uses only the
# last 30 days, where nearly all the articles are.
dated = all_dated[all_dated["published_date"] >= d1 - pd.Timedelta(days=30)]
d0 = dated["published_date"].min()
n_older = len(all_dated) - len(dated)
n_outliers = int((df["topic"] == -1).sum())

st.sidebar.markdown(f'<div class="sb-brand">{FLAG}RTBF<br>Coverage Intelligence</div>', unsafe_allow_html=True)
st.sidebar.write("")
page = st.sidebar.radio(
    "Page",
    ["Overview", "Key Insights", "Topic Explorer", "Article Browser", "Article Map", "Visualizations"],
    label_visibility="collapsed",
)
st.sidebar.caption(
    f"{len(df):,} articles · {d0:%d %b %Y} → {d1:%d %b %Y}. "
    f"{n_older} older articles are left out of the time charts."
)
st.sidebar.caption("Source: public articles from rtbf.be")

st.sidebar.divider()

last_day = dated[dated["published_date"] >= d1 - pd.Timedelta(days=1)]
st.sidebar.markdown(f"**Last day in the data ({d1:%d %b})**")
st.sidebar.metric("New articles", f"{len(last_day):,}")
with_topic = last_day[last_day["topic"] != -1]
if len(with_topic):
    st.sidebar.caption(f"Most covered topic: {with_topic['topic_name'].value_counts().index[0]}")

st.sidebar.download_button(
    "Download articles (CSV)",
    df.to_csv(index=False).encode("utf-8"),
    file_name="rtbf_articles_topics.csv",
    mime="text/csv",
    width="stretch",
)

with st.sidebar.expander("How it works"):
    st.write(
        "Each article is turned into numbers that capture its meaning. BERTopic groups "
        "similar articles into topics and K-Means groups them into clusters. "
        "The topic names were written by hand after reading the keywords."
    )

st.sidebar.markdown(
    "[Code on GitHub](https://github.com/husseinabuammar24-cloud/rtbf_news_analysis)"
)

# ---------------------------------------------------------------- Overview
if page == "Overview":
    page_header(
        "What RTBF is covering",
        "What does RTBF cover, how much, and what is changing? Discovered automatically from the articles.",
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Articles analysed", f"{len(df):,}")
    c2.metric("Topics found", len(real_topics))
    c3.metric("Clusters found", int(df["cluster"].nunique()) if has_cluster else "n/a")
    c4.metric("Period", f"{d0:%d %b} → {d1:%d %b}")

    st.caption(
        f"{n_outliers:,} articles ({n_outliers / len(df):.0%}) did not fit any topic "
        "(BERTopic outliers) and are not counted in 'Topics found'."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Top 15 topics")
        top15 = real_topics.head(15).sort_values("articles")
        st.plotly_chart(hbar(top15, "articles", "label"), width="stretch")
    with right:
        st.subheader("Top 15 RTBF categories")
        cats = df["category"].value_counts().head(15).sort_values().reset_index()
        cats.columns = ["category", "articles"]
        st.plotly_chart(hbar(cats, "articles", "category"), width="stretch")

    st.subheader("Articles published per day")
    per_day = dated.set_index("published_date").resample("D").size().reset_index()
    per_day.columns = ["date", "articles"]
    fig = px.area(per_day, x="date", y="articles", labels={"date": "", "articles": "Articles"})
    fig.update_traces(line_color=RED, fillcolor="rgba(237,41,57,0.15)")
    st.plotly_chart(style(fig, height=300), width="stretch")

    if has_cluster:
        st.subheader("Article clusters (K-Means)")
        summ = load_cluster_summary()
        if summ is not None:
            st.dataframe(summ.sort_values("size", ascending=False), width="stretch", hide_index=True)
        st.caption(
            "Clusters group articles with similar meaning. 'purity' is the share of a cluster that "
            "belongs to its most common RTBF category; low purity means the cluster mixes categories."
        )

# ---------------------------------------------------------------- Key Insights
elif page == "Key Insights":
    page_header("Key insights")

    top = real_topics.iloc[0]
    share = top["articles"] / len(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Largest topic", top["label"])
    c2.metric("Articles in it", f"{int(top['articles']):,}")
    c3.metric("Share of all articles", f"{share:.1%}")

    st.subheader("Top 10 topics")
    t10 = real_topics.head(10).copy()
    t10["share"] = (t10["articles"] / len(df)).map("{:.1%}".format)
    st.dataframe(t10[["label", "articles", "share"]], width="stretch", hide_index=True)

    freq, unit = time_buckets(dated)
    st.subheader(f"Top 5 topics over time (per {unit})")
    top_labels = real_topics.head(5)["label"].tolist()
    trend = (
        dated[dated["topic_name"].isin(top_labels)]
        .groupby([pd.Grouper(key="published_date", freq=freq), "topic_name"])
        .size()
        .reset_index(name="count")
    )
    fig = px.line(trend, x="published_date", y="count", color="topic_name", markers=True,
                  color_discrete_sequence=PALETTE,
                  labels={"published_date": "", "count": "Articles", "topic_name": "Topic"})
    st.plotly_chart(style(fig, height=380), width="stretch")

    st.subheader("Rising and falling topics")
    mid = d0 + (d1 - d0) / 2
    named = dated[dated["topic"] != -1]
    first = named[named["published_date"] < mid].groupby("topic_name").size()
    second = named[named["published_date"] >= mid].groupby("topic_name").size()
    chg = pd.DataFrame({"first_half": first, "second_half": second}).fillna(0).astype(int)
    chg["total"] = chg.sum(axis=1)
    chg = chg[chg["total"] >= 15]
    chg["change_%"] = ((chg["second_half"] - chg["first_half"]) / chg["first_half"].clip(lower=1) * 100).round(0)
    chg = chg.sort_values("change_%", ascending=False)
    st.caption(f"Compares {d0:%d %b} → {mid:%d %b} with {mid:%d %b} → {d1:%d %b}. Only topics with 15+ articles.")
    r1, r2 = st.columns(2)
    r1.markdown("**Rising**")
    r1.dataframe(chg.head(5), width="stretch")
    r2.markdown("**Falling**")
    r2.dataframe(chg.tail(5).sort_values("change_%"), width="stretch")

    st.subheader("Potential coverage gaps")
    st.caption("Smallest topics. Small can mean a real gap or simply a niche; an editor should judge.")
    gaps = real_topics.sort_values("articles").head(10).copy()
    gaps["keywords"] = gaps["keywords"].apply(lambda k: ", ".join(k[:5]))
    st.dataframe(gaps[["label", "articles", "keywords"]], width="stretch", hide_index=True)

    st.subheader("What the data suggests")
    bullets = [
        f"**{top['label']}** is the biggest topic: {int(top['articles']):,} articles ({share:.1%} of coverage).",
        f"The 5 largest topics account for {real_topics.head(5)['articles'].sum() / len(df):.0%} of all articles.",
    ]
    if len(chg) >= 2:
        bullets.append(f"Fastest rising topic: **{chg.index[0]}** ({chg.iloc[0]['change_%']:+.0f}% in the second half of the period).")
        bullets.append(f"Fastest falling topic: **{chg.sort_values('change_%').index[0]}** ({chg['change_%'].min():+.0f}%).")
    bullets.append(f"**{gaps.iloc[0]['label']}** is the thinnest topic ({int(gaps.iloc[0]['articles'])} articles): a candidate for follow-up coverage.")
    bullets.append(f"{n_outliers / len(df):.0%} of articles fit no topic, so one-off stories are not captured by this view.")
    with st.container(border=True):
        st.markdown("\n".join(f"- {b}" for b in bullets))

# ---------------------------------------------------------------- Topic Explorer
elif page == "Topic Explorer":
    page_header("Topic explorer", "Names come from the Label column of topic_info.csv (set in topic_modeling.py).")
    search = st.text_input("Search keyword or topic name")
    for _, row in real_topics.iterrows():
        kws = ", ".join(row["keywords"][:8])
        if search and search.lower() not in f"{row['label']} {kws}".lower():
            continue
        with st.container(border=True):
            st.subheader(f"{row['label']}  ·  topic {row['topic']}")
            st.write(f"**{int(row['articles']):,} articles**")
            st.write(f"**Keywords:** {kws}")

# ---------------------------------------------------------------- Article Browser
elif page == "Article Browser":
    page_header("Article browser")

    f1, f2, f3 = st.columns(3)
    cats = f1.multiselect("Category", sorted(df["category"].dropna().unique()))
    tops = f2.multiselect("Topic", sorted(df["topic_name"].unique()))
    all_min = all_dated["published_date"].min().date()
    dr = f3.date_input("Date", (all_min, d1.date()), min_value=all_min, max_value=d1.date())
    text = st.text_input("Search article title")

    view = df
    if cats:
        view = view[view["category"].isin(cats)]
    if tops:
        view = view[view["topic_name"].isin(tops)]
    if isinstance(dr, tuple) and len(dr) == 2:
        view = view[view["published_date"].between(
            pd.Timestamp(dr[0]), pd.Timestamp(dr[1]) + pd.Timedelta(days=1))]
    if text:
        view = view[view["title"].str.contains(text, case=False, na=False)]

    st.write(f"{len(view):,} articles")
    cols = [c for c in ["title", "category", "topic_name", "cluster", "published_date", "url"] if c in view.columns]
    show = view[cols].rename(columns={"topic_name": "topic"}).sort_values("published_date", ascending=False)
    st.dataframe(
        show,
        width="stretch",
        hide_index=True,
        column_config={"url": st.column_config.LinkColumn("link", display_text="open")},
    )

# ---------------------------------------------------------------- Article Map
elif page == "Article Map":
    page_header(
        "Article map",
        "Each dot is one article. Articles about similar things sit close together. "
        "Hover over a dot to read its title.",
    )
    coords_path = OUT / "doc_map_coords.csv"
    if not coords_path.exists():
        st.warning("Run `python -m src.make_doc_map` first to create outputs/doc_map_coords.csv.")
        st.stop()

    m = df.merge(pd.read_csv(coords_path), on="url", how="inner")

    c1, c2, c3 = st.columns([2, 1, 3])
    options = ["Topic", "RTBF category"] + (["K-Means cluster"] if has_cluster else [])
    colour_by = c1.radio("Colour by", options, horizontal=True)
    hide_out = c2.checkbox("Hide articles with no topic", value=False)
    focus = c3.multiselect(
        "Highlight topics", sorted(m.loc[m["topic"] != -1, "topic_name"].unique())
    )

    if hide_out:
        m = m[m["topic"] != -1]
    m = m.copy()

    # Only as many groups as there are distinct colours; everything else becomes grey,
    # so no two coloured groups ever share a colour.
    n_colours = len(PALETTE)
    if colour_by == "Topic":
        top_t = m.loc[m["topic"] != -1, "topic_name"].value_counts().head(n_colours).index
        m["group"] = m["topic_name"]
        m.loc[(m["topic"] != -1) & ~m["topic_name"].isin(top_t), "group"] = "Other topics"
    elif colour_by == "K-Means cluster":
        m["group"] = "Cluster " + m["cluster"].astype("Int64").astype(str)
    else:
        top_cats = m["category"].value_counts().head(n_colours).index
        m["group"] = m["category"].where(m["category"].isin(top_cats), "Other")
    if focus:
        m["group"] = m["topic_name"].where(m["topic_name"].isin(focus), "Not selected")

    groups = list(m["group"].unique())
    coloured = sorted(g for g in groups if g not in GREY)
    cmap = {g: PALETTE[i % n_colours] for i, g in enumerate(coloured)}
    cmap.update(GREY)
    order = [g for g in GREY if g in groups] + coloured

    fig = px.scatter(
        m, x="x", y="y", color="group",
        hover_name="title",
        hover_data={"category": True, "topic_name": True, "x": False, "y": False, "group": False},
        category_orders={"group": order},
        color_discrete_map=cmap,
        labels={"group": colour_by, "topic_name": "topic"},
    )
    fig.update_traces(marker=dict(size=6, opacity=0.8))
    style(fig, height=720)
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False))
    st.plotly_chart(fig, width="stretch")

    note = f"{len(m):,} articles shown. Grey dots are articles that fit no topic or a smaller topic. "
    if colour_by == "Topic" and not focus:
        note += f"The {n_colours} largest topics are coloured; use 'Highlight topics' to look at any other one. "
    note += "The map is a 2D projection, so distances are approximate and the axes have no meaning."
    st.caption(note)

# ---------------------------------------------------------------- Visualizations
else:
    page_header("Visualizations", "Interactive charts exported from the topic model.")
    files = {
        "Topic bar chart": ("topics_barchart.html", 1100),
        "Topic map": ("topics_map.html", 750),
        "Document map": ("documents_map.html", 750),
        "Topics over time": ("topics_over_time.html", 650),
    }
    tabs = st.tabs(list(files))
    for tab, (fname, height) in zip(tabs, files.values()):
        with tab:
            path = OUT / fname
            if path.exists():
                html_string = path.read_text(encoding="utf-8")
                st.iframe(html_string, height=height)
            else:
                st.warning(f"{fname} not found in outputs/")
