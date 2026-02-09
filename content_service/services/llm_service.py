import os
from langchain_openai import ChatOpenAI
from django.conf import settings
api_key=settings.FIREWORKS_API_KEY


def llm_client():
  

    if not api_key:
        raise ValueError("FIREWORKS_API_KEY is missing. Please set it in environment variables.")

    return ChatOpenAI(
        api_key=api_key,
        base_url="https://api.fireworks.ai/inference/v1",
        model="accounts/fireworks/models/gpt-oss-120b"
    )


def generate_topics(overview, category):
    llm = llm_client()

    prompt = f"""
Generate 10 unique, modern, engaging content topics.

CATEGORY: {category}
OVERVIEW: {overview}

RULES:
- No bullets
- No numbering
- Very clear English
- Short & precise
"""

    res = llm.invoke(prompt)

    final_topics = []
    for line in res.content.split("\n"):
        clean = line.strip().lstrip("-•0123456789. ").strip()
        if len(clean) > 3:
            final_topics.append(clean)

    return final_topics[:10]


def build_post_prompt(overview, category, topics, platform, length):
    topic_lines = "\n".join([f"- {t}" for t in topics])

    return f"""
You are an expert {platform} content creator.

OVERVIEW:
{overview}

CATEGORY:
{category}

SELECTED TOPICS:
{topic_lines}

CONTENT LENGTH REQUIREMENT:
{length}

TASK:
Write a complete, high-quality {platform} post.
Make it engaging, clear, and optimized for audience retention.
"""


def generate_post(overview, category, topics, platform, length):
    llm = llm_client()
    prompt = build_post_prompt(overview, category, topics, platform, length)
    res = llm.invoke(prompt)
    return res.content
