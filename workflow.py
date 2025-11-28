#reflecting changes
from anthropic import Anthropic
import io
import os
import streamlit as st
from rapidfuzz import fuzz
import requests


from drive_manager import (
    get_drive_service,
    api_get_file_content,
    get_guideline_filenames,
    get_framework_content,
    get_all_patient_files
)

client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

#For pulling data from postgres api
def fetch_patient_data():
    print("Calling patient data API...")

    url = "https://backend.qa.continuumcare.ai/api/llm/data?user_id=182&page=2&size=20"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.secrets['API_BEARER_TOKEN']}"
    }

    try:
        r = requests.get(url, headers=headers)
        print("Status:", r.status_code)
        print("Queried URL:", url)
        print("Raw text:", r.text[:200])

        return r.json()

    except Exception as e:
        print("Error:", e)
        return None


def fetch_patient_data_by_id(_):
    print("Fetching HARD-CODED patient URL...")

    url = "https://backend.qa.continuumcare.ai/api/llm/data?user_id=182&page=2&size=20"

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {st.secrets['API_BEARER_TOKEN']}"
    }

    try:
        r = requests.get(url, headers=headers)
        print("Status:", r.status_code)
        print("Queried URL:", url)
        print("Raw text:", r.text[:200])

        return r.json()

    except Exception as e:
        print("Error:", e)
        return None

def load_frameworks():
    print(">>> CACHE USED? cached_frameworks exists and valid:",
          "cached_frameworks" in st.session_state and 
          st.session_state.cached_frameworks is not None and
          len(st.session_state.cached_frameworks) > 0)

    # 1. If cache exists AND has data → return it
    if (
        "cached_frameworks" in st.session_state
        and isinstance(st.session_state.cached_frameworks, list)
        and len(st.session_state.cached_frameworks) > 0
    ):

        print(">>> Returning cached frameworks")
        return st.session_state.cached_frameworks

    print(">>> No valid cache found, loading frameworks from Drive")

    raw = get_framework_content()  # downloads once per session

    frameworks = []
    if raw is None or raw.strip() == "":
        print("⚠️ WARNING: get_framework_content() returned empty content")
    else:
        blocks = raw.split("--- START OF PROMPT FRAMEWORK:")

        for block in blocks[1:]:
            try:
                header, content = block.split("---", 1)
                name = header.strip()
                full_text = content.replace("END OF PROMPT FRAMEWORK:", "").strip()
                frameworks.append({"name": name, "content": full_text})
            except:
                print("⚠️ Skipping malformed framework block")

    # 3. Save to cache
    st.session_state.cached_frameworks = frameworks
    print(">>> Frameworks cached!", len(frameworks))

    return frameworks





# ---------------------------------------------------------
# FUZZY MATCH CHOOSER
# ---------------------------------------------------------
def choose_best_framework(user_query, frameworks):
    """Pick the closest matching framework using fuzzy matching."""
    best_score = -1
    best_framework = frameworks[0]

    for fw in frameworks:
        score = fuzz.partial_ratio(user_query.lower(), fw["name"].lower())
        if score > best_score:
            best_score = score
            best_framework = fw

    print(f"🔍 Fuzzy Score: {best_score} for {best_framework['name']}")
    return best_framework


# ---------------------------------------------------------
# MAIN RESPONSE GENERATOR
# ---------------------------------------------------------

def load_guideline_contents(required_filenames):

    # --- SAFETY NORMALIZATION ---
    if not isinstance(required_filenames, list):
        if isinstance(required_filenames, dict):
            # Claude returned {"files": [...]}
            if "files" in required_filenames and isinstance(required_filenames["files"], list):
                required_filenames = required_filenames["files"]
            else:
                # force fallback
                required_filenames = list(required_filenames.values())
        else:
            # unknown format → force empty list
            required_filenames = []

    # Create cache
    if "cached_guideline_contents" not in st.session_state:
        st.session_state.cached_guideline_contents = {}

    cache = st.session_state.cached_guideline_contents
    service = get_drive_service()

    all_files = get_guideline_filenames()

    for f in all_files:
        name = f["name"]
        if name in required_filenames and name not in cache:
            print("Downloading guideline (selected):", name)
            text = api_get_file_content(service, f["id"], f["mimeType"])
            cache[name] = text

    return cache


def generate_response(user_query):
    print("\n🔍 Starting generate_response()")
    service = get_drive_service()
    patient_files = get_all_patient_files()
    # 1. Load & match framework
    frameworks = load_frameworks()
    best_fw = choose_best_framework(user_query, frameworks)

    chosen_framework_name = best_fw["name"]
    framework_text = best_fw["content"]

    print(f"🧠 Chosen Framework: {chosen_framework_name}")

    system_prompt = f"""
You MUST strictly follow the framework below. 
Do not ignore, modify, or override any part of it.

=== FRAMEWORK START: {chosen_framework_name} ===
{framework_text}
=== FRAMEWORK END ===
"""

    # ----------------------------------------------------------
    # 2. LOAD PATIENT DATA FIRST (IMPORTANT!)
    # ----------------------------------------------------------
    patient_text = ""
    for f in patient_files:
        patient_text += f"\n\n---\nPATIENT FILE: {f['name']}\n{f['content']}"
       

    # ----------------------------------------------------------
    # 3. GUIDELINE SELECTION (FILENAMES + PATIENT DATA)
    # ----------------------------------------------------------
    guideline_files = get_guideline_filenames()
    filename_list = [f["name"] for f in guideline_files]

    selector_prompt = f"""
You are the guideline selector for a health summarization system.

Below is the patient's complete clinical data (all patient files):

=== PATIENT DATA ===
{patient_text}

---

User query:
"{user_query}"

Below is the list of available ADA guideline documents:
{chr(10).join(['- ' + name for name in filename_list])}

Your task:
1. Identify the patient's main clinical issues from the combined data above.
2. Select ONLY the guideline files relevant to those issues.
3. Return ONLY a JSON array of filenames.

Example:
["ADA Glycemic Goals and Hypoglycemia 2025.pdf",
 "ADA ChronicKidneyDiseaseAndRiskMgmt Diabetes 2025.pdf"]
"""

    print("📁 Asking Claude to select relevant guideline filenames...")

    selector_resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{"role": "user", "content": selector_prompt}]
    )

    raw_json = selector_resp.content[0].text
    print("🔍 Claude selector output:", raw_json)

    import json
    try:
        selected_filenames = json.loads(raw_json)
    except:
        selected_filenames = filename_list[:3]   # safe fallback

    print("📌 Selected guideline files:", selected_filenames)

    # ----------------------------------------------------------
    # 4. LOAD ONLY SELECTED GUIDELINE TEXT
    # ----------------------------------------------------------
    guideline_contents = load_guideline_contents(selected_filenames)


    selected_guideline_text = ""
    for name in selected_filenames:
        if name in guideline_contents:
            selected_guideline_text += f"\n\n---\nGUIDELINE FILE: {name}\n{guideline_contents[name]}"


    # ----------------------------------------------------------
    # 5. Final prompt
    # ----------------------------------------------------------
    user_message = f"""
Below are the materials you may use:

=== PATIENT DATA ===
{patient_text}

=== SELECTED ADA GUIDELINES ===
{selected_guideline_text}

---

User's question: {user_query}
"""

    print("🧠 Sending final request to Claude...")

    final_resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return final_resp.content[0].text
