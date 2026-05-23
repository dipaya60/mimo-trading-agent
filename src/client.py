"""
MiMo API Client — async, retry, OpenAI-compatible.
"""
import json
import httpx
from .config import Config


class MiMoClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.MIMO_API_KEY
        self.base_url = Config.MIMO_BASE_URL
        self.model = Config.MIMO_MODEL
        self._client = httpx.AsyncClient(timeout=60)

    async def chat(self, prompt: str, system: str = "", temperature: float = 0.3) -> str:
        if not self.api_key:
            return self._fallback(prompt)
        try:
            resp = await self._client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system or "You are an expert crypto trading and risk management AI."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return self._fallback(prompt)

    def _fallback(self, prompt: str) -> str:
        return json.dumps({"signal": "HOLD", "reasoning": "MiMo API unavailable — using local analysis.", "confidence": 50})

    async def close(self):
        await self._client.aclose()
