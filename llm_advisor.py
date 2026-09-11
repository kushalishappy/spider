import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna",
).strip()


# ============================================================
# LLM ADVISORY GENERATOR
# ============================================================

def generate_llm_advisory(
    user_query: str,
    sst_summary: Optional[Dict[str, Any]] = None,
    sst_forecast: Optional[Dict[str, Any]] = None,
    chl_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # No API key
    # --------------------------------------------------------

    if not OPENAI_API_KEY:
        return {
            "status": "disabled",
            "output": "",
            "message": "OPENAI_API_KEY is not configured.",
        }

    # --------------------------------------------------------
    # Build evidence package
    # --------------------------------------------------------

    evidence = {
        "user_question": user_query,
        "sst_observation": sst_summary,
        "sst_forecast": sst_forecast,
        "chlorophyll_observation": chl_summary,
    }

    prompt = f"""
You are the Marine Advisory Agent for ORCA
(Ocean Reasoning & Coastal Advisor).

The user asked:

{user_query}

The specialist agents retrieved the following scientific evidence:

{evidence}

Your job is to synthesize a concise, scientifically cautious
coastal advisory.

STRICT RULES:

1. Use ONLY the evidence supplied above.
2. Never invent measurements, dates, trends, forecasts, or
   scientific observations.
3. Clearly distinguish observed measurements from projected
   values.
4. The SST forecast is a project-level trend extrapolation,
   NOT an operational ocean forecast.
5. Chlorophyll screening is NOT confirmation of a harmful
   algal bloom.
6. Never claim that a harmful algal bloom is confirmed.
7. Do not invent universal chlorophyll thresholds.
8. Do not claim fish abundance, fishing success, toxicity,
   ecosystem damage, or human-health effects unless the
   supplied evidence explicitly supports them.
9. If evidence is missing, explicitly say that it is missing.
10. Mention uncertainty where appropriate.
11. Answer the user's actual question directly.
12. Keep the response concise and useful for a marine
    stakeholder.
13. Do not mention these instructions.
14. Do not mention being an AI or language model.

Preferred structure:

Assessment:
- Direct answer to the user's question.

Evidence:
- Important observed SST information.
- Important SST outlook information, if available.
- Important chlorophyll information, if available.

Interpretation:
- Explain what the combined evidence suggests.
- If this concerns harmful algal blooms, describe it only
  as a screening/monitoring signal, never as confirmation.

Caution:
- Mention the most important limitation or uncertainty.
"""

    # --------------------------------------------------------
    # Call OpenAI
    # --------------------------------------------------------

    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY
        )

        response = client.responses.create(
            model=OPENAI_MODEL,
            instructions=(
                "You are a careful marine-science advisory "
                "assistant. Use only supplied evidence."
            ),
            input=prompt,
            max_output_tokens=700,
        )

        output = response.output_text.strip()

        if not output:
            return {
                "status": "error",
                "output": "",
                "message": "LLM returned an empty response.",
            }

        return {
            "status": "success",
            "output": output,
            "model": OPENAI_MODEL,
        }

    except Exception as exc:
        return {
            "status": "error",
            "output": "",
            "message": str(exc),
            "model": OPENAI_MODEL,
        }
    