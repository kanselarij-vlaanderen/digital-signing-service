class Template():
    def __init__(self, template_string: str) -> None:
        self.template = string.Template(template_string)

    def safe_substitute(self, **substitutions: typing.Dict[str, str]):
        if mode.dev:
            for (key, val) in substitutions.items():
                valid_sparql_val = (val.startswith('"') or val.startswith("'")
                    or val.startswith('<')
                    or val.isnumeric()
                    or val == "true" or val == "false")
                if not valid_sparql_val:
                    raise Exception(f"You probably forgot to escape: {substitutions}")
        
        return self.template.safe_substitute(**substitutions)
