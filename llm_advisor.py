import google.generativeai as genai

def generate_llm_advisory(user_query: str, sst_summary: dict, sst_forecast: dict, chl_summary: dict) -> dict:
    """
    Generates a conversational, expert marine advisory using Gemini.
    """
    # HARDCODED FOR HACKATHON - Paste your exact Gemini API Key inside the quotes below
    API_KEY = "AQ.Ab8RN6IKhDP0a_huXc5xYI2osjUjywWJGmoZSQZjAcY7LO_KYg" 
    
    try:
        genai.configure(api_key=API_KEY)
        
        # Use Gemini model for fast, intelligent reasoning
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        You are ORCA, an elite conversational Marine & Coastal AI Advisor.
        The user is asking you this specific question: "{user_query}"

        Here is the real-time satellite telemetry data retrieved for their selected coordinate:
        - SST Summary: {sst_summary}
        - SST Forecast: {sst_forecast}
        - Chlorophyll-a & Bloom Risk: {chl_summary}

        Your directives:
        1. Answer their specific question directly, conversationally, and expert-level like an oceanographer.
        2. If they ask about fishing viability or where fish will be, evaluate the Chlorophyll-a levels (1.0 to 3.0 mg/m³ indicates a highly productive Potential Fishing Zone; over 3.0 indicates harmful algal bloom risk; below 1.0 is low productivity).
        3. If they ask about safety, evaluate temperature extremes and bloom risks.
        4. Keep your answer professional, engaging, and concise (3-4 sentences max), grounding all advice strictly in the provided telemetry data. Avoid rigid bullet points or markdown templates.
        """
        
        response = model.generate_content(prompt)
        output_text = response.text.strip()
        
        return {
            "status": "success",
            "output": output_text
        }
        
    except Exception as e:
        return {
            "status": "error",
            "output": f"LLM advisory generation failed: {str(e)}"
        }