# #reflecting changes
# from anthropic import Anthropic
# import io
# import os
# import streamlit as st
# from rapidfuzz import fuzz
# import requests


# from drive_manager import (
#     get_drive_service,
#     api_get_file_content,
#     get_guideline_filenames,
#     get_framework_content,
#     get_all_patient_files
# )

# client = Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# #For pulling data from postgres api
# def fetch_patient_data():
#     print("Calling patient data API...")

#     url = "https://backend.qa.continuumcare.ai/api/llm/data?user_id=182&page=2&size=20"

#     headers = {
#         "Accept": "application/json",
#         "Authorization": f"Bearer {st.secrets['API_BEARER_TOKEN']}"
#     }

#     try:
#         r = requests.get(url, headers=headers)
#         print("Status:", r.status_code)
#         print("Queried URL:", url)
#         print("Raw text:", r.text[:200])

#         return r.json()

#     except Exception as e:
#         print("Error:", e)
#         return None


# def fetch_patient_data_by_id(_):
#     print("Fetching HARD-CODED patient URL...")

#     url = "https://backend.qa.continuumcare.ai/api/llm/data?user_id=182&page=2&size=20"

#     headers = {
#         "Accept": "application/json",
#         "Authorization": f"Bearer {st.secrets['API_BEARER_TOKEN']}"
#     }

#     try:
#         r = requests.get(url, headers=headers)
#         print("Status:", r.status_code)
#         print("Queried URL:", url)
#         print("Raw text:", r.text[:200])

#         return r.json()

#     except Exception as e:
#         print("Error:", e)
#         return None

# def load_frameworks():
#     print(
#         ">>> CACHE USED? cached_frameworks exists and valid:",
#         "cached_frameworks" in st.session_state
#         and isinstance(st.session_state.cached_frameworks, list)
#         and len(st.session_state.cached_frameworks) > 0
#     )

#     # ✅ Return cached frameworks
#     if (
#         "cached_frameworks" in st.session_state
#         and isinstance(st.session_state.cached_frameworks, list)
#         and len(st.session_state.cached_frameworks) > 0
#     ):
#         print(">>> Returning cached frameworks")
#         return st.session_state.cached_frameworks

#     print(">>> No valid cache found, loading frameworks from Drive")

#     raw = get_framework_content()

#     frameworks = []
#     if raw:
#         blocks = raw.split("--- START OF PROMPT FRAMEWORK:")
#         for block in blocks[1:]:
#             try:
#                 header, content = block.split("---", 1)
#                 frameworks.append({
#                     "name": header.strip(),
#                     "content": content.replace(
#                         "END OF PROMPT FRAMEWORK:", ""
#                     ).strip()
#                 })
#             except Exception:
#                 print("⚠️ Skipping malformed framework block")

#     # ✅ Correct cache key
#     st.session_state.cached_frameworks = frameworks
#     print(">>> Frameworks cached!", len(frameworks))

#     return frameworks





# # ---------------------------------------------------------
# # FUZZY MATCH CHOOSER
# # ---------------------------------------------------------
# def choose_best_framework(user_query, frameworks):
#     """Pick the closest matching framework using fuzzy matching."""
#     best_score = -1
#     best_framework = frameworks[0]

#     for fw in frameworks:
#         score = fuzz.partial_ratio(user_query.lower(), fw["name"].lower())
#         if score > best_score:
#             best_score = score
#             best_framework = fw

#     print(f"🔍 Fuzzy Score: {best_score} for {best_framework['name']}")
#     return best_framework


# # ---------------------------------------------------------
# # MAIN RESPONSE GENERATOR
# # ---------------------------------------------------------

# def load_guideline_contents(required_filenames):
#     """
#     Load guideline contents for the specified filenames.
#     Handles various input formats and caches results.
#     """
    
#     print(f"🔍 INPUT TYPE: {type(required_filenames)}")
#     print(f"🔍 INPUT VALUE: {required_filenames}")
    
#     # --- CRITICAL: ALWAYS convert to list first ---
#     if required_filenames is None:
#         required_filenames = []
    
#     # Convert to list based on type
#     if isinstance(required_filenames, str):
#         required_filenames = [required_filenames]
#     elif isinstance(required_filenames, dict):
#         # Try to extract list from dict
#         if "files" in required_filenames:
#             required_filenames = required_filenames["files"]
#         else:
#             # Get all values and flatten
#             temp = []
#             for v in required_filenames.values():
#                 if isinstance(v, list):
#                     temp.extend(v)
#                 elif isinstance(v, str):
#                     temp.append(v)
#             required_filenames = temp
#     elif not isinstance(required_filenames, list):
#         # Unknown type - force to empty list
#         print(f"⚠️ CRITICAL: Unexpected type {type(required_filenames)}, forcing to empty list")
#         required_filenames = []
    
