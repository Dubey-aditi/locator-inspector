"""Locator Inspector UI.

    streamlit run app.py
"""

import pandas as pd
import streamlit as st

from inspector import Report, inspect

EXAMPLES = {
    "SauceDemo — Login button": ("https://www.saucedemo.com", "Login", False),
    "demoqa — Male radio (partial match trap)": ("https://demoqa.com/automation-practice-form", "Male", False),
    "demoqa — First Name, by CSS": ("https://demoqa.com/automation-practice-form", "#firstName", True),
    "Your own": ("", "", False),
}

st.set_page_config(page_title="Locator Inspector", page_icon="🔎", layout="wide")
st.title("🔎 Locator Inspector")
st.caption(
    "Point at one element. See every way Playwright could find it — "
    "and whether each way finds exactly that element, checked on the live page."
)


@st.cache_data(show_spinner=False, ttl=600)
def run(url: str, target: str, css: bool) -> Report:
    """Cached per input, so re-rendering the page does not reopen the browser."""
    return inspect(url, target, css=css)


# ── inputs ────────────────────────────────────────────────────────────────
example = st.selectbox("Example", list(EXAMPLES))
default_url, default_target, default_css = EXAMPLES[example]
left, middle, right = st.columns([3, 2, 1])
url = left.text_input("Page URL", value=default_url, placeholder="https://…")
target = middle.text_input("Element", value=default_target, placeholder="visible text, or a CSS selector")
css = right.checkbox("CSS selector", value=default_css, help="Off: find it by its visible text or label")

if not st.button("Inspect", type="primary", disabled=not (url and target)):
    st.stop()

try:
    with st.spinner("Opening the page and checking every locator…"):
        report = run(url, target, css)
except LookupError as error:
    st.error(f"Could not find the element: {error}")
    st.stop()
except Exception as error:  # a bad URL, a timeout, a page that will not load
    st.error(f"Inspection failed: {type(error).__name__}: {error}")
    st.stop()

# ── summary ───────────────────────────────────────────────────────────────
shot, summary = st.columns([3, 2])
shot.image(report.screenshot, caption="The element, outlined in red", width="stretch")

with summary:
    st.markdown(
        f"**Found via:** {report.found_via}  \n"
        f"**Role:** `{report.role}` · **Name:** `{report.accessible_name}` · **Tag:** `{report.signals['tag']}`"
    )
    st.subheader("Best locator")
    if report.best:
        st.code(report.best.code, language="python")
        st.caption(f"{report.best.kind}: unique, and not a generated value")
    else:
        st.warning("No locator here is both unique and stable.")

    unique = sum(row.ok for row in report.rows)
    a, b, c = st.columns(3)
    a.metric("Locators", len(report.rows))
    b.metric("Unique ✅", unique)
    c.metric("Unsafe ❌", len(report.rows) - unique)

# ── every candidate ───────────────────────────────────────────────────────
st.subheader("Every way to find it")
table = pd.DataFrame(
    [
        {
            "": "✅" if row.ok else "❌",
            "Kind": row.kind,
            "Locator": row.code,
            "Matches": row.matches,
            "Status": row.status + ("  ⚠️ looks generated" if row.generated else ""),
            "Note": row.note,
        }
        for row in report.rows
    ]
)


def colour(row: pd.Series) -> list[str]:
    if row[""] == "❌":
        shade = "#fde2e1"
    elif "generated" in row["Status"]:
        shade = "#fff4d6"
    else:
        shade = "#e3f6e8"
    return [f"background-color: {shade}"] * len(row)


st.dataframe(table.style.apply(colour, axis=1), hide_index=True, width="stretch")

with st.expander("What do the statuses mean?"):
    st.markdown(
        "- **unique** — matches exactly one element, and it is the one you pointed at. Safe to use.\n"
        "- **ambiguous (n)** — matches *n* elements. An automation would act on the first one, "
        "which may not be yours.\n"
        "- **different element** — matches one element, but not yours.\n"
        "- **no match** — finds nothing.\n"
        "- **⚠️ looks generated** — the value looks like a build hash (`css-13cymwt`), "
        "so it may change on the next deploy even though it is unique today.\n\n"
        "Rows without `exact=True` match any name or text *containing* yours — "
        "that is how `Male` also finds `Female`."
    )
