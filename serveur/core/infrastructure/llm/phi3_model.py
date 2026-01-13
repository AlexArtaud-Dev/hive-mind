"""
Implémentation du wrapper LLM pour Phi-3 via llama-cpp-python.

Utilise llama.cpp pour l'inférence CPU optimisée du modèle Phi-3-mini.
"""

from typing import AsyncIterator, Optional, Dict, Any
from pathlib import Path
import asyncio
from datetime import datetime

from llama_cpp import Llama

from core.domain.interfaces import LLMInterface, LLMResponse
from shared.errors import LLMError, ModelLoadError
from config import settings


class Phi3Model(LLMInterface):
    """
    Implémentation LLM pour Phi-3-mini via llama-cpp-python.

    Gère le chargement du modèle GGUF, la génération de texte
    avec streaming, et les optimisations CPU.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        n_ctx: Optional[int] = None,
        n_threads: Optional[int] = None,
        n_gpu_layers: Optional[int] = None,
    ):
        """
        Initialise le modèle Phi-3.

        Args:
            model_path: Chemin vers le fichier GGUF (défaut: depuis config)
            n_ctx: Taille de la fenêtre de contexte (défaut: depuis config)
            n_threads: Nombre de threads CPU (défaut: depuis config)
            n_gpu_layers: Nombre de couches GPU (défaut: 0, CPU-only)

        Raises:
            ModelLoadError: Si le modèle ne peut pas être chargé
        """
        self._model_path = model_path or settings.llm_model_path
        self._n_ctx = n_ctx or settings.llm_context_size
        self._n_threads = n_threads or settings.llm_n_threads
        self._n_gpu_layers = n_gpu_layers or settings.llm_n_gpu_layers

        self._model: Optional[Llama] = None
        self._is_loaded = False

    async def _load_model(self) -> None:
        """
        Charge le modèle en mémoire.

        Exécuté de manière lazy au premier appel.

        Raises:
            ModelLoadError: Si le chargement échoue
        """
        if self._is_loaded:
            return

        try:
            # Vérifier que le fichier existe
            model_file = Path(self._model_path)
            if not model_file.exists():
                raise ModelLoadError(
                    model_name="Phi-3-mini",
                    model_path=self._model_path,
                    message=f"Model file not found at {self._model_path}",
                    timestamp=datetime.utcnow(),
                )

            # Charger le modèle (opération bloquante, executer dans thread)
            loop = asyncio.get_event_loop()
            self._model = await loop.run_in_executor(
                None,
                lambda: Llama(
                    model_path=self._model_path,
                    n_ctx=self._n_ctx,
                    n_threads=self._n_threads,
                    n_gpu_layers=self._n_gpu_layers,
                    verbose=False,
                ),
            )

            self._is_loaded = True

        except ModelLoadError:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            raise ModelLoadError(
                model_name="Phi-3-mini",
                model_path=self._model_path,
                message=f"{str(e)}\n\nDetailed traceback:\n{error_details}",
                context={"error_type": type(e).__name__},
                timestamp=datetime.utcnow(),
            )

    def _format_prompt(self, prompt: str) -> str:
        """
        Formate le prompt selon le template Phi-3.

        Phi-3 utilise le format:
        <|system|>
        System prompt<|end|>
        <|user|>
        User message<|end|>
        <|assistant|>

        Args:
            prompt: Prompt brut

        Returns:
            Prompt formaté pour Phi-3
        """
        # Pour l'instant, format simple
        # TODO: Gérer system prompt + historique conversationnel
        return f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
    ) -> LLMResponse:
        """
        Génère une réponse complète à partir d'un prompt.

        Args:
            prompt: Prompt à envoyer au modèle
            max_tokens: Nombre maximum de tokens à générer
            temperature: Température de génération (0.0-2.0)
            stop_sequences: Séquences pour arrêter la génération

        Returns:
            LLMResponse contenant la réponse générée et métadonnées

        Raises:
            LLMError: Si la génération échoue
        """
        await self._load_model()

        if not self._model:
            raise LLMError(
                message="Model not loaded",
                timestamp=datetime.utcnow(),
            )

        try:
            formatted_prompt = self._format_prompt(prompt)

            # Séquences de stop par défaut pour Phi-3
            default_stops = ["<|end|>", "<|user|>"]
            stops = list(set(default_stops + (stop_sequences or [])))

            # Génération (opération bloquante)
            loop = asyncio.get_event_loop()
            start_time = datetime.utcnow()

            output = await loop.run_in_executor(
                None,
                lambda: self._model(
                    formatted_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stops,
                    echo=False,
                ),
            )

            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            # Extraire le texte généré
            generated_text = output["choices"][0]["text"].strip()
            tokens_used = output["usage"]["total_tokens"]

            return LLMResponse(
                content=generated_text,
                tokens_used=tokens_used,
                metadata={
                    "duration_ms": duration_ms,
                    "model": "Phi-3-mini",
                    "temperature": temperature,
                    "finish_reason": output["choices"][0].get("finish_reason"),
                },
            )

        except Exception as e:
            raise LLMError(
                message=f"Generation failed: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "prompt_length": len(prompt),
                },
                timestamp=datetime.utcnow(),
            )

    async def generate_streaming(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[list[str]] = None,
    ) -> AsyncIterator[str]:
        """
        Génère une réponse en streaming (chunk par chunk).

        Args:
            prompt: Prompt à envoyer au modèle
            max_tokens: Nombre maximum de tokens à générer
            temperature: Température de génération (0.0-2.0)
            stop_sequences: Séquences pour arrêter la génération

        Yields:
            Chunks de texte au fur et à mesure de la génération

        Raises:
            LLMError: Si la génération échoue
        """
        await self._load_model()

        if not self._model:
            raise LLMError(
                message="Model not loaded",
                timestamp=datetime.utcnow(),
            )

        try:
            formatted_prompt = self._format_prompt(prompt)

            # Séquences de stop par défaut pour Phi-3
            default_stops = ["<|end|>", "<|user|>"]
            stops = list(set(default_stops + (stop_sequences or [])))

            # Génération streaming
            stream = self._model(
                formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stops,
                echo=False,
                stream=True,
            )

            for output in stream:
                if "choices" in output and len(output["choices"]) > 0:
                    text = output["choices"][0].get("text", "")
                    if text:
                        yield text

                    # Vérifier si la génération est terminée
                    if output["choices"][0].get("finish_reason") is not None:
                        break

        except Exception as e:
            raise LLMError(
                message=f"Streaming generation failed: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "prompt_length": len(prompt),
                },
                timestamp=datetime.utcnow(),
            )

    async def is_loaded(self) -> bool:
        """
        Vérifie si le modèle est chargé et prêt.

        Returns:
            True si le modèle est prêt à générer
        """
        return self._is_loaded

    async def unload(self) -> None:
        """
        Décharge le modèle de la mémoire.

        Utile pour libérer les ressources quand le modèle n'est plus utilisé.
        """
        if self._model is not None:
            # llama-cpp-python gère le nettoyage automatiquement
            self._model = None
            self._is_loaded = False

    def get_context_size(self) -> int:
        """
        Retourne la taille de la fenêtre de contexte du modèle.

        Returns:
            Nombre de tokens de contexte disponibles
        """
        return self._n_ctx
