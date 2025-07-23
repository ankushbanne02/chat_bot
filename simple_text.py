import json
import os
import requests
import pandas as pd
import ast
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")


sample_parcel_structure = {
    "pic": 460,
    "hostId": "2027756",
    "barcodes": ["0]C05900056383516"],
    "barcode_count": 1,
    "location": "1001.0041.0091",
    "destination": "016",
    "lifeCycle": {
        "registeredAt": None,
        "closedAt": None,
        "status": "sorted"
    },
    "barcodeErr": False,
    "events": [
        {
            "ts": "2025-05-13T07:46:40.312000",
            "type": "ItemInstruction",
            "raw": "HOST-0001|PLC-1001|2025-05-13T07:46:40.306Z|3|460|2027756||"
        },
        {
            "ts": "2025-05-13T07:47:30.837000",
            "type": "ItemPropertiesUpdate",
            "raw": "..."
        },
        {
            "ts": "2025-05-13T07:47:30.850000",
            "type": "ItemInstruction",
            "raw": "..."
        },
        {
            "ts": "2025-05-13T07:48:00.355000",
            "type": "UnverifiedSortReport",
            "raw": "..."
        },
        {
            "ts": "2025-05-13T07:48:39.025000",
            "type": "VerifiedSortReport",
            "raw": "..."
        }
    ],
    "volume_data": {
        "length": 300.0,
        "width": 295.0,
        "height": 200.0,
        "box_volume": 17700.0,
        "real_volume": 16745.0
    }
}



query = input("Enter your query about parcel data: ")

prompt = f"""
You are a Python data assistant. Below is the structure of a single parcel tracking log:

{json.dumps(sample_parcel_structure, indent=2)}

The data you will be analyzing is a Python list named `parcel_data`, where each element follows the above structure.

Generate Python code to answer the user query. Only return a JSON object with:
- "explanation": explanation of how the query will be answered
- "code": Python code to produce the answer and store it in a variable named `result`

User query: {query}
"""


url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

response = requests.post(
    url,
    headers={"Content-Type": "application/json"},
    json={"contents": [{"parts": [{"text": prompt}]}]},
)

try:
    res_json = response.json()

    if "candidates" not in res_json:
        print("\n Gemini API Error:\n", json.dumps(res_json, indent=2))
        raise KeyError("'candidates' key missing in Gemini response.")

    raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]

    
    print("\n Raw Gemini Response:\n", raw_text)

   
    try:
        response_dict = ast.literal_eval(raw_text.strip())
    except Exception as eval_err:
        print(f"\n Failed to parse Gemini response as Python dict:\n{eval_err}")
        response_dict = {}

    if "explanation" in response_dict:
        print("\n📘 Explanation:\n", response_dict["explanation"])
    if "code" in response_dict:
        print("\n📄 Generated Code:\n", response_dict["code"])

        exec_globals = {"parcel_data": parcel_data, "pd": pd}
        exec(response_dict["code"], exec_globals)

        if "result" in exec_globals:
            print("\n📦 Query Result:\n", exec_globals["result"])
        else:
            print("\n 'result' variable not found in executed code.")
    else:
        print("\n Gemini did not return valid code or explanation.")

except Exception as e:
    print(f"\n❌ Error during Gemini response processing or execution:\n{e}")
