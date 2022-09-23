# alexa-pico
Alexa controlled visual timer on Raspberry Pi Pico W

High level architecture of this project can be found here:

http://pico-on-aws.s3-website-eu-west-1.amazonaws.com

This project contains python code for Raspberry Pi Pico W (hereafter Pico) and Alexa hosted Lambda function that realise an Alexa controlled visual timer on Pico.

Furthermore this project uses self hosted IoT Core and DynamoDB and this respository contains their corresponding policies too.

Pico uses micropython-umqtt.simple to connect to IoT Core that can be installed from REPL with
```
import upip  
upip.install('umqtt.simple')
```
available on latest micropython firmware for Pico from: 

https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

Code main.py on Pico further requires importable secrets.py module that contains the following variables:
```
SSID = "your_SSID"  
PASSWORD = "your_wifi_password"  
ENDPOINT = "your_iot_core_endpoint"  
CERT_FILE = "your_der_cert_file"  
KEY_FILE = "your_der_private_key_file"  
```
Please note that certificate and private key downloadable from IoT Core are PEM format. To convert to DER format use:
```
openssl rsa -in private.pem.key -out private.der -outform DER  
openssl x509 -in certificate.pem.crt -out certificate.der -outform DER
```
Once Pico connects with these credentials to self hosted IoT Core endpoint, it subscribes to topic "picow" and publishes initial 0 value to topic "remain".

Certificate needs to have iot_certificate_policy.json attached in IoT Core.

IoT Core needs to have a rule defined to populate DynamoDB table "remain" from topic "remain" with partition key "device" value "picow" and sort key "timestamp" value "${timestamp()}.

This rule needs to have a service role with iot_dynamo_policy.json attached in IAM.

Code lambda_function.py requires importable accountid.py module that contains the following variables:
```
ACCOUNTID = "your_account_id"  
REGION = "your_region"
```
Alexa skill needs to be configured with StartTimerIntent carrying slot named "minutes" and with QueryTimerIntent.

When StartTimerIntent is invoked Alexa hosted Lambda function acquires session token from STS and publishes "minutes" from slot to topic "picow" on self hosted IoT Core.

Pico receives "minutes" from IoT Core broker and starts flashing its LED and publishes remaining minutes to topic "remain" evey minute passed that the IoT rule propagates to DynamoDB table "remain" in turn.

When QueryTimerIntent is invoked Alexa hosted Lambda function queries last entry in table "remain" on self hosted DynamoDB table "remain".

Service role assumed for Alexa hosted Lambda function needs to have alexa_hosted_lamdba_policy.json attached in IAM of self account with trusted entity trusted_entity_for_assumed_service_role.json containing ARN of Alexa hosted Lambda function.
