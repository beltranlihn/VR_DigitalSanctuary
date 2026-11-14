// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureSemanticRecognizerAsset.h"

#include "Animation/PoseAsset.h"
#include "Engine/SkeletalMesh.h"

namespace
{
	struct FPICOHandSemanticFeatureMetadata
	{
		EPICOHandSemanticFeatureType FeatureType;
		const TCHAR* Name;
		float NeutralValue;
		float SuggestedTolerance;
		float SuggestedWeight;
	};

	static constexpr FPICOHandSemanticFeatureMetadata FeatureMetadata[] = {
		{ EPICOHandSemanticFeatureType::ThumbCurl,			TEXT("ThumbCurl"),			0.0f,	0.18f,	1.75f },
		{ EPICOHandSemanticFeatureType::IndexCurl,			TEXT("IndexCurl"),			0.0f,	0.20f,	1.55f },
		{ EPICOHandSemanticFeatureType::MiddleCurl,			TEXT("MiddleCurl"),			0.0f,	0.16f,	1.55f },
		{ EPICOHandSemanticFeatureType::RingCurl,			TEXT("RingCurl"),			0.0f,	0.16f,	1.45f },
		{ EPICOHandSemanticFeatureType::LittleCurl,			TEXT("LittleCurl"),			0.0f,	0.18f,	1.35f },
		{ EPICOHandSemanticFeatureType::IndexMiddleSpread,	TEXT("IndexMiddleSpread"),	0.22f,	0.15f,	0.85f },
		{ EPICOHandSemanticFeatureType::MiddleRingSpread,	TEXT("MiddleRingSpread"),	0.18f,	0.15f,	0.80f },
		{ EPICOHandSemanticFeatureType::RingLittleSpread,	TEXT("RingLittleSpread"),	0.24f,	0.16f,	0.80f },
		{ EPICOHandSemanticFeatureType::ThumbUpness,		TEXT("ThumbUpness"),		0.20f,	0.16f,	1.50f },
		{ EPICOHandSemanticFeatureType::ThumbOpposition,	TEXT("ThumbOpposition"),	0.0f,	0.16f,	1.15f },
		{ EPICOHandSemanticFeatureType::PalmPitch,			TEXT("PalmPitch"),			0.0f,	0.25f,	0.50f },
		{ EPICOHandSemanticFeatureType::PalmRoll,			TEXT("PalmRoll"),			0.0f,	0.25f,	0.50f }
	};

	const FPICOHandSemanticFeatureMetadata* FindFeatureMetadata(EPICOHandSemanticFeatureType FeatureType)
	{
		for (const FPICOHandSemanticFeatureMetadata& Metadata : FeatureMetadata)
		{
			if (Metadata.FeatureType == FeatureType)
			{
				return &Metadata;
			}
		}

		return nullptr;
	}

	bool IsDefaultEnabledSemanticFeature(EPICOHandSemanticFeatureType FeatureType)
	{
		return
			FeatureType != EPICOHandSemanticFeatureType::PalmPitch &&
			FeatureType != EPICOHandSemanticFeatureType::PalmRoll;
	}

	int32 FindMappedBoneIndex(const TMap<EHandKeypoint, FName>& BoneMappings, EHandKeypoint Keypoint, const FReferenceSkeleton& RefSkeleton)
	{
		const FName* BoneName = BoneMappings.Find(Keypoint);
		return (BoneName != nullptr && !BoneName->IsNone()) ? RefSkeleton.FindBoneIndex(*BoneName) : INDEX_NONE;
	}

	bool IsValidBoneIndex(const TArray<FTransform>& Transforms, int32 BoneIndex)
	{
		return BoneIndex != INDEX_NONE && Transforms.IsValidIndex(BoneIndex);
	}

	FVector GetBoneLocationOrZero(const TArray<FTransform>& ComponentTransforms, int32 BoneIndex)
	{
		return IsValidBoneIndex(ComponentTransforms, BoneIndex)
			? ComponentTransforms[BoneIndex].GetLocation()
			: FVector::ZeroVector;
	}

	bool TryGetDirection(const TArray<FTransform>& ComponentTransforms, int32 StartBoneIndex, int32 EndBoneIndex, FVector& OutDirection)
	{
		if (!IsValidBoneIndex(ComponentTransforms, StartBoneIndex) || !IsValidBoneIndex(ComponentTransforms, EndBoneIndex))
		{
			return false;
		}

		FVector Delta = ComponentTransforms[EndBoneIndex].GetLocation() - ComponentTransforms[StartBoneIndex].GetLocation();
		if (!Delta.Normalize())
		{
			return false;
		}

		OutDirection = Delta;
		return true;
	}

