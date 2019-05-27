# Imperva Cloud API Security Integration

Imperva Cloud API Security Integration is a tool that provides easy integration with the Imperva API Security solution to protect APIs that are managed with different API management platforms.

The tool includes predefined integrations with the following API management platforms:
* Red Hat 3scale API Management
* Microsoft Azure API Management
* Amazon API Gateway

In addition, the tool includes the ability to integrate with a local filesystem, and supports adding more integrations.

## Requirements

python 3.5.0 or higher 

## Configuration

In order to run the tool, you need to provide a configuration in JSON format.
The configuration contains the following sections:
* Imperva Management Settings
* Logging Settings
* API Fetchers Settings

------

### Imperva Management Settings

Field | Description
--- | ---
```management_url``` | The Imperva API Security URL
```api_id``` | The API ID for the Imperva management console
```api_key``` | The API Key for the Imperva management console
```site_id``` | The Imperva Cloud WAF site ID
```default_action``` | The API Specification Violation Action. Valid values are "ALERT_ONLY", "BLOCK_REQUEST", "BLOCK_USER", "BLOCK_IP", "IGNORE"

For example:

```json
{
    "management_url":"https://api.imperva.com/api-security/api/",
    "api_id":"12345",
    "api_key":"abcd1234",
    "site_id":"123456789",
    "default_action":"BLOCK_REQUEST"
}
```

------

### Logging Settings

Field | Description
--- | ---
```status_path```| Sets the directory location for reporting the integration run status when it is finished. If left empty, the status will not be written to a file
```log_path``` | Sets the directory location for the tool logging. If left empty, the log will not be written to a file
```level``` | Sets the log level. Valid values are "DEBUG", "INFO" and "ERROR"

For example:

```json
{
    "logging":{
        "status_path":"/var/log/imperva/cloud-api-security",
        "log_path":"/var/log/imperva/cloud-api-security",
        "level":"INFO"
    }
}
```

------

### API Fetchers Settings

Field | Description
--- | ---
```type``` | The fetcher type - should be the name of the Python class name of the fetcher
```active``` | Boolean which indicates if the fetcher is active or not
```settings``` | A JSON of the fetcher settings

------

#### Filesystem Fetcher Settings

Field | Description
--- | ---
```filesystem_path``` | The filesystem path for the API specification files

Example:
```json
{
  "type":"FileSystemFetcher",
  "active":true,
  "settings":{
    "filesystem_path":"/etc/imperva/cloud-api-security/apis"
  }
}
```

------

#### Red Hat 3Scale API Management