#     # Now we're GUARANTEED to have a list
#     # Clean it up - remove None, empty strings, non-strings
#     required_filenames = [str(x).strip() for x in required_filenames if x]
    
#     print(f"✅ NORMALIZED TO LIST: {required_filenames}")
    
#     # ===== FIX: Initialize cache properly =====
#     if "cached_guideline_contents" not in st.session_state:
#         st.session_state.cached_guideline_contents = {}
    
#     # ===== FIX: Ensure cache is a dict, not None =====
#     cache = st.session_state.cached_guideline_contents
#     if cache is None or not isinstance(cache, dict):
#         print("⚠️ Cache was None or invalid, initializing to empty dict")
#         cache = {}
#         st.session_state.cached_guideline_contents = cache
    
#     print(f"📦 Cache status: {len(cache)} items cached")
    
#     service = get_drive_service()
    
#     if not service:
#         print("⚠️ Drive service unavailable")
#         return cache

#     all_files = get_guideline_filenames()
    
#     if not all_files:
#         print("⚠️ No guideline files found")
#         return cache

#     # NOW it's safe to use 'in' operator
#     for f in all_files:
#         name = f["name"]
#         try:
#             if name in required_filenames:
#                 if name not in cache:
#                     print(f"📥 Downloading: {name}")
#                     text = api_get_file_content(service, f["id"], f["mimeType"])
#                     cache[name] = text
#                     print(f"✅ Cached: {name}")
#                 else:
#                     print(f"📦 Already cached: {name}")
#         except Exception as e:
#             print(f"❌ Error with {name}: {e}")
#             cache[name] = f"Error: {str(e)}"

#     return cache

# def generate_response(user_query):
#     print("\n🔍 Starting generate_response()")
#     service = get_drive_service()
#     patient_files = get_all_patient_files()
#     # 1. Load & match framework
#     frameworks = load_frameworks()
#     best_fw = choose_best_framework(user_query, frameworks)

#     chosen_framework_name = best_fw["name"]
#     framework_text = best_fw["content"]

#     print(f"🧠 Chosen Framework: {chosen_framework_name}")

#     system_prompt = f"""
# You MUST strictly follow the framework below. 
# Do not ignore, modify, or override any part of it.

# === FRAMEWORK START: {chosen_framework_name} ===
# {framework_text}
# === FRAMEWORK END ===
# """

#     # ----------------------------------------------------------
#     # 2. LOAD PATIENT DATA FIRST (IMPORTANT!)
#     # ----------------------------------------------------------
#     patient_text = ""
#     for f in patient_files:
#         patient_text += f"\n\n---\nPATIENT FILE: {f['name']}\n{f['content']}"
       

#     # ----------------------------------------------------------
#     # 3. GUIDELINE SELECTION (FILENAMES + PATIENT DATA)
#     # ----------------------------------------------------------
#     guideline_files = get_guideline_filenames()
#     filename_list = [f["name"] for f in guideline_files]

#     selector_prompt = f"""
# You are the guideline selector for a health summarization system.

# Below is the patient's complete clinical data (all patient files):

# === PATIENT DATA ===
# {patient_text}

# ---

# User query:
# "{user_query}"

# Below is the list of available ADA guideline documents:
# {chr(10).join(['- ' + name for name in filename_list])}

# Your task:
# 1. Identify the patient's main clinical issues from the combined data above.
# 2. Select ONLY the guideline files relevant to those issues.
# 3. Return ONLY a JSON array of filenames.

# Example:
# ["ADA Glycemic Goals and Hypoglycemia 2025.pdf",
#  "ADA ChronicKidneyDiseaseAndRiskMgmt Diabetes 2025.pdf"]
# """

#     print("📁 Asking Claude to select relevant guideline filenames...")

#     selector_resp = client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=300,
#         messages=[{"role": "user", "content": selector_prompt}]
#     )

#     raw_json = selector_resp.content[0].text
#     print("🔍 Claude selector output:", raw_json)

#     import json
#     import re

