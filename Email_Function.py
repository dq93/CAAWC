{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "actions": {
      "List_Rows": {
        "runAfter": {},
        "metadata": {
          "operationMetadataId": "b62ecfbb-7b92-45f2-9f83-d1f0b8ae3fc1"
        },
        "type": "ApiConnection",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['excelonlinebusiness']['connectionId']"
            }
          },
          "method": "get",
          "path": "/v1.0/drives/{driveId}/items/{itemId}/workbook/tables/{tableName}/rows"
        }
      },
      "Filter_This_Week": {
        "runAfter": {
          "List_Rows": ["Succeeded"]
        },
        "type": "Query",
        "inputs": {
          "from": "@body('List_Rows')?['value']",
          "where": "@or(lessOrEquals(item()?['Pre-Assessment Renewal'], addDays(utcNow(),7)), lessOrEquals(item()?['Full-Assessment Renewal'], addDays(utcNow(),7)))"
        }
      },
      "Filter_Next_30_Days": {
        "runAfter": {
          "List_Rows": ["Succeeded"]
        },
        "type": "Query",
        "inputs": {
          "from": "@body('List_Rows')?['value']",
          "where": "@or(lessOrEquals(item()?['Pre-Assessment Renewal'], addDays(utcNow(),30)), lessOrEquals(item()?['Full-Assessment Renewal'], addDays(utcNow(),30)))"
        }
      },
      "Group_By_Caseworker": {
        "runAfter": {
          "Filter_This_Week": ["Succeeded"],
          "Filter_Next_30_Days": ["Succeeded"]
        },
        "type": "Compose",
        "inputs": "@union(body('Filter_This_Week'), body('Filter_Next_30_Days'))"
      },
      "Apply_to_each_Caseworker": {
        "runAfter": {
          "Group_By_Caseworker": ["Succeeded"]
        },
        "type": "Foreach",
        "foreach": "@union(outputs('Group_By_Caseworker')?['Caseworker'])",
        "actions": {
          "Filter_Current_Caseworker": {
            "type": "Query",
            "inputs": {
              "from": "@outputs('Group_By_Caseworker')",
              "where": "@equals(item()?['Caseworker'], items('Apply_to_each_Caseworker'))"
            }
          },
          "Create_HTML_Table": {
            "runAfter": {
              "Filter_Current_Caseworker": ["Succeeded"]
            },
            "type": "Table",
            "inputs": {
              "from": "@body('Filter_Current_Caseworker')",
              "columns": [
                { "displayName": "Client ID", "value": "@item()?['Client ID']" },
                { "displayName": "Pre-Assessment Renewal", "value": "@item()?['Pre-Assessment Renewal']" },
                { "displayName": "Full-Assessment Renewal", "value": "@item()?['Full-Assessment Renewal']" }
              ]
            }
          },
          "Send_Email_to_Caseworker": {
            "runAfter": {
              "Create_HTML_Table": ["Succeeded"]
            },
            "type": "ApiConnection",
            "inputs": {
              "host": {
                "connection": {
                  "name": "@parameters('$connections')['office365']['connectionId']"
                }
              },
              "method": "post",
              "path": "/v2/Mail",
              "body": {
                "importance": "Normal",
                "to": "@items('Apply_to_each_Caseworker')",
                "subject": "Weekly Compliance Report",
                "body": "Hello @{items('Apply_to_each_Caseworker')},<br><br>Here are your deadlines:<br><br><b>Due This Week or Next 30 Days:</b><br>@{outputs('Create_HTML_Table')}<br><br>Please ensure all actions are completed on time.<br><br>- Compliance Bot"
              }
            }
          }
        }
      }
    },
    "triggers": {
      "Weekly_Schedule": {
        "recurrence": {
          "frequency": "Week",
          "interval": 1,
          "startTime": "2024-01-01T08:00:00Z",
          "timeZone": "UTC",
          "schedule": { "hours": [8], "minutes": [0], "weekDays": ["Monday"] }
        },
        "type": "Recurrence"
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