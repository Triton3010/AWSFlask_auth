import unittest
import config
import boto3
import json

class TestModule01(unittest.TestCase):

    def setUp(self):
        self.iam_client = boto3.client('iam', config.aws_region, aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key)
        self.cognito_client = boto3.client('cognito-idp', config.aws_region, aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key)

    def test_grouprole_create(self):
        self.response= self.iam_client.create_role(
            RoleName='role_test',
            AssumeRolePolicyDocument=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
            {
            "Effect": "Allow",
            "Principal": {
            "Federated": "cognito-identity.amazonaws.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
            "StringEquals": {
                "cognito-identity.amazonaws.com:aud": config.cognito_pool_id
            }}}]}))

        self.role_arn= self.response['Role']['Arn']
            
        self.response= self.cognito_client.create_group(
            GroupName='test_group',
            UserPoolId=config.cognito_pool_id,
            RoleArn=self.role_arn
            )
        self.assertIsNotNone(self.response)
        print("cognito group and iam role create working fine")

    def tearDown(self):
        self.response = self.cognito_client.delete_group(
           GroupName='test_group',
           UserPoolId=config.cognito_pool_id
        )
        self.response = self.iam_client.delete_role(
           RoleName='role_test'
        )

class TestModule02(unittest.TestCase):
    def setUp(self):
        import hmac
        import hashlib
        import base64

        def get_secret_hash(username, client_id, client_secret):
            message = 'test_user' + config.client_id
            dig = hmac.new(client_secret, msg=message.encode('UTF-8'),
                       digestmod=hashlib.sha256).digest()
            return base64.b64encode(dig).decode()

        self.cognito_client = boto3.client('cognito-idp', config.aws_region, aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key)
        self.response = self.cognito_client.sign_up(
        ClientId=config.client_id,
        SecretHash=get_secret_hash('test_user', config.client_id, bytes(config.client_secret, encoding='utf-8')),
        Username='test_user',
        Password='Test_user123',
        UserAttributes=[
        {
            'Name': 'email',
            'Value': 'test@gmail.com'
        }
        ]
        )
        self.response = self.cognito_client.admin_confirm_sign_up(
        UserPoolId=config.cognito_pool_id,
        Username='test_user'
        )
        self.response = self.cognito_client.admin_initiate_auth(
        UserPoolId=config.cognito_pool_id,
        ClientId=config.client_id,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
        'USERNAME': 'test_user',
        'PASSWORD': 'Test_user123',
        'SECRET_HASH': get_secret_hash('test_user', config.client_id, bytes(config.client_secret, encoding='utf-8'))
        }
        )
        print("user creation in pool setup completed")

    def test_token(self):
        self.json_response = json.loads(json.dumps(self.response))
        self.id_token = self.json_response['AuthenticationResult']['IdToken']
        self.assertIsNotNone(self.id_token)
        print("cognito token retrieval working fine")

    def tearDown(self):
        self.response = self.cognito_client.admin_delete_user(
        UserPoolId=config.cognito_pool_id,
        Username='test_user'
        )

if __name__ == "__main__":
    unittest.main()