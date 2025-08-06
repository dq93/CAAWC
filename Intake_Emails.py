{
    "definition": {
        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
        "actions": {
            "Get_Email": {
                "inputs": {
                    "host": {
                        "connection": {
                            "name": "@parameters('$connections')['office365']['connectionId']"
                        }
                    },
                    "method": "get",
                    "path": "/v2/Mail/OnNewEmail",
                    "queries": {
                        "folderPath": "Inbox",
                        "includeAttachments": False,
                        "onlyUnread": True,
                        "fetchOnlyWithAttachments": False
                    }
                },
                "runAfter": {},
                "type": "ApiConnectionWebhook"
            },
            "Parse_Body_Regex": {
                "inputs": {
                    "functionName": "extractValues",
                    "inputs": [
                        "@{triggerBody()?['body']}",
                        "Client ID:\\s*(\\d+)",
                        "(?i)\\b(intake)\\b|\\b(income verification)\\b|\\b(confidentiality)\\b"
                    ],
                    "method": "POST",
                    "service": "azurefunctions"
                },
                "runAfter": {
                    "Get_Email": ["Succeeded"]
                },
                "type": "Function"
            },
            "Update_Excel": {
                "inputs": {
                    "host": {
                        "connection": {
                            "name": "@parameters('$connections')['excelonlinebusiness']['connectionId']"
                        }
                    },
                    "method": "patch",
                    "path": "/v1.0/drives/{driveId}/items/{itemId}/workbook/tables/{tableName}/rows/{rowId}",
                    "body": {
                        "values": [
                            {
                                "Client ID": "@{outputs('Parse_Body_Regex')?['clientID']}",
                                "Caseworker": "@{triggerBody()?['from']['emailAddress']['address']}",
                                "Initial Intake Date": "@{if(equals(outputs('Parse_Body_Regex')?['action'],'intake'), utcNow(), items('CurrentItem')?['Initial Intake Date'])}",
                                "Pre-Assessment": "@{if(equals(outputs('Parse_Body_Regex')?['action'],'intake'), utcNow(), items('CurrentItem')?['Pre-Assessment'])}",
                                "Full-Assessment": "@{if(equals(outputs('Parse_Body_Regex')?['action'],'intake'), utcNow(), items('CurrentItem')?['Full-Assessment'])}",
                                "Income Verification": "@{if(equals(outputs('Parse_Body_Regex')?['action'],'income verification'), utcNow(), items('CurrentItem')?['Income Verification'])}",
                                "Confidentiality Statement": "@{if(equals(outputs('Parse_Body_Regex')?['action'],'confidentiality'), utcNow(), items('CurrentItem')?['Confidentiality Statement'])}"
                            }
                        ]
                    }
                },
                "runAfter": {
                    "Parse_Body_Regex": ["Succeeded"]
                },
                "type": "ApiConnection"
            }
        },
        "triggers": {
            "When_new_email_arrives": {
                "type": "ApiConnectionWebhook",
                "inputs": {
                    "host": {
                        "connection": {
                            "name": "@parameters('$connections')['office365']['connectionId']"
                        }
                    },
                    "path": "/v2/Mail/OnNewEmail",
                    "queries": {
                        "folderPath": "Inbox"
                    }
                }
            }
        }
    },
    "parameters": {
        "$connections": {
            "value": {
                "office365": {
                    "connectionId": "/providers/Microsoft.PowerApps/apis/shared_office365/connection",
                    "connectionName": "shared_office365",
                    "id": "/subscriptions/{subscriptionId}/providers/Microsoft.Web/locations/{region}/managedApis/office365"
                },
                "excelonlinebusiness": {
                    "connectionId": "/providers/Microsoft.PowerApps/apis/shared_excelonlinebusiness/connection",
                    "connectionName": "shared_excelonlinebusiness",
                    "id": "/subscriptions/{subscriptionId}/providers/Microsoft.Web/locations/{region}/managedApis/excelonlinebusiness"
                }
            }
        }
    }
}