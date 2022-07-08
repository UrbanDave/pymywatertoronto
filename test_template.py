import pymywatertoronto
from datetime import timedelta
from requests import Session
import logging

logging.basicConfig(filename="mywatertoronto.log",level=logging.DEBUG)

account_number="000000000"
client_number="000000000=00"
last_name="lastname"
postal_code="x1x_1x1"
last_payment_method="4"

SCAN_INTERVAL = timedelta(minutes=60)

validate = pymywatertoronto.MyWaterToronto(
        account_number, client_number, last_name, postal_code, last_payment_method, http_session=Session()
        )