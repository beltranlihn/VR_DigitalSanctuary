// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandTrackingComponent.h"
#include "Animation/PoseAsset.h"
#include "HeadMountedDisplayFunctionLibrary.h"
#include "Engine/World.h"
#include "Engine/SkeletalMesh.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "PICO_HandTrackingFunctionLibrary.h"
#include "Serialization/JsonSerializer.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UObjectGlobals.h"

DEFINE_LOG_CATEGORY_STATIC(LogPICOHandGestureMatch, Log, All);

int UHandTrackingComponentPICO::HandTrackingInstanceCount = 0;
bool UHandTrackingComponentPICO::bHandTrackingStartedByComponent = false;

namespace
{
	USkeletalMesh* GetBuiltInHandMesh(EHandTypePICO HandType)
	{
		static TWeakObjectPtr<USkeletalMesh> LeftMesh;
		static TWeakObjectPtr<USkeletalMesh> RightMesh;

		TWeakObjectPtr<USkeletalMesh>& Cache = (HandType == EHandTypePICO::HandRight) ? RightMesh : LeftMesh;
		if (!Cache.IsValid())
		{
			const TCHAR* Path = (HandType == EHandTypePICO::HandRight)
				? TEXT("/PICOOpenXR/Meshes/Hand/Right/SM_Hand_R.SM_Hand_R")
				: TEXT("/PICOOpenXR/Meshes/Hand/Left/SM_Hand_L.SM_Hand_L");

			Cache = LoadObject<USkeletalMesh>(nullptr, Path);
		}

		return Cache.Get();
	}

	bool IsBuiltInHandMeshAsset(const USkinnedAsset* SkinnedAsset)
	{
		if (SkinnedAsset == nullptr)
		{
			return false;
		}

		return SkinnedAsset == GetBuiltInHandMesh(EHandTypePICO::HandLeft) ||
			SkinnedAsset == GetBuiltInHandMesh(EHandTypePICO::HandRight);
	}

	void ApplyBuiltInBoneMappings(EHandTypePICO HandType, TMap<EHandKeypoint, FName>& InOutMappings)
	{
		static const TCHAR* LeftBoneNames[EHandKeypointCount] = {
			TEXT("left_palm"),
			TEXT("left_wrist"),
			TEXT("left_thumb_metacarpal"),
			TEXT("left_thumb_proximal"),
			TEXT("left_thumb_distal"),
			TEXT("left_thumb_tip"),
			TEXT("left_index_metacarpal"),
			TEXT("left_index_proximal"),
			TEXT("left_index_intermediate"),
			TEXT("left_index_distal"),
			TEXT("left_index_tip"),
			TEXT("left_middle_metacarpal"),
			TEXT("left_middle_proximal"),
			TEXT("left_middle_intermediate"),
			TEXT("left_middle_distal"),
			TEXT("left_middle_tip"),
			TEXT("left_ring_metacarpal"),
			TEXT("left_ring_proximal"),
			TEXT("left_ring_intermediate"),
			TEXT("left_ring_distal"),
			TEXT("left_ring_tip"),
			TEXT("left_little_metacarpal"),
			TEXT("left_little_proximal"),
			TEXT("left_little_intermediate"),
			TEXT("left_little_distal"),
			TEXT("left_little_tip")
		};

		static const TCHAR* RightBoneNames[EHandKeypointCount] = {
			TEXT("right_palm"),
			TEXT("right_wrist"),
			TEXT("right_thumb_metacarpal"),
			TEXT("right_thumb_proximal"),
			TEXT("right_thumb_distal"),
			TEXT("right_thumb_tip"),
			TEXT("right_index_metacarpal"),
			TEXT("right_index_proximal"),
			TEXT("right_index_intermediate"),
			TEXT("right_index_distal"),
			TEXT("right_index_tip"),
			TEXT("right_middle_metacarpal"),
			TEXT("right_middle_proximal"),
			TEXT("right_middle_intermediate"),
			TEXT("right_middle_distal"),
			TEXT("right_middle_tip"),
			TEXT("right_ring_metacarpal"),
			TEXT("right_ring_proximal"),
			TEXT("right_ring_intermediate"),
			TEXT("right_ring_distal"),
			TEXT("right_ring_tip"),
			TEXT("right_little_metacarpal"),
			TEXT("right_little_proximal"),
			TEXT("right_little_intermediate"),
			TEXT("right_little_distal"),
			TEXT("right_little_tip")
		};

		const bool bRight = HandType == EHandTypePICO::HandRight;
		const TCHAR* const* DesiredBoneNames = bRight ? RightBoneNames : LeftBoneNames;

		for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
		{
			const EHandKeypoint Key = static_cast<EHandKeypoint>(KeypointIndex);
			FName& Existing = InOutMappings.FindOrAdd(Key);
			const FName LeftName(LeftBoneNames[KeypointIndex]);
			const FName RightName(RightBoneNames[KeypointIndex]);
			if (Existing.IsNone() || Existing == LeftName || Existing == RightName)
			{
				Existing = FName(DesiredBoneNames[KeypointIndex]);
			}
		}
	}

	const TCHAR* GetOpenXRJointName(EHandKeypoint Keypoint)
	{
		static const TCHAR* JointNames[EHandKeypointCount] = {
			TEXT("XR_HAND_JOINT_PALM_EXT"),
			TEXT("XR_HAND_JOINT_WRIST_EXT"),
			TEXT("XR_HAND_JOINT_THUMB_METACARPAL_EXT"),
			TEXT("XR_HAND_JOINT_THUMB_PROXIMAL_EXT"),
			TEXT("XR_HAND_JOINT_THUMB_DISTAL_EXT"),
			TEXT("XR_HAND_JOINT_THUMB_TIP_EXT"),
			TEXT("XR_HAND_JOINT_INDEX_METACARPAL_EXT"),
			TEXT("XR_HAND_JOINT_INDEX_PROXIMAL_EXT"),
			TEXT("XR_HAND_JOINT_INDEX_INTERMEDIATE_EXT"),
			TEXT("XR_HAND_JOINT_INDEX_DISTAL_EXT"),
			TEXT("XR_HAND_JOINT_INDEX_TIP_EXT"),
			TEXT("XR_HAND_JOINT_MIDDLE_METACARPAL_EXT"),
			TEXT("XR_HAND_JOINT_MIDDLE_PROXIMAL_EXT"),
			TEXT("XR_HAND_JOINT_MIDDLE_INTERMEDIATE_EXT"),
			TEXT("XR_HAND_JOINT_MIDDLE_DISTAL_EXT"),
			TEXT("XR_HAND_JOINT_MIDDLE_TIP_EXT"),
			TEXT("XR_HAND_JOINT_RING_METACARPAL_EXT"),
			TEXT("XR_HAND_JOINT_RING_PROXIMAL_EXT"),
			TEXT("XR_HAND_JOINT_RING_INTERMEDIATE_EXT"),
			TEXT("XR_HAND_JOINT_RING_DISTAL_EXT"),
			TEXT("XR_HAND_JOINT_RING_TIP_EXT"),
			TEXT("XR_HAND_JOINT_LITTLE_METACARPAL_EXT"),
			TEXT("XR_HAND_JOINT_LITTLE_PROXIMAL_EXT"),
			TEXT("XR_HAND_JOINT_LITTLE_INTERMEDIATE_EXT"),
			TEXT("XR_HAND_JOINT_LITTLE_DISTAL_EXT"),
			TEXT("XR_HAND_JOINT_LITTLE_TIP_EXT")
		};

		const int32 KeypointIndex = static_cast<int32>(Keypoint);
		return KeypointIndex >= 0 && KeypointIndex < EHandKeypointCount ? JointNames[KeypointIndex] : TEXT("XR_HAND_JOINT_UNKNOWN");
	}

	TSharedRef<FJsonObject> VectorToJsonObject(const FVector& Vector)
	{
		TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
		JsonObject->SetNumberField(TEXT("x"), Vector.X);
		JsonObject->SetNumberField(TEXT("y"), Vector.Y);
		JsonObject->SetNumberField(TEXT("z"), Vector.Z);
		return JsonObject;
	}

	TSharedRef<FJsonObject> QuatToJsonObject(const FQuat& Quat)
	{
		const FQuat NormalizedQuat = Quat.GetNormalized();
		TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
		JsonObject->SetNumberField(TEXT("x"), NormalizedQuat.X);
		JsonObject->SetNumberField(TEXT("y"), NormalizedQuat.Y);
		JsonObject->SetNumberField(TEXT("z"), NormalizedQuat.Z);
		JsonObject->SetNumberField(TEXT("w"), NormalizedQuat.W);
		return JsonObject;
	}

	TSharedRef<FJsonObject> TransformToJsonObject(const FTransform& Transform)
	{
		TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
		JsonObject->SetObjectField(TEXT("translation"), VectorToJsonObject(Transform.GetTranslation()));
		JsonObject->SetObjectField(TEXT("rotation"), QuatToJsonObject(Transform.GetRotation()));
		JsonObject->SetObjectField(TEXT("scale"), VectorToJsonObject(Transform.GetScale3D()));
		return JsonObject;
	}

