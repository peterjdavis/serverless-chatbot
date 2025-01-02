SHELL := /bin/bash
.ONESHELL:

clean :
	rm -rf .venv
	rm -rf .aws-sam
	rm -rf .pytest_cache
	find . | grep -E "(/__pycache__$$|\.pyc$$|\.pyo$$)" | xargs rm -rf

init :
	python3.13 -m venv .venv
	source .venv/bin/activate
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt

get-aws-account-id :
	$(eval AwsAccountId = $(shell aws sts get-caller-identity --query 'Account' --output text))

get-config:
	$(eval StackName = $(shell yq '.stack_name' config.yaml))
	$(eval BedrockModelId = $(shell yq '.bedrock_model_id' config.yaml ))

get-api-access-policy : get-config
	$(eval ApiPolicy = $(shell aws cloudformation describe-stacks \
		--stack-name ${StackName} \
		--query 'Stacks[0].Outputs[?OutputKey==`ChatbotAPIPolicy`].OutputValue' \
		--output text))

get-current-user-arn :
	$(eval CurrentUserArn = $(shell aws sts get-caller-identity --query 'Arn' --output text))


build : 
	sam validate
	if [ $$? != 0 ]; \
	then \
		exit; \
	fi
	
	sam build
	if [ $$? != 0 ]; \
	then \
		exit; \
	fi

deploy : build get-config get-current-user-arn
	sam deploy \
		--stack-name ${StackName} \
		--parameter-overrides \
			CurrentUserArn=$(CurrentUserArn) \
			BedrockModelId=${BedrockModelId}

sync : get-config get-current-user-arn
	sam sync \
		--stack-name ${StackName} \
		--parameter-overrides \
			CurrentUserArn=$(CurrentUserArn) \
			BedrockModelId=${BedrockModelId}

delete : get-config
	sam delete \
		--stack-name ${StackName} \
		--no-prompts

integration : get-api-access-policy
	pytest tests/integration

unit : 
	pytest -v tests/unit