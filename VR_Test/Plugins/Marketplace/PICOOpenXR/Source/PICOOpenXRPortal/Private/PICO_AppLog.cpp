// Fill out your copyright notice in the Description page of Project Settings.


#include "PICO_AppLog.h"

#if PLATFORM_WINDOWS
#include "applogrs.hpp"
#endif

//Todo:Unreal app id
FString PICO_AppLog::StrAppID = "793022";
//Todo:PICO_UnrealSDK
FString PICO_AppLog::StrChannelName = "PICO_UnrealSDK";
//Todo:unreal_xr_sdk
FString PICO_AppLog::StrXRSDK = "unreal_xr_sdk";
bool PICO_AppLog::IsInitialized = false;
PICO_AppLog::PICO_AppLog()
{
}

PICO_AppLog::~PICO_AppLog()
{
}

bool PICO_AppLog::InitAppLog()
{
#if PLATFORM_WINDOWS
	if (IsInitialized)
	{
		return false;
	}
	IsInitialized = true;
	const char* appid = TCHAR_TO_UTF8(*StrAppID);
	const char* channel = TCHAR_TO_UTF8(*StrChannelName);

	applog::AppLog_init(appid, channel);
	UE_LOG(LogAppLog, Verbose, TEXT("AppLog has been initialized."));
	return true;
#else
	return false;
#endif
}

void PICO_AppLog::ShutdownAppLog()
{
#if PLATFORM_WINDOWS
	auto DestroyCallback = []()
	{
		UE_LOG(LogAppLog, Verbose, TEXT("AppLog has been destroyed."));
	};
	
	applog::AppLog_destroy(DestroyCallback);
#endif
}

void PICO_AppLog::AddAppLog(const FString& param, const FString& value)
{
#if PLATFORM_WINDOWS
	FString JsonString=GetJsonStringFromParamAndValue(param,value);

	const char* event = TCHAR_TO_UTF8(*StrXRSDK);
	const char* params = TCHAR_TO_UTF8(*JsonString);
	
	applog::AppLog_onEvent(event,params);
#endif
}

FString PICO_AppLog::GetJsonStringFromParamAndValue(const FString& param, const FString& value)
{
	TSharedPtr<FJsonObject> contentData = MakeShareable(new FJsonObject());
	contentData->SetStringField(param, value);

	FString JsonString;
	TSharedRef<TJsonWriter<>> JsonWriter = TJsonWriterFactory<>::Create(&JsonString);
	FJsonSerializer::Serialize(contentData.ToSharedRef(), JsonWriter);
	JsonWriter->Close();

	return JsonString;
}
