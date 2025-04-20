import requests
import json

url = "http://0.0.0.0:8000//api/tourbookings/"

payload = {'package': '7',
'num_travelers': '1',
'user_age': '19',
'user_blood_group': 'AB +',
'user_current_location': 'Dhaka',
'user_phone_number': '15211',
'user_verification_id': '65461+5'}
files=[
  ('user_picture',('2024-12-24-213136.jpg',open('/home/rokon/Pictures/Webcam/2024-12-24-213136.jpg','rb'),'image/jpeg'))
]
headers = {
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQ1MDc1MzYxLCJpYXQiOjE3NDUwNzE3NjEsImp0aSI6Ijg3NjdlM2FjMzQ4YjQ0OTJiY2YwNDUxM2M4NzcwNzc3IiwidXNlcl9pZCI6OH0.JI3bWtEWXWf5VP_t_nvC3ekUGszLC120pPZC793PxRM',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
