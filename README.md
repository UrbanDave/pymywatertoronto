# MyWaterToronto
Authenticates to MyWaterToronto API, returns account details (premiseList and meterList) and consumption data for the selected meter.  

## Configuration
You need to provide your account information which can be found on a Toronto Water & Solid Waste Management Services Utility Bill.

## Configuration Variables
```
account_number:
  description: Your Account No. found on the utility bill.
  required: true
  type: string
client_number:
  description: Your Client No. found on the utility bill.
  required: true
  type: string
last_name:
  description: Your last name found on the utility bill (or the first last name on a joint account).
  required: true
  type: string
postal_code:
  description: Your postal code found on the utility bill.
  required: true
  type: string
last_payment_method:
  description: A code based on how you made your last payment of the utility bill.
  required: true
  type: string
  values: 0 = N/A
          1 = Pre-Authorized
          2 = Mail-In Cheque
          3 = In-Person
          4 = Bank Payment
          5 = Payment Drop Box
```

## Examples
Copy the test_template.py file and update the account information