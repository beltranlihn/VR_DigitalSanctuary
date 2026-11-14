// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureSemanticRecognizerFactory.h"

#include "EditorFramework/AssetImportData.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "PICO_HandGestureEditorLibrary.h"
#include "PICO_HandGestureSemanticRecognizerAsset.h"

namespace
{
	UAssetImportData* GetOrCreateSemanticRecognizerImportData(UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset)
	{
		if (!RecognizerAsset)
		{
			return nullptr;
		}

#if WITH_EDITORONLY_DATA
		if (!RecognizerAsset->AssetImportData)
		{
			RecognizerAsset->AssetImportData = NewObject<UAssetImportData>(RecognizerAsset, TEXT("AssetImportData"));
		}

		return RecognizerAsset->AssetImportData;
#else
		return nullptr;
#endif
	}

	FString GetSemanticRecognizerImportFilename(const UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset)
	{
		if (!RecognizerAsset)
		{
			return FString();
		}

#if WITH_EDITORONLY_DATA
		if (const UAssetImportData* ImportData = RecognizerAsset->AssetImportData)
		{
						TArray<FString> ImportFilenames;
						ImportData->ExtractFilenames(ImportFilenames);
						if (ImportFilenames.Num() > 0)
						{
								return ImportFilenames[0];
						}

						return ImportData->GetFirstFilename();
		}
#endif

		return FString();
	}

	void UpdateSemanticRecognizerImportFilename(UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, const FString& Filename)
	{
		if (UAssetImportData* ImportData = GetOrCreateSemanticRecognizerImportData(RecognizerAsset))
		{
			ImportData->Update(FPaths::ConvertRelativePathToFull(Filename));
						RecognizerAsset->MarkPackageDirty();
		}
	}
}

UPICOOpenXRHandGestureSemanticRecognizerFactory::UPICOOpenXRHandGestureSemanticRecognizerFactory(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bCreateNew = false;
	bEditorImport = true;
	bText = true;
	SupportedClass = UPICOHandGestureSemanticRecognizerAsset::StaticClass();
	Formats.Add(TEXT("json;PICO OpenXR Hand Gesture Semantic Recognizer JSON"));
}

bool UPICOOpenXRHandGestureSemanticRecognizerFactory::FactoryCanImport(const FString& Filename)
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

	return JsonString.Contains(TEXT("\"schema\"")) &&
		JsonString.Contains(TEXT("\"PICOOpenXR.HandGestureSemanticRecognizer\"")) &&
		JsonString.Contains(TEXT("\"feature_rules\""));
}

UObject* UPICOOpenXRHandGestureSemanticRecognizerFactory::FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled)
{
	bOutOperationCanceled = false;

	UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset = NewObject<UPICOHandGestureSemanticRecognizerAsset>(InParent, InClass ? InClass : UPICOHandGestureSemanticRecognizerAsset::StaticClass(), InName, Flags);
	FString OutError;
	if (!UPICOHandGestureEditorLibrary::ImportSemanticRecognizerJsonFileToRecognizerAsset(Filename, RecognizerAsset, OutError))
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("%s"), *OutError);
		}
		return nullptr;
	}

	UpdateSemanticRecognizerImportFilename(RecognizerAsset, Filename);
	return RecognizerAsset;
}

bool UPICOOpenXRHandGestureSemanticRecognizerFactory::CanReimport(UObject* Obj, TArray<FString>& OutFilenames)
{
	const UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureSemanticRecognizerAsset>(Obj);
	if (!RecognizerAsset)
	{
		return false;
	}

	const FString SourceFilename = GetSemanticRecognizerImportFilename(RecognizerAsset);
	if (SourceFilename.IsEmpty())
	{
		return false;
	}

	OutFilenames.Add(SourceFilename);
	return true;
}

void UPICOOpenXRHandGestureSemanticRecognizerFactory::SetReimportPaths(UObject* Obj, const TArray<FString>& NewReimportPaths)
{
	UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureSemanticRecognizerAsset>(Obj);
	if (RecognizerAsset && ensure(NewReimportPaths.Num() == 1))
	{
		UpdateSemanticRecognizerImportFilename(RecognizerAsset, NewReimportPaths[0]);
	}
}

EReimportResult::Type UPICOOpenXRHandGestureSemanticRecognizerFactory::Reimport(UObject* Obj)
{
	UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureSemanticRecognizerAsset>(Obj);
	if (!RecognizerAsset)
	{
		return EReimportResult::Failed;
	}

	const FString SourceFilename = GetSemanticRecognizerImportFilename(RecognizerAsset);
	if (SourceFilename.IsEmpty())
	{
		return EReimportResult::Failed;
	}

	FString OutError;
	RecognizerAsset->Modify();
	if (!UPICOHandGestureEditorLibrary::ImportSemanticRecognizerJsonFileToRecognizerAsset(SourceFilename, RecognizerAsset, OutError))
	{
		UE_LOG(LogTemp, Error, TEXT("Failed to reimport semantic hand recognizer '%s' from '%s': %s"), *RecognizerAsset->GetPathName(), *SourceFilename, *OutError);
		return EReimportResult::Failed;
	}

	UpdateSemanticRecognizerImportFilename(RecognizerAsset, SourceFilename);
	return EReimportResult::Succeeded;
}

int32 UPICOOpenXRHandGestureSemanticRecognizerFactory::GetPriority() const
{
	return ImportPriority;
}
