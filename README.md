# alexa-pico
Alexa controlled visual timer on Raspberry Pi Pico W

High level architecture of this project can be found here:

![alexa_pico](https://user-images.githubusercontent.com/6145641/194744850-bbeb7948-eff2-47d9-b75a-d23f1b874569.jpg)

Operation is demonstrated in this video:

https://youtu.be/si_6LJFgOxk

This project contains python code for Raspberry Pi Pico W (hereafter Pico) and Alexa hosted Lambda function that realise an Alexa controlled visual timer on Pico.

Furthermore this project uses self hosted IoT Core and DynamoDB and this respository contains their corresponding policies too.

Pico uses micropython-tm1637 for 4-digit display and micropython-umqtt.simple to connect to IoT Core that can be installed from REPL with
```
import upip  
upip.install('micropython-tm1637')
upip.install('micropython-umqtt.simple')
```
available on latest micropython firmware for Pico from:

https://www.raspberrypi.com/documentation/microcontrollers/micropython.html

Code main.py implements timer with the help of a single hardware timer of Pico. State machine of timer is described in the following diagram. Solid line state changes are driven by callback from received messages that stored in variable 'rem'. Dashed line state changes are driven by callback from timer and depletion of variable 'sec' every minute.

![timer_state](https://user-images.githubusercontent.com/6145641/194764992-f21fb2f5-c1ea-4704-86fa-35ab9e54660c.jpg)

Code main.py on Pico further requires importable secrets.py module that contains the following variables:
```
SSID = "your_SSID"  
PASSWORD = "your_wifi_password"  
ENDPOINT = "your_iot_core_endpoint"  
CERT_FILE = "your_pem_cert_file"  
KEY_FILE = "your_pem_private_key_file"  
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

Pico receives "minutes" from IoT Core broker and starts flashing its LED and publishes remaining minutes to topic "remain" every minute passed that the IoT rule propagates to DynamoDB table "remain" in turn.

When QueryTimerIntent is invoked Alexa hosted Lambda function queries last entry in self hosted DynamoDB table "remain".

Service role assumed for Alexa hosted Lambda function needs to have alexa_hosted_lambda_policy.json attached in IAM of self account. Integration between Alexa hosted lambda function and this service role in IAM of self account is achieved by adding trusted entity trusted_entity_for_assumed_service_role.json containing ARN of Alexa hosted Lambda function.