	TSharedRef<FJsonObject> SemanticFeaturesToJsonObject(const FPICOHandSemanticFeatures& Features)
	{
		TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
		static const EPICOHandSemanticFeatureType FeatureTypes[] = {
			EPICOHandSemanticFeatureType::ThumbCurl,
			EPICOHandSemanticFeatureType::IndexCurl,
			EPICOHandSemanticFeatureType::MiddleCurl,
			EPICOHandSemanticFeatureType::RingCurl,
			EPICOHandSemanticFeatureType::LittleCurl,
			EPICOHandSemanticFeatureType::IndexMiddleSpread,
			EPICOHandSemanticFeatureType::MiddleRingSpread,
			EPICOHandSemanticFeatureType::RingLittleSpread,
			EPICOHandSemanticFeatureType::ThumbUpness,
			EPICOHandSemanticFeatureType::ThumbOpposition,
			EPICOHandSemanticFeatureType::PalmPitch,
			EPICOHandSemanticFeatureType::PalmRoll
		};

		for (const EPICOHandSemanticFeatureType FeatureType : FeatureTypes)
		{
			float Value = 0.0f;
			if (PICOHandGestureSemantic::GetFeatureValue(Features, FeatureType, Value))
			{
				JsonObject->SetNumberField(PICOHandGestureSemantic::GetFeatureTypeName(FeatureType), Value);
			}
		}

		return JsonObject;
	}

	void AppendSemanticFeatureRulesToJsonArray(const TArray<FPICOHandSemanticFeatureRule>& FeatureRules, TArray<TSharedPtr<FJsonValue>>& OutRuleValues)
	{
		OutRuleValues.Reserve(OutRuleValues.Num() + FeatureRules.Num());
		for (const FPICOHandSemanticFeatureRule& Rule : FeatureRules)
		{
			TSharedRef<FJsonObject> RuleObject = MakeShared<FJsonObject>();
			RuleObject->SetStringField(TEXT("feature"), PICOHandGestureSemantic::GetFeatureTypeName(Rule.Feature));
			RuleObject->SetBoolField(TEXT("enabled"), Rule.bEnabled);
			RuleObject->SetNumberField(TEXT("target_value"), Rule.TargetValue);
			RuleObject->SetNumberField(TEXT("tolerance"), FMath::Max(Rule.Tolerance, 0.001f));
			RuleObject->SetNumberField(TEXT("weight"), FMath::Max(Rule.Weight, 0.0f));
			RuleObject->SetBoolField(TEXT("required"), Rule.bRequired);
			RuleObject->SetNumberField(TEXT("min_pass_score"), FMath::Clamp(Rule.MinPassScore, 0.0f, 1.0f));
			OutRuleValues.Add(MakeShared<FJsonValueObject>(RuleObject));
		}
	}

	void ClearBuiltInBoneMappings(TMap<EHandKeypoint, FName>& InOutMappings)
	{
		static const TCHAR* LeftBoneNames[EHandKeypointCount] = {
			TEXT("left_palm"),
			TEXT("left_wrist"),
			TEXT("left_thumb_metacarpal"),
			TEXT("left_thumb_proximal"),
			TEXT("left_thumb_distal"),
			TEXT("left_thumb_tip"),
			TEXT("left_index_metacarpal"),
			TEXT("left_index_proximal"),
			TEXT("left_index_intermediate"),
			TEXT("left_index_distal"),
			TEXT("left_index_tip"),
			TEXT("left_middle_metacarpal"),
			TEXT("left_middle_proximal"),
			TEXT("left_middle_intermediate"),
			TEXT("left_middle_distal"),
			TEXT("left_middle_tip"),
			TEXT("left_ring_metacarpal"),
			TEXT("left_ring_proximal"),
			TEXT("left_ring_intermediate"),
			TEXT("left_ring_distal"),
			TEXT("left_ring_tip"),
			TEXT("left_little_metacarpal"),
			TEXT("left_little_proximal"),
			TEXT("left_little_intermediate"),
			TEXT("left_little_distal"),
			TEXT("left_little_tip")
		};

		static const TCHAR* RightBoneNames[EHandKeypointCount] = {
			TEXT("right_palm"),
			TEXT("right_wrist"),
			TEXT("right_thumb_metacarpal"),
			TEXT("right_thumb_proximal"),
			TEXT("right_thumb_distal"),
			TEXT("right_thumb_tip"),
			TEXT("right_index_metacarpal"),
			TEXT("right_index_proximal"),
			TEXT("right_index_intermediate"),
			TEXT("right_index_distal"),
			TEXT("right_index_tip"),
			TEXT("right_middle_metacarpal"),
			TEXT("right_middle_proximal"),
			TEXT("right_middle_intermediate"),
			TEXT("right_middle_distal"),
			TEXT("right_middle_tip"),
			TEXT("right_ring_metacarpal"),
			TEXT("right_ring_proximal"),
			TEXT("right_ring_intermediate"),
			TEXT("right_ring_distal"),
			TEXT("right_ring_tip"),
			TEXT("right_little_metacarpal"),
			TEXT("right_little_proximal"),
			TEXT("right_little_intermediate"),
			TEXT("right_little_distal"),
			TEXT("right_little_tip")
		};

		for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
		{
			const EHandKeypoint Key = static_cast<EHandKeypoint>(KeypointIndex);
			if (FName* Existing = InOutMappings.Find(Key))
			{
				const FName LeftName(LeftBoneNames[KeypointIndex]);
				const FName RightName(RightBoneNames[KeypointIndex]);
				if (*Existing == LeftName || *Existing == RightName)
				{
					*Existing = NAME_None;
				}
			}
		}
	}

	int32 ResolvePoseIndex(const UPoseAsset* PoseAsset, FName PoseName)
	{
		if (PoseAsset == nullptr || PoseAsset->GetNumPoses() <= 0)
		{
			return INDEX_NONE;
		}

		if (!PoseName.IsNone())
		{
			const int32 NamedPoseIndex = PoseAsset->GetPoseIndexByName(PoseName);
			if (NamedPoseIndex != INDEX_NONE)
			{
				return NamedPoseIndex;
			}
		}

		const int32 DefaultPoseIndex = PoseAsset->GetPoseIndexByName(TEXT("Pose_0"));
		return DefaultPoseIndex != INDEX_NONE ? DefaultPoseIndex : 0;
	}

	bool BuildTargetPoseTransforms(const UPoseAsset* PoseAsset, int32 PoseIndex, const FReferenceSkeleton& RefSkeleton, TArray<FTransform>& OutLocalTransforms, TArray<FTransform>& OutComponentTransforms, int32* OutRawPoseTransformCount = nullptr, int32* OutTrackCount = nullptr, int32* OutMatchedTrackCount = nullptr)
	{
		if (PoseAsset == nullptr || PoseIndex == INDEX_NONE)
		{
			return false;
		}

		TArray<FTransform> TargetInfluencedLocalTransforms;
		TArray<FPoseAssetInfluenceForPose> TargetInfluences;
		if (!PoseAsset->ConvertToFullPose(PoseIndex, TargetInfluencedLocalTransforms, TargetInfluences))
		{
			return false;
		}

		const TArray<FName>& TrackNames = PoseAsset->GetTrackNames();
		if (OutRawPoseTransformCount != nullptr)
		{
			*OutRawPoseTransformCount = TargetInfluencedLocalTransforms.Num();
		}
		if (OutTrackCount != nullptr)
		{
			*OutTrackCount = TrackNames.Num();
		}
		if (OutMatchedTrackCount != nullptr)
		{
			*OutMatchedTrackCount = 0;
		}

		const int32 NumBones = RefSkeleton.GetNum();
		OutComponentTransforms.SetNum(NumBones);
		OutLocalTransforms = RefSkeleton.GetRefBonePose();

		for (const FPoseAssetInfluenceForPose& Influence : TargetInfluences)
		{
			if (TrackNames.IsValidIndex(Influence.TrackIndex) && TargetInfluencedLocalTransforms.IsValidIndex(Influence.BoneTransformIndex))
			{
				const FName BoneName = TrackNames[Influence.TrackIndex];
				const int32 BoneIndex = RefSkeleton.FindBoneIndex(BoneName);
				if (OutLocalTransforms.IsValidIndex(BoneIndex))
				{
					OutLocalTransforms[BoneIndex] = TargetInfluencedLocalTransforms[Influence.BoneTransformIndex];
					if (OutMatchedTrackCount != nullptr)
					{
						++(*OutMatchedTrackCount);
					}
				}
			}
		}

		for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
		{
			const FTransform& LocalTransform = OutLocalTransforms[BoneIndex];
			const int32 ParentIndex = RefSkeleton.GetParentIndex(BoneIndex);
			OutComponentTransforms[BoneIndex] = ParentIndex != INDEX_NONE
				? LocalTransform * OutComponentTransforms[ParentIndex]
				: LocalTransform;
		}

		return true;
	}

	FTransform GetCurrentLocalTransform(UHandTrackingComponentPICO* Component, const FReferenceSkeleton& RefSkeleton, int32 BoneIndex, FName BoneName)
	{
		if (Component == nullptr)
		{
			return FTransform::Identity;
		}

		const FTransform CurrentComponentTransform = Component->GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace);
		const int32 ParentIndex = RefSkeleton.GetParentIndex(BoneIndex);
		if (ParentIndex == INDEX_NONE)
		{
			return CurrentComponentTransform;
		}

