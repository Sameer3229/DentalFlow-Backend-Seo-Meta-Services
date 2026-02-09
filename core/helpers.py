from langchain_core.prompts import PromptTemplate
from langchain_fireworks import Fireworks
import os
import json
from django.conf import settings
api_key=settings.FIREWORKS_API_KEY


def generate_seo_description(page_data: dict, max_tokens: int = 1000) -> str:
    
    # Load API key from environment
    if not api_key:
        raise ValueError("FIREWORKS_API_KEY not found in environment variables.")

    os.environ["FIREWORKS_API_KEY"] = api_key

    # Initialize LLM
    llm = Fireworks(
        model="accounts/fireworks/models/glm-4p5",
        max_tokens=max_tokens
    )

    # Prepare prompt
    prompt = f"""
You are an expert SEO analyst.
I am providing you data about a single page of a website.
Your task is to generate a **detailed SEO description** of this page, including:
1. Current SEO issues
2. Impact of issues on search engine performance
3. Recommendations for improvement
4. Suggestions to improve traffic and ranking

Page data:
{json.dumps(page_data, indent=2)}

Please write a professional, detailed description suitable for a website SEO report.
"""

    # Invoke the LLM
    output = llm.invoke(prompt)
    return output


def handle_serializer_exception(val, custom_message="-"):
    print("val.errors", val.errors)
    if "error" in val.errors:
        error = val.errors["error"][0]
    else:
        key = next(iter(val.errors))
        error = key + ", " + val.errors[key][0]
        error = error.replace("non_field_errors, ", "")

    if custom_message != "-":
        if "unique" in str(error).lower():
            error = custom_message
    return error
