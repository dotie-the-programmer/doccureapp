import datetime
import base64
import requests
from requests.auth import HTTPBasicAuth

class MpesaAccessToken:
    consumer_key = "8BtRzxtxLIhRj1oU4C2nzCvDTlodbec55MTmBpxGko6QlotF"
    consumer_secret = "zH4j5As0vHB2zwx5g4aVWWnzbK2AhgD7kMjiF895MRfQX99QfMpD3EiOgAGv0ypM"

    @classmethod
    def generate_access_token(cls):
        api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        response = requests.get(api_url, auth=HTTPBasicAuth(cls.consumer_key, cls.consumer_secret))
        return response.json().get('access_token')


class LipanaMpesaPpassword:
    Business_short_code = "174379"
    passkey = "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"

    @classmethod
    def generate_password(cls):
        time_now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = cls.Business_short_code + cls.passkey + time_now
        encoded = base64.b64encode(data_to_encode.encode())
        return encoded.decode('utf-8'), time_now
