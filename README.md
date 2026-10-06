# 🔎 Locator Inspector

Point at one element on a web page. See every way Playwright could find it, and whether each way finds exactly that element, checked on the live page.

A locator that works today can still be wrong. `get_by_role("radio", name="Male")` also matches **Fe**male. A class like `css-13cymwt` changes on the next deploy. An XPath breaks when anything above it moves. Locator Inspector builds every candidate locator for an element, runs each one against the real page, and tells you which ones are safe to use.

## What you get

For the **Male** radio button on [demoqa's practice form](https://demoqa.com/automation-practice-form):

```
https://demoqa.com/automation-practice-form  →  'Male'  (found via label)
role='radio'  name='Male'  tag=input

✅ unique             id                     page.locator("#gender-radio-1")
❌ ambiguous (3)      name                   page.locator("input[name='gender']")
✅ unique             role + name            page.get_by_role("radio", name="Male", exact=True)
❌ ambiguous (2)      role + name (partial)  page.get_by_role("radio", name="Male")
✅ unique             label                  page.get_by_label("Male", exact=True)
❌ ambiguous (6)      css class              page.locator("input.form-check-input")
✅ unique             xpath                  page.locator("xpath=/html[1]/body[1]/div[1]/…/input[1]")

best: page.locator("#gender-radio-1")
```

The web app shows the same results as a colour-coded table, with a screenshot of the page and the element outlined in red.

### What the statuses mean

| Status | Meaning |
| --- | --- |
| **unique** | Matches exactly one element, and it is the one you pointed at. Safe to use. |
| **ambiguous (n)** | Matches *n* elements. An automation would act on the first one, which may not be yours. |
| **different element** | Matches one element, but not yours. |
| **no match** | Finds nothing. |
| **⚠️ looks generated** | The value looks like a build hash, so it may change on the next deploy even though it is unique today. |

The **best** locator is the first one, in the order of the table, that is unique and does not look generated.

## Run it locally

You need Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The app downloads Playwright's headless Chromium the first time it starts. On Linux, Chromium also needs some system libraries: `playwright install-deps chromium` installs them (it asks for your password).

### From the terminal

```bash
python inspector.py https://www.saucedemo.com Login
python inspector.py https://demoqa.com/automation-practice-form "#firstName" --css
```

Without `--css`, the second argument is the element's visible text, label or placeholder. With `--css`, it is a CSS selector. If you run the CLI before the web app, run `playwright install chromium` first.

## How it works

All the logic is in [`inspector.py`](inspector.py), in four steps:

1. **Find** the element you mean. A CSS selector is used as given. Otherwise it tries, in order: a button or link with that exact name, then a label, a placeholder, exact text, and finally partial text. If several elements match, it uses the first and says so.
2. **Read** everything that might identify it, inside the browser: test-id attributes (`data-testid`, `data-test`, `data-test-id`), `id`, `name`, `placeholder`, label, text, classes and XPath, plus the role and accessible name Playwright computes.
3. **Build** a candidate locator from each of those, in priority order: test id, id, name, role + name, label, placeholder, text, CSS class, XPath. Role and text also get a version without `exact=True` to show what partial matching catches.
4. **Check** each candidate with Playwright itself: how many elements it matches, and whether the first match is the element from step 1.

[`app.py`](app.py) is the Streamlit interface. It caches each result for 10 minutes, so re-running the same inspection does not reopen the browser.

## Deploy on Streamlit Community Cloud

1. Fork this repository.
2. On [share.streamlit.io](https://share.streamlit.io), click **Create app** and choose your fork, branch `master` and main file `app.py`. Under **Advanced settings**, pick Python 3.11.
3. Deploy.

Two files make Playwright work there. [`packages.txt`](packages.txt) lists the Linux libraries Chromium needs, which Community Cloud installs with apt. [`app.py`](app.py) downloads the browser itself when it starts. The first deploy and the first inspection are slower because of these.

## Limitations

- Elements inside iframes are not found.
- Pages behind a login are not supported: the browser starts with no session.
- The page gets one second after it loads for client-side rendering. Elements that appear later may be missed.

## License

[MIT](LICENSE)