#     # Try to parse the JSON response
#     selected_filenames = []
#     try:
#         # First, try direct JSON parsing
#         selected_filenames = json.loads(raw_json)
#         print("✅ Successfully parsed JSON directly")
#     except json.JSONDecodeError:
#         print("⚠️ Direct JSON parsing failed, trying to extract JSON from text...")
        
#         # Try to find JSON array in the text
#         json_match = re.search(r'\[.*?\]', raw_json, re.DOTALL)
#         if json_match:
#             try:
#                 selected_filenames = json.loads(json_match.group(0))
#                 print("✅ Successfully extracted JSON from text")
#             except json.JSONDecodeError:
#                 print("❌ Could not parse extracted JSON")
#                 selected_filenames = filename_list[:3]  # Fallback
#         else:
#             print("❌ No JSON array found in response")
#             selected_filenames = filename_list[:3]  # Fallback

#     # --- NORMALIZE BEFORE USING ---
#     if isinstance(selected_filenames, dict):
#         if "files" in selected_filenames and isinstance(selected_filenames["files"], list):
#             selected_filenames = selected_filenames["files"]
#         else:
#             # Extract values
#             selected_filenames = []
#             for value in selected_filenames.values():
#                 if isinstance(value, list):
#                     selected_filenames.extend(value)
#                 elif isinstance(value, str):
#                     selected_filenames.append(value)

#     elif isinstance(selected_filenames, str):
#         selected_filenames = [selected_filenames]

#     elif not isinstance(selected_filenames, list):
#         print(f"⚠️ Unexpected type: {type(selected_filenames)}, using fallback")
#         selected_filenames = filename_list[:3]

#     # Ensure all items are strings
#     selected_filenames = [str(item) for item in selected_filenames if item]

#     # Fallback if empty
#     if not selected_filenames:
#         print("⚠️ No files selected, using first 3 as fallback")
#         selected_filenames = filename_list[:3]

#     print("📌 Final selected guideline files:", selected_filenames)

#     # ----------------------------------------------------------
#     # 4. LOAD ONLY SELECTED GUIDELINE TEXT
#     # ----------------------------------------------------------
#     guideline_contents = load_guideline_contents(selected_filenames)


#     selected_guideline_text = ""
#     for name in selected_filenames:
#         if name in guideline_contents:
#             selected_guideline_text += f"\n\n---\nGUIDELINE FILE: {name}\n{guideline_contents[name]}"


#     # ----------------------------------------------------------
#     # 5. Final prompt
#     # ----------------------------------------------------------
#     user_message = f"""
# Below are the materials you may use:

# === PATIENT DATA ===
# {patient_text}

# === SELECTED ADA GUIDELINES ===
# {selected_guideline_text}

# ---

# User's question: {user_query}
# """

#     print("🧠 Sending final request to Claude...")

#     final_resp = client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=2000,
#         system=system_prompt,
#         messages=[{"role": "user", "content": user_message}],
#     )

#     return final_resp.content[0].text



import os
import io
import streamlit as st
from rapidfuzz import fuzz
from google import genai
from google.genai import types
from pathlib import Path
import json  # To read JSON files
import csv   # To read CSV files
from io import StringIO # To handle CSV reading from string data
# import anthropic
from anthropic import Anthropic

# --- Configuration & Secrets ---
# WARNING: Embed your actual key here. Using a placeholder for safety.

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
CLAUDE_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
GUIDELINE_STORE_NAME = st.secrets["GUIDELINE_STORE_NAME"]

genai_client = genai.Client(api_key=GEMINI_API_KEY)
claude = Anthropic(api_key=CLAUDE_API_KEY)


# Define your File Search Store name (The ID you got from the indexing script)

PATIENT_DATA_FOLDER = "user_data" 

# NOTE: The frameworks.py file must be in the same directory
try:
    from frameworks import FRAMEWORK_DATA as frameworks_list
    print("Frameworks loaded successfully from frameworks.py")
except ImportError:
    print("⚠️ ERROR: Could not import FRAMEWORK_DATA from frameworks.py. Ensure file exists.")
    frameworks_list = []
    
# --- Helper Functions (Frameworks) ---

def load_frameworks():
    """Returns the imported list of frameworks."""
    return frameworks_list

