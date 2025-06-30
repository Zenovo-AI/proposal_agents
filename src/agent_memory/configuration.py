class Configuration:
    def __init__(self, user_id: str, system_prompt: str, model: str):
        self.user_id = user_id
        self.system_prompt = system_prompt
        self.model = model

    @staticmethod
    def from_runnable_config(config: dict) -> "Configuration":
        cfg_dict = config.get("configurable", {})
        user_id = cfg_dict.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id in config.configurable")

        model = cfg_dict.get("model", "openai:gpt-4.1")
        system_prompt = cfg_dict.get(
            "system_prompt",
            "You are a helpful AI assistant. Use long‑term memory when available."
        )

        return Configuration(user_id=user_id, system_prompt=system_prompt, model=model)

    

