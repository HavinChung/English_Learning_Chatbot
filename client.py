from openai import OpenAI

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key="",
)

FAST_MODEL = "x-ai/grok-4.1-fast:free"

SMART_MODEL = "tngtech/deepseek-r1t2-chimera:free"

def call_llm_fast(system_prompt: str, user_message: str) -> str:
    completion = client.chat.completions.create(
        model=FAST_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return completion.choices[0].message.content

def call_llm(system_prompt: str, user_message: str) -> str:
    completion = client.chat.completions.create(
        model=SMART_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return completion.choices[0].message.content