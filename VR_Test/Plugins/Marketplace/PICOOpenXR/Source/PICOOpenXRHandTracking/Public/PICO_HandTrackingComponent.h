// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/PoseableMeshComponent.h"
#include "HeadMountedDisplayTypes.h"
#include "PICO_HandGestureRecognizerAsset.h"
#include "PICO_HandGestureSemanticRecognizerAsset.h"
#include "PICO_HandTrackingComponent.generated.h"

class UPoseAsset;
class USkinnedAsset;
struct FReferenceSkeleton;

struct FPICORuntimeGesturePose
{
	TArray<FTransform> LocalTransforms;
	TArray<FTransform> ComponentTransforms;
};

struct FPICORuntimeGestureSemanticCapture
{
	FPICOHandSemanticFeatures Features;
	TArray<FPICOHandSemanticFeatureRule> FeatureRules;
	float MatchThreshold = 0.75f;
};

struct FPICOGestureTargetPoseCache
{
	TWeakObjectPtr<const UPoseAsset> PoseAsset;
	TWeakObjectPtr<const USkinnedAsset> SkinnedAsset;
	FName PoseName = NAME_None;
	int32 PoseIndex = INDEX_NONE;
	int32 RefSkeletonBoneCount = 0;
	int32 RawPoseTransformCount = 0;
	int32 TrackCount = 0;
	int32 MatchedTrackCount = 0;
	TArray<FTransform> LocalTransforms;
	TArray<FTransform> ComponentTransforms;

	void Reset()
	{
		PoseAsset.Reset();
		SkinnedAsset.Reset();
		PoseName = NAME_None;
		PoseIndex = INDEX_NONE;
		RefSkeletonBoneCount = 0;
		RawPoseTransformCount = 0;
		TrackCount = 0;
		MatchedTrackCount = 0;
		LocalTransforms.Reset();
		ComponentTransforms.Reset();
	}
};

struct FPICOGestureSemanticFeatureCache
{
	TWeakObjectPtr<const UPoseAsset> PoseAsset;
	TWeakObjectPtr<const USkinnedAsset> SkinnedAsset;
	FName PoseName = NAME_None;
	int32 PoseIndex = INDEX_NONE;
	bool bIsValid = false;
	FPICOHandSemanticFeatures Features;

	void Reset()
	{
		PoseAsset.Reset();
		SkinnedAsset.Reset();
		PoseName = NAME_None;
		PoseIndex = INDEX_NONE;
		bIsValid = false;
		Features = FPICOHandSemanticFeatures();
	}
};

UENUM(BlueprintType)
enum class EHandTypePICO : uint8
{
	HandLeft,
	HandRight,
};

UCLASS(Blueprintable, ClassGroup = (PICO), meta = (BlueprintSpawnableComponent, DisplayName = "Hand Tracking Component PICO"))
class PICOOPENXRHANDTRACKING_API UHandTrackingComponentPICO : public UPoseableMeshComponent
{
	GENERATED_UCLASS_BODY()

public:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	virtual void OnRegister() override;
	virtual void TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

#if WITH_EDITOR
	virtual void PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent) override;
