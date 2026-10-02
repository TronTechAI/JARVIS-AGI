import json
import os
import requests
from typing import Union, List, Dict
from dotenv import load_dotenv

load_dotenv()

def generate(
    conversation: Union[str, List[Dict[str, str]]],
    model: str = 'meta-llama/Meta-Llama-3.1-405B-Instruct',
    system_prompt: str = "Be helpful and friendly. Keep your response straightforward, short, and concise.",
    max_tokens: int = 512,
    temperature: float = 0.7,
    stream: bool = True,
    chunk_size: int = 1
) -> Union[str, None]:
    """
    Generates responses using various large language models (LLMs) for conversational interactions.
    
    Args:
        conversation (Union[str, List[Dict[str, str]]]): A single user query or conversation history.
        model (str): The identifier of the LLM to be used.
        system_prompt (str): The initial system message to guide the conversation.
        max_tokens (int): The maximum number of tokens to be generated.
        temperature (float): The randomness of the LLM's output.
        stream (bool): Whether to stream the response from the LLM.
        chunk_size (int): The size of chunks to be streamed from the LLM.

    Models:
            - "meta-llama/Meta-Llama-3.1-405B-Instruct"
            - "meta-llama/Meta-Llama-3.1-70B-Instruct"
            - "meta-llama/Meta-Llama-3.1-8B-Instruct"
            - "nvidia/Nemotron-4-340B-Instruct"
            - "meta-llama/Meta-Llama-3-70B-Instruct"
            - "meta-llama/Meta-Llama-3-8B-Instruct" 
            - "mistralai/Mixtral-8x22B-Instruct-v0.1"
            - "mistralai/Mixtral-8x22B-v0.1"
            - "microsoft/WizardLM-2-8x22B"
            - "microsoft/WizardLM-2-7B"
            - "HuggingFaceH4/zephyr-orpo-141b-A35b-v0.1"
            - "google/gemma-1.1-7b-it"
            - "databricks/dbrx-instruct"
            - "mistralai/Mixtral-8x7B-Instruct-v0.1"
            - "mistralai/Mistral-7B-Instruct-v0.2"
            - "meta-llama/Llama-2-70b-chat-hf"
            - "cognitivecomputations/dolphin-2.6-mixtral-8x7b"

    Returns:
        Union[str, None]: The LLM's response if successful, otherwise None.
    """
    API_URL = "https://api.deepinfra.com/v1/openai/chat/completions"
    
    headers = {
        "Accept": "text/event-stream",
        "Authorization": f"Bearer {os.environ.get('DEEPINFRA')}",
        "Content-Type": "application/json",
    }

    if isinstance(conversation, str):
        conversation = [{"role": "user", "content": conversation}]
    elif not isinstance(conversation, list):
        raise ValueError("Conversation must be either a string or a list of dictionaries")

    conversation.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": model,
        "messages": conversation,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stop": [],
        "stream": True
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        
        full_response = ""
        for line in response.iter_lines(decode_unicode=True, chunk_size=chunk_size):
            if line.startswith("data:"):
                try:
                    content = json.loads(line[5:])
                    if content != "[DONE]":
                        delta_content = content.get("choices", [{}])[0].get("delta", {}).get("content")
                        if delta_content:
                            if stream:
                                print(delta_content, end="", flush=True)
                            full_response += delta_content

                except:
                    continue
        
        return full_response.strip()
    
    except requests.RequestException as e:
        print(f"Error occurred during API request: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response content: {e.response.text}")
        return None

if __name__ == "__main__":
    single_query = "What is the capital of France?"
    response = generate(conversation=single_query, system_prompt="Be detailed", stream=True)

    conversation_history = [
        {"role": "user", "content": "My name is Sreejan."},
        {"role": "assistant", "content": "Nice to meet you, Sreejan."},
        {"role": "user", "content": "What is my name?"}
    ]
    response = generate(conversation=conversation_history, system_prompt="Talk like Shakespeare", stream=True)

