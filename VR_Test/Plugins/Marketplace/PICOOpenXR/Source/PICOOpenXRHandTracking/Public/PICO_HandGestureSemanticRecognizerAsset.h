// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "HeadMountedDisplayTypes.h"
#include "PICO_HandGestureSemanticRecognizerAsset.generated.h"

class UPoseAsset;
class UAssetImportData;
struct FReferenceSkeleton;

UENUM(BlueprintType)
enum class EPICOHandSemanticFeatureType : uint8
{
	ThumbCurl,
	IndexCurl,
	MiddleCurl,
	RingCurl,
	LittleCurl,
	IndexMiddleSpread,
	MiddleRingSpread,
	RingLittleSpread,
	ThumbUpness,
	ThumbOpposition,
	PalmPitch,
	PalmRoll
};

USTRUCT(BlueprintType)
struct FPICOHandSemanticFeatureRule
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	EPICOHandSemanticFeatureType Feature = EPICOHandSemanticFeatureType::ThumbCurl;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	float TargetValue = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture", meta = (ClampMin = "0.001"))
	float Tolerance = 0.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture", meta = (ClampMin = "0.0"))
	float Weight = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	bool bRequired = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MinPassScore = 0.5f;
};

USTRUCT(BlueprintType)
struct FPICOHandSemanticFeatures
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float ThumbCurl = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float IndexCurl = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float MiddleCurl = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float RingCurl = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float LittleCurl = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float IndexMiddleSpread = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float MiddleRingSpread = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float RingLittleSpread = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float ThumbUpness = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float ThumbOpposition = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float PalmPitch = 0.0f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "PICO|HandTracking|SemanticGesture")
	float PalmRoll = 0.0f;
};

UCLASS(BlueprintType)
class PICOOPENXRHANDTRACKING_API UPICOHandGestureSemanticRecognizerAsset : public UDataAsset
{
	GENERATED_BODY()

public:
#if WITH_EDITORONLY_DATA
	UPROPERTY(VisibleAnywhere, Instanced, Category = "Import")
	TObjectPtr<UAssetImportData> AssetImportData = nullptr;
#endif

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	TObjectPtr<UPoseAsset> TargetPoseAsset = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	FName PoseName = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float MatchThreshold = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|HandTracking|SemanticGesture")
	TArray<FPICOHandSemanticFeatureRule> FeatureRules;
};

namespace PICOHandGestureSemantic
{
	PICOOPENXRHANDTRACKING_API void BuildDefaultBoneMappings(bool bIsRightHand, TMap<EHandKeypoint, FName>& OutMappings);
	PICOOPENXRHANDTRACKING_API bool GetFeatureValue(const FPICOHandSemanticFeatures& Features, EPICOHandSemanticFeatureType FeatureType, float& OutValue);
	PICOOPENXRHANDTRACKING_API FString GetFeatureTypeName(EPICOHandSemanticFeatureType FeatureType);
	PICOOPENXRHANDTRACKING_API bool TryParseFeatureType(const FString& FeatureTypeName, EPICOHandSemanticFeatureType& OutFeatureType);
	PICOOPENXRHANDTRACKING_API float GetNeutralFeatureValue(EPICOHandSemanticFeatureType FeatureType);
	PICOOPENXRHANDTRACKING_API float GetSuggestedTolerance(EPICOHandSemanticFeatureType FeatureType);
	PICOOPENXRHANDTRACKING_API float GetSuggestedWeight(EPICOHandSemanticFeatureType FeatureType);
	PICOOPENXRHANDTRACKING_API bool ExtractSemanticFeatures(bool bIsRightHand, const FReferenceSkeleton& RefSkeleton, const TMap<EHandKeypoint, FName>& BoneMappings, const TArray<FTransform>& LocalTransforms, const TArray<FTransform>& ComponentTransforms, FPICOHandSemanticFeatures& OutFeatures, FString* OutError = nullptr);
	PICOOPENXRHANDTRACKING_API void GenerateSuggestedFeatureRules(const FPICOHandSemanticFeatures& TargetFeatures, TArray<FPICOHandSemanticFeatureRule>& OutRules, float& OutSuggestedMatchThreshold);
}
