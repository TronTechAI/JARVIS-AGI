import requests
import json
import os
import re
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()  # Load environment variables from .env file

def generate(
    conversation_history: List[Dict[str, str]],
    system_prompt: Optional[str] = "You are a helpful and friendly AI assistant.",
    model: str = "meta-llama/llama-3-8b-instruct:free",
    max_tokens: int = 8096,
    temperature: float = 0.85,
    frequency_penalty: float = 0.34,
    presence_penalty: float = 0.06,
    repetition_penalty: float = 1.0,
    top_k: int = 0,
    stream: bool = True
) -> str:
    """
    Sends a request to the OpenRouter API and returns the generated text using the specified model.
    The system prompt is added at the beginning of the conversation history to guide the AI's behavior.

    Args:
        conversation_history: A list of dictionaries representing the conversation history.
                              Each dictionary should have "content" and "role" keys,
                              where "role" is either "system" or "user".
        system_prompt: An optional system prompt to guide the AI's behavior.
                       This prompt is added at the beginning of the conversation history.
        model: The language model to use for generating the response.
        max_tokens: The maximum number of tokens to generate in the response.
        temperature: A parameter controlling the diversity of the generated response.
        frequency_penalty: A penalty applied to tokens with low frequency in the training data.
        presence_penalty: A penalty applied to tokens based on their presence in the prompt.
        repetition_penalty: A penalty applied to repeated tokens in the generated response.
        top_k: The number of highest probability tokens to consider at each step of generation.
        stream: Whether to stream the response & show in real time

    Returns:
        The generated text.

    Available models:
    - Free:
        - "openchat/openchat-7b"
        - "huggingfaceh4/zephyr-7b-beta"
        - "mistralai/mistral-7b-instruct:free"
        - "meta-llama/llama-3-8b-instruct:free"
    
    - Flagship Opensource:
        - "meta-llama/llama-3-8b-instruct:extended"
        - "lynn/soliloquy-l3"
        - "mistralai/mixtral-8x22b-instruct"
        - "meta-llama/llama-3-70b-instruct:nitro"

    - Premium:
        - "openai/gpt-4"
        - "openai/gpt-4-0314"
        - "anthropic/claude-3-opus"
        - "anthropic/claude-3-opus:beta"
        - "openai/gpt-4-turbo"
    """

    # Add the system prompt to the beginning of the conversation history
    if system_prompt:
        conversation_history.insert(0, {"role": "system", "content": system_prompt})

    headers = {"Authorization": f"Bearer {os.environ.get('OPENROUTER')}"}
    payload = json.dumps({
        "messages": conversation_history,
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "repetition_penalty": repetition_penalty,
        "top_k": top_k,
        "stream": True,
    })

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=payload,
            stream=True
        )
        completion = ""
        for line in response.iter_lines(decode_unicode=True, chunk_size=1):
            if line:
                modified_value: str = re.sub("data:", "", line)
                try:
                    json_modified_value = json.loads(modified_value)
                    completion += json_modified_value['choices'][0]['delta']['content']
                    if stream: print(json_modified_value['choices'][0]['delta']['content'], end="", flush=True)
                except json.JSONDecodeError:
                    continue
        return completion
    except requests.RequestException as e:
        return f"Failed to Get Response\nError: {e}\nResponse: {response.text}"

if __name__ == "__main__":
    # Example usage with conversation history and system prompt
    conversation = [
        {"role": "user", "content": "My name is Clara and I live in Berkeley."},
        {"role": "assistant", "content": "Hi Clara! How can I help you today?"},
        {"role": "user", "content": "What is my name?"},
    ]
    
    response = generate(conversation, system_prompt="Talk Like Shakesphere")
    print("\n\n" + response)