Field | Description
--- | ---
```three_scale_url``` | The URL to the 3Scale API management
```three_scale_access_token``` | The 3Scale access token. To generate an access token, see the 3Scale [documentation](https://access.redhat.com/documentation/en-us/red_hat_3scale/2.3/html/accounts/tokens)

Example:
```json
{
  "type":"ThreeScaleFetcher",
  "active":true,
  "settings":{
    "three_scale_url":"my-apis-for-imperva.3scale.net",
    "three_scale_access_token":"abcd1234"
  }
}
```

------

#### Microsoft Azure API Management

The integration is based on the Azure API Management REST API. To enable it, see the [Azure documentation](https://docs.microsoft.com/en-us/rest/api/apimanagement/apimanagementrest/api-management-rest)

Field | Description
--- | ---
```subscription_id``` | The subscription ID
```resource_group_name``` | The name of the resource group
```service_name``` | The service name
```access_token``` | The Azure API Management REST API access token. To generate one, see the [documentation](https://docs.microsoft.com/en-us/rest/api/apimanagement/apimanagementrest/azure-api-management-rest-api-authentication#ManuallyCreateToken)

Example:

```json
{
  "type":"AzureFetcher",
  "active":true,
  "settings":{
    "subscription_id":"1234",
    "resource_group_name":"abcd1234",
    "service_name":"abcd",
    "access_token":"SharedAccessSignature abcd1234"
  }
}
```

------

#### Amazon API Gateway

In order to integrate with AWS we use [Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html#), which is the AWS SDK for Python.
An installation is required as described in this [documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#installation), and can be done by running:
```
pip install boto3
```

Field | Description
--- | ---
```aws_access_key_id``` | The access key for your AWS account
```aws_secret_access_key``` | The secret key for your AWS account
```aws_region``` | The AWS region

Example:

```json
{
  "type":"AwsApiGwFetcher",
  "active":true,
  "settings":{
    "aws_access_key_id":"1234",
    "aws_secret_access_key":"abcd1234",
    "aws_region":"eu-west-1"
  }
}
```

------

### Full settings JSON example:

```json
{
  "logging":{
    "status_path":"/var/log/imperva/cloud-api-security",
    "log_path":"/var/log/imperva/cloud-api-security",
    "level":"DEBUG"
  },
  "api_id":"12345",
  "api_key":"abcd1234",
  "site_id":"123456789",
  "management_url":"https://api.imperva.com/api-security/api/",
  "default_action":"BLOCK_REQUEST",
  "fetchers":[
    {
      "type":"FileSystemFetcher",
      "active":true,
      "settings":{
        "filesystem_path":"/etc/imperva/cloud-api-security/apis"
      }
    },
    {
      "type":"ThreeScaleFetcher",
      "active":true,
      "settings":{
        "three_scale_url":"my-apis-for-imperva.3scale.net",
        "three_scale_access_token":"abcd1234"
      }
    },
    {
      "type":"AzureFetcher",
      "active":true,
      "settings":{
        "subscription_id":"1234",
        "resource_group_name":"abcd1234",
        "service_name":"abcd",
        "access_token":"SharedAccessSignature abcd1234"
      }
    },
    {
      "type":"AwsApiGwFetcher",
      "active":true,
      "settings":{
        "aws_access_key_id":"1234",
        "aws_secret_access_key":"abcd1234",
        "aws_region":"eu-west-1"
      }
    }
  ]
}
```


## Running

In order to run the integration, you need to provide the configuration as a file location or directly as a JSON string. 

To run with a configuration file use:
```
python3 ApiSecurityManager.py -p <path_to_config_file>
```

To run directly with a configuration JSON use:
```
python3 ApiSecurityManager.py -c {"the configuration json"}
```

Note that if no parameter is passed, the default file location is `/etc/imperva/cloud-api-security/config/config.json`.

You can always run the following to get help information:
```
python3 ApiSecurityManager.py -h
```

## Status

At the end of the run, the tool returns a numeric status which indicates if the run had errors, or if it was fully successful.
For a fully successful run, a zero value (```0```) is returned. For any run were an error occurred, a non-zero value is returned.

In addition, a full status report in JSON format is provided. The status report is printed into the log, and if a file path is provided in the configuration JSON (```status_path``` in the ```logging``` section), the status report will be written to there with a file named ```status.json```.

The status report JSON structure is as follows:

Field | Description
--- | ---
```time``` | The execution end time (epoch in milliseconds)
```has_errors``` | True if there were errors, otherwise false 
```apis``` | An object with three object values - "added", "updated", and "deleted". Each object contains two list - "success" and "error", of APIs according to the action and if it was successful or not
```fetchers``` | An object containing two lists - "success" and "error" of fetchers according to if the tool managed to fetch APIs from them

Example:

```json
{
    "time": 1554374853797, 
    "has_errors": true, 
    "apis": {
        "added": {
            "success":["api-123.example.com/api1", "api-123.example.com/api2"],
            "error": ["api.my-site.com/api"]
        }, 
        "updated": {
            "success": ["api-portal.myportal.com/store"],
            "error": []
        }, 
        "deleted": {
            "success": ["api-portal.myportal.com/partners-api"],
            "error": []
        }
    }, 
    "fetchers": {
        "success": ["ThreeScaleFetcher", "AzureFetcher", "AwsApiGwFetcher"],
        "error": ["FileSystemFetcher"]
    }
}
```

## Getting Help

If you have questions about the library, be sure to check out the source code documentation.
If you still have questions, reach out to me via email at doron.lehmann@imperva.com.

## Reporting Bugs

Open a Git Issue and include as much information as possible. If possible, provide sample code that illustrates the problem you're encountering. If you're experiencing a bug on a specific repository only, provide a link to it, if possible. Do not open a Git Issue for help, leave it only for bug reports.