def choose_best_framework(user_query, frameworks):
    """Pick the closest matching framework using fuzzy matching."""
    if not frameworks:
        return {"name": "Default", "content": "You are a helpful assistant."}
        
    best_score = -1
    best_framework = frameworks[0]

    for fw in frameworks:
        # Use name and potential keywords for matching
        match_string = fw.get("name", "") + " ".join(fw.get("keywords", []))
        score = fuzz.partial_ratio(user_query.lower(), match_string.lower())
        
        if score > best_score:
            best_score = score
            best_framework = fw

    print(f"🔍 Fuzzy Score: {best_score} for {best_framework['name']}")
    return best_framework

# --- Helper Functions (Patient Data Handling) ---

def csv_to_llm_text(csv_data):
    """Converts a CSV string into a readable, line-by-line text format for the LLM."""
    output = []
    # Use StringIO to treat the string data as a file
    csvfile = StringIO(csv_data) 
    reader = csv.DictReader(csvfile)

    if reader.fieldnames:
        output.append("HEADERS: " + " | ".join(reader.fieldnames))
        output.append("-" * 50)
        
    for i, row in enumerate(reader):
        row_str = f"ROW {i+1}: "
        row_details = []
        for key, value in row.items():
            if value and str(value).strip(): 
                row_details.append(f"{key.strip()}={str(value).strip()}")
        
        output.append(row_str + ", ".join(row_details))

    return "\n".join(output)


def load_local_patient_data(folder_path=PATIENT_DATA_FOLDER):
    """Reads and concatenates content from all files (JSON/CSV) in the local folder."""
    print(f"📂 Loading patient data from: {folder_path}")
    patient_text = []
    path = Path(folder_path)
    
    if not path.is_dir():
        print(f"⚠️ ERROR: Directory not found: {folder_path}")
        return "\n--- PATIENT DATA: NONE FOUND ---\n"
        
    for file_path in path.iterdir():
        if file_path.is_file() and not file_path.name.startswith('.'):
            
            try:
                raw_content = file_path.read_text(encoding='utf-8')
                content_for_llm = ""

                if file_path.suffix.lower() == '.json':
                    # Parse and format JSON data
                    data = json.loads(raw_content)
                    content_for_llm = json.dumps(data, indent=2) 
                    
                elif file_path.suffix.lower() == '.csv':
                    # Convert CSV data to readable text format
                    content_for_llm = csv_to_llm_text(raw_content)

                else:
                    # Treat other file types as raw text (e.g., .txt)
                    content_for_llm = raw_content

                if content_for_llm:
                    patient_text.append(f"\n\n--- PATIENT FILE: {file_path.name} (Format: {file_path.suffix.upper()})\n{content_for_llm}")

            except Exception as e:
                print(f"⚠️ Could not process file {file_path.name}: {e}")
                
    if not patient_text:
        return "\n--- PATIENT DATA: NONE FOUND ---\n"
        
    return "\n".join(patient_text)

