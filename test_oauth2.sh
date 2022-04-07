# To run this test you need first to crate a "Resource owner password-based" OAUTH2 App
BASE_URL=http://localhost:8000
USERNAME=admin
PASSWORD=*****
CLIENT_ID=*************
CLIENT_SECRET=******************

TOKEN=$(http --form POST ${BASE_URL}/o/token/ grant_type=password username=${USERNAME} password=${PASSWORD} -a ${CLIENT_ID}:${CLIENT_SECRET} | jq -r '.access_token')
http ${BASE_URL}/o/userinfo/ scopes=openid,write claims=username "Authorization:Bearer ${TOKEN}" --all -v
