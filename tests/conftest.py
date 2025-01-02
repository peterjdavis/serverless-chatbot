import pytest
import yaml


class LambdaContext:
    def __init__(self, context={}):
        self.function_name = context.get("function_name", "test-function")
        self.function_version = context.get("function_version", "1.0")
        self.invoked_function_arn = context.get(
            "invoked_function_arn",
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        )
        self.memory_limit_in_mb = context.get("memory_limit_in_mb", 128)
        self.aws_request_id = context.get("aws_request_id", "test-request-id")
        self.log_group_name = context.get("log_group_name", "test-log-group")
        self.log_stream_name = context.get("log_stream_name", "test-log-stream")


@pytest.fixture
def base_lambda_context():
    return LambdaContext()


@pytest.fixture(scope="session")
def chatbot_lambda_event():
    return {
        "body": None,
        "resource": "/chat",
        "path": "/chat",
        "httpMethod": "POST",
        "queryStringParameters": {"foo": "bar"},
        "pathParameters": {"proxy": "path/to/resource"},
        "stageVariables": {"baz": "qux"},
        "headers": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "en-US,en;q=0.8",
            "Cache-Control": "max-age=0",
            "CloudFront-Forwarded-Proto": "https",
            "CloudFront-Is-Desktop-Viewer": "true",
            "CloudFront-Is-Mobile-Viewer": "false",
            "CloudFront-Is-SmartTV-Viewer": "false",
            "CloudFront-Is-Tablet-Viewer": "false",
            "CloudFront-Viewer-Country": "US",
            "Host": "1234567890.execute-api.{dns_suffix}",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Custom User Agent String",
            "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
            "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
            "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
        },
        "requestContext": {
            "accountId": "123456789012",
            "resourceId": "123456",
            "stage": "prod",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "identity": {
                "cognitoIdentityPoolId": None,
                "accountId": None,
                "cognitoIdentityId": None,
                "caller": None,
                "apiKey": None,
                "sourceIp": "127.0.0.1",
                "cognitoAuthenticationType": None,
                "cognitoAuthenticationProvider": None,
                "userArn": None,
                "userAgent": "Custom User Agent String",
                "user": None,
            },
            "resourcePath": "/chat",
            "httpMethod": "POST",
            "apiId": "1234567890",
        },
    }


@pytest.fixture(scope="session")
def get_config():
    with open("config.yaml", "r") as file:
        config = yaml.safe_load(file)
    return config


@pytest.fixture(scope="session")
def bedrock_model_id(get_config):
    return get_config["bedrock_model_id"]
