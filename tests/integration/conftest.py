import pytest
import os
import boto3
import json

from time import sleep

from requests_auth_aws_sigv4 import AWSSigV4


class APIRole:
    def __init__(
        self,
        aws_region: str,
        api_access_role_name: str,
        api_access_policy_arn: str = None,
    ):

        self.aws_region = aws_region
        self.api_access_role_name = api_access_role_name
        self.api_access_policy_arn = api_access_policy_arn

        self.create_role()

    def _get_current_user_arn(self):
        sts_client = boto3.client("sts")
        response = sts_client.get_caller_identity()
        return response["Arn"]

    def create_role(self):
        iam_client = boto3.client("iam")

        try:
            response = iam_client.create_role(
                RoleName=self.api_access_role_name,
                AssumeRolePolicyDocument=json.dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": self._get_current_user_arn()},
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    }
                ),
            )

            self.api_access_role_arn = response["Role"]["Arn"]

        except iam_client.exceptions.EntityAlreadyExistsException:
            response = iam_client.get_role(RoleName=self.api_access_role_name)
            self.api_access_role_arn = response["Role"]["Arn"]

        if self.api_access_policy_arn is not None:
            iam_client.attach_role_policy(
                RoleName=self.api_access_role_name, PolicyArn=self.api_access_policy_arn
            )

    def delete_role(self):
        iam_client = boto3.client("iam")

        if self.api_access_policy_arn is not None:
            iam_client.detach_role_policy(
                RoleName=self.api_access_role_name, PolicyArn=self.api_access_policy_arn
            )

        iam_client.delete_role(RoleName=self.api_access_role_name)

    def assume_role(self):
        sts_client = boto3.client("sts")

        # try to assume the role 5 times with exponential backoff
        response = None
        for i in range(5):
            try:
                response = sts_client.assume_role(
                    RoleArn=self.api_access_role_arn, RoleSessionName="test-session"
                )
                break
            except sts_client.exceptions.ClientError as e:
                if e.response["Error"]["Code"] == "AccessDenied":
                    sleep(2**i)
                else:
                    raise e

        self.api_access_role_credentials = response["Credentials"]

    def api_request_auth(self):
        self.assume_role()
        auth = AWSSigV4(
            service="execute-api",
            aws_access_key_id=self.api_access_role_credentials["AccessKeyId"],
            aws_secret_access_key=self.api_access_role_credentials["SecretAccessKey"],
            aws_session_token=self.api_access_role_credentials["SessionToken"],
            region=self.aws_region,
        )

        return auth


@pytest.fixture()
def get_region():
    region_checks = [
        # check if set through ENV vars
        os.environ.get("AWS_REGION"),
        os.environ.get("AWS_DEFAULT_REGION"),
        # else check if set in config or in boto already
        boto3.DEFAULT_SESSION.region_name if boto3.DEFAULT_SESSION else None,
        boto3.Session().region_name,
    ]
    for region in region_checks:
        if region:
            return region


@pytest.fixture()
def stack_name(get_config):
    return get_config["stack_name"]


@pytest.fixture()
def api_access_policy_arn(stack_outputs):
    api_access_policy_arn = stack_outputs["ChatbotAPIPolicy"]
    return api_access_policy_arn


@pytest.fixture()
def stack_outputs(stack_name):
    """Fixture to retrieve CloudFormation stack outputs."""
    cfn_client = boto3.client("cloudformation")
    try:
        response = cfn_client.describe_stacks(StackName=stack_name)
        if not response["Stacks"]:
            raise ValueError(f"Stack {stack_name} not found")

        # Convert the outputs into a dictionary for easier access
        outputs = {}
        for output in response["Stacks"][0]["Outputs"]:
            outputs[output["OutputKey"]] = output["OutputValue"]

        return outputs

    except cfn_client.exceptions.ClientError as e:
        raise Exception(f"Error retrieving stack outputs: {str(e)}")


@pytest.fixture()
def chatbot_api_uri(stack_outputs):
    chatbot_api_uri = stack_outputs["ChatbotApi"]
    return chatbot_api_uri

@pytest.fixture()
def ddb_table_name(stack_outputs):
    ddb_table_name = stack_outputs["ChatbotHistoryDDBTable"]
    return ddb_table_name

@pytest.fixture()
def api_success_request_auth(get_region, stack_name, api_access_policy_arn):

    aws_region = get_region
    _api_request_auth = APIRole(
        aws_region=aws_region,
        api_access_role_name=f"{stack_name}-{aws_region}-test-api-success-role",
        api_access_policy_arn=api_access_policy_arn,
    )
    api_requests_auth = _api_request_auth.api_request_auth()

    yield api_requests_auth

    _api_request_auth.delete_role()