#endif

	/** Which type of the skeleton mesh, left hand or right hand. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "PICO|HandTracking")
	EHandTypePICO SkeletonMeshType;

	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "PICO|HandTracking")
	bool bUseBuiltInHandMesh;

	/** By default only updates the position of the Wrist binding bone. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "PICO|HandTracking")
	bool ApplyLocationToEveryBone;

	/** Whether to automatically hide this component based on the validity of the hand tracking data. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "PICO|HandTracking")
	bool AutoHide;

	/** Bone mapping for custom hand skeletal meshes */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "PICO|HandTracking")
	TMap<EHandKeypoint, FName> BoneMappings;

	/** Auto scale this hand component, default scale = 1.0f */
	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = "PICO|HandTracking")
	bool AutoScaleComponent;

	/**
	 * Match the current hand pose against a PoseAsset target pose.
	 * Returns true when OutScore is greater than or equal to MatchThreshold.
	 */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool MatchGesturePosePICO(UPoseAsset* TargetPoseAsset, FName PoseName, float& OutScore, float MatchThreshold = 0.75f, float AngularToleranceDeg = 35.0f, bool bIncludeWrist = false, bool bIncludePalm = false, bool bUseRuntimePose = false);

	/**
	 * Capture the current runtime hand pose into this component.
	 * Also synchronizes the runtime semantic capture with the same pose name and can optionally export both JSON payloads.
	 * Returns the stored runtime pose name, or None on failure.
	 */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	FName CaptureCurrentGesturePosePICO(FName PoseName = NAME_None, bool bExportJsonPose = false, bool bExportJsonSemantic = false);

	/** Last runtime hand pose name captured by CaptureCurrentGesturePosePICO. */
	UPROPERTY(BlueprintReadOnly, Category = "PICO|HandTracking|Gesture")
	FName LastRuntimeGesturePoseName;

	/** Last runtime hand pose JSON file exported by CaptureCurrentGesturePosePICO. */
	UPROPERTY(BlueprintReadOnly, Category = "PICO|HandTracking|Gesture")
	FString LastRuntimeGesturePoseJsonPath;

	/** Whether the last CaptureCurrentGesturePosePICO call successfully wrote a JSON file. */
	UPROPERTY(BlueprintReadOnly, Category = "PICO|HandTracking|Gesture")
	bool bLastRuntimeGesturePoseJsonSaved;

	/** Last runtime semantic capture name synchronized by CaptureCurrentGesturePosePICO. */
	UPROPERTY(BlueprintReadOnly, Category = "PICO|HandTracking|Gesture")
	FName LastRuntimeGestureSemanticName;

	/** Last runtime semantic recognizer JSON file exported during CaptureCurrentGesturePosePICO. */
	UPROPERTY(BlueprintReadOnly, Category = "PICO|HandTracking|Gesture")
	FString LastRuntimeGestureSemanticJsonPath;

	/** Whether the last semantic export triggered by CaptureCurrentGesturePosePICO successfully wrote a JSON file. */
	UPROPERTY(BlueprintReadOnly, Category = "PICO|HandTracking|Gesture")
	bool bLastRuntimeGestureSemanticJsonSaved;

	/** Returns true if the named runtime captured pose exists in this component cache. */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool GetRuntimeGestureCapturedPosePICO(FName PoseName, FString& OutJsonPath) const;

	/** Returns all runtime captured pose names currently stored in this component cache. */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	TArray<FName> GetRuntimeGestureCapturedPoseNamesPICO() const;

	/** Removes a runtime captured pose from this component cache. Optionally deletes the matching local JSON file. */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool RemoveRuntimeGestureCapturedPosePICO(FName PoseName, bool bDeleteLocalJson = false);

	/** Returns true if the named runtime captured semantic recognizer exists in this component cache. */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool GetRuntimeGestureCapturedSemanticPICO(FName PoseName, FString& OutJsonPath) const;

	/** Returns all runtime captured semantic recognizer names currently stored in this component cache. */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	TArray<FName> GetRuntimeGestureCapturedSemanticNamesPICO() const;

	/** Removes a runtime captured semantic recognizer from this component cache. Optionally deletes the matching local JSON file. */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool RemoveRuntimeGestureCapturedSemanticPICO(FName PoseName, bool bDeleteLocalJson = false);

	/**
	 * Match the current hand pose with a configurable recognizer asset.
	 * The score is normalized to 0..1, where 1 means the current pose is identical to the target under the active rules.
	 */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool MatchGestureRecognizerPICO(UPICOHandGestureRecognizerAsset* RecognizerAsset, float& OutScore);

	/**
	 * Match the current hand pose against a semantic recognizer built from reusable hand features such as curl and spread.
	 */
	UFUNCTION(BlueprintCallable, Category = "PICO|HandTracking|Gesture")
	bool MatchGestureSemanticPICO(UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, float& OutScore, bool bUseRuntimeSemantic = false, FName RuntimeSemanticName = NAME_None);
private:
	void UpdateRuntimeGestureCurrentPoseCache();
	FName CaptureCurrentGestureSemanticInternal(FName PoseName, bool bExportJsonSemantic);
	bool GetCurrentSemanticFeatures(FPICOHandSemanticFeatures& OutFeatures);
	bool GetCachedTargetSemanticFeatures(const UPoseAsset* TargetPoseAsset, FName PoseName, int32 PoseIndex, const FReferenceSkeleton& RefSkeleton, FPICOHandSemanticFeatures& OutFeatures);
	bool GetCachedTargetPoseTransforms(const UPoseAsset* TargetPoseAsset, FName PoseName, int32 PoseIndex, const FReferenceSkeleton& RefSkeleton, const TArray<FTransform>*& OutLocalTransforms, const TArray<FTransform>*& OutComponentTransforms, int32* OutRawPoseTransformCount = nullptr, int32* OutTrackCount = nullptr, int32* OutMatchedTrackCount = nullptr);
	void ResetGestureTargetPoseCache();

	bool bHandTrackingAvailable;
	bool bIsRunning;
	bool bRuntimeGestureCurrentPoseCacheValid;
	bool bRuntimeGesturePoseReceivedTrackingData;
	bool bRuntimeGestureExportWristRotationValid;
	bool bRuntimeGestureCurrentSemanticFeatureCacheValid;
	FQuat RuntimeGestureExportWristRotation;
	TArray<FTransform> RuntimeGestureCurrentPoseLocalTransforms;
	TArray<FTransform> RuntimeGestureCurrentPoseComponentTransforms;
	FPICOHandSemanticFeatures RuntimeGestureCurrentSemanticFeatures;
	TMap<FName, FPICORuntimeGesturePose> RuntimeGestureCapturedPoses;
	TMap<FName, FString> RuntimeGestureCapturedPoseJsonPaths;
	TMap<FName, FPICORuntimeGestureSemanticCapture> RuntimeGestureCapturedSemantics;
	TMap<FName, FString> RuntimeGestureCapturedSemanticJsonPaths;
	FPICOGestureTargetPoseCache GestureTargetPoseCache;
	FPICOGestureSemanticFeatureCache GestureTargetSemanticFeatureCache;

	static int HandTrackingInstanceCount;
	static bool bHandTrackingStartedByComponent;
};
