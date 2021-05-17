package main

import (
	"fmt"
	"github.com/huobirdcenter/huobi_golang/pkg/client"
)
  
  // Get the timestamp from Huobi server and print on console
  client := new(client.CommonClient).Init(config.Host)
  resp, err := client.GetTimestamp()
  
  if err != nil {
	applogger.Error("Get timestamp error: %s", err)
  } else {
	applogger.Info("Get timestamp: %d", resp)
  }
  
  
  // Get the list of accounts owned by this API user and print the detail on console
  client := new(client.AccountClient).Init(config.AccessKey, config.SecretKey, config.Host)
  resp, err := client.GetAccountInfo()
  if err != nil {
	applogger.Error("Get account error: %s", err)
  } else {
	applogger.Info("Get account, count=%d", len(resp))
	for _, result := range resp {
	  applogger.Info("account: %+v", result)
	}
  }