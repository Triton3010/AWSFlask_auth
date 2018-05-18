from functools import wraps
from flask import request, jsonify
import jwt
import boto3
import os
import sys
import requests
from . import config
import simplejson as json
from jose import jwt, JWTError


def pool_url(aws_region, aws_user_pool):
	""" Create an Amazon cognito issuer URL from a region and pool id
	Args:
		aws_region (string): The region the pool was created in.
		aws_user_pool (string): The Amazon region ID.
	Returns:
		string: a URL
	"""
	return (
		"https://cognito-idp.{}.amazonaws.com/{}".
		format(aws_region, aws_user_pool)
	)


def get_client_id_from_access_token(aws_region, aws_user_pool, token):
	""" Pulls the client ID out of an Access Token
	"""
	claims = get_claims(aws_region, aws_user_pool, token)
	if claims.get('token_use') != 'access':
		raise ValueError('Not an access token')

	return claims.get('client_id')


def get_client_id_from_id_token(token):
	""" Pulls the audience (client id) out of an id_token
	"""
	# header, payload, _ = get_token_segments(token)
	payload = jwt.get_unverified_claims(token)
	return payload.get('aud')


def get_user_email(aws_region, aws_user_pool, client_id, id_token):
	""" Pulls the user email out of an id token
	"""
	claims = get_claims(aws_region, aws_user_pool, id_token, client_id)
	if claims.get('token_use') != 'id':
		raise ValueError('Not an ID Token')

	return {'user_email': claims.get('email'), 'user_group': claims.get('cognito:groups') }


def get_claims(aws_region, aws_user_pool, token, audience=None):
	""" Given a token (and optionally an audience), validate and
	return the claims for the token
	"""

	header = jwt.get_unverified_header(token)
	kid = header['kid']

	verify_url = pool_url(aws_region, aws_user_pool)

	keys = aws_key_dict(aws_region, aws_user_pool)

	key = keys.get(kid)

	kargs = {"issuer": verify_url}
	if audience is not None:
		kargs["audience"] = audience

	claims = jwt.decode(
		token,
		key,
		**kargs
	)
	print("important-->", claims)

	return claims


def aws_key_dict(aws_region, aws_user_pool):
	""" Fetches the AWS JWT validation file (if necessary) and then converts
	this file into a keyed dictionary that can be used to validate a web-token
	we've been passed
	Args:
		aws_user_pool (string): the ID for the user pool
	Returns:
		dict: a dictonary of values
	"""
	filename = os.path.abspath(
		os.path.join(
			os.path.dirname(sys.argv[0]), 'aws_{}.json'.format(aws_user_pool)
		)
	)

	if not os.path.isfile(filename):
		# If we can't find the file already, try to download it.
		aws_data = requests.get(
			pool_url(aws_region, aws_user_pool) + '/.well-known/jwks.json'
		)
		aws_jwt = json.loads(aws_data.text)
		with open(filename, 'w+') as json_data:
			json_data.write(aws_data.text)
			json_data.close()

	else:
		with open(filename) as json_data:
			aws_jwt = json.load(json_data)
			json_data.close()

	# We want a dictionary keyed by the kid, not a list.
	result = {}
	for item in aws_jwt['keys']:
		result[item['kid']] = item

	print('key dict result--->', result)

	return result

def login_check(t):

	@wraps(t)
	def decorated(*args, **kwargs):

		#token = None
		id_token = request.cookies.get('token_cookie')
		print("token is here in middleware --->", id_token)

		if id_token:
			try:
				aws_region = config.aws_region
				aws_pool = config.cognito_pool_id
				client_id= config.client_id
				details = get_user_email(aws_region, aws_pool, client_id, id_token )
				print(details)

			except jwt.ExpiredSignatureError:
				return jsonify({ 'message': 'token has expired'})

			except:
				return jsonify({ 'message': 'token is invalid'}), 403

		else:
			return jsonify({ 'message': 'token is missing'})

		return t(details, *args, **kwargs)

	return decorated



