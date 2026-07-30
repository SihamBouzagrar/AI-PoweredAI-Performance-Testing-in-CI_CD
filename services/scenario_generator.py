from prompts.scenario_prompt import ScenarioPromptBuilder


class ScenarioGenerator:

    def __init__(self):
        self.builder = ScenarioPromptBuilder()

    def build_prompt(self, specification, analysis):
        return self.builder.build(specification, analysis)