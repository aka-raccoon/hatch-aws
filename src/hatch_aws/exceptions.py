class ParameterIsMissing(Exception):
    def __init__(self, lambda_name: str, parameter: str) -> None:
        self.name = lambda_name
        self.parameter = parameter
        super().__init__(
            f"Lambda function '{self.name}' is missing required '{self.parameter}' parameter."
        )


class UnsupportedTypeForParameter(Exception):
    def __init__(self, lambda_name: str, parameter: str) -> None:
        self.name = lambda_name
        self.parameter = parameter
        super().__init__(
            f"Lambda function '{self.name}' has unsupported type for '{self.parameter}' parameter. "
            "Only string is supported. Functions !Sub, !Ref and others are not supported yet."
        )