	float CalculateRotationAngleDeg(const FQuat& CurrentRotation, const FQuat& TargetRotation)
	{
		const float Dot = FMath::Abs(CurrentRotation.GetNormalized() | TargetRotation.GetNormalized());
		return FMath::RadiansToDegrees(2.0f * FMath::Acos(FMath::Clamp(Dot, 0.0f, 1.0f)));
	}

	float CalculateNormalizedCurl(const TArray<FTransform>& LocalTransforms, const TArray<FTransform>& ReferenceLocalTransforms, const TArray<int32>& BoneIndices)
	{
		float Accumulated = 0.0f;
		int32 Count = 0;
		for (const int32 BoneIndex : BoneIndices)
		{
			if (!IsValidBoneIndex(LocalTransforms, BoneIndex) || !ReferenceLocalTransforms.IsValidIndex(BoneIndex))
			{
				continue;
			}

			const float AngleDeg = CalculateRotationAngleDeg(LocalTransforms[BoneIndex].GetRotation(), ReferenceLocalTransforms[BoneIndex].GetRotation());
			Accumulated += FMath::Clamp(AngleDeg / 90.0f, 0.0f, 1.0f);
			++Count;
		}

		return Count > 0 ? Accumulated / static_cast<float>(Count) : 0.0f;
	}

	float CalculateNormalizedSpread(const FVector& DirectionA, const FVector& DirectionB)
	{
		const float Dot = FMath::Clamp(DirectionA | DirectionB, -1.0f, 1.0f);
		const float AngleDeg = FMath::RadiansToDegrees(FMath::Acos(Dot));
		return FMath::Clamp(AngleDeg / 45.0f, 0.0f, 1.0f);
	}
}

void PICOHandGestureSemantic::BuildDefaultBoneMappings(bool bIsRightHand, TMap<EHandKeypoint, FName>& OutMappings)
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

	const TCHAR* const* DesiredBoneNames = bIsRightHand ? RightBoneNames : LeftBoneNames;
	OutMappings.Reset();
	for (int32 KeypointIndex = 0; KeypointIndex < EHandKeypointCount; ++KeypointIndex)
	{
		OutMappings.Add(static_cast<EHandKeypoint>(KeypointIndex), FName(DesiredBoneNames[KeypointIndex]));
	}
}

bool PICOHandGestureSemantic::GetFeatureValue(const FPICOHandSemanticFeatures& Features, EPICOHandSemanticFeatureType FeatureType, float& OutValue)
{
	switch (FeatureType)
	{
	case EPICOHandSemanticFeatureType::ThumbCurl:
		OutValue = Features.ThumbCurl;
		return true;
	case EPICOHandSemanticFeatureType::IndexCurl:
		OutValue = Features.IndexCurl;
		return true;
	case EPICOHandSemanticFeatureType::MiddleCurl:
		OutValue = Features.MiddleCurl;
		return true;
	case EPICOHandSemanticFeatureType::RingCurl:
		OutValue = Features.RingCurl;
		return true;
	case EPICOHandSemanticFeatureType::LittleCurl:
		OutValue = Features.LittleCurl;
		return true;
	case EPICOHandSemanticFeatureType::IndexMiddleSpread:
		OutValue = Features.IndexMiddleSpread;
		return true;
	case EPICOHandSemanticFeatureType::MiddleRingSpread:
		OutValue = Features.MiddleRingSpread;
		return true;
	case EPICOHandSemanticFeatureType::RingLittleSpread:
		OutValue = Features.RingLittleSpread;
		return true;
	case EPICOHandSemanticFeatureType::ThumbUpness:
		OutValue = Features.ThumbUpness;
		return true;
	case EPICOHandSemanticFeatureType::ThumbOpposition:
		OutValue = Features.ThumbOpposition;
		return true;
	case EPICOHandSemanticFeatureType::PalmPitch:
		OutValue = Features.PalmPitch;
		return true;
	case EPICOHandSemanticFeatureType::PalmRoll:
		OutValue = Features.PalmRoll;
		return true;
	default:
		OutValue = 0.0f;
		return false;
	}
}

FString PICOHandGestureSemantic::GetFeatureTypeName(EPICOHandSemanticFeatureType FeatureType)
{
	if (const FPICOHandSemanticFeatureMetadata* Metadata = FindFeatureMetadata(FeatureType))
	{
		return Metadata->Name;
	}

	return TEXT("UnknownFeature");
}

