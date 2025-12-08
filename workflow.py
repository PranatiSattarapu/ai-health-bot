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
    print(
        ">>> CACHE USED? cached_frameworks exists and valid:",
        "cached_frameworks" in st.session_state
        and isinstance(st.session_state.cached_frameworks, list)
        and len(st.session_state.cached_frameworks) > 0
    )

    # ✅ Return cached frameworks
    if (
        "cached_frameworks" in st.session_state
        and isinstance(st.session_state.cached_frameworks, list)
        and len(st.session_state.cached_frameworks) > 0
    ):
        print(">>> Returning cached frameworks")
        return st.session_state.cached_frameworks

    print(">>> No valid cache found, loading frameworks from Drive")

    raw = get_framework_content()

    frameworks = []
    if raw:
        blocks = raw.split("--- START OF PROMPT FRAMEWORK:")
        for block in blocks[1:]:
            try:
                header, content = block.split("---", 1)
                frameworks.append({
                    "name": header.strip(),
                    "content": content.replace(
                        "END OF PROMPT FRAMEWORK:", ""
                    ).strip()
                })
            except Exception:
                print("⚠️ Skipping malformed framework block")

    # ✅ Correct cache key
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
    """
    Load guideline contents for the specified filenames.
    Handles various input formats and caches results.
    """
    
    print(f"🔍 INPUT TYPE: {type(required_filenames)}")
    print(f"🔍 INPUT VALUE: {required_filenames}")
    
    # --- CRITICAL: ALWAYS convert to list first ---
    if required_filenames is None:
        required_filenames = []
    
    # Convert to list based on type
    if isinstance(required_filenames, str):
        required_filenames = [required_filenames]
    elif isinstance(required_filenames, dict):
        # Try to extract list from dict
        if "files" in required_filenames:
            required_filenames = required_filenames["files"]
        else:
            # Get all values and flatten
            temp = []
            for v in required_filenames.values():
                if isinstance(v, list):
                    temp.extend(v)
                elif isinstance(v, str):
                    temp.append(v)
            required_filenames = temp
    elif not isinstance(required_filenames, list):
        # Unknown type - force to empty list
        print(f"⚠️ CRITICAL: Unexpected type {type(required_filenames)}, forcing to empty list")
        required_filenames = []
    
    # Now we're GUARANTEED to have a list
    # Clean it up - remove None, empty strings, non-strings
    required_filenames = [str(x).strip() for x in required_filenames if x]
    
    print(f"✅ NORMALIZED TO LIST: {required_filenames}")
    
    # ===== FIX: Initialize cache properly =====
    if "cached_guideline_contents" not in st.session_state:
        st.session_state.cached_guideline_contents = {}
    
    # ===== FIX: Ensure cache is a dict, not None =====
    cache = st.session_state.cached_guideline_contents
    if cache is None or not isinstance(cache, dict):
        print("⚠️ Cache was None or invalid, initializing to empty dict")
        cache = {}
        st.session_state.cached_guideline_contents = cache
    
    print(f"📦 Cache status: {len(cache)} items cached")
    
    service = get_drive_service()
    
    if not service:
        print("⚠️ Drive service unavailable")
        return cache

    all_files = get_guideline_filenames()
    
    if not all_files:
        print("⚠️ No guideline files found")
        return cache

    # NOW it's safe to use 'in' operator
    for f in all_files:
        name = f["name"]
        try:
            if name in required_filenames:
                if name not in cache:
                    print(f"📥 Downloading: {name}")
                    text = api_get_file_content(service, f["id"], f["mimeType"])
                    cache[name] = text
                    print(f"✅ Cached: {name}")
                else:
                    print(f"📦 Already cached: {name}")
        except Exception as e:
            print(f"❌ Error with {name}: {e}")
            cache[name] = f"Error: {str(e)}"

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
    import re

    # Try to parse the JSON response
    selected_filenames = []
    try:
        # First, try direct JSON parsing
        selected_filenames = json.loads(raw_json)
        print("✅ Successfully parsed JSON directly")
    except json.JSONDecodeError:
        print("⚠️ Direct JSON parsing failed, trying to extract JSON from text...")
        
        # Try to find JSON array in the text
        json_match = re.search(r'\[.*?\]', raw_json, re.DOTALL)
        if json_match:
            try:
                selected_filenames = json.loads(json_match.group(0))
                print("✅ Successfully extracted JSON from text")
            except json.JSONDecodeError:
                print("❌ Could not parse extracted JSON")
                selected_filenames = filename_list[:3]  # Fallback
        else:
            print("❌ No JSON array found in response")
            selected_filenames = filename_list[:3]  # Fallback

    # --- NORMALIZE BEFORE USING ---
    if isinstance(selected_filenames, dict):
        if "files" in selected_filenames and isinstance(selected_filenames["files"], list):
            selected_filenames = selected_filenames["files"]
        else:
            # Extract values
            selected_filenames = []
            for value in selected_filenames.values():
                if isinstance(value, list):
                    selected_filenames.extend(value)
                elif isinstance(value, str):
                    selected_filenames.append(value)

    elif isinstance(selected_filenames, str):
        selected_filenames = [selected_filenames]

    elif not isinstance(selected_filenames, list):
        print(f"⚠️ Unexpected type: {type(selected_filenames)}, using fallback")
        selected_filenames = filename_list[:3]

    # Ensure all items are strings
    selected_filenames = [str(item) for item in selected_filenames if item]

    # Fallback if empty
    if not selected_filenames:
        print("⚠️ No files selected, using first 3 as fallback")
        selected_filenames = filename_list[:3]

    print("📌 Final selected guideline files:", selected_filenames)

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
