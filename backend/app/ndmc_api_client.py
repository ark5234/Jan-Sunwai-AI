"""
NDMC Model API Client for Result Comparison.

The NDMC model is trained on municipal data and provides alternative
classifications. This module compares local model results with NDMC
predictions to improve reliability:

- If both models predict the same category → use local model (faster, cheaper)
- If results differ → use NDMC model (more authoritative for NDMC data)
"""

import os
import logging
import requests
import time
from typing import Any
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from app.config import settings
from app.category_utils import canonicalize_label, CANONICAL_CATEGORIES


logger = logging.getLogger("JanSunwaiAI.ndmc")

# ═══════════════════════════════════════════════════════════════════
# CIRCUIT BREAKER: Track NDMC API failures
# If N consecutive failures occur within T seconds, temporarily disable NDMC
# ═══════════════════════════════════════════════════════════════════

class NDMCCircuitBreaker:
    """Simple circuit breaker for NDMC API failures."""
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.is_open = False  # True when circuit is "open" (disabled)
    
    def record_failure(self) -> None:
        """Record a failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                f"NDMC Circuit Breaker OPEN: {self.failure_count} consecutive failures. "
                f"NDMC API disabled for {self.cooldown_seconds}s."
            )
    
    def record_success(self) -> None:
        """Reset failure count and close circuit on success."""
        self.failure_count = 0
        self.is_open = False
    
    def can_call_api(self) -> bool:
        """Check if API can be called (circuit not open, or cooldown expired)."""
        if not self.is_open:
            return True
        
        if self.last_failure_time is None:
            return True
        
        elapsed = datetime.now() - self.last_failure_time
        if elapsed >= timedelta(seconds=self.cooldown_seconds):
            self.is_open = False
            self.failure_count = 0
            logger.info("NDMC Circuit Breaker CLOSED: cooldown expired, retrying API.")
            return True
        
        return False


_ndmc_breaker = NDMCCircuitBreaker(failure_threshold=3, cooldown_seconds=60)


# Map NDMC category names (if different) to canonical categories
_NDMC_TO_CANONICAL: dict[str, str] = {
    "Air_Pollution": "Health Department",  # Environmental/air quality → Health
    "Bell_Mouth": "Civil Department",
    "CIVIL_ENGINEERING_DEPARTMENT-I": "Civil Department",
    "CIVIL_ENGINEERING_DEPARTMENT-II": "Civil Department",
    "CIVIL_ENGINEERING_DEPARTMENT-III_(ACE)": "Civil Department",
    "CPWD": "Civil Department",
    "Commercial_Department": "Commercial",
    "EBR_Department": "EBR Department",
    "Electricity-II": "Electrical Department",
    "Electricity_-I": "Electrical Department",
    "Enforcement_Department_(North)": "Enforcement",
    "Enforcement_Department_(South)": "Enforcement",
    "Fire_Department": "Fire Department",
    "Health_licensing": "Health Department",
    "Horticulture_Department": "Horticulture",
    "IT_Department": "IT Department",
    "Medical_Services": "Health Department",
    "Metro_Waste": "Health Department",
    "Monsoon": "Civil Department",
    "NDMC_Municipal_Housing": "Civil Department",
    "Parking_Management_System": "Enforcement",
    "Public_Health_Department": "Health Department",
    "PTU_Department": "Uncategorized",
    "VBD_Department": "VBD Department",
    "Welfare_Department": "Uncategorized",
}


def _fuzzy_match_category(unknown_category: str, similarity_threshold: float = 0.75) -> str | None:
    """Fuzzy-match unknown NDMC category to nearest canonical category."""
    unknown_lower = str(unknown_category).lower().strip()
    if not unknown_lower:
        return None
    
    best_match: str | None = None
    best_ratio = 0.0
    
    for canonical in CANONICAL_CATEGORIES:
        canonical_lower = canonical.lower()
        ratio = SequenceMatcher(None, unknown_lower, canonical_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = canonical
    
    if best_ratio >= similarity_threshold:
        logger.info(
            f"Fuzzy-mapped NDMC category '{unknown_category}' to '{best_match}' (similarity: {best_ratio:.2%})"
        )
        return best_match
    
    return None


def _map_ndmc_category(ndmc_category: str) -> str:
    """Convert NDMC category to our canonical form."""
    # First try direct mapping
    if ndmc_category in _NDMC_TO_CANONICAL:
        return _NDMC_TO_CANONICAL[ndmc_category]
    
    # Then try canonicalize (handles variations)
    canonical = canonicalize_label(ndmc_category)
    if canonical in CANONICAL_CATEGORIES:
        return canonical
    
    # Try fuzzy matching as fallback
    fuzzy_match = _fuzzy_match_category(ndmc_category, similarity_threshold=0.75)
    if fuzzy_match:
        return fuzzy_match
    
    # If no match found, log and return Uncategorized
    logger.warning(f"NDMC category '{ndmc_category}' could not be mapped to any canonical category; returning Uncategorized")
    return "Uncategorized"


def _extract_ndmc_server_version(response: requests.Response, api_response: dict[str, Any]) -> str | None:
    header_candidates = (
        "x-server-version",
        "x-api-version",
        "x-version",
        "server-version",
        "version",
        "x-model-version",
        "x-build-version",
    )
    for header_name in header_candidates:
        header_value = response.headers.get(header_name)
        if header_value:
            return str(header_value).strip()

    body_candidates = (
        "server_version",
        "service_version",
        "api_version",
        "version",
        "model_version",
        "build_version",
    )
    for body_key in body_candidates:
        body_value = api_response.get(body_key)
        if body_value:
            return str(body_value).strip()

    return None


def call_ndmc_api(image_path: str) -> dict[str, Any]:
    """
    Call NDMC prediction API for the given image.
    
    This is a synchronous function designed to be called via asyncio.to_thread().
    
    Args:
        image_path: Absolute path to the image file
        
    Returns:
        dict with keys:
            - success: bool (True if API call succeeded)
            - category: str (canonical category or "Uncategorized")
            - confidence: float (0.0-1.0, if available from NDMC)
            - raw_response: dict (full NDMC API response)
            - error: str (error message if failed)
    """
    
    if not settings.ndmc_api_enabled:
        return {
            "success": False,
            "category": "Uncategorized",
            "confidence": 0.0,
            "raw_response": {},
            "error": "NDMC API is disabled in configuration",
        }
    
    # Check circuit breaker
    if not _ndmc_breaker.can_call_api():
        logger.warning("NDMC API circuit breaker is open; skipping call")
        return {
            "success": False,
            "category": "Uncategorized",
            "confidence": 0.0,
            "raw_response": {},
            "error": "NDMC API circuit breaker is open; too many recent failures",
        }
    
    if not os.path.exists(image_path):
        return {
            "success": False,
            "category": "Uncategorized",
            "confidence": 0.0,
            "raw_response": {},
            "error": f"Image file not found: {image_path}",
        }
    
    try:
        # Prepare headers
        headers = {
            "Accept": "application/json",
        }
        if settings.ndmc_api_token:
            headers["Authorization"] = f"Bearer {settings.ndmc_api_token}"
        
        # Prepare files and data
        with open(image_path, "rb") as f:
            files = {
                "file": (os.path.basename(image_path), f, "image/jpeg"),
            }
            data = {
                "top_k": "5",
                "use_tta": "true",
            }
            
            # Make the request
            logger.info("NDMC request start", extra={"image": image_path})
            start = time.perf_counter()
            response = requests.post(
                settings.ndmc_api_url,
                files=files,
                data=data,
                headers=headers,
                timeout=settings.ndmc_api_timeout_seconds,
            )
            elapsed_ms = round((time.perf_counter() - start) * 1000.0, 2)
            logger.info("NDMC request finished", extra={"status": response.status_code, "elapsed_ms": elapsed_ms})
        
        # Handle response
        if response.status_code == 200:
            try:
                api_response = response.json()
                response_headers = {str(key): str(value) for key, value in response.headers.items()}
                server_version = _extract_ndmc_server_version(response, api_response)
                
                # Record success in circuit breaker
                _ndmc_breaker.record_success()

                # Extract candidates if available
                candidates: list[dict[str, Any]] = []
                if isinstance(api_response, dict) and "predictions" in api_response and isinstance(api_response["predictions"], list):
                    for pred in api_response["predictions"]:
                        # NDMC responses often contain 'department' and 'confidence' or 'confidence_percentage'
                        dep = pred.get("department") or pred.get("category") or pred.get("full_class") or "Uncategorized"
                        raw_conf = pred.get("confidence") or pred.get("score") or pred.get("confidence_percentage")
                        conf = 0.0
                        try:
                            if isinstance(raw_conf, str) and raw_conf.endswith("%"):
                                conf = float(raw_conf.strip("%")) / 100.0
                            else:
                                conf = float(raw_conf)
                                if conf > 1.0 and conf <= 100.0:
                                    conf = conf / 100.0
                        except Exception:
                            conf = 0.0
                        canonical = _map_ndmc_category(str(dep))
                        candidates.append({"raw_label": dep, "department": canonical, "confidence": round(conf, 4)})

                # Fallback: try to extract single category/confidence
                ndmc_category = _extract_ndmc_category(api_response)
                canonical_category = _map_ndmc_category(ndmc_category)
                confidence = _extract_ndmc_confidence(api_response)

                logger.info(
                    f"NDMC API success: {ndmc_category} -> {canonical_category} (confidence: {confidence})",
                    extra={"candidates_count": len(candidates), "server_version": server_version}
                )

                return {
                    "success": True,
                    "category": canonical_category,
                    "confidence": confidence,
                    "candidates": candidates,
                    "server_version": server_version,
                    "http_status": response.status_code,
                    "response_headers": response_headers,
                    "raw_response": api_response,
                    "error": None,
                }
            except (ValueError, KeyError) as e:
                logger.error(f"Failed to parse NDMC API response: {e}")
                _ndmc_breaker.record_failure()
                return {
                    "success": False,
                    "category": "Uncategorized",
                    "confidence": 0.0,
                    "server_version": None,
                    "http_status": response.status_code,
                    "response_headers": {str(key): str(value) for key, value in response.headers.items()},
                    "raw_response": {"error": "JSON parse failed"},
                    "error": f"Failed to parse NDMC API JSON: {str(e)}",
                }
        else:
            logger.warning(
                f"NDMC API returned status {response.status_code}: {response.text[:200]}"
            )
            _ndmc_breaker.record_failure()
            return {
                "success": False,
                "category": "Uncategorized",
                "confidence": 0.0,
                "server_version": None,
                "http_status": response.status_code,
                "response_headers": {str(key): str(value) for key, value in response.headers.items()},
                "raw_response": {"status": response.status_code},
                "error": f"NDMC API returned {response.status_code}",
            }
    
    except requests.exceptions.Timeout:
        logger.error(f"NDMC API timeout after {settings.ndmc_api_timeout_seconds}s")
        _ndmc_breaker.record_failure()
        return {
            "success": False,
            "category": "Uncategorized",
            "confidence": 0.0,
            "server_version": None,
            "http_status": None,
            "response_headers": {},
            "raw_response": {},
            "error": f"NDMC API timeout after {settings.ndmc_api_timeout_seconds}s",
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"NDMC API request failed: {e}")
        _ndmc_breaker.record_failure()
        return {
            "success": False,
            "category": "Uncategorized",
            "confidence": 0.0,
            "server_version": None,
            "http_status": None,
            "response_headers": {},
            "raw_response": {},
            "error": f"NDMC API request failed: {str(e)}",
        }
    
    except Exception as e:
        logger.error(f"Unexpected error calling NDMC API: {e}")
        _ndmc_breaker.record_failure()
        return {
            "success": False,
            "category": "Uncategorized",
            "confidence": 0.0,
            "server_version": None,
            "http_status": None,
            "response_headers": {},
            "raw_response": {},
            "error": f"Unexpected error: {str(e)}",
        }
    

def _extract_ndmc_category(api_response: dict[str, Any]) -> str:
    """
    Extract category from NDMC API response.
    
    Adjust this function based on the actual NDMC API response structure.
    Common patterns:
    - {"prediction": "category_name"}
    - {"top_prediction": "category_name"}
    - {"predictions": [{"category": "name", "score": 0.9}]}
    - {"result": {"category": "name"}}
    """
    
    # Prefer the ranked department field from NDMC responses. The category/full_class
    # is the finer-grained class label and can map to Uncategorized even when the
    # top-ranked department is valid for routing.
    if "best_prediction" in api_response and isinstance(api_response["best_prediction"], dict):
        best = api_response["best_prediction"]
        if best.get("department"):
            return str(best["department"]).strip()
        if best.get("category"):
            return str(best["category"]).strip()

    if "predictions" in api_response and isinstance(api_response["predictions"], list):
        if api_response["predictions"]:
            top_pred = api_response["predictions"][0]
            if isinstance(top_pred, dict) and top_pred.get("department"):
                return str(top_pred["department"]).strip()

    # Try common response structures
    if "prediction" in api_response:
        return str(api_response["prediction"]).strip()
    
    if "top_prediction" in api_response:
        return str(api_response["top_prediction"]).strip()
    
    if "category" in api_response:
        return str(api_response["category"]).strip()
    
    if "result" in api_response and isinstance(api_response["result"], dict):
        result = api_response["result"]
        if "category" in result:
            return str(result["category"]).strip()
    
    if "predictions" in api_response and isinstance(api_response["predictions"], list):
        if api_response["predictions"]:
            top_pred = api_response["predictions"][0]
            if isinstance(top_pred, dict) and "department" in top_pred:
                return str(top_pred["department"]).strip()
            if isinstance(top_pred, dict) and "category" in top_pred:
                return str(top_pred["category"]).strip()
            elif isinstance(top_pred, str):
                return top_pred.strip()
    
    # Fallback
    logger.warning(f"Could not extract category from NDMC response: {api_response}")
    return "Uncategorized"
    

def _extract_ndmc_confidence(api_response: dict[str, Any]) -> float:
    """
    Extract confidence/score from NDMC API response.
    
    Common patterns:
    - {"score": 0.95}
    - {"confidence": 0.95}
    - {"predictions": [{"score": 0.95}]}
    """
    
    if "best_prediction" in api_response and isinstance(api_response["best_prediction"], dict):
        best = api_response["best_prediction"]
        if "confidence" in best:
            try:
                return min(1.0, max(0.0, float(best["confidence"]) / 100.0 if float(best["confidence"]) > 1.0 else float(best["confidence"])))
            except (ValueError, TypeError):
                pass
        if "confidence_percentage" in best:
            try:
                return min(1.0, max(0.0, float(str(best["confidence_percentage"]).strip("%")).__truediv__(100.0)))
            except (ValueError, TypeError, AttributeError):
                pass

    if "predictions" in api_response and isinstance(api_response["predictions"], list):
        if api_response["predictions"]:
            top_pred = api_response["predictions"][0]
            if isinstance(top_pred, dict):
                if "confidence" in top_pred:
                    try:
                        value = float(top_pred["confidence"])
                        return min(1.0, max(0.0, value / 100.0 if value > 1.0 else value))
                    except (ValueError, TypeError):
                        pass
                if "confidence_percentage" in top_pred:
                    try:
                        return min(1.0, max(0.0, float(str(top_pred["confidence_percentage"]).strip("%")) / 100.0))
                    except (ValueError, TypeError):
                        pass

    # Try common response structures
    if "score" in api_response:
        try:
            return min(1.0, max(0.0, float(api_response["score"])))
        except (ValueError, TypeError):
            pass
    
    if "confidence" in api_response:
        try:
            return min(1.0, max(0.0, float(api_response["confidence"])))
        except (ValueError, TypeError):
            pass
    
    if "predictions" in api_response and isinstance(api_response["predictions"], list):
        if api_response["predictions"]:
            top_pred = api_response["predictions"][0]
            if isinstance(top_pred, dict) and "score" in top_pred:
                try:
                    return min(1.0, max(0.0, float(top_pred["score"])))
                except (ValueError, TypeError):
                    pass
            elif isinstance(top_pred, dict) and "confidence" in top_pred:
                try:
                    return min(1.0, max(0.0, float(top_pred["confidence"])))
                except (ValueError, TypeError):
                    pass
    
    if "result" in api_response and isinstance(api_response["result"], dict):
        result = api_response["result"]
        if "score" in result:
            try:
                return min(1.0, max(0.0, float(result["score"])))
            except (ValueError, TypeError):
                pass
    
    # Default confidence if not found
    return 0.5


def _best_non_uncategorized_candidate(candidates: list[dict[str, Any]] | None) -> tuple[str | None, float]:
    """Return the strongest non-Uncategorized candidate, if any."""
    if not candidates:
        return None, 0.0

    best_category: str | None = None
    best_confidence = 0.0

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        raw_department = candidate.get("department") or candidate.get("category") or candidate.get("raw_label")
        canonical_department = canonicalize_label(str(raw_department or ""))
        if canonical_department == "Uncategorized":
            continue
        try:
            confidence = float(candidate.get("confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        if confidence >= best_confidence:
            best_category = canonical_department
            best_confidence = confidence

    return best_category, best_confidence
    

def compare_classifications(
    local_result: dict[str, Any],
    ndmc_result: dict[str, Any],
    use_ndmc_on_mismatch: bool = True,
    local_candidates: list[dict[str, Any]] | None = None,
    ndmc_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Compare local model result with NDMC result.
    
    Logic:
    - If both predict the same category → return local result (faster, cheaper)
    - If results differ → return NDMC result (more authoritative if mismatch)
    - If NDMC failed → return local result
    
    Args:
        local_result: dict from local classifier with 'category', 'confidence', etc.
        ndmc_result: dict from NDMC API with 'success', 'category', 'confidence'
        use_ndmc_on_mismatch: if True, prefer NDMC when categories differ
        
    Returns:
        dict with combined result:
            - category: selected category
            - confidence: selected confidence
            - method: 'local', 'ndmc', or 'local_by_default'
            - local_category: original local prediction
            - ndmc_category: NDMC prediction (if available)
            - comparison: detailed comparison info
    """
    
    local_category = local_result.get("category", "Uncategorized")
    local_confidence = local_result.get("confidence", 0.0)
    local_candidate_category, local_candidate_confidence = _best_non_uncategorized_candidate(local_candidates)
    
    # If NDMC call failed, use local result
    if not ndmc_result.get("success", False):
        if local_category == "Uncategorized" and local_candidate_category:
            return {
                "category": local_candidate_category,
                "confidence": local_candidate_confidence or local_confidence,
                "method": "local_candidate_fallback",
                "local_category": local_category,
                "ndmc_category": None,
                "comparison": {
                    "match": False,
                    "reason": "NDMC API unavailable; using best local candidate instead of Uncategorized",
                    "local_confidence": local_confidence,
                    "local_candidate": local_candidate_category,
                    "local_candidate_confidence": local_candidate_confidence,
                },
            }
        return {
            "category": local_category,
            "confidence": local_confidence,
            "method": "local_by_default",
            "local_category": local_category,
            "ndmc_category": None,
            "comparison": {
                "match": False,
                "reason": f"NDMC API unavailable: {ndmc_result.get('error', 'unknown error')}",
            },
        }
    
    ndmc_category = ndmc_result.get("category", "Uncategorized")
    ndmc_confidence = ndmc_result.get("confidence", 0.0)
    ndmc_candidate_category, ndmc_candidate_confidence = _best_non_uncategorized_candidate(ndmc_candidates or ndmc_result.get("candidates"))

    if ndmc_category == "Uncategorized" and ndmc_candidate_category:
        return {
            "category": ndmc_candidate_category,
            "confidence": ndmc_candidate_confidence or ndmc_confidence,
            "method": "ndmc_candidate_fallback",
            "local_category": local_category,
            "ndmc_category": ndmc_category,
            "comparison": {
                "match": False,
                "reason": "Top NDMC label was Uncategorized; using best NDMC candidate",
                "local_prediction": local_category,
                "local_confidence": local_confidence,
                "ndmc_prediction": ndmc_category,
                "ndmc_confidence": ndmc_confidence,
                "ndmc_candidate": ndmc_candidate_category,
                "ndmc_candidate_confidence": ndmc_candidate_confidence,
            },
        }

    if local_category == "Uncategorized" and local_candidate_category and ndmc_category == "Uncategorized":
        return {
            "category": local_candidate_category,
            "confidence": local_candidate_confidence or local_confidence,
            "method": "local_candidate_fallback",
            "local_category": local_category,
            "ndmc_category": ndmc_category,
            "comparison": {
                "match": False,
                "reason": "Both models returned Uncategorized; using best local candidate",
                "local_prediction": local_category,
                "local_confidence": local_confidence,
                "local_candidate": local_candidate_category,
                "local_candidate_confidence": local_candidate_confidence,
                "ndmc_prediction": ndmc_category,
                "ndmc_confidence": ndmc_confidence,
            },
        }
    
    # Normalize categories for comparison (handle slight variations)
    local_norm = local_category.lower().strip()
    ndmc_norm = ndmc_category.lower().strip()
    categories_match = local_norm == ndmc_norm
    
    if categories_match:
        # Same category → use local (faster)
        return {
            "category": local_category,
            "confidence": local_confidence,
            "method": "local",
            "local_category": local_category,
            "ndmc_category": ndmc_category,
            "comparison": {
                "match": True,
                "reason": "Both models agree on category",
                "local_confidence": local_confidence,
                "ndmc_confidence": ndmc_confidence,
            },
        }
    else:
        # Different categories
        if use_ndmc_on_mismatch:
            # Use NDMC (more authoritative)
            return {
                "category": ndmc_category,
                "confidence": ndmc_confidence,
                "method": "ndmc",
                "local_category": local_category,
                "ndmc_category": ndmc_category,
                "comparison": {
                    "match": False,
                    "reason": "Categories differ; using NDMC model",
                    "local_prediction": local_category,
                    "local_confidence": local_confidence,
                    "ndmc_prediction": ndmc_category,
                    "ndmc_confidence": ndmc_confidence,
                },
            }
        else:
            # Use local (fallback)
            return {
                "category": local_category,
                "confidence": local_confidence,
                "method": "local",
                "local_category": local_category,
                "ndmc_category": ndmc_category,
                "comparison": {
                    "match": False,
                    "reason": "Categories differ; using local model",
                    "local_prediction": local_category,
                    "local_confidence": local_confidence,
                    "ndmc_prediction": ndmc_category,
                    "ndmc_confidence": ndmc_confidence,
                },
            }
