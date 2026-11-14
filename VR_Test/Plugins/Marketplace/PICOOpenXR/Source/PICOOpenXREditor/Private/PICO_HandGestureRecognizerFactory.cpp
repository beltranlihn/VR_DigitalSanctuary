// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureRecognizerFactory.h"

#include "EditorFramework/AssetImportData.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "PICO_HandGestureEditorLibrary.h"
#include "PICO_HandGestureRecognizerAsset.h"

namespace
{
        UAssetImportData* GetOrCreateRecognizerImportData(UPICOHandGestureRecognizerAsset* RecognizerAsset)
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

        FString GetRecognizerImportFilename(const UPICOHandGestureRecognizerAsset* RecognizerAsset)
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

        void UpdateRecognizerImportFilename(UPICOHandGestureRecognizerAsset* RecognizerAsset, const FString& Filename)
        {
                if (UAssetImportData* ImportData = GetOrCreateRecognizerImportData(RecognizerAsset))
                {
                        ImportData->Update(FPaths::ConvertRelativePathToFull(Filename));
						RecognizerAsset->MarkPackageDirty();
                }
        }
}

UPICOOpenXRHandGestureRecognizerFactory::UPICOOpenXRHandGestureRecognizerFactory(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	bCreateNew = false;
	bEditorImport = true;
	bText = true;
	SupportedClass = UPICOHandGestureRecognizerAsset::StaticClass();
	Formats.Add(TEXT("json;PICO OpenXR Hand Gesture Recognizer JSON"));
}

bool UPICOOpenXRHandGestureRecognizerFactory::FactoryCanImport(const FString& Filename)
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
		JsonString.Contains(TEXT("\"PICOOpenXR.HandGestureRecognizer\"")) &&
		JsonString.Contains(TEXT("\"joint_rules\""));
}

UObject* UPICOOpenXRHandGestureRecognizerFactory::FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled)
{
	bOutOperationCanceled = false;

	UPICOHandGestureRecognizerAsset* RecognizerAsset = NewObject<UPICOHandGestureRecognizerAsset>(InParent, InClass ? InClass : UPICOHandGestureRecognizerAsset::StaticClass(), InName, Flags);
	FString OutError;
	if (!UPICOHandGestureEditorLibrary::ImportRecognizerJsonFileToRecognizerAsset(Filename, RecognizerAsset, OutError))
	{
		if (Warn)
		{
			Warn->Logf(ELogVerbosity::Error, TEXT("%s"), *OutError);
		}
		return nullptr;
	}

        UpdateRecognizerImportFilename(RecognizerAsset, Filename);
	return RecognizerAsset;
}

bool UPICOOpenXRHandGestureRecognizerFactory::CanReimport(UObject* Obj, TArray<FString>& OutFilenames)
{
        const UPICOHandGestureRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureRecognizerAsset>(Obj);
        if (!RecognizerAsset)
        {
                return false;
        }

        const FString SourceFilename = GetRecognizerImportFilename(RecognizerAsset);
        if (SourceFilename.IsEmpty())
        {
                return false;
        }

        OutFilenames.Add(SourceFilename);
        return true;
}

void UPICOOpenXRHandGestureRecognizerFactory::SetReimportPaths(UObject* Obj, const TArray<FString>& NewReimportPaths)
{
        UPICOHandGestureRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureRecognizerAsset>(Obj);
        if (RecognizerAsset && ensure(NewReimportPaths.Num() == 1))
        {
                UpdateRecognizerImportFilename(RecognizerAsset, NewReimportPaths[0]);
        }
}

EReimportResult::Type UPICOOpenXRHandGestureRecognizerFactory::Reimport(UObject* Obj)
{
        UPICOHandGestureRecognizerAsset* RecognizerAsset = Cast<UPICOHandGestureRecognizerAsset>(Obj);
        if (!RecognizerAsset)
        {
                return EReimportResult::Failed;
        }

        const FString SourceFilename = GetRecognizerImportFilename(RecognizerAsset);
        if (SourceFilename.IsEmpty())
        {
                return EReimportResult::Failed;
        }

        FString OutError;
        RecognizerAsset->Modify();
        if (!UPICOHandGestureEditorLibrary::ImportRecognizerJsonFileToRecognizerAsset(SourceFilename, RecognizerAsset, OutError))
        {
                UE_LOG(LogTemp, Error, TEXT("Failed to reimport hand recognizer '%s' from '%s': %s"), *RecognizerAsset->GetPathName(), *SourceFilename, *OutError);
                return EReimportResult::Failed;
        }

        UpdateRecognizerImportFilename(RecognizerAsset, SourceFilename);
        return EReimportResult::Succeeded;
}

int32 UPICOOpenXRHandGestureRecognizerFactory::GetPriority() const
{
        return ImportPriority;
}