		const FName ParentBoneName = RefSkeleton.GetBoneName(ParentIndex);
		const FTransform ParentComponentTransform = Component->GetBoneTransformByName(ParentBoneName, EBoneSpaces::ComponentSpace);
		return CurrentComponentTransform.GetRelativeTransform(ParentComponentTransform);
	}

	float CalculateGestureRotationAngleDeg(const FQuat& CurrentRotation, const FQuat& TargetRotation)
	{
		const float Dot = FMath::Abs(CurrentRotation.GetNormalized() | TargetRotation.GetNormalized());
		return FMath::RadiansToDegrees(2.0f * FMath::Acos(FMath::Clamp(Dot, 0.0f, 1.0f)));
	}

	float CalculateRotationScore(const FQuat& CurrentRotation, const FQuat& TargetRotation, float AngularToleranceDeg)
	{
		const float SafeTolerance = FMath::Max(AngularToleranceDeg, 1.0f);
		const float AngleDeg = CalculateGestureRotationAngleDeg(CurrentRotation, TargetRotation);
		return 1.0f - FMath::Clamp(AngleDeg / SafeTolerance, 0.0f, 1.0f);
	}

	float CalculatePositionScore(const FVector& CurrentPosition, const FVector& TargetPosition, float PositionToleranceCm)
	{
		const float SafeTolerance = FMath::Max(PositionToleranceCm, 0.1f);
		const float Distance = FVector::Distance(CurrentPosition, TargetPosition);
		return 1.0f - FMath::Clamp(Distance / SafeTolerance, 0.0f, 1.0f);
	}

	float CalculateSemanticFeatureScore(float CurrentValue, float TargetValue, float Tolerance)
	{
		const float SafeTolerance = FMath::Max(Tolerance, 0.001f);
		const float NormalizedError = (CurrentValue - TargetValue) / SafeTolerance;
		return FMath::Exp(-0.5f * NormalizedError * NormalizedError);
	}
}

UHandTrackingComponentPICO::UHandTrackingComponentPICO(const FObjectInitializer& ObjectInitializer)
	:Super(ObjectInitializer)
	, SkeletonMeshType(EHandTypePICO::HandLeft)
	, bUseBuiltInHandMesh(true)
	, ApplyLocationToEveryBone(false)
	, AutoHide(false)
	, bLastRuntimeGesturePoseJsonSaved(false)
	, bLastRuntimeGestureSemanticJsonSaved(false)
	, bHandTrackingAvailable(false)
	, bIsRunning(false)
	, bRuntimeGestureCurrentPoseCacheValid(false)
	, bRuntimeGesturePoseReceivedTrackingData(false)
	, bRuntimeGestureExportWristRotationValid(false)
	, bRuntimeGestureCurrentSemanticFeatureCacheValid(false)
	, RuntimeGestureExportWristRotation(FQuat::Identity)
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.bStartWithTickEnabled = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;

	for (int KeypointIndex = 0; KeypointIndex < EHandKeypointCount; KeypointIndex++)
	{
		BoneMappings.Add(EHandKeypoint(KeypointIndex), NAME_None);
	}

	if (bUseBuiltInHandMesh)
	{
		ApplyBuiltInBoneMappings(SkeletonMeshType, BoneMappings);

		if (GetSkinnedAsset() == nullptr)
		{
			static ConstructorHelpers::FObjectFinder<USkeletalMesh> LeftMeshFinder(TEXT("/PICOOpenXR/Meshes/Hand/Left/SM_Hand_L.SM_Hand_L"));
			static ConstructorHelpers::FObjectFinder<USkeletalMesh> RightMeshFinder(TEXT("/PICOOpenXR/Meshes/Hand/Right/SM_Hand_R.SM_Hand_R"));

			USkeletalMesh* DesiredMesh = (SkeletonMeshType == EHandTypePICO::HandRight)
				? (RightMeshFinder.Succeeded() ? RightMeshFinder.Object : nullptr)
				: (LeftMeshFinder.Succeeded() ? LeftMeshFinder.Object : nullptr);

			if (DesiredMesh != nullptr)
			{
				SetSkinnedAsset(DesiredMesh);
			}
		}
	}
}

void UHandTrackingComponentPICO::OnRegister()
{
	Super::OnRegister();
	ResetGestureTargetPoseCache();

	if (!bUseBuiltInHandMesh)
	{
		return;
	}

	USkinnedAsset* CurrentAsset = GetSkinnedAsset();
	USkeletalMesh* DesiredMesh = GetBuiltInHandMesh(SkeletonMeshType);
	if (DesiredMesh != nullptr && (CurrentAsset == nullptr || IsBuiltInHandMeshAsset(CurrentAsset)))
	{
		SetSkinnedAssetAndUpdate(DesiredMesh);
	}

	ApplyBuiltInBoneMappings(SkeletonMeshType, BoneMappings);
}

#if WITH_EDITOR
void UHandTrackingComponentPICO::PostEditChangeProperty(FPropertyChangedEvent& PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);

	const FName PropertyName = PropertyChangedEvent.GetPropertyName();
	if (PropertyName != GET_MEMBER_NAME_CHECKED(UHandTrackingComponentPICO, bUseBuiltInHandMesh) &&
		PropertyName != GET_MEMBER_NAME_CHECKED(UHandTrackingComponentPICO, SkeletonMeshType))
	{
		return;
	}

	if (bUseBuiltInHandMesh)
	{
		USkinnedAsset* CurrentAsset = GetSkinnedAsset();
		USkeletalMesh* DesiredMesh = GetBuiltInHandMesh(SkeletonMeshType);
		if (DesiredMesh != nullptr && (CurrentAsset == nullptr || IsBuiltInHandMeshAsset(CurrentAsset)))
		{
			SetSkinnedAssetAndUpdate(DesiredMesh);
		}
		ApplyBuiltInBoneMappings(SkeletonMeshType, BoneMappings);
	}
	else
	{
		if (IsBuiltInHandMeshAsset(GetSkinnedAsset()))
		{
			SetSkinnedAssetAndUpdate(nullptr);
		}
		ClearBuiltInBoneMappings(BoneMappings);
	}

	ResetGestureTargetPoseCache();
	MarkRenderStateDirty();
}
#endif

void UHandTrackingComponentPICO::BeginPlay()
{
	Super::BeginPlay();
	if (UHandTrackingFunctionLibraryPICO::IsHandTrackingSupportPICO())
	{
		bHandTrackingAvailable = true;
	}
	if (AutoHide)
	{
		SetHiddenInGame(true, true);
	}
	bRuntimeGestureCurrentPoseCacheValid = false;
	bRuntimeGesturePoseReceivedTrackingData = false;
	bRuntimeGestureExportWristRotationValid = false;
	bRuntimeGestureCurrentSemanticFeatureCacheValid = false;
	RuntimeGestureExportWristRotation = FQuat::Identity;
	RuntimeGestureCurrentPoseLocalTransforms.Reset();
	RuntimeGestureCurrentPoseComponentTransforms.Reset();
	RuntimeGestureCurrentSemanticFeatures = FPICOHandSemanticFeatures();
	RuntimeGestureCapturedPoses.Reset();
	RuntimeGestureCapturedPoseJsonPaths.Reset();
	RuntimeGestureCapturedSemantics.Reset();
	RuntimeGestureCapturedSemanticJsonPaths.Reset();
	ResetGestureTargetPoseCache();
	LastRuntimeGesturePoseName = NAME_None;
	LastRuntimeGesturePoseJsonPath.Reset();
	bLastRuntimeGesturePoseJsonSaved = false;
	LastRuntimeGestureSemanticName = NAME_None;
	LastRuntimeGestureSemanticJsonPath.Reset();
	bLastRuntimeGestureSemanticJsonSaved = false;
	++HandTrackingInstanceCount;
}

void UHandTrackingComponentPICO::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
	HandTrackingInstanceCount = FMath::Max(HandTrackingInstanceCount - 1, 0);
	if (HandTrackingInstanceCount == 0 && bHandTrackingStartedByComponent)
	{
		UHandTrackingFunctionLibraryPICO::StopHandTrackingPICO();
		bHandTrackingStartedByComponent = false;
	}
}

