import streamlit as st

from extractor import extract_action_items


st.set_page_config(page_title="Email Action Item Extractor", page_icon="📧", layout="wide")

st.title("Email Action Item Extractor")
st.caption("Paste a long email and extract tasks, due dates, people, and urgency hints.")

default_text = (
    "Can you send the slides by Friday, follow up with Jasmine next week, "
    "and review the budget before the meeting?"
)

email_text = st.text_area(
    "Email Text",
    value=default_text,
    height=280,
    placeholder="Paste your full email content here...",
)

extract_clicked = st.button("Extract Tasks", type="primary")

if extract_clicked:
    results = extract_action_items(email_text)

    if not results:
        st.warning("No obvious action items found. Try adding clearer task verbs.")
    else:
        st.success(f"Found {len(results)} action item(s).")
        st.markdown("---")

        for idx, item in enumerate(results, start=1):
            with st.container(border=True):
                st.subheader(f"Task {idx}")
                st.write(f"**Task:** {item['task']}")
                st.write(f"**Due Date:** {item['due_date'] or 'Not specified'}")

                people = item["people"]
                people_label = ", ".join(people) if people else "Not specified"
                st.write(f"**Person Mentioned:** {people_label}")

                priority_emoji = "🔴" if item["priority"] == "High" else "🟡"
                st.write(f"**Priority:** {priority_emoji} {item['priority']}")

st.markdown("---")
st.caption(
    "MVP note: This version is rule-based and beginner-friendly. "
    "You can later extend it with Notion or Google Calendar integrations."
)
