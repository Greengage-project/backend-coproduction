import requests

response = requests.get('http://localhost/coproduction/api/v1/coproductionprocesses/74618e17-a44c-4de0-8cfe-8e32e6104628/download')

with open('downloaded_file.zip', 'wb') as f:
    f.write(response.content)