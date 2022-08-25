import pytest

from hatch_aws.aws import AwsLambda
from hatch_aws.exceptions import ParameterIsMissing, UnsupportedTypeForParameter


def test_aws_lambda_code_uri_missing_exception():
    with pytest.raises(ParameterIsMissing):
        AwsLambda(default_code_uri=None, default_handler=None, resource={}, name="Test")


def test_aws_lambda_code_uri_unsupported_type_exception():
    with pytest.raises(UnsupportedTypeForParameter):
        AwsLambda(default_code_uri={"!Sub": "test"}, default_handler=None, resource={}, name="Test")
