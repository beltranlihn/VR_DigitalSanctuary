// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "HeadMountedDisplayTypes.h"
#include "PICO_HandGestureRecognizerAsset.generated.h"

class UPoseAsset;
class UAssetImportData;

USTRUCT(BlueprintType)
struct FPICOHandGestureJointMatchRule
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	EHandKeypoint Joint = EHandKeypoint::Palm;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	bool bMatchRotation = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	bool bMatchPosition = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture", meta = (ClampMin = "0.0"))
	float Weight = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture", meta = (ClampMin = "1.0", ClampMax = "180.0"))
	float AngularToleranceDeg = 35.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture", meta = (ClampMin = "0.1"))
	float PositionToleranceCm = 5.0f;
};

UCLASS(BlueprintType)
class PICOOPENXRHANDTRACKING_API UPICOHandGestureRecognizerAsset : public UDataAsset
{
	GENERATED_BODY()

public:
#if WITH_EDITORONLY_DATA
        UPROPERTY(VisibleAnywhere, Instanced, Category = "Import")
        TObjectPtr<UAssetImportData> AssetImportData = nullptr;
#endif

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	TObjectPtr<UPoseAsset> TargetPoseAsset = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	FName PoseName = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	bool bUseDefaultFullPoseRulesWhenEmpty = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture")
	TArray<FPICOHandGestureJointMatchRule> JointRules;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|Gesture", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MatchThreshold = 0.75f;
};
