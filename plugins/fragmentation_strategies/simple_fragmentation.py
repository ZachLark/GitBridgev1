from plugin_loader import FragmentationStrategyPlugin

class SimpleFragmentationPlugin(FragmentationStrategyPlugin):
    @property
    def plugin_name(self) -> str:
        return "simple"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: dict) -> bool:
        return True
    
    def fragment_task(self, prompt: str, task_type: str, domain: str, master_task_id: str):
        return [{"task_id": f"{master_task_id}_main", "description": prompt}]