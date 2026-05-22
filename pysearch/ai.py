import litellm

litellm.set_verbose = False


def explain_code(code: str) -> str:
    """Verilen kodu AI ile açıklar."""
    response = litellm.completion(
        model="ollama/llama3.2",
        api_base="http://localhost:11434",
        messages=[
            {
                "role": "system",
                "content": "Sen bir kod açıklama asistanısın. Türkçe olarak kısa ve net açıklamalar yap.",
            },
            {
                "role": "user",
                "content": f"Bu kodu açıkla:\n\n```\n{code}\n```",
            },
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content


def suggest_refactor(code: str) -> str:
    """Verilen kod için refactor önerisi sunar."""
    response = litellm.completion(
        model="ollama/llama3.2",
        api_base="http://localhost:11434",
        messages=[
            {
                "role": "system",
                "content": "Sen bir kod kalitesi asistanısın. Türkçe olarak kısa refactor önerileri sun.",
            },
            {
                "role": "user",
                "content": f"Bu kod için refactor önerisi ver:\n\n```\n{code}\n```",
            },
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content