void UHandTrackingComponentPICO::UpdateRuntimeGestureCurrentPoseCache()
{
	bRuntimeGestureCurrentPoseCacheValid = false;
	bRuntimeGestureCurrentSemanticFeatureCacheValid = false;
	RuntimeGestureCurrentPoseLocalTransforms.Reset();
	RuntimeGestureCurrentPoseComponentTransforms.Reset();
	RuntimeGestureCurrentSemanticFeatures = FPICOHandSemanticFeatures();

	if (GetSkinnedAsset() == nullptr)
	{
		return;
	}

	const FReferenceSkeleton& RefSkeleton = GetSkinnedAsset()->GetRefSkeleton();
	const int32 NumBones = RefSkeleton.GetNum();
	RuntimeGestureCurrentPoseLocalTransforms.SetNum(NumBones);
	RuntimeGestureCurrentPoseComponentTransforms.SetNum(NumBones);

	for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
	{
		const FName BoneName = RefSkeleton.GetBoneName(BoneIndex);
		RuntimeGestureCurrentPoseComponentTransforms[BoneIndex] = GetBoneTransformByName(BoneName, EBoneSpaces::ComponentSpace);
		RuntimeGestureCurrentPoseLocalTransforms[BoneIndex] = GetCurrentLocalTransform(this, RefSkeleton, BoneIndex, BoneName);
	}

	const FName* WristBoneName = BoneMappings.Find(EHandKeypoint::Wrist);
	const int32 WristBoneIndex = WristBoneName != nullptr && !WristBoneName->IsNone()
		? RefSkeleton.FindBoneIndex(*WristBoneName)
		: INDEX_NONE;
	if (bRuntimeGestureExportWristRotationValid && RuntimeGestureCurrentPoseLocalTransforms.IsValidIndex(WristBoneIndex))
	{
		// Wrist is the first runtime pose bone under the skeleton root, so bake the tracked wrist
		// orientation into the exported wrist local pose to preserve whole-hand orientation after JSON import.
		RuntimeGestureCurrentPoseLocalTransforms[WristBoneIndex].SetRotation(RuntimeGestureExportWristRotation.GetNormalized());
		for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
		{
			const int32 ParentIndex = RefSkeleton.GetParentIndex(BoneIndex);
			RuntimeGestureCurrentPoseComponentTransforms[BoneIndex] = ParentIndex != INDEX_NONE
				? RuntimeGestureCurrentPoseLocalTransforms[BoneIndex] * RuntimeGestureCurrentPoseComponentTransforms[ParentIndex]
				: RuntimeGestureCurrentPoseLocalTransforms[BoneIndex];
		}
	}

	bRuntimeGestureCurrentPoseCacheValid = true;
}

void UHandTrackingComponentPICO::ResetGestureTargetPoseCache()
{
	GestureTargetPoseCache.Reset();
	GestureTargetSemanticFeatureCache.Reset();
}

bool UHandTrackingComponentPICO::GetCurrentSemanticFeatures(FPICOHandSemanticFeatures& OutFeatures)
{
	OutFeatures = FPICOHandSemanticFeatures();

	if (GetSkinnedAsset() == nullptr)
	{
		return false;
	}

	if (!bRuntimeGestureCurrentPoseCacheValid)
	{
		UpdateRuntimeGestureCurrentPoseCache();
	}

	if (!bRuntimeGestureCurrentPoseCacheValid)
	{
		return false;
	}

	if (!bRuntimeGestureCurrentSemanticFeatureCacheValid)
	{
		FString SemanticError;
		if (!PICOHandGestureSemantic::ExtractSemanticFeatures(
				SkeletonMeshType == EHandTypePICO::HandRight,
				GetSkinnedAsset()->GetRefSkeleton(),
				BoneMappings,
				RuntimeGestureCurrentPoseLocalTransforms,
				RuntimeGestureCurrentPoseComponentTransforms,
				RuntimeGestureCurrentSemanticFeatures,
				&SemanticError))
		{
			UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: current feature extraction error: %s"), *SemanticError);
			return false;
		}

		bRuntimeGestureCurrentSemanticFeatureCacheValid = true;
	}

	OutFeatures = RuntimeGestureCurrentSemanticFeatures;
	return true;
}

bool UHandTrackingComponentPICO::GetCachedTargetPoseTransforms(const UPoseAsset* TargetPoseAsset, FName PoseName, int32 PoseIndex, const FReferenceSkeleton& RefSkeleton, const TArray<FTransform>*& OutLocalTransforms, const TArray<FTransform>*& OutComponentTransforms, int32* OutRawPoseTransformCount, int32* OutTrackCount, int32* OutMatchedTrackCount)
{
	OutLocalTransforms = nullptr;
	OutComponentTransforms = nullptr;

	if (TargetPoseAsset == nullptr || PoseIndex == INDEX_NONE || GetSkinnedAsset() == nullptr)
	{
		return false;
	}

	const int32 RefSkeletonBoneCount = RefSkeleton.GetNum();
	const bool bCacheValid =
		GestureTargetPoseCache.PoseAsset.Get() == TargetPoseAsset &&
		GestureTargetPoseCache.SkinnedAsset.Get() == GetSkinnedAsset() &&
		GestureTargetPoseCache.PoseName == PoseName &&
		GestureTargetPoseCache.PoseIndex == PoseIndex &&
		GestureTargetPoseCache.RefSkeletonBoneCount == RefSkeletonBoneCount &&
		GestureTargetPoseCache.LocalTransforms.Num() == RefSkeletonBoneCount &&
		GestureTargetPoseCache.ComponentTransforms.Num() == RefSkeletonBoneCount;

	if (!bCacheValid)
	{
		GestureTargetPoseCache.Reset();
		GestureTargetPoseCache.PoseAsset = TargetPoseAsset;
		GestureTargetPoseCache.SkinnedAsset = GetSkinnedAsset();
		GestureTargetPoseCache.PoseName = PoseName;
		GestureTargetPoseCache.PoseIndex = PoseIndex;
		GestureTargetPoseCache.RefSkeletonBoneCount = RefSkeletonBoneCount;

		if (!BuildTargetPoseTransforms(
			TargetPoseAsset,
			PoseIndex,
			RefSkeleton,
			GestureTargetPoseCache.LocalTransforms,
			GestureTargetPoseCache.ComponentTransforms,
			&GestureTargetPoseCache.RawPoseTransformCount,
			&GestureTargetPoseCache.TrackCount,
			&GestureTargetPoseCache.MatchedTrackCount))
		{
			GestureTargetPoseCache.Reset();
			return false;
		}
	}

	OutLocalTransforms = &GestureTargetPoseCache.LocalTransforms;
	OutComponentTransforms = &GestureTargetPoseCache.ComponentTransforms;
	if (OutRawPoseTransformCount != nullptr)
	{
		*OutRawPoseTransformCount = GestureTargetPoseCache.RawPoseTransformCount;
	}
	if (OutTrackCount != nullptr)
	{
		*OutTrackCount = GestureTargetPoseCache.TrackCount;
	}
	if (OutMatchedTrackCount != nullptr)
	{
		*OutMatchedTrackCount = GestureTargetPoseCache.MatchedTrackCount;
	}
	return true;
}

bool UHandTrackingComponentPICO::GetCachedTargetSemanticFeatures(const UPoseAsset* TargetPoseAsset, FName PoseName, int32 PoseIndex, const FReferenceSkeleton& RefSkeleton, FPICOHandSemanticFeatures& OutFeatures)
{
	OutFeatures = FPICOHandSemanticFeatures();

	const bool bCacheValid =
		GestureTargetSemanticFeatureCache.bIsValid &&
		GestureTargetSemanticFeatureCache.PoseAsset.Get() == TargetPoseAsset &&
		GestureTargetSemanticFeatureCache.SkinnedAsset.Get() == GetSkinnedAsset() &&
		GestureTargetSemanticFeatureCache.PoseName == PoseName &&
		GestureTargetSemanticFeatureCache.PoseIndex == PoseIndex;

	if (!bCacheValid)
	{
		const TArray<FTransform>* TargetLocalTransforms = nullptr;
		const TArray<FTransform>* TargetComponentTransforms = nullptr;
		if (!GetCachedTargetPoseTransforms(TargetPoseAsset, PoseName, PoseIndex, RefSkeleton, TargetLocalTransforms, TargetComponentTransforms))
		{
			return false;
		}

		FPICOHandSemanticFeatures ExtractedFeatures;
		FString SemanticError;
		if (!PICOHandGestureSemantic::ExtractSemanticFeatures(
				SkeletonMeshType == EHandTypePICO::HandRight,
				RefSkeleton,
				BoneMappings,
				*TargetLocalTransforms,
				*TargetComponentTransforms,
				ExtractedFeatures,
				&SemanticError))
		{
			UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: target feature extraction error: %s"), *SemanticError);
			return false;
		}

		GestureTargetSemanticFeatureCache.Reset();
		GestureTargetSemanticFeatureCache.PoseAsset = TargetPoseAsset;
		GestureTargetSemanticFeatureCache.SkinnedAsset = GetSkinnedAsset();
		GestureTargetSemanticFeatureCache.PoseName = PoseName;
		GestureTargetSemanticFeatureCache.PoseIndex = PoseIndex;
		GestureTargetSemanticFeatureCache.bIsValid = true;
		GestureTargetSemanticFeatureCache.Features = ExtractedFeatures;
	}

	OutFeatures = GestureTargetSemanticFeatureCache.Features;
	return true;
}

