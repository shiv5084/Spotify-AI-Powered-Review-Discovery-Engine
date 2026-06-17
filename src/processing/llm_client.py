import os
import yaml
import logging
from groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class GroqClient:
    """Initializes and provides the Groq LLM client utilizing config.yaml parameters."""

    def __init__(self, config_path: str = "config.yaml"):
        load_dotenv()
        
        # Resolve path dynamically if path is run from subdirectory
        if not os.path.exists(config_path):
            # Try to look for it in the parent directory or search upwards
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            possible_path = os.path.abspath(os.path.join(curr_dir, "..", "..", config_path))
            if os.path.exists(possible_path):
                config_path = possible_path
        
        self.config = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to read config.yaml from {config_path}: {e}. Using default parameters.")
        else:
            logger.warning(f"config.yaml not found at {config_path}. Using default parameters.")
            
        llm_config = self.config.get("llm", {})
        self.model_name = llm_config.get("model_name", "llama-3.3-70b-versatile")
        self.temperature = float(llm_config.get("temperature", 0.1))
        self.max_tokens = int(llm_config.get("max_tokens", 4096))

        default_rate_limit = {
            "batch_size": 5,
            "min_request_interval_seconds": 3.0,
            "max_retries": 5,
            "initial_backoff_seconds": 5,
            "max_backoff_seconds": 120,
        }
        self.rate_limit = {**default_rate_limit, **llm_config.get("rate_limit", {})}
        
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable is not set. Please define it in your .env file."
            )
        
        self.client = Groq(api_key=self.api_key)
        logger.info(f"GroqClient successfully initialized using model {self.model_name}.")

    def get_client(self) -> Groq:
        """Returns the raw Groq client object."""
        return self.client
