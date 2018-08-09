# Disclaimer: This is a very raw script which works in specific conditions. Nowhere near standard.
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

ip_addr = '10.8.198.38'  # Appliance IP
base_auth = HTTPBasicAuth('admin', 'smartvm')
passed=0
failed=list()





#v2v-transformation-mappings-create
url = "https://" + ip_addr + "/api/transformation_mappings"

payload = '''{
"name": "InsomniaTransformationMap",
"description": "Mapping creation test via Insomnia REST",
"state": "draft",
"transformation_mapping_items": [
{ "source": "/api/clusters/2", "destination": "/api/clusters/1" },
{ "source": "/api/data_stores/6", "destination": "/api/data_stores/1" },
{ "source": "/api/data_stores/5", "destination": "/api/data_stores/1" },
{ "source": "/api/lans/9", "destination": "/api/lans/2" }
]
}
'''
headers = {
    'content-type': "application/json",
}

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)
if (not 'error' in response.text) and ('created_at' in response.text):
	passed+=1
else:
	failed.append([response.status_code,response.content])





#v2v-transformation-mappings-create-invalid
url = "https://"+ ip_addr +"/api/transformation_mappings"

payload = '''{
"name": "InsomniaTransformationMap",
"description": "Mapping creation test via Insomnia REST",
"state": "draft",
"transformation_mapping_items": [
{ "source": "/api//3", "destination": "/api/clusters/1" },
{ "source": "/api/data_stores/12", "destination": "/api/data_stores/1" },
{ "source": "/api/data_stores/5", "destination": "/api/data_stores/1" },
{ "source": "/api/lans/9", "destination": "/api/lans/2" }
]
}
'''
headers = {
    'content-type': "application/json",
}

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if ('error' in response.text) and (not 'created_at' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])





#v2v-transformation-mappings-get
url = "https://"+ ip_addr +"/api/transformation_mappings"

payload = ""
headers = {
    'content-type': "application/json",
}

response = requests.request("GET", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ( 'resources' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])





#v2v-transformation-mappings-get-wit-id-attributes
url = "https://"+ ip_addr +"/api/transformation_mappings/1"

payload = "{\n\"attributes\": \"transformation_mapping_items\"\n}"
headers = {
    'content-type': "application/json",
}

response = requests.request("GET", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ('transformation_mapping_items' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])






#v2v-service-templates
#service-templates-get
url = "https://"+ ip_addr +"/api/service_templates/"

payload = ""
headers = {}

response = requests.request("GET", url, data=payload, headers=headers, verify=False, auth=base_auth)





#v2v-service-templates-create-post

url = "https://" + ip_addr + "/api/service_templates/"

payload = '''
{
    "name": "planInsomnia",
    "prov_type":"generic_transformation_plan",
    "config_info":
    {
        "transformation_mapping_id":"1",
        "actions":
        [
            {
                "vm_id":"2"
            }
        ]
    }
}
'''
headers = {
    'content-type': "application/json",
    }

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ('created_at' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])





#v2v-service-templates-get-with-id
url = "https://"+ ip_addr +"/api/service_templates/1"

payload = ""
headers = {}

response = requests.request("GET", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ('created_at' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])


#v2v-service-templates-post-with-id-valid
url = "https://"+ ip_addr +"/api/service_templates/1"

payload = "{\n   \"action\": \"order\"\n}\n"
headers = {
    'content-type': "application/json",
    }

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ('status' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])







#v2v-service-templates-post-with-id-invalid
url = "https://"+ ip_addr +"/api/service_templates/1"

payload = "{\n   \"action\": \"oder\"\n}\n"
headers = {
    'content-type': "application/json",
    }

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if ('error' in response.content) or (response.status_code == 400):
	passed += 1
else:
	failed.append([response.status_code,response.content])







#v2v-service-templates-post-delete-invalid
url = "https://"+ ip_addr +"/api/service_templates/0"

payload = "{\n   \"action\": \"delete\"\n}\n"
headers = {
    'content-type': "application/json",
    }

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if ('error' in response.text) and ('RecordNotFound' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])






#v2v-service-templates-post-delete-invalid
url = "https://"+ ip_addr +"/api/service_templates/1"