FName UHandTrackingComponentPICO::CaptureCurrentGesturePosePICO(FName PoseName, bool bExportJsonPose, bool bExportJsonSemantic)
{
	LastRuntimeGesturePoseJsonPath.Reset();
	bLastRuntimeGesturePoseJsonSaved = false;
	if (GetSkinnedAsset() == nullptr)
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGesturePosePICO failed: SkinnedAsset is null"));
		return NAME_None;
	}

	if (!bRuntimeGesturePoseReceivedTrackingData)
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGesturePosePICO failed: no valid hand tracking pose has been received"));
		return NAME_None;
	}

	UpdateRuntimeGestureCurrentPoseCache();
	if (!bRuntimeGestureCurrentPoseCacheValid)
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGesturePosePICO failed: current runtime pose cache is invalid"));
		return NAME_None;
	}

	const FReferenceSkeleton& RefSkeleton = GetSkinnedAsset()->GetRefSkeleton();
	const FString HandName = SkeletonMeshType == EHandTypePICO::HandRight ? TEXT("Right") : TEXT("Left");
	const FName EffectivePoseName = PoseName.IsNone()
		? FName(*FString::Printf(TEXT("RuntimeCapture_%s"), *HandName))
		: PoseName;
	const FString EffectivePoseNameString = EffectivePoseName.ToString();
	const FString SafePoseName = FPaths::MakeValidFileName(EffectivePoseNameString);

	FPICORuntimeGesturePose CapturedPose;
	CapturedPose.LocalTransforms = RuntimeGestureCurrentPoseLocalTransforms;
	CapturedPose.ComponentTransforms = RuntimeGestureCurrentPoseComponentTransforms;
	RuntimeGestureCapturedPoses.Add(EffectivePoseName, MoveTemp(CapturedPose));
	RuntimeGestureCapturedPoseJsonPaths.Remove(EffectivePoseName);
	LastRuntimeGesturePoseName = EffectivePoseName;
	CaptureCurrentGestureSemanticInternal(EffectivePoseName, bExportJsonSemantic);

	if (!bExportJsonPose)
	{
		UE_LOG(LogPICOHandGestureMatch, Log, TEXT("CaptureCurrentGesturePosePICO: Captured PoseName=%s ExportJson=0"),
			*EffectivePoseNameString);
		return EffectivePoseName;
	}

	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("pose_name"), EffectivePoseNameString);
	TArray<TSharedPtr<FJsonValue>> JointValues;

	if (const FName* WristBoneName = BoneMappings.Find(EHandKeypoint::Wrist))
	{
		const int32 WristBoneIndex = !WristBoneName->IsNone() ? RefSkeleton.FindBoneIndex(*WristBoneName) : INDEX_NONE;
		if (RuntimeGestureCurrentPoseComponentTransforms.IsValidIndex(WristBoneIndex))
		{
			TSharedRef<FJsonObject> WristRelativePoseObject = MakeShared<FJsonObject>();
			WristRelativePoseObject->SetStringField(TEXT("xr_joint"), GetOpenXRJointName(EHandKeypoint::Wrist));
			WristRelativePoseObject->SetStringField(TEXT("bone_name"), WristBoneName->ToString());
			WristRelativePoseObject->SetStringField(TEXT("space"), TEXT("component"));
			WristRelativePoseObject->SetObjectField(TEXT("transform"), TransformToJsonObject(RuntimeGestureCurrentPoseComponentTransforms[WristBoneIndex]));
			RootObject->SetObjectField(TEXT("wrist_relative_pose"), WristRelativePoseObject);
		}
	}

	for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
	{
		const EHandKeypoint Keypoint = static_cast<EHandKeypoint>(KeypointIndex);
		const FName* BoneName = BoneMappings.Find(Keypoint);
		if (BoneName == nullptr || BoneName->IsNone())
		{
			UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGesturePosePICO JSON export failed: missing bone mapping for keypoint %d"), KeypointIndex);
			return EffectivePoseName;
		}

		const int32 BoneIndex = RefSkeleton.FindBoneIndex(*BoneName);
		if (!RuntimeGestureCurrentPoseLocalTransforms.IsValidIndex(BoneIndex))
		{
			UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGesturePosePICO JSON export failed: missing bone %s"), *BoneName->ToString());
			return EffectivePoseName;
		}

		TSharedRef<FJsonObject> JointObject = MakeShared<FJsonObject>();
		JointObject->SetStringField(TEXT("xr_joint"), GetOpenXRJointName(Keypoint));
		JointObject->SetStringField(TEXT("bone_name"), BoneName->ToString());
		JointObject->SetObjectField(TEXT("transform"), TransformToJsonObject(RuntimeGestureCurrentPoseLocalTransforms[BoneIndex]));
		JointValues.Add(MakeShared<FJsonValueObject>(JointObject));
	}

	RootObject->SetArrayField(TEXT("joints"), JointValues);

	FString JsonString;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	if (!FJsonSerializer::Serialize(RootObject, Writer))
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGesturePosePICO JSON export failed: serialize failed"));
		return EffectivePoseName;
	}

	const FString OutputDirectory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("PICOOpenXR/HandGestureCaptures"));
	IFileManager::Get().MakeDirectory(*OutputDirectory, true);
	const FString OutputFilename = OutputDirectory / FString::Printf(TEXT("PICO_%s_OpenXRHandPose.json"), *SafePoseName);
	const bool bSaved = FFileHelper::SaveStringToFile(JsonString, *OutputFilename);
	bLastRuntimeGesturePoseJsonSaved = bSaved;
	if (bSaved)
	{
		LastRuntimeGesturePoseJsonPath = OutputFilename;
		RuntimeGestureCapturedPoseJsonPaths.Add(EffectivePoseName, LastRuntimeGesturePoseJsonPath);
	}
	UE_LOG(LogPICOHandGestureMatch, Log, TEXT("CaptureCurrentGesturePosePICO: Captured PoseName=%s ExportJson=1 Saved=%d Joints=%d Path=%s"),
		*EffectivePoseNameString,
		bSaved ? 1 : 0,
		JointValues.Num(),
		*OutputFilename);
	return EffectivePoseName;
}

FName UHandTrackingComponentPICO::CaptureCurrentGestureSemanticInternal(FName PoseName, bool bExportJsonSemantic)
{
	LastRuntimeGestureSemanticJsonPath.Reset();
	bLastRuntimeGestureSemanticJsonSaved = false;

	if (GetSkinnedAsset() == nullptr)
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGestureSemanticInternal failed: SkinnedAsset is null"));
		return NAME_None;
	}

	if (!bRuntimeGesturePoseReceivedTrackingData)
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGestureSemanticInternal failed: no valid hand tracking pose has been received"));
		return NAME_None;
	}

	FPICOHandSemanticFeatures CurrentFeatures;
	if (!GetCurrentSemanticFeatures(CurrentFeatures))
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGestureSemanticInternal failed: current runtime semantic feature cache is invalid"));
		return NAME_None;
	}

	const FString HandName = SkeletonMeshType == EHandTypePICO::HandRight ? TEXT("Right") : TEXT("Left");
	const FName EffectivePoseName = PoseName.IsNone()
		? FName(*FString::Printf(TEXT("RuntimeCapture_%s"), *HandName))
		: PoseName;
	const FString EffectivePoseNameString = EffectivePoseName.ToString();
	const FString SafePoseName = FPaths::MakeValidFileName(EffectivePoseNameString);

	FPICORuntimeGestureSemanticCapture CapturedSemantic;
	CapturedSemantic.Features = CurrentFeatures;
	PICOHandGestureSemantic::GenerateSuggestedFeatureRules(CapturedSemantic.Features, CapturedSemantic.FeatureRules, CapturedSemantic.MatchThreshold);
	RuntimeGestureCapturedSemantics.Add(EffectivePoseName, MoveTemp(CapturedSemantic));
	RuntimeGestureCapturedSemanticJsonPaths.Remove(EffectivePoseName);
	LastRuntimeGestureSemanticName = EffectivePoseName;

	if (!bExportJsonSemantic)
	{
		UE_LOG(LogPICOHandGestureMatch, Log, TEXT("CaptureCurrentGestureSemanticInternal: Captured PoseName=%s ExportJson=0"),
			*EffectivePoseNameString);
		return EffectivePoseName;
	}

	const FPICORuntimeGestureSemanticCapture* StoredSemantic = RuntimeGestureCapturedSemantics.Find(EffectivePoseName);
	if (StoredSemantic == nullptr)
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGestureSemanticInternal failed: semantic capture %s was not stored"), *EffectivePoseNameString);
		return NAME_None;
	}

	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("schema"), TEXT("PICOOpenXR.HandGestureSemanticRecognizer"));
	RootObject->SetNumberField(TEXT("version"), 1);
	RootObject->SetStringField(TEXT("capture_source"), TEXT("runtime"));
	RootObject->SetNumberField(TEXT("match_threshold"), FMath::Clamp(StoredSemantic->MatchThreshold, 0.0f, 1.0f));

	TSharedRef<FJsonObject> TargetPoseObject = MakeShared<FJsonObject>();
	TargetPoseObject->SetStringField(TEXT("pose_asset"), FString::Printf(TEXT("PICO_%s_OpenXRHandPose"), *SafePoseName));
	TargetPoseObject->SetStringField(TEXT("pose_name"), EffectivePoseNameString);
	RootObject->SetObjectField(TEXT("target_pose"), TargetPoseObject);
	RootObject->SetObjectField(TEXT("captured_features"), SemanticFeaturesToJsonObject(StoredSemantic->Features));

	TArray<TSharedPtr<FJsonValue>> RuleValues;
	AppendSemanticFeatureRulesToJsonArray(StoredSemantic->FeatureRules, RuleValues);
	RootObject->SetArrayField(TEXT("feature_rules"), RuleValues);

	FString JsonString;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&JsonString);
	if (!FJsonSerializer::Serialize(RootObject, Writer))
	{
		UE_LOG(LogPICOHandGestureMatch, Warning, TEXT("CaptureCurrentGestureSemanticInternal JSON export failed: serialize failed"));
		return EffectivePoseName;
	}

	const FString OutputDirectory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("PICOOpenXR/HandGestureCaptures"));
	IFileManager::Get().MakeDirectory(*OutputDirectory, true);
	const FString OutputFilename = OutputDirectory / FString::Printf(TEXT("PICO_%s_SemanticRecognizer.json"), *SafePoseName);
	const bool bSaved = FFileHelper::SaveStringToFile(JsonString, *OutputFilename);
	bLastRuntimeGestureSemanticJsonSaved = bSaved;
	if (bSaved)
	{
		LastRuntimeGestureSemanticJsonPath = OutputFilename;
		RuntimeGestureCapturedSemanticJsonPaths.Add(EffectivePoseName, LastRuntimeGestureSemanticJsonPath);
	}

	UE_LOG(LogPICOHandGestureMatch, Log, TEXT("CaptureCurrentGestureSemanticInternal: Captured PoseName=%s ExportJson=1 Saved=%d Rules=%d Path=%s"),
		*EffectivePoseNameString,
		bSaved ? 1 : 0,
		StoredSemantic->FeatureRules.Num(),
		*OutputFilename);
	return EffectivePoseName;
}

