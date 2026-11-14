// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureRecognizerExporter.h"

#include "PICO_HandGestureEditorLibrary.h"
#include "PICO_HandGestureRecognizerAsset.h"

UPICOOpenXRHandGestureRecognizerExporter::UPICOOpenXRHandGestureRecognizerExporter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	SupportedClass = UPICOHandGestureRecognizerAsset::StaticClass();
	bText = true;
	PreferredFormatIndex = 0;
	FormatExtension.Add(TEXT("json"));
	FormatDescription.Add(TEXT("PICO OpenXR Hand Gesture Recognizer JSON"));
}

bool UPICOOpenXRHandGestureRecognizerExporter::SupportsObject(UObject* Object) const
{
	return Super::SupportsObject(Object) && Cast<UPICOHandGestureRecognizerAsset>(Object) != nullptr;
}

bool UPICOOpenXRHandGestureRecognizerExporter::ExportText(const FExportObjectInnerContext* Context, UObject* Object, const TCHAR* Type, FOutputDevice& Ar, FFeedbackContext* Warn, uint32 PortFlags)
{
	UPICOHandGestureRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureRecognizerAsset>(Object);
	if (!RecognizerAsset)
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("PICO hand gesture recognizer exporter only supports UPICOHandGestureRecognizerAsset."));
		}
		return false;
	}

	FString OutJson;
	FString OutError;
	if (!UPICOHandGestureEditorLibrary::ExportRecognizerAssetToJson(RecognizerAsset, FString(), OutJson, OutError))
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("%s"), *OutError);
		}
		return false;
	}

	Ar.Log(*OutJson);
	return true;
}
