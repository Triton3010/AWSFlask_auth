from functools import wraps
from flask import jsonify
import os

def permission_req(t):
	@wraps(t)
	def decorated(details, *args, **kwargs):
		script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
		file_name = "group_detail.json"
		abs_file_path = os.path.join(script_dir, file_name)
		data = json.load(open(abs_file_path))
		for each_obj in data:
			if each_obj['group_name']==details['user_group'][0]:
				allow = each_obj['allowed_functions']
				if t.__name__ not in allow:
					return jsonify({ 'message': 'Forbidden access'}), 401
		return t(details, *args, **kwargs)
	return decorated
