class OllamaClient:
    def __init__(self, ollama_host) -> None:
        self.host = ollama_host

    def generate(
        self,
        user_prompt: str,
        system_prompt: str | None,
        model: str = "qwen2.5:7b",
        temperature: float = 0.2,
        top_p: float = 0.9,
        top_k: int = 40,
        json_mode: bool = False,
    ) -> str:

        import requests

        payload = {
            "model": model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": 1000,
            },
        }
        if json_mode:
            payload["format"] = "json"

        response = requests.post(f"{self.host}/api/generate", json=payload)
        response.raise_for_status()

        return response.json()