bool UHandTrackingComponentPICO::GetRuntimeGestureCapturedPosePICO(FName PoseName, FString& OutJsonPath) const
{
	OutJsonPath.Reset();
	if (PoseName.IsNone() || !RuntimeGestureCapturedPoses.Contains(PoseName))
	{
		return false;
	}

	if (const FString* JsonPath = RuntimeGestureCapturedPoseJsonPaths.Find(PoseName))
	{
		OutJsonPath = *JsonPath;
	}
	return true;
}

TArray<FName> UHandTrackingComponentPICO::GetRuntimeGestureCapturedPoseNamesPICO() const
{
	TArray<FName> PoseNames;
	RuntimeGestureCapturedPoses.GetKeys(PoseNames);
	return PoseNames;
}

bool UHandTrackingComponentPICO::RemoveRuntimeGestureCapturedPosePICO(FName PoseName, bool bDeleteLocalJson)
{
	if (PoseName.IsNone() || RuntimeGestureCapturedPoses.Remove(PoseName) <= 0)
	{
		return false;
	}

	FString JsonPath;
	if (const FString* CachedJsonPath = RuntimeGestureCapturedPoseJsonPaths.Find(PoseName))
	{
		JsonPath = *CachedJsonPath;
	}
	else if (bDeleteLocalJson)
	{
		const FString OutputDirectory = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("PICOOpenXR/HandGestureCaptures"));
		const FString SafePoseName = FPaths::MakeValidFileName(PoseName.ToString());
		JsonPath = OutputDirectory / FString::Printf(TEXT("PICO_%s_OpenXRHandPose.json"), *SafePoseName);
	}

	RuntimeGestureCapturedPoseJsonPaths.Remove(PoseName);
	if (LastRuntimeGesturePoseName == PoseName)
	{
		LastRuntimeGesturePoseName = NAME_None;
		LastRuntimeGesturePoseJsonPath.Reset();
		bLastRuntimeGesturePoseJsonSaved = false;
	}

	if (bDeleteLocalJson && !JsonPath.IsEmpty() && FPaths::FileExists(JsonPath))
	{
		const bool bDeleted = IFileManager::Get().Delete(*JsonPath, false, true);
		UE_LOG(LogPICOHandGestureMatch, Log, TEXT("RemoveRuntimeGestureCapturedPosePICO: PoseName=%s DeleteJson=1 Deleted=%d Path=%s"),
			*PoseName.ToString(),
			bDeleted ? 1 : 0,
			*JsonPath);
	}
	else
	{
		UE_LOG(LogPICOHandGestureMatch, Log, TEXT("RemoveRuntimeGestureCapturedPosePICO: PoseName=%s DeleteJson=%d Path=%s"),
			*PoseName.ToString(),
			bDeleteLocalJson ? 1 : 0,
			*JsonPath);
	}

	return true;
}

bool UHandTrackingComponentPICO::GetRuntimeGestureCapturedSemanticPICO(FName PoseName, FString& OutJsonPath) const
{
	const FName EffectivePoseName = PoseName.IsNone() ? LastRuntimeGestureSemanticName : PoseName;
	OutJsonPath.Reset();

	if (!RuntimeGestureCapturedSemantics.Contains(EffectivePoseName))
	{
		return false;
	}

	if (const FString* ExistingPath = RuntimeGestureCapturedSemanticJsonPaths.Find(EffectivePoseName))
	{
		OutJsonPath = *ExistingPath;
	}

	return true;
}

TArray<FName> UHandTrackingComponentPICO::GetRuntimeGestureCapturedSemanticNamesPICO() const
{
	TArray<FName> Names;
	RuntimeGestureCapturedSemantics.GetKeys(Names);
	Names.Sort(FNameLexicalLess());
	return Names;
}

bool UHandTrackingComponentPICO::RemoveRuntimeGestureCapturedSemanticPICO(FName PoseName, bool bDeleteLocalJson)
{
	const FName EffectivePoseName = PoseName.IsNone() ? LastRuntimeGestureSemanticName : PoseName;
	if (EffectivePoseName.IsNone())
	{
		return false;
	}

	if (!RuntimeGestureCapturedSemantics.Remove(EffectivePoseName))
	{
	    return false;
	}

	FString JsonPath;
	if (const FString* ExistingPath = RuntimeGestureCapturedSemanticJsonPaths.Find(EffectivePoseName))
	{
		JsonPath = *ExistingPath;
	}
	else
	{
		const FString SafePoseName = FPaths::MakeValidFileName(EffectivePoseName.ToString());
		JsonPath = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("PICOOpenXR/HandGestureCaptures")) / FString::Printf(TEXT("PICO_%s_SemanticRecognizer.json"), *SafePoseName);
	}

	RuntimeGestureCapturedSemanticJsonPaths.Remove(EffectivePoseName);
	if (LastRuntimeGestureSemanticName == EffectivePoseName)
	{
		LastRuntimeGestureSemanticName = NAME_None;
		LastRuntimeGestureSemanticJsonPath.Reset();
		bLastRuntimeGestureSemanticJsonSaved = false;
	}

	if (bDeleteLocalJson && !JsonPath.IsEmpty() && FPaths::FileExists(JsonPath))
	{
		const bool bDeleted = IFileManager::Get().Delete(*JsonPath, false, true);
		UE_LOG(LogPICOHandGestureMatch, Log, TEXT("RemoveRuntimeGestureCapturedSemanticPICO: PoseName=%s DeleteJson=1 Deleted=%d Path=%s"),
			*EffectivePoseName.ToString(),
			bDeleted ? 1 : 0,
			*JsonPath);
	}
	else
	{
		UE_LOG(LogPICOHandGestureMatch, Log, TEXT("RemoveRuntimeGestureCapturedSemanticPICO: PoseName=%s DeleteJson=%d Path=%s"),
			*EffectivePoseName.ToString(),
			bDeleteLocalJson ? 1 : 0,
			*JsonPath);
	}

	return true;
}

