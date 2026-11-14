// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_PoseAssetExporter.h"

#include "Animation/PoseAsset.h"
#include "PICO_HandGestureEditorLibrary.h"

UPICOOpenXRPoseAssetExporter::UPICOOpenXRPoseAssetExporter(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	SupportedClass = UPoseAsset::StaticClass();
	bText = true;
	PreferredFormatIndex = 0;
	FormatExtension.Add(TEXT("json"));
	FormatDescription.Add(TEXT("PICO OpenXR Hand Pose JSON"));
}

bool UPICOOpenXRPoseAssetExporter::SupportsObject(UObject* Object) const
{
	return Super::SupportsObject(Object) && Cast<UPoseAsset>(Object) != nullptr;
}

bool UPICOOpenXRPoseAssetExporter::ExportText(const FExportObjectInnerContext* Context, UObject* Object, const TCHAR* Type, FOutputDevice& Ar, FFeedbackContext* Warn, uint32 PortFlags)
{
	UPoseAsset* PoseAsset = Cast<UPoseAsset>(Object);
	if (!PoseAsset)
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("PICO hand pose exporter only supports UPoseAsset."));
		}
		return false;
	}

	FString OutJson;
	FString OutError;
	if (!UPICOHandGestureEditorLibrary::ExportPoseAssetPoseToJson(PoseAsset, NAME_None, FString(), OutJson, OutError))
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
