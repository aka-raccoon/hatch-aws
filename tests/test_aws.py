import pytest

from hatch_aws.aws import Sam


def test_sam_init(asset):
    sam = Sam(template=asset("sam-template.yml"))

    lambda1, lambda2, lambda3, *other = sam.lambdas

    assert lambda1.path.as_posix() == "my_app/lambdas/lambda1"
    assert lambda1.name == "MyLambda1Func"

    assert lambda2.path.as_posix() == "my_app/lambdas/lambda2"
    assert lambda2.name == "MyLambda2Func"

    assert lambda3.path.as_posix() == "."
    assert lambda3.name == "MyLambda3Func"

    assert not other


def test_unsupported_template(asset):
    with pytest.raises(AttributeError):
        Sam(template=asset("sam-template-unsupported-handler.yml"))
