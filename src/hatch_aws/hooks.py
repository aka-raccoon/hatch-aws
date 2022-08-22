from hatchling.plugin import hookimpl

from hatch_aws.builder import AwsBuilder


@hookimpl
def hatch_register_builder():
    return AwsBuilder
