// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/AssetUserData.h"
#include "PICO_PoseAssetImportData.generated.h"

UCLASS()
class PICOOPENXREDITOR_API UPICOOpenXRHandPoseJsonImportData : public UAssetUserData
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, Category = "Import")
	FString SourceJsonFile;
};