void UHandTrackingComponentPICO::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	bool bHidden = true;
	bRuntimeGestureExportWristRotationValid = false;
	RuntimeGestureExportWristRotation = FQuat::Identity;
	if (GetSkinnedAsset())
	{
		FXRHandTrackingState Data;
		UHeadMountedDisplayFunctionLibrary::GetHandTrackingState(this, EXRSpaceType::UnrealWorldSpace, EControllerHand(SkeletonMeshType), Data);
		if (Data.bValid)
		{
			bHidden = false;
			for (auto& BoneMapping : BoneMappings)
			{
				const auto& HandKeypoint = BoneMapping.Key;
				const auto& BoneName = BoneMapping.Value;
				int32 BoneIndex = GetSkinnedAsset()->GetRefSkeleton().FindBoneIndex(BoneName);
				if (BoneIndex >= 0)
				{
					if (Data.HandKeyLocations.IsValidIndex((uint8)HandKeypoint))
					{
						const FQuat& WorldRotation = Data.HandKeyRotations[(uint8)HandKeypoint];
						const FVector& WorldLocation = Data.HandKeyLocations[(uint8)HandKeypoint];

						SetBoneRotationByName(BoneName, WorldRotation.Rotator(), EBoneSpaces::WorldSpace);

						if (HandKeypoint == EHandKeypoint::Wrist || ApplyLocationToEveryBone)
						{
							SetBoneLocationByName(BoneName, WorldLocation, EBoneSpaces::WorldSpace);
						}

						if (HandKeypoint == EHandKeypoint::Wrist)
						{
							RuntimeGestureExportWristRotation = WorldRotation.GetNormalized();
							bRuntimeGestureExportWristRotationValid = true;
							this->SetWorldLocation(WorldLocation);
							this->SetWorldRotation(WorldRotation);
						}

						if (AutoScaleComponent)
						{
							float Scale = 1.0f;
							UHandTrackingFunctionLibraryPICO::GetHandTrackingMeshScalePICO(EControllerHand(SkeletonMeshType), Scale);
							this->SetRelativeScale3D(FVector(Scale));
						}
					}
				}
			}
		}
		else if (bHandTrackingAvailable)
		{
			if (!bIsRunning)
			{
				if (UHandTrackingFunctionLibraryPICO::StartHandTrackingPICO())
				{
					bHandTrackingStartedByComponent = true;
				}
			}

			bIsRunning = UHandTrackingFunctionLibraryPICO::IsHandTrackingRunningPICO();

			// Fallback: use UHandTrackingFunctionLibraryPICO when GetMotionControllerData returns invalid data
			TArray<FVector> OutPositions;
			TArray<FQuat> OutRotations;
			TArray<float> OutRadii;
			TArray<FVector> LinearVelocity;
			TArray<FVector> AngularVelocity;
			float Scale = 1.0f;
			if (bIsRunning && UHandTrackingFunctionLibraryPICO::UpdateHandTrackingDataPICO() && UHandTrackingFunctionLibraryPICO::GetHandTrackingDataPICO(EControllerHand(SkeletonMeshType), OutPositions, OutRotations, OutRadii, LinearVelocity, AngularVelocity, Scale))
			{
				bHidden = false;
				for (auto& BoneMapping : BoneMappings)
				{
					const auto& HandKeypoint = BoneMapping.Key;
					const auto& BoneName = BoneMapping.Value;
					int32 BoneIndex = GetSkinnedAsset()->GetRefSkeleton().FindBoneIndex(BoneName);
					if (BoneIndex >= 0)
					{
						uint8 KeypointIndex = (uint8)HandKeypoint;
						if (OutPositions.IsValidIndex(KeypointIndex) && OutRotations.IsValidIndex(KeypointIndex))
						{
							const FQuat& WorldRotation = OutRotations[KeypointIndex];
							const FVector& WorldLocation = OutPositions[KeypointIndex];

							SetBoneRotationByName(BoneName, WorldRotation.Rotator(), EBoneSpaces::WorldSpace);

							if (HandKeypoint == EHandKeypoint::Wrist || ApplyLocationToEveryBone)
							{
								SetBoneLocationByName(BoneName, WorldLocation, EBoneSpaces::WorldSpace);
							}

							if (HandKeypoint == EHandKeypoint::Wrist)
							{
							RuntimeGestureExportWristRotation = WorldRotation.GetNormalized();
							bRuntimeGestureExportWristRotationValid = true;
								this->SetWorldLocation(WorldLocation);
								this->SetWorldRotation(WorldRotation);
							}

							if (AutoScaleComponent)
							{
								this->SetRelativeScale3D(FVector(Scale));
							}
						}
					}
				}
			}
		}
	}

	if (!bHidden)
	{
		bRuntimeGesturePoseReceivedTrackingData = true;
	}
	else
	{
		bRuntimeGesturePoseReceivedTrackingData = false;
		bRuntimeGestureCurrentPoseCacheValid = false;
		bRuntimeGestureCurrentSemanticFeatureCacheValid = false;
		bRuntimeGestureExportWristRotationValid = false;
		RuntimeGestureExportWristRotation = FQuat::Identity;
		RuntimeGestureCurrentPoseLocalTransforms.Reset();
		RuntimeGestureCurrentPoseComponentTransforms.Reset();
		RuntimeGestureCurrentSemanticFeatures = FPICOHandSemanticFeatures();
	}

	if (AutoHide && bHidden != bHiddenInGame)
	{
		SetHiddenInGame(bHidden, true);
	}

	if (!bHidden)
	{
		UpdateRuntimeGestureCurrentPoseCache();
	}
}

bool UHandTrackingComponentPICO::MatchGesturePosePICO(UPoseAsset* TargetPoseAsset, FName PoseName, float& OutScore, float MatchThreshold, float AngularToleranceDeg, bool bIncludeWrist, bool bIncludePalm, bool bUseRuntimePose)
{
	OutScore = 0.0f;

	if (GetSkinnedAsset() == nullptr || (!bUseRuntimePose && TargetPoseAsset == nullptr))
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGesturePosePICO failed: TargetPoseAsset=%s SkinnedAsset=%s UseRuntimePose=%d"),
			*GetNameSafe(TargetPoseAsset),
			*GetNameSafe(GetSkinnedAsset()),
			bUseRuntimePose ? 1 : 0);
		return false;
	}
	if (!bRuntimeGesturePoseReceivedTrackingData)
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGesturePosePICO failed: no valid hand tracking pose has been received"));
		return false;
	}

	const FReferenceSkeleton& RefSkeleton = GetSkinnedAsset()->GetRefSkeleton();
	const int32 PoseIndex = bUseRuntimePose ? INDEX_NONE : ResolvePoseIndex(TargetPoseAsset, PoseName);
	const TArray<FTransform>* TargetLocalTransforms = nullptr;
	const TArray<FTransform>* TargetComponentTransforms = nullptr;
	FName RuntimePoseName = NAME_None;

	if (bUseRuntimePose)
	{
		RuntimePoseName = PoseName.IsNone() ? LastRuntimeGesturePoseName : PoseName;
		const FPICORuntimeGesturePose* RuntimePose = RuntimeGestureCapturedPoses.Find(RuntimePoseName);
		if (RuntimePose == nullptr)
		{
			UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGesturePosePICO failed: runtime pose %s was not captured"), *RuntimePoseName.ToString());
			return false;
		}

		TargetLocalTransforms = &RuntimePose->LocalTransforms;
		TargetComponentTransforms = &RuntimePose->ComponentTransforms;
	}
	else if (!GetCachedTargetPoseTransforms(TargetPoseAsset, PoseName, PoseIndex, RefSkeleton, TargetLocalTransforms, TargetComponentTransforms))
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGesturePosePICO failed: PoseAsset=%s RequestedPose=%s ResolvedPoseIndex=%d NumPoses=%d"),
			*GetNameSafe(TargetPoseAsset),
			*PoseName.ToString(),
			PoseIndex,
			TargetPoseAsset->GetNumPoses());
		return false;
	}

	const float EffectiveAngularToleranceDeg = FMath::Max(AngularToleranceDeg, 1.0f);
	const float EffectiveMatchThreshold = FMath::Clamp(MatchThreshold, 0.0f, 1.0f);
	float WeightedScore = 0.0f;
	float TotalWeight = 0.0f;

	if (!bRuntimeGestureCurrentPoseCacheValid)
	{
		UpdateRuntimeGestureCurrentPoseCache();
	}

	for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
	{
		const EHandKeypoint Keypoint = static_cast<EHandKeypoint>(KeypointIndex);
		if ((!bIncludePalm && Keypoint == EHandKeypoint::Palm) ||
			(!bIncludeWrist && Keypoint == EHandKeypoint::Wrist))
		{
			continue;
		}

		const FName* BoneName = BoneMappings.Find(Keypoint);
		if (BoneName == nullptr || BoneName->IsNone())
		{
			continue;
		}

		const int32 BoneIndex = RefSkeleton.FindBoneIndex(*BoneName);
		if (TargetLocalTransforms == nullptr || !TargetLocalTransforms->IsValidIndex(BoneIndex) || !RuntimeGestureCurrentPoseLocalTransforms.IsValidIndex(BoneIndex))
		{
			continue;
		}

		const FTransform& CurrentTransform = RuntimeGestureCurrentPoseLocalTransforms[BoneIndex];
		const float AngleDeg = CalculateGestureRotationAngleDeg(CurrentTransform.GetRotation(), (*TargetLocalTransforms)[BoneIndex].GetRotation());
		const float JointScore = 1.0f - FMath::Clamp(AngleDeg / FMath::Max(EffectiveAngularToleranceDeg, 1.0f), 0.0f, 1.0f);
		WeightedScore += JointScore;
		TotalWeight += 1.0f;
	}

	OutScore = TotalWeight > 0.0f ? WeightedScore / TotalWeight : 0.0f;
	return OutScore >= EffectiveMatchThreshold;
}

