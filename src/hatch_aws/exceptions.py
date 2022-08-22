class CodeUriMissing(Exception):
    def __init__(self, lambda_name: str) -> None:
        self.name = lambda_name
        super().__init__(f"Lambda function '{self.name}' is missing required 'CodeUri' parameter!")


class CodeUriUnsupportedType(Exception):
    def __init__(self, lambda_name: str) -> None:
        self.name = lambda_name
        super().__init__(
            f"Lambda function '{self.name}' has unsupported type for 'CodeUri' parameter."
            "Only string is supported. Functions !Sub, !Ref and others are not supported yet."
        )