bool PICOHandGestureSemantic::TryParseFeatureType(const FString& FeatureTypeName, EPICOHandSemanticFeatureType& OutFeatureType)
{
	for (const FPICOHandSemanticFeatureMetadata& Metadata : FeatureMetadata)
	{
		if (FeatureTypeName.Equals(Metadata.Name, ESearchCase::IgnoreCase))
		{
			OutFeatureType = Metadata.FeatureType;
			return true;
		}
	}

	return false;
}

float PICOHandGestureSemantic::GetNeutralFeatureValue(EPICOHandSemanticFeatureType FeatureType)
{
	if (const FPICOHandSemanticFeatureMetadata* Metadata = FindFeatureMetadata(FeatureType))
	{
		return Metadata->NeutralValue;
	}

	return 0.0f;
}

float PICOHandGestureSemantic::GetSuggestedTolerance(EPICOHandSemanticFeatureType FeatureType)
{
	if (const FPICOHandSemanticFeatureMetadata* Metadata = FindFeatureMetadata(FeatureType))
	{
		return Metadata->SuggestedTolerance;
	}

	return 0.2f;
}

float PICOHandGestureSemantic::GetSuggestedWeight(EPICOHandSemanticFeatureType FeatureType)
{
	if (const FPICOHandSemanticFeatureMetadata* Metadata = FindFeatureMetadata(FeatureType))
	{
		return Metadata->SuggestedWeight;
	}

	return 1.0f;
}

