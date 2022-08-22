import pytest

from hatch_aws.aws import AwsLambda
from hatch_aws.exceptions import CodeUriMissing, CodeUriUnsupportedType


def test_aws_lambda_code_uri_missing_exception():
    with pytest.raises(CodeUriMissing):
        AwsLambda(default_path=None, resource={}, name="Test")


def test_aws_lambda_code_uri_unsupported_type_exception():
    with pytest.raises(CodeUriUnsupportedType):
        AwsLambda(default_path={"!Sub": "test"}, resource={}, name="Test")
