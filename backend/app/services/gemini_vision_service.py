import asyncio
import base64
import hashlib
import io
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from PIL import Image, ImageOps
from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import VisionObservationCache
from app.models.llm import StructuredObservation, VisionAnalysis
from app.utils.exceptions import ImageProcessingException
from app.utils.logger import get_logger

logger = get_logger("service.gemini_vision")


class GeminiVisionService:
    """Gemini-powered vision service with preprocessing, hashing, and SQLite caching."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.gemini_api_key
        self.base_url = (base_url or settings.gemini_base_url).rstrip("/")
        self.model = model or settings.gemini_model
        self.timeout_seconds = settings.gemini_timeout_seconds
        self.max_retries = settings.gemini_max_retries
        self.retry_backoff_seconds = settings.gemini_retry_backoff_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def analyze(
        self,
        *,
        image_base64: str,
        crop_type: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        original_bytes = self._decode_base64(image_base64)
        self._validate_image_size(original_bytes)

        preprocessed_bytes = self._preprocess_image(original_bytes)
        image_hash = hashlib.sha256(preprocessed_bytes).hexdigest()
        original_hash = hashlib.sha256(original_bytes).hexdigest()

        cached = self._get_cached_analysis(db, image_hash) if db is not None else None
        if cached:
            logger.info("gemini_cache_hit", image_hash=image_hash, model=self.model)
            self._increment_cache_hit(db, cached)
            return self._cache_row_to_payload(cached, cache_hit=True)

        logger.info(
            "gemini_cache_miss",
            image_hash=image_hash,
            original_hash=original_hash,
            model=self.model,
            image_bytes=len(original_bytes),
            preprocessed_bytes=len(preprocessed_bytes),
        )

        try:
            analysis = await self._request_gemini(
                preprocessed_bytes=preprocessed_bytes,
                crop_type=crop_type,
            )
            payload = self._analysis_to_payload(
                analysis,
                crop_type=crop_type,
                image_hash=image_hash,
                original_hash=original_hash,
                original_bytes=len(original_bytes),
                preprocessed_bytes=len(preprocessed_bytes),
            )
            if db is not None:
                self._store_cache(db, payload)
            logger.info("gemini_analysis_complete", image_hash=image_hash, model=self.model)
            return payload
        except Exception as exc:
            logger.warning("gemini_analysis_failed", image_hash=image_hash, error=str(exc))
            fallback = self._heuristic_fallback(original_bytes, crop_type)
            fallback.update(
                {
                    "crop_type": crop_type,
                    "image_hash": image_hash,
                    "original_hash": original_hash,
                    "image_bytes": len(original_bytes),
                    "preprocessed_bytes": len(preprocessed_bytes),
                    "gemini_model": self.model,
                    "source": "heuristic_fallback",
                    "cache_hit": False,
                    "gemini_error": str(exc),
                }
            )
            return fallback

    def _decode_base64(self, image_base64: str) -> bytes:
        try:
            if image_base64.startswith("data:"):
                image_base64 = image_base64.split(",", 1)[1]
            return base64.b64decode(image_base64, validate=True)
        except Exception as exc:
            raise ImageProcessingException(f"Invalid image payload: {exc}") from exc

    def _validate_image_size(self, image_bytes: bytes) -> None:
        if len(image_bytes) > settings.gemini_max_upload_bytes:
            raise ImageProcessingException(
                f"Image exceeds configured upload limit of {settings.gemini_max_upload_bytes} bytes"
            )

    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = ImageOps.exif_transpose(img).convert("RGB")
                width, height = img.size
                max_side = max(width, height)
                if max_side > settings.gemini_max_image_side:
                    scale = settings.gemini_max_image_side / float(max_side)
                    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                buffer = io.BytesIO()
                img.save(
                    buffer,
                    format="JPEG",
                    quality=settings.gemini_image_jpeg_quality,
                    optimize=True,
                    progressive=True,
                )
                return buffer.getvalue()
        except Exception as exc:
            raise ImageProcessingException(f"Failed to preprocess image: {exc}") from exc

    async def _request_gemini(self, *, preprocessed_bytes: bytes, crop_type: str) -> VisionAnalysis:
        if not self.api_key:
            raise ImageProcessingException("GEMINI_API_KEY is not configured")

        url = f"{self.base_url}/models/{self.model}:generateContent"
        payload = self._build_payload(preprocessed_bytes, crop_type)
        timeout = httpx.Timeout(self.timeout_seconds)
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            started_at = asyncio.get_running_loop().time()
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, params={"key": self.api_key}, json=payload)

                latency_ms = (asyncio.get_running_loop().time() - started_at) * 1000
                logger.info(
                    "gemini_response",
                    model=self.model,
                    status_code=response.status_code,
                    latency_ms=round(latency_ms, 2),
                    attempt=attempt,
                )

                if response.status_code in {429, 500, 502, 503, 504}:
                    retry_after = self._retry_delay(response, attempt)
                    last_error = ImageProcessingException(
                        f"Gemini returned transient status {response.status_code}: {response.text[:200]}"
                    )
                    if attempt < self.max_retries:
                        logger.warning(
                            "gemini_retry",
                            attempt=attempt,
                            status_code=response.status_code,
                            retry_after=round(retry_after, 2),
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise last_error

                if response.status_code >= 400:
                    raise ImageProcessingException(
                        f"Gemini request failed with status {response.status_code}: {response.text[:500]}"
                    )

                data = response.json()
                content_text = self._extract_content_text(data)
                payload = self._extract_json(content_text)
                normalized_payload = self._normalize_gemini_response(payload)
                return VisionAnalysis.model_validate(normalized_payload)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = ImageProcessingException(f"Gemini transport error: {exc}")
                if attempt < self.max_retries:
                    delay = self.retry_backoff_seconds * (2 ** (attempt - 1))
                    logger.warning("gemini_retry", attempt=attempt, error=str(exc), retry_after=round(delay, 2))
                    await asyncio.sleep(delay)
                    continue
                raise last_error

        if last_error:
            raise last_error
        raise ImageProcessingException("Gemini request failed unexpectedly")

    def _sanitize_schema_for_gemini(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Remove $defs and $ref from schema since Gemini doesn't support them."""
        if not isinstance(schema, dict):
            return schema
        
        cleaned = {}
        for key, value in schema.items():
            if key in {"$defs", "$ref", "$schema"}:
                continue
            if isinstance(value, dict):
                cleaned[key] = self._sanitize_schema_for_gemini(value)
            elif isinstance(value, list):
                cleaned[key] = [self._sanitize_schema_for_gemini(item) if isinstance(item, dict) else item for item in value]
            else:
                cleaned[key] = value
        return cleaned

    def _build_payload(self, preprocessed_bytes: bytes, crop_type: str) -> Dict[str, Any]:
        schema = self._sanitize_schema_for_gemini(VisionAnalysis.model_json_schema())
        
        instructions = [
            "Analyze the crop image and return only structured JSON matching the schema.",
            "Describe visible symptoms only; do not diagnose a disease.",
            "Include confidence, uncertainties, follow-up questions, and image quality notes.",
            "If the image is insufficient, set needs_follow_up to true.",
        ]
        
        if crop_type == "auto_detect":
            instructions.append("Detect and identify the crop type from the image and return it in the crop_type field.")
            prompt = {
                "crop_type": "auto_detect",
                "instructions": instructions,
            }
        else:
            prompt = {
                "crop_type": crop_type,
                "instructions": instructions,
            }

        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": json.dumps(prompt, ensure_ascii=False)},
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": base64.b64encode(preprocessed_bytes).decode("utf-8"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1400,
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        }

    def _extract_content_text(self, data: Dict[str, Any]) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            raise ImageProcessingException("Gemini response did not include candidates")

        content = (candidates[0].get("content") or {}) if isinstance(candidates[0], dict) else {}
        parts = content.get("parts") or []
        texts: List[str] = []
        for part in parts:
            if isinstance(part, dict) and part.get("text"):
                texts.append(str(part["text"]))

        text = "\n".join(texts).strip()
        if not text:
            raise ImageProcessingException("Gemini response did not include text content")
        return text

    def _extract_json(self, text: str) -> Dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`")
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            start = stripped.find("{")
            end = stripped.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(stripped[start : end + 1])
            raise ImageProcessingException("Gemini returned non-JSON content")

    def _normalize_gemini_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Gemini response to handle cases where it returns strings instead of objects or uses different field names."""
        if not isinstance(data, dict):
            return data

        normalized = {}
        for key, value in data.items():
            if key == "observations" and isinstance(value, list):
                # Handle case where observations are strings instead of objects
                normalized_observations = []
                for obs in value:
                    if isinstance(obs, str):
                        # Convert string description to structured observation
                        normalized_observations.append({
                            "category": "general",
                            "description": obs,
                            "confidence": 0.7,
                            "visible_signs": [],
                        })
                    elif isinstance(obs, dict):
                        # Normalize observation dict to ensure required fields
                        normalized_obs = dict(obs)
                        # Map Gemini's field names to expected schema
                        if "type" in normalized_obs and "category" not in normalized_obs:
                            normalized_obs["category"] = normalized_obs.pop("type")
                        if "confidence" not in normalized_obs:
                            normalized_obs["confidence"] = 0.7
                        if "description" not in normalized_obs and "text" in normalized_obs:
                            normalized_obs["description"] = normalized_obs.pop("text")
                        if "visible_signs" not in normalized_obs:
                            normalized_obs["visible_signs"] = []
                        if "location" not in normalized_obs:
                            normalized_obs["location"] = None
                        if "severity" not in normalized_obs:
                            normalized_obs["severity"] = None
                        normalized_observations.append(normalized_obs)
                    else:
                        normalized_observations.append({
                            "category": "general",
                            "description": str(obs),
                            "confidence": 0.5,
                            "visible_signs": [],
                        })
                normalized[key] = normalized_observations
            elif isinstance(value, dict):
                normalized[key] = self._normalize_gemini_response(value)
            elif isinstance(value, list):
                normalized[key] = [
                    self._normalize_gemini_response(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[key] = value
        return normalized

    def _analysis_to_payload(
        self,
        analysis: VisionAnalysis,
        *,
        crop_type: str,
        image_hash: str,
        original_hash: str,
        original_bytes: int,
        preprocessed_bytes: int,
    ) -> Dict[str, Any]:
        observations = [obs.model_dump() if isinstance(obs, StructuredObservation) else dict(obs) for obs in analysis.observations]
        return {
            "crop_type": analysis.crop_type or crop_type,
            "image_hash": image_hash,
            "original_hash": original_hash,
            "image_bytes": original_bytes,
            "preprocessed_bytes": preprocessed_bytes,
            "gemini_model": self.model,
            "source": "gemini",
            "cache_hit": False,
            "image_quality_score": round(float(analysis.image_quality_score), 3),
            "confidence": round(float(analysis.confidence), 3),
            "observations": observations,
            "uncertainties": analysis.uncertainties,
            "follow_up_questions": analysis.follow_up_questions,
            "needs_follow_up": analysis.needs_follow_up,
            "quality_notes": analysis.quality_notes,
            "summary": analysis.summary,
            "created_at": datetime.utcnow().isoformat(),
        }

    def _store_cache(self, db: Session, payload: Dict[str, Any]) -> None:
        row = VisionObservationCache(
            image_hash=payload["image_hash"],
            original_hash=payload["original_hash"],
            crop_type=payload.get("crop_type"),
            gemini_model=payload["gemini_model"],
            image_bytes=payload.get("image_bytes"),
            preprocessed_bytes=payload.get("preprocessed_bytes"),
            image_quality_score=payload.get("image_quality_score", 0.0),
            confidence=payload.get("confidence", 0.0),
            observations=payload.get("observations", []),
            uncertainties=payload.get("uncertainties", []),
            follow_up_questions=payload.get("follow_up_questions", []),
            quality_notes=payload.get("quality_notes", []),
            summary=payload.get("summary"),
            needs_follow_up=payload.get("needs_follow_up", False),
            source=payload.get("source", "gemini"),
            raw_response=payload,
            cache_hits=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=datetime.utcnow(),
        )
        db.add(row)
        db.commit()

    def _get_cached_analysis(self, db: Session, image_hash: str) -> Optional[VisionObservationCache]:
        return db.query(VisionObservationCache).filter_by(image_hash=image_hash).first()

    def _increment_cache_hit(self, db: Session, row: VisionObservationCache) -> None:
        row.cache_hits = (row.cache_hits or 0) + 1
        row.last_used_at = datetime.utcnow()
        row.updated_at = datetime.utcnow()
        db.add(row)
        db.commit()

    def _cache_row_to_payload(self, row: VisionObservationCache, *, cache_hit: bool) -> Dict[str, Any]:
        payload = dict(row.raw_response or {})
        payload.update(
            {
                "crop_type": row.crop_type or payload.get("crop_type"),
                "image_hash": row.image_hash,
                "original_hash": row.original_hash,
                "image_bytes": row.image_bytes,
                "preprocessed_bytes": row.preprocessed_bytes,
                "gemini_model": row.gemini_model,
                "source": row.source or "gemini",
                "cache_hit": cache_hit,
                "cache_hits": row.cache_hits,
                "image_quality_score": row.image_quality_score,
                "confidence": row.confidence,
                "observations": row.observations or [],
                "uncertainties": row.uncertainties or [],
                "follow_up_questions": row.follow_up_questions or [],
                "quality_notes": row.quality_notes or [],
                "summary": row.summary or payload.get("summary", ""),
                "needs_follow_up": row.needs_follow_up,
            }
        )
        return payload

    def _heuristic_fallback(self, image_bytes: bytes, crop_type: str) -> Dict[str, Any]:
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img = ImageOps.exif_transpose(img).convert("RGB")
                image = img
        except Exception as exc:
            raise ImageProcessingException(f"Fallback image decode failed: {exc}") from exc

        import cv2
        import numpy as np

        array = np.array(image)
        bgr = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        mean_brightness = float(np.mean(gray) / 255.0)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        quality = max(0.0, min(1.0, (min(1.0, laplacian_var / 100.0) * 0.5) + (1.0 - abs(0.5 - mean_brightness)) * 0.5))

        observations: List[Dict[str, Any]] = []
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        h, w = bgr.shape[:2]
        total_pixels = max(1, h * w)

        brown_mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([30, 200, 200]))
        brown_pixels = cv2.countNonZero(brown_mask)
        if brown_pixels > total_pixels * 0.02:
            observations.append(
                {
                    "category": "lesion",
                    "description": "Brown/tan lesions detected",
                    "confidence": 0.78,
                    "visible_signs": ["brown patches", "irregular lesion-like discoloration"],
                }
            )

        yellow_mask = cv2.inRange(hsv, np.array([20, 100, 100]), np.array([40, 255, 255]))
        yellow_pixels = cv2.countNonZero(yellow_mask)
        if yellow_pixels > total_pixels * 0.01:
            observations.append(
                {
                    "category": "necrosis",
                    "description": "Yellow/necrotic areas detected",
                    "confidence": 0.72,
                    "visible_signs": ["yellowing", "tissue death"],
                }
            )

        if not observations:
            observations.append(
                {
                    "category": "uncertain",
                    "description": "No strong visible lesion patterns detected",
                    "confidence": 0.45,
                    "visible_signs": [],
                }
            )

        follow_up_questions = [
            "Please upload a clearer, well-lit image with the affected area centered.",
        ]
        return {
            "image_hash": None,
            "original_hash": None,
            "image_bytes": len(image_bytes),
            "preprocessed_bytes": None,
            "gemini_model": self.model,
            "source": "heuristic_fallback",
            "cache_hit": False,
            "image_quality_score": round(quality, 3),
            "confidence": round(min(1.0, max(0.0, quality)), 3),
            "observations": observations,
            "uncertainties": ["Gemini unavailable; local fallback used."],
            "follow_up_questions": follow_up_questions,
            "needs_follow_up": True,
            "quality_notes": [
                "Fallback analysis used because Gemini could not be reached.",
            ],
            "summary": "Local heuristic fallback used to preserve pipeline continuity.",
        }

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), self.retry_backoff_seconds)
            except ValueError:
                pass
        return self.retry_backoff_seconds * (2 ** (attempt - 1))
