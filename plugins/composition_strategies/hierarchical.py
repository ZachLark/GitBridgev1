from plugin_loader import CompositionStrategyPlugin

class HierarchicalCompositionPlugin(CompositionStrategyPlugin):
    @property
    def plugin_name(self) -> str:
        return "hierarchical"
    
    @property
    def plugin_version(self) -> str:
        return "1.0.0"
    
    def validate_config(self, config: dict) -> bool:
        return True
    
    def compose_results(self, results: list, strategy_config: dict):
        return {"composition_method": "hierarchical", "composed": True}