bool PICOHandGestureSemantic::ExtractSemanticFeatures(bool bIsRightHand, const FReferenceSkeleton& RefSkeleton, const TMap<EHandKeypoint, FName>& BoneMappings, const TArray<FTransform>& LocalTransforms, const TArray<FTransform>& ComponentTransforms, FPICOHandSemanticFeatures& OutFeatures, FString* OutError)
{
	OutFeatures = FPICOHandSemanticFeatures();

	if (LocalTransforms.Num() != RefSkeleton.GetNum() || ComponentTransforms.Num() != RefSkeleton.GetNum())
	{
		if (OutError != nullptr)
		{
			*OutError = TEXT("Semantic feature extraction failed: transform counts do not match the reference skeleton.");
		}
		return false;
	}

	const TArray<FTransform>& ReferenceLocalTransforms = RefSkeleton.GetRefBonePose();

	const int32 PalmIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::Palm, RefSkeleton);
	const int32 WristIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::Wrist, RefSkeleton);
	const int32 ThumbMetacarpalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::ThumbMetacarpal, RefSkeleton);
	const int32 ThumbProximalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::ThumbProximal, RefSkeleton);
	const int32 ThumbDistalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::ThumbDistal, RefSkeleton);
	const int32 ThumbTipIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::ThumbTip, RefSkeleton);
	const int32 IndexMetacarpalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::IndexMetacarpal, RefSkeleton);
	const int32 IndexProximalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::IndexProximal, RefSkeleton);
	const int32 IndexIntermediateIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::IndexIntermediate, RefSkeleton);
	const int32 IndexDistalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::IndexDistal, RefSkeleton);
	const int32 IndexTipIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::IndexTip, RefSkeleton);
	const int32 MiddleMetacarpalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::MiddleMetacarpal, RefSkeleton);
	const int32 MiddleProximalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::MiddleProximal, RefSkeleton);
	const int32 MiddleIntermediateIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::MiddleIntermediate, RefSkeleton);
	const int32 MiddleDistalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::MiddleDistal, RefSkeleton);
	const int32 RingMetacarpalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::RingMetacarpal, RefSkeleton);
	const int32 RingProximalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::RingProximal, RefSkeleton);
	const int32 RingIntermediateIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::RingIntermediate, RefSkeleton);
	const int32 RingDistalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::RingDistal, RefSkeleton);
	const int32 LittleMetacarpalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::LittleMetacarpal, RefSkeleton);
	const int32 LittleProximalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::LittleProximal, RefSkeleton);
	const int32 LittleIntermediateIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::LittleIntermediate, RefSkeleton);
	const int32 LittleDistalIndex = FindMappedBoneIndex(BoneMappings, EHandKeypoint::LittleDistal, RefSkeleton);

	OutFeatures.ThumbCurl = CalculateNormalizedCurl(LocalTransforms, ReferenceLocalTransforms, { ThumbMetacarpalIndex, ThumbProximalIndex, ThumbDistalIndex });
	OutFeatures.IndexCurl = CalculateNormalizedCurl(LocalTransforms, ReferenceLocalTransforms, { IndexProximalIndex, IndexIntermediateIndex, IndexDistalIndex });
	OutFeatures.MiddleCurl = CalculateNormalizedCurl(LocalTransforms, ReferenceLocalTransforms, { MiddleProximalIndex, MiddleIntermediateIndex, MiddleDistalIndex });
	OutFeatures.RingCurl = CalculateNormalizedCurl(LocalTransforms, ReferenceLocalTransforms, { RingProximalIndex, RingIntermediateIndex, RingDistalIndex });
	OutFeatures.LittleCurl = CalculateNormalizedCurl(LocalTransforms, ReferenceLocalTransforms, { LittleProximalIndex, LittleIntermediateIndex, LittleDistalIndex });

	const int32 RootIndex = PalmIndex != INDEX_NONE ? PalmIndex : WristIndex;
	const FVector RootLocation = GetBoneLocationOrZero(ComponentTransforms, RootIndex);
	const FVector IndexAnchor = GetBoneLocationOrZero(ComponentTransforms, IndexProximalIndex != INDEX_NONE ? IndexProximalIndex : IndexMetacarpalIndex);
	const FVector MiddleAnchor = GetBoneLocationOrZero(ComponentTransforms, MiddleProximalIndex != INDEX_NONE ? MiddleProximalIndex : MiddleMetacarpalIndex);
	const FVector RingAnchor = GetBoneLocationOrZero(ComponentTransforms, RingProximalIndex != INDEX_NONE ? RingProximalIndex : RingMetacarpalIndex);
	const FVector LittleAnchor = GetBoneLocationOrZero(ComponentTransforms, LittleProximalIndex != INDEX_NONE ? LittleProximalIndex : LittleMetacarpalIndex);

	FVector IndexDirection = IndexAnchor - RootLocation;
	FVector MiddleDirection = MiddleAnchor - RootLocation;
	FVector RingDirection = RingAnchor - RootLocation;
	FVector LittleDirection = LittleAnchor - RootLocation;
	IndexDirection.Normalize();
	MiddleDirection.Normalize();
	RingDirection.Normalize();
	LittleDirection.Normalize();

	if (!IndexDirection.IsNearlyZero() && !MiddleDirection.IsNearlyZero())
	{
		OutFeatures.IndexMiddleSpread = CalculateNormalizedSpread(IndexDirection, MiddleDirection);
	}
	if (!MiddleDirection.IsNearlyZero() && !RingDirection.IsNearlyZero())
	{
		OutFeatures.MiddleRingSpread = CalculateNormalizedSpread(MiddleDirection, RingDirection);
	}
	if (!RingDirection.IsNearlyZero() && !LittleDirection.IsNearlyZero())
	{
		OutFeatures.RingLittleSpread = CalculateNormalizedSpread(RingDirection, LittleDirection);
	}

	const FVector WristLocation = GetBoneLocationOrZero(ComponentTransforms, WristIndex != INDEX_NONE ? WristIndex : RootIndex);
	const FVector MiddleRootLocation = GetBoneLocationOrZero(ComponentTransforms, MiddleMetacarpalIndex != INDEX_NONE ? MiddleMetacarpalIndex : MiddleProximalIndex);

	FVector PalmForward = MiddleRootLocation - WristLocation;
	if (!PalmForward.Normalize())
	{
		PalmForward = FVector::ForwardVector;
	}

	FVector PalmAcross = IndexAnchor - LittleAnchor;
	if (bIsRightHand)
	{
		PalmAcross *= -1.0f;
	}
	if (!PalmAcross.Normalize())
	{
		PalmAcross = FVector::RightVector;
	}

	FVector PalmNormal = PalmAcross ^ PalmForward;
	if (!PalmNormal.Normalize())
	{
		PalmNormal = FVector::UpVector;
	}

	FVector ThumbDirection;
	if (!TryGetDirection(ComponentTransforms, ThumbMetacarpalIndex, ThumbTipIndex != INDEX_NONE ? ThumbTipIndex : ThumbDistalIndex, ThumbDirection))
	{
		ThumbDirection = FVector::ZeroVector;
	}

	if (!ThumbDirection.IsNearlyZero())
	{
		OutFeatures.ThumbUpness = FMath::Abs(ThumbDirection | PalmNormal);
	}

	const FVector ThumbTipLocation = GetBoneLocationOrZero(ComponentTransforms, ThumbTipIndex != INDEX_NONE ? ThumbTipIndex : ThumbDistalIndex);
	const FVector IndexTipLocation = GetBoneLocationOrZero(ComponentTransforms, IndexTipIndex != INDEX_NONE ? IndexTipIndex : IndexDistalIndex);
	const float ThumbIndexDistanceCm = FVector::Distance(ThumbTipLocation, IndexTipLocation);
	OutFeatures.ThumbOpposition = 1.0f - FMath::Clamp(ThumbIndexDistanceCm / 8.0f, 0.0f, 1.0f);

	OutFeatures.PalmPitch = FMath::Clamp(PalmForward.Z, -1.0f, 1.0f);
	OutFeatures.PalmRoll = FMath::Clamp(PalmAcross.Z, -1.0f, 1.0f);

	return true;
}

