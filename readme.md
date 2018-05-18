AWS Cognito group based authentication with user management
---

This project gives the developer fine grain control over their users through group based permission using AWS Cognito
Also included are Python middlewares(decorator) for checking if the user is logged in through AWS Cognito called **login_check**
and another middleware which checks the permissions for that user called **permission_req** 

### How to setup
---
* Fill up all the aws credential variables and region in **config.py**, create your user pool in AWS Cognito and fill the cognito pool id and
  client id. Please also provide client_secret if you wish to test the module using test_module script.


* You manage your groups and permissions using group_detail.json, a sample object is filled for you. 

   group_name - name of your user group

   group_policy - aws policy for the role attached to that group, refer to the link below to generate your fine-controlled policies
   [AWS Policy Generator](https://awspolicygen.s3.amazonaws.com/policygen.html)

   created - **important** can have two values "true"/"false", tracks if the group if already created or not. Should always be "false" to start with,
   create.py script will automatically set this to "true" once created.

   allowed_functions - list of all the allowed routes for this group's users

   #sample object  
    {  
     "group_name": "Default",  
     "group_policy":  
     {  
        "Version": "2012-10-17",  
        "Statement": [  
        {  
            "Sid": "Stmt1524591948858",  
            "Action": "cognito-idp:*",  
            "Effect": "Allow",  
            "Resource": "arn:aws:cognito-idp:us-east-1:userid:userpool/pool_id"  
        }]  
     },  
     "created": "false",  
     "allowed_functions": ["protected", "admin_panel", "view_data"]  
     }   



* Simply run the script **create.py** to create your AWS user group with mentioned policy and allowed functions attached to it.
If you want to add more groups, simply add another object in group_detail.json and again run create.py, please make sure to keep all the related
files in the same directory.  

* Note: This module assumes single group per user only 

### Using middlewares

**login_check** middleware(or decorator) checks if the user already has a valid AWS Cognito token or not to access the route, works much like
@login_required decorator in Flask  
**permission_req** middleware checks your allowed functions for the group and restricts the access if the route in not present in it.  
**Note:** permission_req middleware depends on login_check middleware to return it the user group to check allowed functions for that group, so
it cannot be used singularly. You can however, use login_check middleware only but note that it returns details json having "user_group" & "user_email"
keys 

```
#Sample code 
@app.route('/protected', methods=['GET', 'POST'])
@login_check
@permission_req
def protected():
    return jsonify({'message': 'authentication is required to access this route'})

``` 