bool UHandTrackingComponentPICO::MatchGestureRecognizerPICO(UPICOHandGestureRecognizerAsset* RecognizerAsset, float& OutScore)
{
	OutScore = 0.0f;

	if (RecognizerAsset == nullptr || RecognizerAsset->TargetPoseAsset == nullptr || GetSkinnedAsset() == nullptr)
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureRecognizerPICO failed: Recognizer=%s TargetPoseAsset=%s SkinnedAsset=%s"),
			*GetNameSafe(RecognizerAsset),
			RecognizerAsset != nullptr ? *GetNameSafe(RecognizerAsset->TargetPoseAsset) : TEXT("<null recognizer>"),
			*GetNameSafe(GetSkinnedAsset()));
		return false;
	}
	if (!bRuntimeGesturePoseReceivedTrackingData)
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureRecognizerPICO failed: no valid hand tracking pose has been received"));
		return false;
	}
	if (!bRuntimeGestureCurrentPoseCacheValid)
	{
		UpdateRuntimeGestureCurrentPoseCache();
	}

	const int32 PoseIndex = ResolvePoseIndex(RecognizerAsset->TargetPoseAsset, RecognizerAsset->PoseName);
	const FReferenceSkeleton& RefSkeleton = GetSkinnedAsset()->GetRefSkeleton();

	const TArray<FTransform>* TargetLocalTransforms = nullptr;
	const TArray<FTransform>* TargetComponentTransforms = nullptr;
	if (!GetCachedTargetPoseTransforms(RecognizerAsset->TargetPoseAsset, RecognizerAsset->PoseName, PoseIndex, RefSkeleton, TargetLocalTransforms, TargetComponentTransforms))
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureRecognizerPICO failed: Recognizer=%s PoseAsset=%s RequestedPose=%s ResolvedPoseIndex=%d NumPoses=%d"),
			*GetNameSafe(RecognizerAsset),
			*GetNameSafe(RecognizerAsset->TargetPoseAsset),
			*RecognizerAsset->PoseName.ToString(),
			PoseIndex,
			RecognizerAsset->TargetPoseAsset->GetNumPoses());
		return false;
	}

	TArray<FPICOHandGestureJointMatchRule> ActiveRules = RecognizerAsset->JointRules;
	if (ActiveRules.Num() == 0 && RecognizerAsset->bUseDefaultFullPoseRulesWhenEmpty)
	{
		for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
		{
			const EHandKeypoint Keypoint = static_cast<EHandKeypoint>(KeypointIndex);

			FPICOHandGestureJointMatchRule& Rule = ActiveRules.AddDefaulted_GetRef();
			Rule.Joint = Keypoint;
			Rule.bEnabled = Keypoint != EHandKeypoint::Palm && Keypoint != EHandKeypoint::Wrist;
		}
	}

	float WeightedScore = 0.0f;
	float TotalWeight = 0.0f;

	for (const FPICOHandGestureJointMatchRule& Rule : ActiveRules)
	{
		if (!Rule.bEnabled || Rule.Weight <= 0.0f || (!Rule.bMatchRotation && !Rule.bMatchPosition))
		{
			continue;
		}

		const FName* BoneName = BoneMappings.Find(Rule.Joint);
		if (BoneName == nullptr || BoneName->IsNone())
		{
			continue;
		}

		const int32 BoneIndex = RefSkeleton.FindBoneIndex(*BoneName);
		if (TargetLocalTransforms == nullptr || TargetComponentTransforms == nullptr || !TargetLocalTransforms->IsValidIndex(BoneIndex) || !TargetComponentTransforms->IsValidIndex(BoneIndex))
		{
			continue;
		}

		if (!RuntimeGestureCurrentPoseLocalTransforms.IsValidIndex(BoneIndex) || !RuntimeGestureCurrentPoseComponentTransforms.IsValidIndex(BoneIndex))
		{
			continue;
		}

		const FTransform& CurrentLocalTransform = RuntimeGestureCurrentPoseLocalTransforms[BoneIndex];
		const FTransform& CurrentComponentTransform = RuntimeGestureCurrentPoseComponentTransforms[BoneIndex];
		float RuleScore = 0.0f;
		float RuleParts = 0.0f;

		if (Rule.bMatchRotation)
		{
			const float AngleDeg = CalculateGestureRotationAngleDeg(CurrentLocalTransform.GetRotation(), (*TargetLocalTransforms)[BoneIndex].GetRotation());
			const float RotationScore = 1.0f - FMath::Clamp(AngleDeg / FMath::Max(Rule.AngularToleranceDeg, 1.0f), 0.0f, 1.0f);
			RuleScore += RotationScore;
			RuleParts += 1.0f;
		}

		if (Rule.bMatchPosition)
		{
			const float PositionScore = CalculatePositionScore(CurrentComponentTransform.GetLocation(), (*TargetComponentTransforms)[BoneIndex].GetLocation(), Rule.PositionToleranceCm);
			RuleScore += PositionScore;
			RuleParts += 1.0f;
		}

		if (RuleParts > 0.0f)
		{
			WeightedScore += (RuleScore / RuleParts) * Rule.Weight;
			TotalWeight += Rule.Weight;
		}
	}

	OutScore = TotalWeight > 0.0f ? WeightedScore / TotalWeight : 0.0f;
	return OutScore >= FMath::Clamp(RecognizerAsset->MatchThreshold, 0.0f, 1.0f);
}

bool UHandTrackingComponentPICO::MatchGestureSemanticPICO(UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, float& OutScore, bool bUseRuntimeSemantic, FName RuntimeSemanticName)
{
	OutScore = 0.0f;

	if (GetSkinnedAsset() == nullptr)
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: SkinnedAsset is null"));
		return false;
	}
	if (!bRuntimeGesturePoseReceivedTrackingData)
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: no valid hand tracking pose has been received"));
		return false;
	}

	FPICOHandSemanticFeatures CurrentFeatures;
	if (!GetCurrentSemanticFeatures(CurrentFeatures))
	{
		return false;
	}

	const TArray<FPICOHandSemanticFeatureRule>* ActiveRules = nullptr;
	FPICOHandSemanticFeatures TargetFeatures;
	bool bHasTargetFeatures = false;
	float EffectiveThreshold = 0.75f;
	int32 PoseIndex = INDEX_NONE;
	FName ActiveRuntimeSemanticName = NAME_None;

	if (bUseRuntimeSemantic)
	{
		ActiveRuntimeSemanticName = RuntimeSemanticName.IsNone() ? LastRuntimeGestureSemanticName : RuntimeSemanticName;
		const FPICORuntimeGestureSemanticCapture* RuntimeSemantic = RuntimeGestureCapturedSemantics.Find(ActiveRuntimeSemanticName);
		if (RuntimeSemantic == nullptr)
		{
			UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: runtime semantic %s was not captured"), *ActiveRuntimeSemanticName.ToString());
			return false;
		}

		ActiveRules = &RuntimeSemantic->FeatureRules;
		TargetFeatures = RuntimeSemantic->Features;
		bHasTargetFeatures = true;
		EffectiveThreshold = FMath::Clamp(RuntimeSemantic->MatchThreshold, 0.0f, 1.0f);
	}
	else
	{
		if (RecognizerAsset == nullptr)
		{
			UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: Recognizer is null"));
			return false;
		}

		ActiveRules = &RecognizerAsset->FeatureRules;
		EffectiveThreshold = FMath::Clamp(RecognizerAsset->MatchThreshold, 0.0f, 1.0f);

		if (RecognizerAsset->TargetPoseAsset != nullptr)
		{
			PoseIndex = ResolvePoseIndex(RecognizerAsset->TargetPoseAsset, RecognizerAsset->PoseName);
			const FReferenceSkeleton& RefSkeleton = GetSkinnedAsset()->GetRefSkeleton();
			if (!GetCachedTargetSemanticFeatures(RecognizerAsset->TargetPoseAsset, RecognizerAsset->PoseName, PoseIndex, RefSkeleton, TargetFeatures))
			{
				UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: Recognizer=%s PoseAsset=%s RequestedPose=%s ResolvedPoseIndex=%d NumPoses=%d"),
					*GetNameSafe(RecognizerAsset),
					*GetNameSafe(RecognizerAsset->TargetPoseAsset),
					*RecognizerAsset->PoseName.ToString(),
					PoseIndex,
					RecognizerAsset->TargetPoseAsset->GetNumPoses());
				return false;
			}

			bHasTargetFeatures = true;
		}
	}

	if (ActiveRules == nullptr || ActiveRules->Num() == 0)
	{
		UE_LOG(LogPICOHandGestureMatch, VeryVerbose, TEXT("MatchGestureSemanticPICO failed: no semantic feature rules available. UseRuntimeSemantic=%d Recognizer=%s RuntimeSemantic=%s"),
			bUseRuntimeSemantic ? 1 : 0,
			*GetNameSafe(RecognizerAsset),
			*ActiveRuntimeSemanticName.ToString());
		return false;
	}

	float WeightedScore = 0.0f;
	float TotalWeight = 0.0f;
	int32 RequiredFailures = 0;

	for (const FPICOHandSemanticFeatureRule& Rule : *ActiveRules)
	{
		if (!Rule.bEnabled || Rule.Weight <= 0.0f)
		{
			continue;
		}

		float CurrentValue = 0.0f;
		float TargetValue = Rule.TargetValue;
		if (!PICOHandGestureSemantic::GetFeatureValue(CurrentFeatures, Rule.Feature, CurrentValue))
		{
			continue;
		}

		if (bHasTargetFeatures)
		{
			float AutoTargetValue = 0.0f;
			if (PICOHandGestureSemantic::GetFeatureValue(TargetFeatures, Rule.Feature, AutoTargetValue))
			{
				TargetValue = AutoTargetValue;
			}
		}

		const float FeatureScore = CalculateSemanticFeatureScore(CurrentValue, TargetValue, Rule.Tolerance);
		const float EffectiveMinPassScore = FMath::Clamp(Rule.MinPassScore, 0.0f, 1.0f);
		if (Rule.bRequired && FeatureScore < EffectiveMinPassScore)
		{
			++RequiredFailures;
		}

		WeightedScore += FeatureScore * Rule.Weight;
		TotalWeight += Rule.Weight;
	}

	OutScore = TotalWeight > 0.0f ? WeightedScore / TotalWeight : 0.0f;
	const bool bMatched = RequiredFailures == 0 && OutScore >= EffectiveThreshold;

	return bMatched;
}
