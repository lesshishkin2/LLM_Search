from openai import OpenAI
import logging


logger = logging.getLogger(__name__)
client = OpenAI()


def ask_gpt(model, prompt, response_format, reasoning=False, timeout=60):
    messages = [
        {"role": "system", "content": prompt},
    ]

    while True:
        try:
            if reasoning:
                completion = client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
                    response_format=response_format,
                    reasoning_effort="high",
                    timeout=timeout
                )
            else:
                completion = client.beta.chat.completions.parse(
                    model=model,
                    temperature=0,
                    messages=messages,
                    response_format=response_format,
                    timeout=timeout
                )
            return completion.choices[0].message.parsed
        except Exception as e:
            logger.error(f"An error occurred: {e}. Retrying...")
            user_input = input("Press Enter to retry or type 'exit' to quit: ")
            if user_input.lower() == 'exit':
                logger.info("Exiting the retry loop.")
                raise RuntimeError("Exiting the retry loop due to errors.")