def generate_response(user_query):
    print("\n🔍 Starting generate_response (Gemini File Search + Claude)")

    # 1. Load & match framework
    frameworks = load_frameworks()
    best_fw = choose_best_framework(user_query, frameworks)

    chosen_framework_name = best_fw["name"]
    framework_text = best_fw["content"]

    print(f"🧠 Chosen Framework: {chosen_framework_name}")

    system_prompt = f"""
You MUST strictly follow everything defined in the framework. 
Do NOT override format, tone, or safety rules.

=== FRAMEWORK START: {chosen_framework_name} ===
{framework_text}
=== FRAMEWORK END ===
CRITICAL CITATION RULES:

The framework above contains example citations.
DO NOT use those example names.

You MUST cite ONLY from the "RETRIEVED GUIDELINE TEXT" section.

Rules:
- Use the exact filenames exactly as shown in the retrieved guideline text
- Do NOT rename, clean, summarize, or normalize filenames
- Every factual clinical statement must be supported by a citation
- If no guideline supports a statement, explicitly write:
  "No guideline citation available."
"""

    # 2. Load patient data
    patient_text = load_local_patient_data()

    # 3. USE GEMINI FILE SEARCH FOR RETRIEVAL
    print("📄 Calling Gemini FileSearch to retrieve relevant guideline chunks...")

    # Initialize variables BEFORE try block
    guideline_text = "No guideline chunks retrieved."
    sources_set = set()
    cleaned_sources = []

    try:
        # Create a more detailed retrieval prompt
        retrieval_prompt = f"""
        You MUST use the provided File Search tool.
        Do NOT answer from general knowledge.
        Search the clinical practice guidelines for information relevant to:


Query: {user_query}

Patient context: {patient_text[:600]}

Find specific recommendations, target values, and evidence-based protocols.
"""

        # Use raw REST API format - most compatible across SDK versions
        rag_resp = genai_client.models.generate_content(
            model="gemini-2.5-flash",  # More stable, better free tier limits
            contents=retrieval_prompt,
            config=types.GenerateContentConfig(
                tools=[{
                    "fileSearch": {
                        "fileSearchStoreNames": [GUIDELINE_STORE_NAME]
                    }
                }],
                max_output_tokens=2000,
                temperature=0.2
            )
        )

        print("\n===== DEBUG: GEMINI FILESEARCH OUTPUT =====")
        
        # Check if we have candidates
        if not rag_resp.candidates:
            print("❌ No candidates returned by Gemini")
            print("Response object:", rag_resp)
            print("Prompt was:", retrieval_prompt[:300], "...")
            
            # Check for safety ratings or blocks
            if hasattr(rag_resp, 'prompt_feedback'):
                print("Prompt feedback:", rag_resp.prompt_feedback)
            
            guideline_text = "No guideline chunks retrieved."
            sources_set = set()
        else:
            grounding = rag_resp.candidates[0].grounding_metadata
            
            if grounding is None:
                print("❌ No grounding metadata returned.")
                # Check if there's any response text at all
                try:
                    response_text = rag_resp.text if rag_resp.text else "No response text"
                    print("Response text:", response_text[:500])
                except (AttributeError, TypeError) as e:
                    print(f"⚠️ Could not access response text: {e}")
                    print("Response object:", rag_resp)
            else:
                chunks = grounding.grounding_chunks
                print(f"✅ Total Chunks Retrieved: {len(chunks)}")

                # OPTIONAL: Limit to top N chunks if you want control
                MAX_CHUNKS = 10  # Set to None to use all chunks
                if MAX_CHUNKS and len(chunks) > MAX_CHUNKS:
                    print(f"⚠️ Limiting to top {MAX_CHUNKS} chunks (out of {len(chunks)})")
                    chunks = chunks[:MAX_CHUNKS]

                retrieved_chunks = []

                if len(chunks) == 0:
                    print("❌ No chunks returned by FileSearch.")
                else:
                    for idx, c in enumerate(chunks):
                        print(f"\n--- Chunk {idx+1} ---")
                        print("Source File:", c.retrieved_context.title)
                        
                        # Try to access offset attributes if they exist
                        try:
                            print("Start Offset:", c.retrieved_context.start_offset)
                            print("End Offset:", c.retrieved_context.end_offset)
                        except AttributeError:
                            pass  # These attributes may not exist in all SDK versions
                        
                        CHUNK_PREVIEW_LEN = 1000  # or bigger
                        chunk_text = c.retrieved_context.text

                        print(f"Text Snippet ({min(len(chunk_text), CHUNK_PREVIEW_LEN)} chars):")
                        print(chunk_text[:CHUNK_PREVIEW_LEN], "...")

                        print("----------------------------------------")
                        
                        retrieved_chunks.append(f"[From: {c.retrieved_context.title}]\n{c.retrieved_context.text}")
                        sources_set.add(c.retrieved_context.title)

                    guideline_text = "\n\n---\n\n".join(retrieved_chunks)
        
        # Clean up source names for better citation formatting (always run this)
       
    except Exception as e:
        print("⚠️ FileSearch error:", e)
        import traceback
        traceback.print_exc()
        # Additional debugging
        print("\n=== DEBUGGING INFO ===")
        print("Model:", "gemini-2.5-pro")
        print("File store:", GUIDELINE_STORE_NAME)
        print("Query:", user_query)
        print("Patient data length:", len(patient_text) if patient_text else 0)
        
        guideline_text = "Error retrieving guidelines."
        sources_set = set()
    
    # 4. SEND EVERYTHING TO CLAUDE FOR FINAL ANSWER
    print("🧠 Sending context to Claude for final structured answer...")

    final_prompt = f"""
Below is all the available information to answer the user's question.
Use it STRICTLY under the rules of the provided framework.

=== PATIENT DATA ===
{patient_text}

=== RETRIEVED GUIDELINE TEXT ===
{guideline_text}


---

User question: {user_query}
"""

    try:
        claude_resp = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            system=system_prompt,
            messages=[{"role": "user", "content": final_prompt}]
        )

        return claude_resp.content[0].text

    except Exception as e:
        print("Claude API Error:", e)
        import traceback
        traceback.print_exc()
        return f"Error generating final answer: {e}"