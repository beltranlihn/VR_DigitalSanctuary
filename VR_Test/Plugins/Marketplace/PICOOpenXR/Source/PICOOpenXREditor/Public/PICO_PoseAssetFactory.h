// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EditorReimportHandler.h"
#include "Factories/Factory.h"
#include "PICO_PoseAssetFactory.generated.h"

UCLASS()
class PICOOPENXREDITOR_API UPICOOpenXRPoseAssetFactory : public UFactory, public FReimportHandler
{
	GENERATED_BODY()

public:
	UPICOOpenXRPoseAssetFactory(const FObjectInitializer& ObjectInitializer);

	virtual bool FactoryCanImport(const FString& Filename) override;
	virtual UObject* FactoryCreateFile(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, const FString& Filename, const TCHAR* Parms, FFeedbackContext* Warn, bool& bOutOperationCanceled) override;

	virtual bool CanReimport(UObject* Obj, TArray<FString>& OutFilenames) override;
	virtual void SetReimportPaths(UObject* Obj, const TArray<FString>& NewReimportPaths) override;
	virtual EReimportResult::Type Reimport(UObject* Obj) override;
	virtual int32 GetPriority() const override;
};
