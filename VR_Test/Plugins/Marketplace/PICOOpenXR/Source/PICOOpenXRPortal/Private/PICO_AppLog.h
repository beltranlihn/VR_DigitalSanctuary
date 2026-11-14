// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
DEFINE_LOG_CATEGORY_STATIC(LogAppLog, Log, All);

/**
 * 
 */
class PICOOPENXRPORTAL_API PICO_AppLog
{
public:
	PICO_AppLog();
	~PICO_AppLog();

	static bool InitAppLog();
	static void ShutdownAppLog();

	static void AddAppLog(const FString& param, const FString& value);
	
private:
	static FString GetJsonStringFromParamAndValue(const FString& param, const FString& value);

	static FString StrAppID;
	static FString StrChannelName;
	static FString StrXRSDK;
	static bool IsInitialized;
};