void PICOHandGestureSemantic::GenerateSuggestedFeatureRules(const FPICOHandSemanticFeatures& TargetFeatures, TArray<FPICOHandSemanticFeatureRule>& OutRules, float& OutSuggestedMatchThreshold)
{
	struct FRuleCandidate
	{
		FPICOHandSemanticFeatureRule Rule;
		float Salience = 0.0f;
		float Priority = 0.0f;
	};

	TArray<FRuleCandidate> Candidates;
	Candidates.Reserve(UE_ARRAY_COUNT(FeatureMetadata));

	for (const FPICOHandSemanticFeatureMetadata& Metadata : FeatureMetadata)
	{
		float TargetValue = 0.0f;
		if (!GetFeatureValue(TargetFeatures, Metadata.FeatureType, TargetValue))
		{
			continue;
		}

		FRuleCandidate Candidate;
		Candidate.Rule.Feature = Metadata.FeatureType;
		Candidate.Rule.TargetValue = TargetValue;
		Candidate.Rule.Tolerance = Metadata.SuggestedTolerance;
		Candidate.Rule.Weight = Metadata.SuggestedWeight;
		Candidate.Rule.MinPassScore = 0.40f;
		Candidate.Salience = FMath::Abs(TargetValue - Metadata.NeutralValue);
		Candidate.Priority = (0.25f + Candidate.Salience) * Metadata.SuggestedWeight;
		Candidates.Add(Candidate);
	}

	Candidates.Sort([](const FRuleCandidate& A, const FRuleCandidate& B)
	{
		return A.Priority > B.Priority;
	});

	for (int32 CandidateIndex = 0; CandidateIndex < Candidates.Num(); ++CandidateIndex)
	{
		FRuleCandidate& Candidate = Candidates[CandidateIndex];
		const FPICOHandSemanticFeatureMetadata* Metadata = FindFeatureMetadata(Candidate.Rule.Feature);
		if (!Metadata)
		{
			continue;
		}

		Candidate.Rule.bEnabled = IsDefaultEnabledSemanticFeature(Candidate.Rule.Feature);
		if (Candidate.Rule.bEnabled)
		{
			Candidate.Rule.Weight = Metadata->SuggestedWeight * (1.0f + FMath::Clamp(Candidate.Salience * 1.5f, 0.0f, 1.5f));
		}
		else
		{
			Candidate.Rule.Weight = Metadata->SuggestedWeight * 0.5f;
		}
	}

	int32 RequiredAssigned = 0;
	for (FRuleCandidate& Candidate : Candidates)
	{
		if (!Candidate.Rule.bEnabled)
		{
			continue;
		}

		const bool bIsStrongAnchorFeature =
			Candidate.Rule.Feature == EPICOHandSemanticFeatureType::ThumbCurl ||
			Candidate.Rule.Feature == EPICOHandSemanticFeatureType::ThumbUpness ||
			Candidate.Rule.Feature == EPICOHandSemanticFeatureType::MiddleCurl;
		const bool bShouldRequire =
			RequiredAssigned < 2 &&
			bIsStrongAnchorFeature &&
			Candidate.Salience >= 0.22f &&
			Candidate.Rule.Weight >= 1.40f;
		Candidate.Rule.bRequired = bShouldRequire;
		Candidate.Rule.MinPassScore = bShouldRequire ? 0.50f : 0.40f;
		RequiredAssigned += bShouldRequire ? 1 : 0;
	}

	OutRules.Reset();
	OutRules.Reserve(Candidates.Num());
	for (const FRuleCandidate& Candidate : Candidates)
	{
		OutRules.Add(Candidate.Rule);
	}

	OutSuggestedMatchThreshold = 0.75f;
}
