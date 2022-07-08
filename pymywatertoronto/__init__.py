"""Package to interact with MyWaterToronto service."""

from datetime import datetime, timedelta
import json
import logging

from requests import Session

API_LIMIT = 60

DEFAULT_TIMEOUT = 30

API_BASE_URL = 'https://secure.toronto.ca/cc_api/svcaccount_v1/WaterAccount'
API_VALIDATE_URL = '{0}{1}'.format(API_BASE_URL, '/validate')  # noqa: S105
API_ACCOUNTDETAILS_URL = '{0}{1}'.format(API_BASE_URL, '/accountdetails')
API_CONSUMPTION_URL = '{0}{1}'.format(API_BASE_URL, '/consumption')

LOGGER = logging.getLogger(__name__)

def _response_error(message, response):
    if response.status_code == 200:  # noqa: WPS432
        return

    if response.status_code == 400:  # noqa: WPS432
        error_message = json.loads(response.text)['error']
    else:
        error_message = json.loads(response.text)['message']

    raise Exception(
        """Message:{0}.
            Response code returned:{1}.
            Eror message returned:{2}.""".format(message, response.status_code, error_message),
    )


class MyWaterToronto(object):  # noqa: WPS214
    """Interact with API Validation."""

    def __init__(  # noqa: WPS211
        self,
        account_number,
        client_number,
        last_name,
        postal_code,
        last_payment_method,
        http_session=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        """

        Initialize the data object.

        Args:
            account_number: Your Account No. found on the utility bill.
            client_number: Your Client No. found on the utility bill.
            last_name: Your last name found on the utility bill (or the first last name on a joint account).
            postal_code: Your postal code found on the utility bill.
            last_payment_method: A code based on how you made your last payment of the utility bill.
              values: 0 = N/A
                      1 = Pre-Authorized
                      2 = Mail-In Cheque
                      3 = In-Person
                      4 = Bank Payment
                      5 = Payment Drop Box
            http_session: Requests Session()
            timeout: Requests timeout for throttling.

        """

        self.__account_number = account_number
        self.__client_number = client_number
        self.__account_number_full = self.__account_number + "-" + self.__client_number
        self.__last_name = last_name
        self.__postal_code = postal_code
        self.__last_payment_method = last_payment_method

        if http_session is None:
            self.__http_session = Session()
        else:
            self.__http_session = http_session

        self.__timeout = timeout
        self.__refToken = None
        self.authorization_header = None

        self.__account = None
        self.__accountType = None
        self.__premiseList = []

        self.__validate()
        self.__get_account_details()
        #self._get_consumption()

    def __validate(self):
        """Validate the account information and obtain refToken."""

        payload = {'API_OP': 'VALIDATE',
                   'ACCOUNT_NUMBER': self.__account_number_full,
                   'LAST_NAME': self.__last_name,
                   'POSTAL_CODE': self.__postal_code,
                   'LAST_PAYMENT_METHOD': self.__last_payment_method}

        headers = {'content-type': 'application/json'}
        response = self.__http_session.request(
            'POST',
            API_VALIDATE_URL,
            json=payload,
            headers=headers,
            timeout=self.__timeout,
        )

        LOGGER.debug('Validate Payload: %s', payload)  # noqa: WPS323
        LOGGER.debug('Validate Response: %s', response.text)  # noqa: WPS323

        # Check for response errors.
        _response_error("Unable to validate account number{0}".format(self.__account_number_full), response)

        # Save the refToken 
        self.__refToken = json.loads(response.text)['validateResponse']['refToken']

        return

    def __get_account_details(self):
        """Get the account data."""

        params_json = {"API_OP":"ACCOUNTDETAILS","ACCOUNT_NUMBER":self.__account_number_full}
        params = {"refToken":self.__refToken,
                  "json": json.dumps(params_json)}
        
        headers = {'content-type': 'application/json'}

        response = self.__http_session.request(
            "GET",
            API_ACCOUNTDETAILS_URL,
            params=params,
            headers=headers,
            timeout=self.__timeout,
        )

        LOGGER.debug('Response URL: %s', response.url)  # noqa: WPS323
        LOGGER.debug('Account Details Params: %s', params)  # noqa: WPS323
        LOGGER.debug('Account Details Response: %s', response.text)  # noqa: WPS323

        # Check for response errors.
        _response_error("Unable to get account details for account number{0}".format(self.__account_number_full), response)

        # Get the JSON of the account details
        accountDetails = json.loads(response.text)
        self.__account = accountDetails["account"]
        self.__accountType = accountDetails["accountType"]

        premiseListObject = accountDetails["premiseList"]

        for premiseItem in premiseListObject:
            # Get the premise data for each premise associated with an account
            premise = Premise( premiseId = premiseItem["premiseId"],
                               address = premiseItem["address"],
                               addrNum = premiseItem["addrNum"],
                               addrSuf = premiseItem["addrSuf"],
                               addrName = premiseItem["addrName"],
                               addrCity = premiseItem["addrCity"],
                               addrState = premiseItem["addrState"],
                               addrZip = premiseItem["addrZip"],
                               ward = premiseItem["ward"] )

            # Get the list of meters associated with the current premise
            meterListObject = premiseItem["meterList"]

            for meterItem in meterListObject:
                # Get the meter data for each meter associated with a premise
                meter = Meter( miu = meterItem["miu"],
                               meterSize = meterItem["meterSize"],
                               meterNumber = meterItem["meterNumber"],
                               intervalMins = meterItem["intervalMins"],
                               meterClass = meterItem["meterClass"],
                               meterInstallDate = meterItem["meterInstallDate"],
                               meterManufacturerType = meterItem["meterManufacturerType"],
                               firstReadDate = meterItem["firstReadDate"],
                               lastReadDate = meterItem["lastReadDate"],
                               lastReading = meterItem["lastReading"],
                               unitOfMeasure =meterItem["unitofMeasure"] )

                # Add the meter to the premise
                premise.addMeter( meter )

            # Add the premise to the premise list for the account
            self.addPremise( premise )
        return


    def __get_consumption(self):
        """Get the meter consumption data"""

        params_json = {"API_OP":"CONSUMPTION",
                       "ACCOUNT_NUMBER":self.__account_number_full}
        params = {"refToken":self.__refToken,
                  "json": json.dumps(params_json)}
        
        headers = {'content-type': 'application/json'}

        response = self.__http_session.request(
            "GET",
            API_CONSUMPTION_URL,
            params=params,
            headers=headers,
            timeout=self.__timeout,
        )

        LOGGER.debug('Response URL: %s', response.url)  # noqa: WPS323
        LOGGER.debug('Consumption Params: %s', params)  # noqa: WPS323
        LOGGER.debug('Consumption Response: %s', response.text)  # noqa: WPS323

        # Check for response errors.
        _response_error("Unable to get consumption data for account number{0}".format(self.__account_number_full), response)
        return

    def addPremise(self, premise):
        self.__premiseList.append(premise)


class Premise(object):
    """Object to store premise information."""

    def __init__(  # noqa: WPS211
        self,
        premiseId,
        address,
        addrNum,
        addrSuf,
        addrName,
        addrCity,
        addrState,
        addrZip,
        ward,
    ):

        """

        Initialize the data object.
        """

        self.__premiseId = premiseId
        self.__address = address
        self.__addrNum = addrNum
        self.__addrSuf = addrSuf
        self.__addrName = addrName
        self.__addrCity = addrCity
        self.__addrState = addrState
        self.__addrZip = addrZip
        self.__ward = ward

        self.__meterList = []

    @property
    def premiseId(self):
        return self.__premiseId

    @property
    def address(self):
        return self.__address

    @property
    def addrNum(self):
        return self.__addrNum

    @property
    def addrSuf(self):
        return self.__addrSuf

    @property
    def addrName(self):
        return self.__addrName

    @property
    def addrCity(self):
        return self.__addrCity

    @property
    def addrState(self):
        return self.__addrState

    @property
    def addrZip(self):
        return self.__addrZip

    @property
    def ward(self):
        return self.__ward

    @property
    def meterList(self):
        return self.__meterList

    def addMeter(self, meter):
        self.__meterList.append(meter)


class Meter(object):
    """Object to store meter information."""

    def __init__(  # noqa: WPS211
        self,
        miu,
        meterSize,
        meterNumber,
        intervalMins,
        meterClass,
        meterInstallDate,
        meterManufacturerType,
        firstReadDate,
        lastReadDate,
        lastReading,
        unitOfMeasure,
    ):

        self.__miu = miu
        self.__meterSize = meterSize
        self.__meterNumber = meterNumber
        self.__intervalMins = int(intervalMins)
        self.__meterClass = meterClass
        self.__meterInstallDate = datetime.strptime(meterInstallDate, "%Y-%m-%d")
        self.__meterManufacturerType = meterManufacturerType
        self.__firstReadDate = datetime.strptime(firstReadDate, "%Y-%m-%d")
        self.__lastReadDate = datetime.strptime(lastReadDate, "%Y-%m-%d")
        self.__lastReading = float(lastReading)
        self.__unitOfMeasure = unitOfMeasure

    @property
    def miu(self):
        return self.__miu

    @property
    def meterSize(self):
        return self.__meterSize

    @property
    def meterNumber(self):
        return self.__meterNumber

    @property
    def intervalMins(self):
        return self.__intervalMins

    @property
    def meterClass(self):
        return self.__meterClass

    @property
    def meterInstallDate(self):
        return self.__meterInstallDate

    @property
    def meterManufacturerType(self):
        return self.__meterManufacturerType

    @property
    def firstReadDate(self):
        return self.__firstReadDate

    @property
    def lastReadDate(self):
        return self.__lastReadDate

    @property
    def lastReading(self):
        return self.__lastReading

    @property
    def unitOfMeasure(self):
        return self.__unitOfMeasure