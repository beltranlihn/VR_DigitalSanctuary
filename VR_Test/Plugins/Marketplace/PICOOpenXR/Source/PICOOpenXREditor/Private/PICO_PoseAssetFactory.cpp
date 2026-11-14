// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_PoseAssetFactory.h"

#include "Animation/PoseAsset.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "PICO_HandGestureEditorLibrary.h"
#include "PICO_PoseAssetImportData.h"

namespace
{
	UPICOOpenXRHandPoseJsonImportData* GetOrCreateHandPoseJsonImportData(UPoseAsset* PoseAsset)
	{
		if (!PoseAsset)
		{
			return nullptr;
		}

		if (UPICOOpenXRHandPoseJsonImportData* ImportData = PoseAsset->GetAssetUserData<UPICOOpenXRHandPoseJsonImportData>())
		{
			return ImportData;
		}

		UPICOOpenXRHandPoseJsonImportData* ImportData = NewObject<UPICOOpenXRHandPoseJsonImportData>(PoseAsset, TEXT("PICOOpenXRHandPoseJsonImportData"));
		PoseAsset->AddAssetUserData(ImportData);
		return ImportData;
	}

	FString GetHandPoseJsonImportFilename(UPoseAsset* PoseAsset)
	{
		if (!PoseAsset)
		{
			return FString();
		}

		if (const UPICOOpenXRHandPoseJsonImportData* ImportData = PoseAsset->GetAssetUserData<UPICOOpenXRHandPoseJsonImportData>())
		{
			return ImportData->SourceJsonFile;
		}

		return FString();
	}

	void UpdateHandPoseJsonImportFilename(UPoseAsset* PoseAsset, const FString& Filename)
	{
		if (UPICOOpenXRHandPoseJsonImportData* ImportData = GetOrCreateHandPoseJsonImportData(PoseAsset))
		{
			ImportData->SourceJsonFile = FPaths::ConvertRelativePathToFull(Filename);
		}
	}
}

UPICOOpenXRPoseAssetFactory::UPICOOpenXRPoseAssetFactory(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bCreateNew = false;
	bEditorImport = true;
	bText = true;
	SupportedClass = UPoseAsset::StaticClass();
	Formats.Add(TEXT("json;PICO OpenXR Hand Pose JSON"));
}

bool UPICOOpenXRPoseAssetFactory::FactoryCanImport(const FString& Filename)
{
	if (!FPaths::GetExtension(Filename).Equals(TEXT("json"), ESearchCase::IgnoreCase))
	{
		return false;
	}

	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *Filename))
	{
		return false;
	}

	return JsonString.Contains(TEXT("\"joints\"")) && JsonString.Contains(TEXT("\"xr_joint\""));
}

UObject* UPICOOpenXRPoseAssetFactory::FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled)
{
	bOutOperationCanceled = false;

	UPoseAsset* PoseAsset = NewObject<UPoseAsset>(InParent, InClass ? InClass : UPoseAsset::StaticClass(), InName, Flags);
	FString OutError;
	if (!UPICOHandGestureEditorLibrary::ImportOpenXRHandPoseJsonFileToPoseAsset(Filename, PoseAsset, OutError))
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("%s"), *OutError);
		}
		return nullptr;
	}

	UpdateHandPoseJsonImportFilename(PoseAsset, Filename);
	return PoseAsset;
}

bool UPICOOpenXRPoseAssetFactory::CanReimport(UObject* Obj, TArray<FString>& OutFilenames)
{
	UPoseAsset* PoseAsset = Cast<UPoseAsset>(Obj);
	if (!PoseAsset)
	{
		return false;
	}

	const FString SourceFilename = GetHandPoseJsonImportFilename(PoseAsset);
	if (SourceFilename.IsEmpty())
	{
		return false;
	}

	OutFilenames.Add(SourceFilename);
	return true;
}

void UPICOOpenXRPoseAssetFactory::SetReimportPaths(UObject* Obj, const TArray<FString>& NewReimportPaths)
{
	UPoseAsset* PoseAsset = Cast<UPoseAsset>(Obj);
	if (PoseAsset && ensure(NewReimportPaths.Num() == 1))
	{
		UpdateHandPoseJsonImportFilename(PoseAsset, NewReimportPaths[0]);
	}
}

EReimportResult::Type UPICOOpenXRPoseAssetFactory::Reimport(UObject* Obj)
{
	UPoseAsset* PoseAsset = Cast<UPoseAsset>(Obj);
	if (!PoseAsset)
	{
		return EReimportResult::Failed;
	}

	const FString SourceFilename = GetHandPoseJsonImportFilename(PoseAsset);
	if (SourceFilename.IsEmpty())
	{
		return EReimportResult::Failed;
	}

	FString OutError;
	PoseAsset->Modify();
	if (!UPICOHandGestureEditorLibrary::ImportOpenXRHandPoseJsonFileToPoseAsset(SourceFilename, PoseAsset, OutError))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to reimport hand PoseAsset '%s' from '%s': %s"), *PoseAsset->GetPathName(), *SourceFilename, *OutError);
		return EReimportResult::Failed;
	}

	UpdateHandPoseJsonImportFilename(PoseAsset, SourceFilename);
	return EReimportResult::Succeeded;
}

int32 UPICOOpenXRPoseAssetFactory::GetPriority() const
{
	return ImportPriority;
}
