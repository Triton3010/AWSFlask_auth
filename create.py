import json
from . import config
import boto3

iam_client = boto3.client('iam', config.aws_region, aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key)
cognito_client = boto3.client('cognito-idp', config.aws_region, aws_access_key_id=config.aws_access_key_id, aws_secret_access_key=config.aws_secret_access_key)

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
file_name = "group_detail.json"
abs_file_path = os.path.join(script_dir, file_name)
data = json.load(open(abs_file_path))
index=0
for each_obj in data:
	if each_obj['created'] == "false":
			response= iam_client.create_role(
				RoleName='role_' + each_obj['group_name'],
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

			role_arn= response['Role']['Arn']

			response= iam_client.put_role_policy(
			RoleName='role_' + each_obj['group_name'],
			PolicyName= each_obj['group_name'] + '_policy',
			PolicyDocument=json.dumps(each_obj['group_policy'])
			)
			response= cognito_client.create_group(
			GroupName=each_obj['group_name'],
			UserPoolId=config.cognito_pool_id,
			RoleArn=role_arn
			)
			obj= each_obj
			obj['created']= 'true'
			print(index, 'will be deleted')
			data.pop(index)
			data.append(obj)
			with open("group_detail.json", "w") as jsonFile:
				json.dump(data, jsonFile)
			print(index)
			index+=1
	else:
		response = iam_client.get_role_policy(
		RoleName='role_' + each_obj['group_name'],
		PolicyName= each_obj['group_name'] + '_policy'
		)
		if response['PolicyDocument'] != each_obj['group_policy']:
			print('policy change on', index, 'th object')
			response = iam_client.delete_role_policy(
			RoleName='role_' + each_obj['group_name'],
			PolicyName=each_obj['group_name'] + '_policy'
			)

			response= iam_client.put_role_policy(
			RoleName='role_' + each_obj['group_name'],
			PolicyName= each_obj['group_name'] + '_policy',
			PolicyDocument=json.dumps(each_obj['group_policy'])
			)
		print(index)
		index+=1 