payload = "{\n   \"action\": \"delete\"\n}\n"
headers = {
    'content-type': "application/json",
    }

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ('deleting' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])









#v2v-lans-by-cluster
url = "https://" + ip_addr + "/api/clusters/1"

payload = "{\"attributes\":\"lans\"}"
headers = {
    'content-type': "application/json",
    }

response = requests.request("GET", url, data=payload, headers=headers, verify=False, auth=base_auth)

if (not 'error' in response.text) and ('lans' in response.text):
	passed += 1
else:
	failed.append([response.status_code,response.content])


#v2v-transformation-mappings-create-1-for-delete
url = "https://" + ip_addr + "/api/transformation_mappings"

payload = '''{
"name": "InsomniaTransformationMap1",
"description": "Mapping creation test via Insomnia REST",
"state": "draft",
"transformation_mapping_items": [
{ "source": "/api/clusters/2", "destination": "/api/clusters/1" },
{ "source": "/api/data_stores/6", "destination": "/api/data_stores/1" },
{ "source": "/api/data_stores/5", "destination": "/api/data_stores/1" },
{ "source": "/api/lans/9", "destination": "/api/lans/2" }
]
}
'''
headers = {
    'content-type': "application/json",
}

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)
if (not 'error' in response.text) and ('created_at' in response.text):
	passed+=1
else:
	failed.append([response.status_code,response.content])


#v2v-transformation-mappings-create-2-for-delete
url = "https://" + ip_addr + "/api/transformation_mappings"

payload = '''{
"name": "InsomniaTransformationMap2",
"description": "Mapping creation test via Insomnia REST",
"state": "draft",
"transformation_mapping_items": [
{ "source": "/api/clusters/2", "destination": "/api/clusters/1" },
{ "source": "/api/data_stores/6", "destination": "/api/data_stores/1" },
{ "source": "/api/data_stores/5", "destination": "/api/data_stores/1" },
{ "source": "/api/lans/9", "destination": "/api/lans/2" }
]
}
'''
headers = {
    'content-type': "application/json",
}

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)
if (not 'error' in response.text) and ('created_at' in response.text):
	passed+=1
else:
	failed.append([response.status_code,response.content])


#v2v-transformation-mappings-create-3-for-delete
url = "https://" + ip_addr + "/api/transformation_mappings"

payload = '''{
"name": "InsomniaTransformationMap3",
"description": "Mapping creation test via Insomnia REST",
"state": "draft",
"transformation_mapping_items": [
{ "source": "/api/clusters/2", "destination": "/api/clusters/1" },
{ "source": "/api/data_stores/6", "destination": "/api/data_stores/1" },
{ "source": "/api/data_stores/5", "destination": "/api/data_stores/1" },
{ "source": "/api/lans/9", "destination": "/api/lans/2" }
]
}
'''
headers = {
    'content-type': "application/json",
}

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)
if (not 'error' in response.text) and ('created_at' in response.text):
	passed+=1
else:
	failed.append([response.status_code,response.content])


# delete single mapping with DELETE
url = "https://" + ip_addr + "/api/transformation_mappings/1"

payload = ""
headers = {
    'content-type': "application/json",
    }

response = requests.request("DELETE", url, data=payload, headers=headers, verify=False, auth=base_auth)

if response.status_code == 204:
	passed+=1
else:
	failed.append([response.status_code,response.content])

#delete single mapping with POST
url = "https://" + ip_addr + "/api/transformation_mappings/2"

payload = '''
{
"action" : "delete"
}
'''

headers = {
    'content-type': "application/json",
}


response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if response.status_code == 200:
	passed+=1
else:
	failed.append([response.status_code,response.content])

# bulk delete mappings
url = "https://" + ip_addr + "/api/transformation_mappings"

payload = '''
{
"action": "delete",
"resources": [{"id": "3"}, {"id": "4"}]}
'''
headers = {
    'content-type': "application/json",
}

response = requests.request("POST", url, data=payload, headers=headers, verify=False, auth=base_auth)

if response.status_code == 200:
	passed+=1
else:
	failed.append([response.status_code,response.content])

#############################

print("************Result**************")
print("Total {} tests passed".format(passed))
print("Failed Tests count is {} and those are:".format(len(failed)))
for failure in failed:
	print(failure)
	print("\n\n")
