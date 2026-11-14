// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureSemanticRecognizerExporter.h"

#include "PICO_HandGestureEditorLibrary.h"
#include "PICO_HandGestureSemanticRecognizerAsset.h"

UPICOOpenXRHandGestureSemanticRecognizerExporter::UPICOOpenXRHandGestureSemanticRecognizerExporter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	SupportedClass = UPICOHandGestureSemanticRecognizerAsset::StaticClass();
	bText = true;
	PreferredFormatIndex = 0;
	FormatExtension.Add(TEXT("json"));
	FormatDescription.Add(TEXT("PICO OpenXR Hand Gesture Semantic Recognizer JSON"));
}

bool UPICOOpenXRHandGestureSemanticRecognizerExporter::SupportsObject(UObject* Object) const
{
	return Super::SupportsObject(Object) && Cast<UPICOHandGestureSemanticRecognizerAsset>(Object) != nullptr;
}

bool UPICOOpenXRHandGestureSemanticRecognizerExporter::ExportText(const FExportObjectInnerContext* Context, UObject* Object, const TCHAR* Type, FOutputDevice& Ar, FFeedbackContext* Warn, uint32 PortFlags)
{
	UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureSemanticRecognizerAsset>(Object);
	if (!RecognizerAsset)
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("PICO hand gesture semantic recognizer exporter only supports UPICOHandGestureSemanticRecognizerAsset."));
		}
		return false;
	}

	FString OutJson;
	FString OutError;
	if (!UPICOHandGestureEditorLibrary::ExportSemanticRecognizerAssetToJson(RecognizerAsset, FString(), OutJson, OutError))
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
