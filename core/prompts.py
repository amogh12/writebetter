def build_messages(text: str, instructions: str, n: int) -> list[dict]:
    if n == 3:
        style_note = (
            " Variant 1: minimal fix — grammar and clarity only."
            " Variant 2: polished and fluent."
            " Variant 3: concise."
        )
    else:
        style_note = " Each variant must differ clearly in style or approach."

    system = (
        f"You rewrite the user's text in clearer English. "
        f"Preserve meaning, names, numbers, links, and formatting. "
        f"Return ONLY a JSON array of exactly {n} strings, each a distinct variant. "
        f"No commentary.{style_note}"
    )
    user = f"Instructions: {instructions}\n\nText:\n{text}"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
