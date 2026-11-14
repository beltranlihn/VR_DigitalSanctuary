// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_HandGestureEditorLibrary.h"

#include "Animation/PoseAsset.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimSequence.h"
#include "Dom/JsonObject.h"
#include "Engine/SkeletalMesh.h"
#include "Logging/LogMacros.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "PICO_HandAssetPaths.h"
#include "PICO_HandGestureRecognizerAsset.h"
#include "PICO_HandGestureSemanticRecognizerAsset.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UObject/SoftObjectPath.h"

DEFINE_LOG_CATEGORY_STATIC(LogPICOHandGestureEditorLibrary, Log, All);

namespace
{
	struct FOpenXRJointExportMapping
	{
		const TCHAR* XRJointName;
		const TCHAR* LeftBoneName;
		const TCHAR* RightBoneName;
	};

	struct FParsedOpenXRJointPose
	{
		FString XRJointName;
		FName   BoneName;
		FTransform Transform;
	};

	static constexpr FOpenXRJointExportMapping OpenXRJointMappings[] = {
		{ TEXT("XR_HAND_JOINT_PALM_EXT"),                 TEXT("left_palm"),                 TEXT("right_palm") },
		{ TEXT("XR_HAND_JOINT_WRIST_EXT"),                TEXT("left_wrist"),                TEXT("right_wrist") },
		{ TEXT("XR_HAND_JOINT_THUMB_METACARPAL_EXT"),     TEXT("left_thumb_metacarpal"),     TEXT("right_thumb_metacarpal") },
		{ TEXT("XR_HAND_JOINT_THUMB_PROXIMAL_EXT"),       TEXT("left_thumb_proximal"),       TEXT("right_thumb_proximal") },
		{ TEXT("XR_HAND_JOINT_THUMB_DISTAL_EXT"),         TEXT("left_thumb_distal"),         TEXT("right_thumb_distal") },
		{ TEXT("XR_HAND_JOINT_THUMB_TIP_EXT"),            TEXT("left_thumb_tip"),            TEXT("right_thumb_tip") },
		{ TEXT("XR_HAND_JOINT_INDEX_METACARPAL_EXT"),     TEXT("left_index_metacarpal"),     TEXT("right_index_metacarpal") },
		{ TEXT("XR_HAND_JOINT_INDEX_PROXIMAL_EXT"),       TEXT("left_index_proximal"),       TEXT("right_index_proximal") },
		{ TEXT("XR_HAND_JOINT_INDEX_INTERMEDIATE_EXT"),   TEXT("left_index_intermediate"),   TEXT("right_index_intermediate") },
		{ TEXT("XR_HAND_JOINT_INDEX_DISTAL_EXT"),         TEXT("left_index_distal"),         TEXT("right_index_distal") },
		{ TEXT("XR_HAND_JOINT_INDEX_TIP_EXT"),            TEXT("left_index_tip"),            TEXT("right_index_tip") },
		{ TEXT("XR_HAND_JOINT_MIDDLE_METACARPAL_EXT"),    TEXT("left_middle_metacarpal"),    TEXT("right_middle_metacarpal") },
		{ TEXT("XR_HAND_JOINT_MIDDLE_PROXIMAL_EXT"),      TEXT("left_middle_proximal"),      TEXT("right_middle_proximal") },
		{ TEXT("XR_HAND_JOINT_MIDDLE_INTERMEDIATE_EXT"),  TEXT("left_middle_intermediate"),  TEXT("right_middle_intermediate") },
		{ TEXT("XR_HAND_JOINT_MIDDLE_DISTAL_EXT"),        TEXT("left_middle_distal"),        TEXT("right_middle_distal") },
		{ TEXT("XR_HAND_JOINT_MIDDLE_TIP_EXT"),           TEXT("left_middle_tip"),           TEXT("right_middle_tip") },
		{ TEXT("XR_HAND_JOINT_RING_METACARPAL_EXT"),      TEXT("left_ring_metacarpal"),      TEXT("right_ring_metacarpal") },
		{ TEXT("XR_HAND_JOINT_RING_PROXIMAL_EXT"),        TEXT("left_ring_proximal"),        TEXT("right_ring_proximal") },
		{ TEXT("XR_HAND_JOINT_RING_INTERMEDIATE_EXT"),    TEXT("left_ring_intermediate"),    TEXT("right_ring_intermediate") },
		{ TEXT("XR_HAND_JOINT_RING_DISTAL_EXT"),          TEXT("left_ring_distal"),          TEXT("right_ring_distal") },
		{ TEXT("XR_HAND_JOINT_RING_TIP_EXT"),             TEXT("left_ring_tip"),             TEXT("right_ring_tip") },
		{ TEXT("XR_HAND_JOINT_LITTLE_METACARPAL_EXT"),    TEXT("left_little_metacarpal"),    TEXT("right_little_metacarpal") },
		{ TEXT("XR_HAND_JOINT_LITTLE_PROXIMAL_EXT"),      TEXT("left_little_proximal"),      TEXT("right_little_proximal") },
		{ TEXT("XR_HAND_JOINT_LITTLE_INTERMEDIATE_EXT"),  TEXT("left_little_intermediate"),  TEXT("right_little_intermediate") },
		{ TEXT("XR_HAND_JOINT_LITTLE_DISTAL_EXT"),        TEXT("left_little_distal"),        TEXT("right_little_distal") },
		{ TEXT("XR_HAND_JOINT_LITTLE_TIP_EXT"),           TEXT("left_little_tip"),           TEXT("right_little_tip") }
	};

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
		TSharedRef<FJsonObject> JsonObject = MakeShared<FJsonObject>();
		JsonObject->SetNumberField(TEXT("x"), Quat.X);
		JsonObject->SetNumberField(TEXT("y"), Quat.Y);
		JsonObject->SetNumberField(TEXT("z"), Quat.Z);
		JsonObject->SetNumberField(TEXT("w"), Quat.W);
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

	bool JsonObjectToVector(const TSharedPtr<FJsonObject>& JsonObject, const TCHAR* FieldName, FVector& OutVector)
	{
		const TSharedPtr<FJsonObject>* VectorObject = nullptr;
		if (!JsonObject.IsValid() || !JsonObject->TryGetObjectField(FieldName, VectorObject) || !VectorObject || !VectorObject->IsValid())
		{
			return false;
		}

		double X = 0.0;
		double Y = 0.0;
		double Z = 0.0;
		if (!(*VectorObject)->TryGetNumberField(TEXT("x"), X) ||
			!(*VectorObject)->TryGetNumberField(TEXT("y"), Y) ||
			!(*VectorObject)->TryGetNumberField(TEXT("z"), Z))
		{
			return false;
		}

		OutVector = FVector(X, Y, Z);
		return true;
	}

	bool JsonObjectToQuat(const TSharedPtr<FJsonObject>& JsonObject, const TCHAR* FieldName, FQuat& OutQuat)
	{
		const TSharedPtr<FJsonObject>* QuatObject = nullptr;
		if (!JsonObject.IsValid() || !JsonObject->TryGetObjectField(FieldName, QuatObject) || !QuatObject || !QuatObject->IsValid())
		{
			return false;
		}

		double X = 0.0;
		double Y = 0.0;
		double Z = 0.0;
		double W = 1.0;
		if (!(*QuatObject)->TryGetNumberField(TEXT("x"), X) ||
			!(*QuatObject)->TryGetNumberField(TEXT("y"), Y) ||
			!(*QuatObject)->TryGetNumberField(TEXT("z"), Z) ||
			!(*QuatObject)->TryGetNumberField(TEXT("w"), W))
		{
			return false;
		}

		OutQuat = FQuat(X, Y, Z, W);
		OutQuat.Normalize();
		return true;
	}

	bool JsonObjectToTransform(const TSharedPtr<FJsonObject>& JsonObject, const TCHAR* FieldName, FTransform& OutTransform)
	{
		const TSharedPtr<FJsonObject>* TransformObject = nullptr;
		if (!JsonObject.IsValid() || !JsonObject->TryGetObjectField(FieldName, TransformObject) || !TransformObject || !TransformObject->IsValid())
		{
			return false;
		}

		FVector Translation = FVector::ZeroVector;
		FVector Scale = FVector::OneVector;
		FQuat Rotation = FQuat::Identity;

		if (!JsonObjectToVector(*TransformObject, TEXT("translation"), Translation) ||
			!JsonObjectToQuat(*TransformObject, TEXT("rotation"), Rotation) ||
			!JsonObjectToVector(*TransformObject, TEXT("scale"), Scale))
		{
			return false;
		}

		OutTransform = FTransform(Rotation, Translation, Scale);
		return true;
	}

	bool ResolveHandPrefix(const TArray<FName>& TrackNames, const TCHAR*& OutHandPrefix)
	{
		int32 LeftMatches = 0;
		int32 RightMatches = 0;

		for (const FOpenXRJointExportMapping& Mapping : OpenXRJointMappings)
		{
			if (TrackNames.Contains(FName(Mapping.LeftBoneName)))
			{
				++LeftMatches;
			}

			if (TrackNames.Contains(FName(Mapping.RightBoneName)))
			{
				++RightMatches;
			}
		}

		if (RightMatches == UE_ARRAY_COUNT(OpenXRJointMappings) && LeftMatches == 0)
		{
			OutHandPrefix = TEXT("right");
			return true;
		}

		if (LeftMatches == UE_ARRAY_COUNT(OpenXRJointMappings) && RightMatches == 0)
		{
			OutHandPrefix = TEXT("left");
			return true;
		}

		return false;
	}

	bool ResolveHandPrefixFromBoneNames(const TArray<FParsedOpenXRJointPose>& JointPoses, const TCHAR*& OutHandPrefix)
	{
		int32 LeftMatches = 0;
		int32 RightMatches = 0;

		for (const FParsedOpenXRJointPose& JointPose : JointPoses)
		{
			const FString BoneNameString = JointPose.BoneName.ToString();
			if (BoneNameString.StartsWith(TEXT("left_")))
			{
				++LeftMatches;
			}
			else if (BoneNameString.StartsWith(TEXT("right_")))
			{
				++RightMatches;
			}
		}

		if (RightMatches == JointPoses.Num() && JointPoses.Num() > 0)
		{
				OutHandPrefix = TEXT("right");
				return true;
		}

		if (LeftMatches == JointPoses.Num() && JointPoses.Num() > 0)
		{
				OutHandPrefix = TEXT("left");
				return true;
		}

		return false;
	}

	bool LoadBuiltInHandAssets(const TCHAR* HandPrefix, USkeletalMesh*& OutHandMesh, USkeleton*& OutSkeleton, FString& OutError)
	{
		const PICOOpenXREditor::FBuiltInHandAssetPaths& AssetPaths = PICOOpenXREditor::GetBuiltInHandAssetPaths(HandPrefix);

		OutHandMesh = LoadObject<USkeletalMesh>(nullptr, AssetPaths.SkeletalMeshPath);
		if (!OutHandMesh)
		{
			OutError = FString::Printf(
				TEXT("Missing built-in %s hand skeletal mesh '%s'."),
				HandPrefix,
				AssetPaths.SkeletalMeshPath);
			return false;
		}

		OutSkeleton = LoadObject<USkeleton>(nullptr, AssetPaths.SkeletonPath);
		if (!OutSkeleton)
		{
			OutError = FString::Printf(
				TEXT("Missing built-in %s hand skeleton '%s'."),
				HandPrefix,
				AssetPaths.SkeletonPath);
			return false;
		}

		if (OutHandMesh->GetSkeleton() != OutSkeleton)
		{
			OutError = FString::Printf(
				TEXT("Built-in %s hand asset mismatch. Mesh '%s' is not bound to skeleton '%s'."),
				HandPrefix,
				AssetPaths.SkeletalMeshPath,
				AssetPaths.SkeletonPath);
			return false;
		}

		return true;
	}

	const FOpenXRJointExportMapping* FindMappingByXRJointName(const FString& XRJointName)
	{
		for (const FOpenXRJointExportMapping& Mapping : OpenXRJointMappings)
		{
			if (XRJointName == Mapping.XRJointName)
			{
				return &Mapping;
			}
		}

		return nullptr;
	}

	const FOpenXRJointExportMapping* FindMappingByKeypoint(EHandKeypoint Keypoint)
	{
		const int32 KeypointIndex = static_cast<int32>(Keypoint);
		return UE_ARRAY_COUNT(OpenXRJointMappings) > KeypointIndex && KeypointIndex >= 0
			? &OpenXRJointMappings[KeypointIndex]
			: nullptr;
	}

	bool TryGetKeypointByXRJointName(const FString& XRJointName, EHandKeypoint& OutKeypoint)
	{
		for (int32 KeypointIndex = 0; KeypointIndex < UE_ARRAY_COUNT(OpenXRJointMappings); ++KeypointIndex)
		{
			if (XRJointName == OpenXRJointMappings[KeypointIndex].XRJointName)
			{
				OutKeypoint = static_cast<EHandKeypoint>(KeypointIndex);
				return true;
			}
		}

		return false;
	}

	void AddUniquePackageDirectory(TArray<FString>& InOutPackageDirectories, const FString& PackageDirectory)
	{
		if (!PackageDirectory.IsEmpty())
		{
			InOutPackageDirectories.AddUnique(PackageDirectory);
		}
	}

	FString TryConvertFilenameDirectoryToPackagePath(const FString& SourceFilename)
	{
		if (SourceFilename.IsEmpty())
		{
			return FString();
		}

		const FString AbsoluteSourceDirectory = FPaths::GetPath(FPaths::ConvertRelativePathToFull(SourceFilename));
		FString RelativeContentPath;
		if (!FPackageName::TryConvertFilenameToLongPackageName(AbsoluteSourceDirectory, RelativeContentPath))
		{
			return FString();
		}

		return RelativeContentPath;
	}

	UPoseAsset* LoadTargetPoseAssetRelativeToObject(const FString& PoseAssetPath, const UObject* SourceObject, const FString& SourceFilename, FString& OutResolvedPath)
	{
		OutResolvedPath.Reset();
		if (PoseAssetPath.IsEmpty())
		{
			return nullptr;
		}

		if (UPoseAsset* PoseAsset = LoadObject<UPoseAsset>(nullptr, *PoseAssetPath))
		{
			OutResolvedPath = PoseAssetPath;
			return PoseAsset;
		}

		FString PackagePath;
		FString AssetName;
		if (PoseAssetPath.Split(TEXT("."), &PackagePath, &AssetName, ESearchCase::CaseSensitive, ESearchDir::FromEnd) && !AssetName.IsEmpty())
		{
			// Object path: /Game/Folder/Asset.Asset -> Asset
		}
		else
		{
			AssetName = FPaths::GetBaseFilename(PoseAssetPath);
		}

		if (AssetName.IsEmpty())
		{
			return nullptr;
		}

		TArray<FString> CandidatePackageDirectories;
		const UPackage* SourcePackage = SourceObject != nullptr ? SourceObject->GetOutermost() : nullptr;
		const FString SourcePackageName = SourcePackage != nullptr ? SourcePackage->GetName() : FString();
		if (FPackageName::IsValidLongPackageName(SourcePackageName))
		{
			AddUniquePackageDirectory(CandidatePackageDirectories, FPackageName::GetLongPackagePath(SourcePackageName));
		}
		AddUniquePackageDirectory(CandidatePackageDirectories, TryConvertFilenameDirectoryToPackagePath(SourceFilename));

		for (const FString& CandidatePackageDirectory : CandidatePackageDirectories)
		{
			const FString SameDirectoryObjectPath = FString::Printf(TEXT("%s/%s.%s"), *CandidatePackageDirectory, *AssetName, *AssetName);
			OutResolvedPath = SameDirectoryObjectPath;
			if (UPoseAsset* PoseAsset = LoadObject<UPoseAsset>(nullptr, *SameDirectoryObjectPath))
			{
				return PoseAsset;
			}
		}

		return nullptr;
	}

	UPoseAsset* LoadRecognizerTargetPoseAsset(const FString& PoseAssetPath, const UObject* SourceObject, const FString& SourceFilename, FString& OutResolvedPath)
	{
		return LoadTargetPoseAssetRelativeToObject(PoseAssetPath, SourceObject, SourceFilename, OutResolvedPath);
	}

	FString StripRecognizerSuffix(const FString& Name)
	{
		FString BaseName = Name;
		BaseName.RemoveFromEnd(TEXT("_SemanticRecognizer"), ESearchCase::IgnoreCase);
		BaseName.RemoveFromEnd(TEXT("_Recognizer"), ESearchCase::IgnoreCase);
		return BaseName;
	}

	void AddUniquePoseAssetCandidate(TArray<FString>& InOutCandidates, const FString& Candidate)
	{
		if (!Candidate.IsEmpty())
		{
			InOutCandidates.AddUnique(Candidate);
		}
	}

	UPoseAsset* ResolveRecognizerTargetPoseAsset(const FString& PoseAssetPath, const FString& PoseNameString, const UObject* SourceObject, const FString& SourceFilename, FString& OutResolvedPath)
	{
		if (!PoseAssetPath.IsEmpty())
		{
			if (UPoseAsset* LoadedPoseAsset = LoadRecognizerTargetPoseAsset(PoseAssetPath, SourceObject, SourceFilename, OutResolvedPath))
			{
				return LoadedPoseAsset;
			}
		}

		TArray<FString> CandidateNames;
		AddUniquePoseAssetCandidate(CandidateNames, PoseNameString);
		AddUniquePoseAssetCandidate(CandidateNames, FString::Printf(TEXT("%s_OpenXRHandPose"), *PoseNameString));
		AddUniquePoseAssetCandidate(CandidateNames, FString::Printf(TEXT("PICO_%s_OpenXRHandPose"), *PoseNameString));

		const FString SourceBaseName = StripRecognizerSuffix(FPaths::GetBaseFilename(SourceFilename));
		AddUniquePoseAssetCandidate(CandidateNames, SourceBaseName);
		AddUniquePoseAssetCandidate(CandidateNames, FString::Printf(TEXT("%s_OpenXRHandPose"), *SourceBaseName));

		const FString AssetBaseName = SourceObject != nullptr ? StripRecognizerSuffix(SourceObject->GetName()) : FString();
		AddUniquePoseAssetCandidate(CandidateNames, AssetBaseName);
		AddUniquePoseAssetCandidate(CandidateNames, FString::Printf(TEXT("%s_OpenXRHandPose"), *AssetBaseName));

		for (const FString& CandidateName : CandidateNames)
		{
			if (UPoseAsset* LoadedPoseAsset = LoadRecognizerTargetPoseAsset(CandidateName, SourceObject, SourceFilename, OutResolvedPath))
			{
				return LoadedPoseAsset;
			}
		}

		return nullptr;
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

	bool ImportRecognizerJsonToRecognizerAssetInternal(const FString& JsonString, UPICOHandGestureRecognizerAsset* RecognizerAsset, const FString& SourceFilename, FString& OutError);
	bool ImportSemanticRecognizerJsonToRecognizerAssetInternal(const FString& JsonString, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, const FString& SourceFilename, FString& OutError);

	bool BuildTargetPoseTransforms(const UPoseAsset* PoseAsset, int32 PoseIndex, const FReferenceSkeleton& RefSkeleton, TArray<FTransform>& OutLocalTransforms, TArray<FTransform>& OutComponentTransforms)
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

		const int32 NumBones = RefSkeleton.GetNum();
		OutComponentTransforms.SetNum(NumBones);
		OutLocalTransforms = RefSkeleton.GetRefBonePose();
		const TArray<FName>& TrackNames = PoseAsset->GetTrackNames();

		for (const FPoseAssetInfluenceForPose& Influence : TargetInfluences)
		{
			if (TrackNames.IsValidIndex(Influence.TrackIndex) && TargetInfluencedLocalTransforms.IsValidIndex(Influence.BoneTransformIndex))
			{
				const int32 BoneIndex = RefSkeleton.FindBoneIndex(TrackNames[Influence.TrackIndex]);
				if (OutLocalTransforms.IsValidIndex(BoneIndex))
				{
					OutLocalTransforms[BoneIndex] = TargetInfluencedLocalTransforms[Influence.BoneTransformIndex];
				}
			}
		}

		for (int32 BoneIndex = 0; BoneIndex < NumBones; ++BoneIndex)
		{
			const int32 ParentIndex = RefSkeleton.GetParentIndex(BoneIndex);
			OutComponentTransforms[BoneIndex] = ParentIndex != INDEX_NONE
				? OutLocalTransforms[BoneIndex] * OutComponentTransforms[ParentIndex]
				: OutLocalTransforms[BoneIndex];
		}

		return true;
	}

	bool ExtractSemanticPoseFeaturesFromPoseAsset(const UPoseAsset* PoseAsset, FName PoseName, FPICOHandSemanticFeatures& OutFeatures, FString& OutError)
	{
		OutFeatures = FPICOHandSemanticFeatures();
		if (PoseAsset == nullptr)
		{
			OutError = TEXT("PoseAsset is null.");
			return false;
		}

		const int32 PoseIndex = ResolvePoseIndex(PoseAsset, PoseName);
		if (PoseIndex == INDEX_NONE)
		{
			OutError = TEXT("Failed to resolve pose index for semantic recognizer generation.");
			return false;
		}

		USkeleton* Skeleton = PoseAsset->GetSkeleton();
		if (Skeleton == nullptr)
		{
			OutError = TEXT("PoseAsset skeleton is null.");
			return false;
		}

		const FReferenceSkeleton& RefSkeleton = Skeleton->GetReferenceSkeleton();
		TArray<FTransform> LocalTransforms;
		TArray<FTransform> ComponentTransforms;
		if (!BuildTargetPoseTransforms(PoseAsset, PoseIndex, RefSkeleton, LocalTransforms, ComponentTransforms))
		{
			OutError = TEXT("Failed to build pose transforms for semantic recognizer generation.");
			return false;
		}

		const TCHAR* HandPrefix = nullptr;
		if (!ResolveHandPrefix(PoseAsset->GetTrackNames(), HandPrefix))
		{
			OutError = TEXT("Semantic recognizer generation requires a built-in PICO OpenXR hand PoseAsset.");
			return false;
		}

		TMap<EHandKeypoint, FName> BoneMappings;
		const bool bIsRightHand = FCString::Stricmp(HandPrefix, TEXT("right")) == 0;
		PICOHandGestureSemantic::BuildDefaultBoneMappings(bIsRightHand, BoneMappings);

		if (!PICOHandGestureSemantic::ExtractSemanticFeatures(bIsRightHand, RefSkeleton, BoneMappings, LocalTransforms, ComponentTransforms, OutFeatures, &OutError))
		{
			return false;
		}

		return true;
	}

	bool ParseOpenXRHandPoseJson(const FString& JsonString, TArray<FParsedOpenXRJointPose>& OutJointPoses, FString& OutError, FName* OutPoseName = nullptr)
	{
		TSharedPtr<FJsonObject> RootObject;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
		if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
		{
			OutError = TEXT("Failed to parse JSON.");
			return false;
		}

		const TArray<TSharedPtr<FJsonValue>>* JointValues = nullptr;
		if (!RootObject->TryGetArrayField(TEXT("joints"), JointValues) || !JointValues)
		{
			OutError = TEXT("JSON does not contain a valid 'joints' array.");
			return false;
		}

		if (OutPoseName)
		{
			FString PoseNameString;
			*OutPoseName = RootObject->TryGetStringField(TEXT("pose_name"), PoseNameString) && !PoseNameString.IsEmpty()
				? FName(*PoseNameString)
				: NAME_None;
		}

		if (JointValues->Num() != UE_ARRAY_COUNT(OpenXRJointMappings))
		{
			OutError = FString::Printf(TEXT("Expected %d joints, found %d."), UE_ARRAY_COUNT(OpenXRJointMappings), JointValues->Num());
			return false;
		}

		TSet<FString> SeenXRJoints;
		OutJointPoses.Reset();
		OutJointPoses.Reserve(JointValues->Num());

		for (int32 JointIndex = 0; JointIndex < JointValues->Num(); ++JointIndex)
		{
			const TSharedPtr<FJsonObject>* JointObject = nullptr;
			if (!(*JointValues)[JointIndex].IsValid() || !(*JointValues)[JointIndex]->TryGetObject(JointObject) || !JointObject || !JointObject->IsValid())
			{
				OutError = FString::Printf(TEXT("Joint entry %d is invalid."), JointIndex);
				return false;
			}

			FString XRJointName;
			FString BoneNameString;
			if (!(*JointObject)->TryGetStringField(TEXT("xr_joint"), XRJointName) ||
				!(*JointObject)->TryGetStringField(TEXT("bone_name"), BoneNameString))
			{
				OutError = FString::Printf(TEXT("Joint entry %d is missing 'xr_joint' or 'bone_name'."), JointIndex);
				return false;
			}

			const FOpenXRJointExportMapping* Mapping = FindMappingByXRJointName(XRJointName);
			if (!Mapping)
			{
				OutError = FString::Printf(TEXT("Unsupported xr_joint '%s'."), *XRJointName);
				return false;
			}

			if (SeenXRJoints.Contains(XRJointName))
			{
				OutError = FString::Printf(TEXT("Duplicate xr_joint '%s'."), *XRJointName);
				return false;
			}
			SeenXRJoints.Add(XRJointName);

			FTransform Transform;
			if (!JsonObjectToTransform(*JointObject, TEXT("transform"), Transform))
			{
				OutError = FString::Printf(TEXT("Joint '%s' has an invalid transform."), *XRJointName);
				return false;
			}

			FParsedOpenXRJointPose& JointPose = OutJointPoses.AddDefaulted_GetRef();
			JointPose.XRJointName = XRJointName;
			JointPose.BoneName = FName(*BoneNameString);
			JointPose.Transform = Transform;
		}

		return true;
	}

	bool BuildOpenXRHandLocalTransformsFromJson(const FString& JsonString, USkeletalMesh*& OutHandMesh, USkeleton*& OutSkeleton, const TCHAR*& OutHandPrefix, TArray<FTransform>& OutLocalTransforms, FString& OutError, FName* OutPoseName = nullptr)
	{
		TArray<FParsedOpenXRJointPose> JointPoses;
		if (!ParseOpenXRHandPoseJson(JsonString, JointPoses, OutError, OutPoseName))
		{
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		if (!ResolveHandPrefixFromBoneNames(JointPoses, OutHandPrefix))
		{
			OutError = TEXT("Joint bone names are not consistently left_* or right_*.");
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		if (!LoadBuiltInHandAssets(OutHandPrefix, OutHandMesh, OutSkeleton, OutError))
		{
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		const FReferenceSkeleton& RefSkeleton = OutSkeleton->GetReferenceSkeleton();
		OutLocalTransforms = RefSkeleton.GetRefBonePose();

		for (const FOpenXRJointExportMapping& Mapping : OpenXRJointMappings)
		{
			const FParsedOpenXRJointPose* JointPose = JointPoses.FindByPredicate([&Mapping](const FParsedOpenXRJointPose& InJointPose)
			{
				return InJointPose.XRJointName == Mapping.XRJointName;
			});

			if (!JointPose)
			{
				OutError = FString::Printf(TEXT("Missing required joint '%s'."), Mapping.XRJointName);
				UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
				return false;
			}

			const FName ExpectedBoneName(FCString::Stricmp(OutHandPrefix, TEXT("right")) == 0 ? Mapping.RightBoneName : Mapping.LeftBoneName);
			if (JointPose->BoneName != ExpectedBoneName)
			{
				OutError = FString::Printf(
					TEXT("Joint '%s' expected bone '%s' but found '%s'."),
					Mapping.XRJointName,
					*ExpectedBoneName.ToString(),
					*JointPose->BoneName.ToString());
				UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
				return false;
			}

			const int32 BoneIndex = RefSkeleton.FindBoneIndex(ExpectedBoneName);
			if (BoneIndex == INDEX_NONE)
			{
				OutError = FString::Printf(TEXT("Bone '%s' was not found in the target skeleton."), *ExpectedBoneName.ToString());
				UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
				return false;
			}

			OutLocalTransforms[BoneIndex] = JointPose->Transform;
		}

		return true;
	}

	bool FillAnimSequenceWithLocalTransforms(UAnimSequence* AnimSequence, USkeletalMesh* HandMesh, USkeleton* Skeleton, const TArray<FTransform>& LocalTransforms, FString& OutError)
	{
		if (!AnimSequence)
		{
			OutError = TEXT("AnimSequence is null.");
			return false;
		}

		if (!HandMesh || !Skeleton)
		{
			OutError = TEXT("Target hand mesh or skeleton is null.");
			return false;
		}

		const FReferenceSkeleton& RefSkeleton = Skeleton->GetReferenceSkeleton();
		if (LocalTransforms.Num() != RefSkeleton.GetRefBonePose().Num())
		{
			OutError = FString::Printf(
				TEXT("Local transform count mismatch. Transforms=%d RefPose=%d."),
				LocalTransforms.Num(),
				RefSkeleton.GetRefBonePose().Num());
			return false;
		}

		AnimSequence->SetSkeleton(Skeleton);
		AnimSequence->SetPreviewMesh(HandMesh, false);
		AnimSequence->GetController().InitializeModel();
		if (!AnimSequence->CreateAnimation(HandMesh))
		{
			OutError = TEXT("Failed to create animation sequence from the built-in hand mesh.");
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		IAnimationDataController& Controller = AnimSequence->GetController();
		IAnimationDataController::FScopedBracket ScopedBracket(Controller, NSLOCTEXT("PICOHandGestureEditor", "FillAnimSequenceWithLocalTransforms", "Importing OpenXR hand pose JSON to AnimSequence"), false);
		Controller.SetFrameRate(FFrameRate(30, 1), false);
		Controller.SetNumberOfFrames(1, false);

		for (int32 BoneIndex = 0; BoneIndex < LocalTransforms.Num(); ++BoneIndex)
		{
			const FName BoneName = RefSkeleton.GetBoneName(BoneIndex);
			const FTransform& LocalTransform = LocalTransforms[BoneIndex];
			Controller.SetBoneTrackKeys(
				BoneName,
				TArray<FVector3f>{ FVector3f(LocalTransform.GetTranslation()), FVector3f(LocalTransform.GetTranslation()) },
				TArray<FQuat4f>{ FQuat4f(LocalTransform.GetRotation()), FQuat4f(LocalTransform.GetRotation()) },
				TArray<FVector3f>{ FVector3f(LocalTransform.GetScale3D()), FVector3f(LocalTransform.GetScale3D()) },
				false);
		}

		Controller.NotifyPopulated();
		AnimSequence->MarkPackageDirty();
		AnimSequence->PostEditChange();
		return true;
	}

	bool SerializeJointValuesToJson(const TArray<TSharedPtr<FJsonValue>>& JointValues, FName PoseName, const FString& OutputFilename, FString& OutJson, FString& OutError)
	{
	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
		if (!PoseName.IsNone())
		{
			RootObject->SetStringField(TEXT("pose_name"), PoseName.ToString());
		}
		RootObject->SetArrayField(TEXT("joints"), JointValues);

		const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutJson);
		if (!FJsonSerializer::Serialize(RootObject, Writer))
		{
			OutError = TEXT("Failed to serialize pose JSON.");
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		if (!OutputFilename.IsEmpty())
		{
			const FString AbsoluteOutputFilename = FPaths::ConvertRelativePathToFull(OutputFilename);
			if (!FFileHelper::SaveStringToFile(OutJson, *AbsoluteOutputFilename))
			{
				OutError = FString::Printf(TEXT("Failed to save pose JSON to '%s'."), *AbsoluteOutputFilename);
				UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
				return false;
			}
		}

		return true;
	}

}

bool UPICOHandGestureEditorLibrary::ExportPoseAssetPoseToJson(UPoseAsset* PoseAsset, FName PoseName, const FString& OutputFilename, FString& OutJson, FString& OutError)
{
	OutJson.Reset();
	OutError.Reset();

	if (!PoseAsset)
	{
		OutError = TEXT("PoseAsset is null.");
		return false;
	}

	if (PoseName.IsNone())
	{
		if (PoseAsset->GetNumPoses() <= 0)
		{
			OutError = FString::Printf(TEXT("PoseAsset '%s' does not contain any poses."), *PoseAsset->GetPathName());
			return false;
		}

		PoseName = PoseAsset->GetPoseIndexByName(TEXT("Pose_0")) != INDEX_NONE ? FName(TEXT("Pose_0")) : PoseAsset->GetPoseNameByIndex(0);
	}

	const int32 PoseIndex = PoseAsset->GetPoseIndexByName(PoseName);
	if (PoseIndex == INDEX_NONE)
	{
		OutError = FString::Printf(TEXT("Pose '%s' does not exist in '%s'."), *PoseName.ToString(), *PoseAsset->GetPathName());
		return false;
	}

	TArray<FTransform> FullPose;
	if (!PoseAsset->GetFullPose(PoseIndex, FullPose))
	{
		OutError = FString::Printf(TEXT("Failed to read full pose '%s' from '%s'."), *PoseName.ToString(), *PoseAsset->GetPathName());
		return false;
	}

	const TArray<FName>& TrackNames = PoseAsset->GetTrackNames();
	if (FullPose.Num() != TrackNames.Num())
	{
		OutError = FString::Printf(
			TEXT("Pose data size mismatch. Tracks=%d Full=%d."),
			TrackNames.Num(),
			FullPose.Num());
		return false;
	}

	const TCHAR* HandPrefix = nullptr;
	if (!ResolveHandPrefix(TrackNames, HandPrefix))
	{
		OutError = FString::Printf(
			TEXT("PoseAsset '%s' does not match the expected OpenXR left/right 26-joint bone naming."),
			*PoseAsset->GetPathName());
		UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
		return false;
	}

	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("pose_name"), PoseName.ToString());
	TArray<TSharedPtr<FJsonValue>> JointValues;
	JointValues.Reserve(UE_ARRAY_COUNT(OpenXRJointMappings));

	const bool bIsRightHand = FCString::Stricmp(HandPrefix, TEXT("right")) == 0;
	for (const FOpenXRJointExportMapping& Mapping : OpenXRJointMappings)
	{
		const FName BoneName(bIsRightHand ? Mapping.RightBoneName : Mapping.LeftBoneName);
		const int32 TrackIndex = TrackNames.Find(BoneName);
		if (!FullPose.IsValidIndex(TrackIndex))
		{
			OutError = FString::Printf(
				TEXT("Missing OpenXR joint bone '%s' in PoseAsset '%s'."),
				*BoneName.ToString(),
				*PoseAsset->GetPathName());
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		TSharedRef<FJsonObject> JointObject = MakeShared<FJsonObject>();
		JointObject->SetStringField(TEXT("xr_joint"), Mapping.XRJointName);
		JointObject->SetStringField(TEXT("bone_name"), BoneName.ToString());
		JointObject->SetObjectField(TEXT("transform"), TransformToJsonObject(FullPose[TrackIndex]));

		JointValues.Add(MakeShared<FJsonValueObject>(JointObject));
	}
	RootObject->SetArrayField(TEXT("joints"), JointValues);

	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutJson);
	if (!FJsonSerializer::Serialize(RootObject, Writer))
	{
		OutError = TEXT("Failed to serialize pose JSON.");
		UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
		return false;
	}

	if (!OutputFilename.IsEmpty())
	{
		const FString AbsoluteOutputFilename = FPaths::ConvertRelativePathToFull(OutputFilename);
		if (!FFileHelper::SaveStringToFile(OutJson, *AbsoluteOutputFilename))
		{
			OutError = FString::Printf(TEXT("Failed to save pose JSON to '%s'."), *AbsoluteOutputFilename);
			UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
			return false;
		}

		UE_LOG(
			LogPICOHandGestureEditorLibrary,
			Log,
			TEXT("Exported OpenXR 26-joint pose '%s' from '%s' to '%s'."),
			*PoseName.ToString(),
			*PoseAsset->GetPathName(),
			*AbsoluteOutputFilename);
	}

	return true;
}

bool UPICOHandGestureEditorLibrary::ExportRecognizerAssetToJson(UPICOHandGestureRecognizerAsset* RecognizerAsset, const FString& OutputFilename, FString& OutJson, FString& OutError)
{
	OutJson.Reset();
	OutError.Reset();

	if (!RecognizerAsset)
	{
		OutError = TEXT("RecognizerAsset is null.");
		return false;
	}

	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("schema"), TEXT("PICOOpenXR.HandGestureRecognizer"));
	RootObject->SetNumberField(TEXT("version"), 1);
	RootObject->SetNumberField(TEXT("match_threshold"), FMath::Clamp(RecognizerAsset->MatchThreshold, 0.0f, 1.0f));
	RootObject->SetBoolField(TEXT("use_default_full_pose_rules_when_empty"), RecognizerAsset->bUseDefaultFullPoseRulesWhenEmpty);

	TSharedRef<FJsonObject> TargetPoseObject = MakeShared<FJsonObject>();
	TargetPoseObject->SetStringField(TEXT("pose_asset"), RecognizerAsset->TargetPoseAsset != nullptr ? RecognizerAsset->TargetPoseAsset->GetPathName() : FString());
	TargetPoseObject->SetStringField(TEXT("pose_name"), RecognizerAsset->PoseName.ToString());
	RootObject->SetObjectField(TEXT("target_pose"), TargetPoseObject);

	TArray<TSharedPtr<FJsonValue>> RuleValues;
	RuleValues.Reserve(RecognizerAsset->JointRules.Num());
	for (const FPICOHandGestureJointMatchRule& Rule : RecognizerAsset->JointRules)
	{
		const FOpenXRJointExportMapping* Mapping = FindMappingByKeypoint(Rule.Joint);
		if (Mapping == nullptr)
		{
			OutError = FString::Printf(TEXT("Unsupported recognizer joint enum value %d."), static_cast<int32>(Rule.Joint));
			return false;
		}

		TSharedRef<FJsonObject> RuleObject = MakeShared<FJsonObject>();
		RuleObject->SetStringField(TEXT("joint"), Mapping->XRJointName);
		RuleObject->SetBoolField(TEXT("enabled"), Rule.bEnabled);
		RuleObject->SetBoolField(TEXT("match_rotation"), Rule.bMatchRotation);
		RuleObject->SetBoolField(TEXT("match_position"), Rule.bMatchPosition);
		RuleObject->SetNumberField(TEXT("weight"), FMath::Max(Rule.Weight, 0.0f));
		RuleObject->SetNumberField(TEXT("angular_tolerance_deg"), FMath::Clamp(Rule.AngularToleranceDeg, 1.0f, 180.0f));
		RuleObject->SetNumberField(TEXT("position_tolerance_cm"), FMath::Max(Rule.PositionToleranceCm, 0.1f));
		RuleValues.Add(MakeShared<FJsonValueObject>(RuleObject));
	}
	RootObject->SetArrayField(TEXT("joint_rules"), RuleValues);

	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutJson);
	if (!FJsonSerializer::Serialize(RootObject, Writer))
	{
		OutError = TEXT("Failed to serialize recognizer JSON.");
		return false;
	}

	if (!OutputFilename.IsEmpty())
	{
		const FString AbsoluteOutputFilename = FPaths::ConvertRelativePathToFull(OutputFilename);
		if (!FFileHelper::SaveStringToFile(OutJson, *AbsoluteOutputFilename))
		{
			OutError = FString::Printf(TEXT("Failed to save recognizer JSON to '%s'."), *AbsoluteOutputFilename);
			return false;
		}
	}

	return true;
}

bool UPICOHandGestureEditorLibrary::ExportSemanticRecognizerAssetToJson(UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, const FString& OutputFilename, FString& OutJson, FString& OutError)
{
	OutJson.Reset();
	OutError.Reset();

	if (!RecognizerAsset)
	{
		OutError = TEXT("RecognizerAsset is null.");
		return false;
	}

	TSharedRef<FJsonObject> RootObject = MakeShared<FJsonObject>();
	RootObject->SetStringField(TEXT("schema"), TEXT("PICOOpenXR.HandGestureSemanticRecognizer"));
	RootObject->SetNumberField(TEXT("version"), 1);
	RootObject->SetNumberField(TEXT("match_threshold"), FMath::Clamp(RecognizerAsset->MatchThreshold, 0.0f, 1.0f));

	TSharedRef<FJsonObject> TargetPoseObject = MakeShared<FJsonObject>();
	TargetPoseObject->SetStringField(TEXT("pose_asset"), RecognizerAsset->TargetPoseAsset != nullptr ? RecognizerAsset->TargetPoseAsset->GetPathName() : FString());
	TargetPoseObject->SetStringField(TEXT("pose_name"), RecognizerAsset->PoseName.ToString());
	RootObject->SetObjectField(TEXT("target_pose"), TargetPoseObject);

	TArray<TSharedPtr<FJsonValue>> RuleValues;
	RuleValues.Reserve(RecognizerAsset->FeatureRules.Num());
	for (const FPICOHandSemanticFeatureRule& Rule : RecognizerAsset->FeatureRules)
	{
		TSharedRef<FJsonObject> RuleObject = MakeShared<FJsonObject>();
		RuleObject->SetStringField(TEXT("feature"), PICOHandGestureSemantic::GetFeatureTypeName(Rule.Feature));
		RuleObject->SetBoolField(TEXT("enabled"), Rule.bEnabled);
		RuleObject->SetNumberField(TEXT("target_value"), Rule.TargetValue);
		RuleObject->SetNumberField(TEXT("tolerance"), FMath::Max(Rule.Tolerance, 0.001f));
		RuleObject->SetNumberField(TEXT("weight"), FMath::Max(Rule.Weight, 0.0f));
		RuleObject->SetBoolField(TEXT("required"), Rule.bRequired);
		RuleObject->SetNumberField(TEXT("min_pass_score"), FMath::Clamp(Rule.MinPassScore, 0.0f, 1.0f));
		RuleValues.Add(MakeShared<FJsonValueObject>(RuleObject));
	}
	RootObject->SetArrayField(TEXT("feature_rules"), RuleValues);

	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&OutJson);
	if (!FJsonSerializer::Serialize(RootObject, Writer))
	{
		OutError = TEXT("Failed to serialize semantic recognizer JSON.");
		return false;
	}

	if (!OutputFilename.IsEmpty())
	{
		const FString AbsoluteOutputFilename = FPaths::ConvertRelativePathToFull(OutputFilename);
		if (!FFileHelper::SaveStringToFile(OutJson, *AbsoluteOutputFilename))
		{
			OutError = FString::Printf(TEXT("Failed to save semantic recognizer JSON to '%s'."), *AbsoluteOutputFilename);
			return false;
		}
	}

	return true;
}

bool UPICOHandGestureEditorLibrary::ImportRecognizerJsonFileToRecognizerAsset(const FString& JsonFilename, UPICOHandGestureRecognizerAsset* RecognizerAsset, FString& OutError)
{
	OutError.Reset();

	const FString AbsoluteJsonFilename = FPaths::ConvertRelativePathToFull(JsonFilename);
	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *AbsoluteJsonFilename))
	{
		OutError = FString::Printf(TEXT("Failed to read recognizer JSON file '%s'."), *AbsoluteJsonFilename);
		UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
		return false;
	}

	return ImportRecognizerJsonToRecognizerAssetInternal(JsonString, RecognizerAsset, AbsoluteJsonFilename, OutError);
}

bool UPICOHandGestureEditorLibrary::ImportRecognizerJsonToRecognizerAsset(const FString& JsonString, UPICOHandGestureRecognizerAsset* RecognizerAsset, FString& OutError)
{
	return ImportRecognizerJsonToRecognizerAssetInternal(JsonString, RecognizerAsset, FString(), OutError);
}

namespace
{
bool ImportRecognizerJsonToRecognizerAssetInternal(const FString& JsonString, UPICOHandGestureRecognizerAsset* RecognizerAsset, const FString& SourceFilename, FString& OutError)
{
	OutError.Reset();

	if (!RecognizerAsset)
	{
		OutError = TEXT("RecognizerAsset is null.");
		return false;
	}

	TSharedPtr<FJsonObject> RootObject;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
	{
		OutError = TEXT("Failed to parse recognizer JSON.");
		return false;
	}

	FString Schema;
	if (!RootObject->TryGetStringField(TEXT("schema"), Schema) || Schema != TEXT("PICOOpenXR.HandGestureRecognizer"))
	{
		OutError = TEXT("Recognizer JSON has an invalid or missing schema.");
		return false;
	}

	float ImportedMatchThreshold = RecognizerAsset->MatchThreshold;
	bool bImportedUseDefaultRules = RecognizerAsset->bUseDefaultFullPoseRulesWhenEmpty;
	UPoseAsset* ImportedTargetPoseAsset = RecognizerAsset->TargetPoseAsset;
	FName ImportedPoseName = RecognizerAsset->PoseName;
	TArray<FPICOHandGestureJointMatchRule> ImportedJointRules = RecognizerAsset->JointRules;

	double MatchThreshold = ImportedMatchThreshold;
	RootObject->TryGetNumberField(TEXT("match_threshold"), MatchThreshold);
	ImportedMatchThreshold = FMath::Clamp(static_cast<float>(MatchThreshold), 0.0f, 1.0f);

	bool bUseDefaultRules = bImportedUseDefaultRules;
	if (RootObject->TryGetBoolField(TEXT("use_default_full_pose_rules_when_empty"), bUseDefaultRules))
	{
		bImportedUseDefaultRules = bUseDefaultRules;
	}

	const TSharedPtr<FJsonObject>* TargetPoseObject = nullptr;
	if (RootObject->TryGetObjectField(TEXT("target_pose"), TargetPoseObject) && TargetPoseObject != nullptr && TargetPoseObject->IsValid())
	{
		FString PoseAssetPath;
		(*TargetPoseObject)->TryGetStringField(TEXT("pose_asset"), PoseAssetPath);

		FString PoseNameString;
		if ((*TargetPoseObject)->TryGetStringField(TEXT("pose_name"), PoseNameString))
		{
			ImportedPoseName = PoseNameString.IsEmpty() ? NAME_None : FName(*PoseNameString);
		}

		FString ResolvedPoseAssetPath;
		UPoseAsset* LoadedPoseAsset = ResolveRecognizerTargetPoseAsset(PoseAssetPath, PoseNameString, RecognizerAsset, SourceFilename, ResolvedPoseAssetPath);
		if (LoadedPoseAsset != nullptr)
		{
			ImportedTargetPoseAsset = LoadedPoseAsset;
		}
		else if (!PoseAssetPath.IsEmpty())
		{
			OutError = FString::Printf(TEXT("Failed to load pose asset '%s'. Also tried same-directory path '%s'."), *PoseAssetPath, *ResolvedPoseAssetPath);
			return false;
		}

	}

	const TArray<TSharedPtr<FJsonValue>>* RuleValues = nullptr;
	if (RootObject->TryGetArrayField(TEXT("joint_rules"), RuleValues) && RuleValues != nullptr)
	{
		ImportedJointRules.Reset();
		for (int32 RuleIndex = 0; RuleIndex < RuleValues->Num(); ++RuleIndex)
		{
			const TSharedPtr<FJsonObject>* RuleObject = nullptr;
			if (!(*RuleValues)[RuleIndex].IsValid() || !(*RuleValues)[RuleIndex]->TryGetObject(RuleObject) || RuleObject == nullptr || !RuleObject->IsValid())
			{
				OutError = FString::Printf(TEXT("Recognizer rule entry %d is not an object."), RuleIndex);
				return false;
			}

			FString XRJointName;
			if (!(*RuleObject)->TryGetStringField(TEXT("joint"), XRJointName))
			{
				OutError = FString::Printf(TEXT("Recognizer rule entry %d is missing 'joint'."), RuleIndex);
				return false;
			}

			EHandKeypoint Keypoint = EHandKeypoint::Palm;
			if (!TryGetKeypointByXRJointName(XRJointName, Keypoint))
			{
				OutError = FString::Printf(TEXT("Recognizer rule entry %d has unsupported joint '%s'."), RuleIndex, *XRJointName);
				return false;
			}

			FPICOHandGestureJointMatchRule& Rule = ImportedJointRules.AddDefaulted_GetRef();
			Rule.Joint = Keypoint;

			bool bBoolValue = Rule.bEnabled;
			if ((*RuleObject)->TryGetBoolField(TEXT("enabled"), bBoolValue))
			{
				Rule.bEnabled = bBoolValue;
			}
			bBoolValue = Rule.bMatchRotation;
			if ((*RuleObject)->TryGetBoolField(TEXT("match_rotation"), bBoolValue))
			{
				Rule.bMatchRotation = bBoolValue;
			}
			bBoolValue = Rule.bMatchPosition;
			if ((*RuleObject)->TryGetBoolField(TEXT("match_position"), bBoolValue))
			{
				Rule.bMatchPosition = bBoolValue;
			}

			double NumberValue = Rule.Weight;
			if ((*RuleObject)->TryGetNumberField(TEXT("weight"), NumberValue))
			{
				Rule.Weight = FMath::Max(static_cast<float>(NumberValue), 0.0f);
			}
			NumberValue = Rule.AngularToleranceDeg;
			if ((*RuleObject)->TryGetNumberField(TEXT("angular_tolerance_deg"), NumberValue))
			{
				Rule.AngularToleranceDeg = FMath::Clamp(static_cast<float>(NumberValue), 1.0f, 180.0f);
			}
			NumberValue = Rule.PositionToleranceCm;
			if ((*RuleObject)->TryGetNumberField(TEXT("position_tolerance_cm"), NumberValue))
			{
				Rule.PositionToleranceCm = FMath::Max(static_cast<float>(NumberValue), 0.1f);
			}
		}
	}

	RecognizerAsset->MatchThreshold = ImportedMatchThreshold;
	RecognizerAsset->bUseDefaultFullPoseRulesWhenEmpty = bImportedUseDefaultRules;
	RecognizerAsset->TargetPoseAsset = ImportedTargetPoseAsset;
	RecognizerAsset->PoseName = ImportedPoseName;
	RecognizerAsset->JointRules = MoveTemp(ImportedJointRules);
	RecognizerAsset->MarkPackageDirty();
	RecognizerAsset->PostEditChange();
	return true;
}
}

bool UPICOHandGestureEditorLibrary::ImportSemanticRecognizerJsonFileToRecognizerAsset(const FString& JsonFilename, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, FString& OutError)
{
	OutError.Reset();

	const FString AbsoluteJsonFilename = FPaths::ConvertRelativePathToFull(JsonFilename);
	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *AbsoluteJsonFilename))
	{
		OutError = FString::Printf(TEXT("Failed to read semantic recognizer JSON file '%s'."), *AbsoluteJsonFilename);
		UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
		return false;
	}

	return ImportSemanticRecognizerJsonToRecognizerAssetInternal(JsonString, RecognizerAsset, AbsoluteJsonFilename, OutError);
}

bool UPICOHandGestureEditorLibrary::ImportSemanticRecognizerJsonToRecognizerAsset(const FString& JsonString, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, FString& OutError)
{
	return ImportSemanticRecognizerJsonToRecognizerAssetInternal(JsonString, RecognizerAsset, FString(), OutError);
}

namespace
{
bool ImportSemanticRecognizerJsonToRecognizerAssetInternal(const FString& JsonString, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, const FString& SourceFilename, FString& OutError)
{
	OutError.Reset();

	if (!RecognizerAsset)
	{
		OutError = TEXT("RecognizerAsset is null.");
		return false;
	}

	TSharedPtr<FJsonObject> RootObject;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonString);
	if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
	{
		OutError = TEXT("Failed to parse semantic recognizer JSON.");
		return false;
	}

	FString Schema;
	if (!RootObject->TryGetStringField(TEXT("schema"), Schema) || Schema != TEXT("PICOOpenXR.HandGestureSemanticRecognizer"))
	{
		OutError = TEXT("Semantic recognizer JSON has an invalid or missing schema.");
		return false;
	}

	float ImportedMatchThreshold = RecognizerAsset->MatchThreshold;
	UPoseAsset* ImportedTargetPoseAsset = RecognizerAsset->TargetPoseAsset;
	FName ImportedPoseName = RecognizerAsset->PoseName;
	TArray<FPICOHandSemanticFeatureRule> ImportedFeatureRules = RecognizerAsset->FeatureRules;

	double MatchThreshold = ImportedMatchThreshold;
	RootObject->TryGetNumberField(TEXT("match_threshold"), MatchThreshold);
	ImportedMatchThreshold = FMath::Clamp(static_cast<float>(MatchThreshold), 0.0f, 1.0f);

	const TSharedPtr<FJsonObject>* TargetPoseObject = nullptr;
	if (RootObject->TryGetObjectField(TEXT("target_pose"), TargetPoseObject) && TargetPoseObject != nullptr && TargetPoseObject->IsValid())
	{
		FString PoseAssetPath;
		(*TargetPoseObject)->TryGetStringField(TEXT("pose_asset"), PoseAssetPath);

		FString PoseNameString;
		if ((*TargetPoseObject)->TryGetStringField(TEXT("pose_name"), PoseNameString))
		{
			ImportedPoseName = PoseNameString.IsEmpty() ? NAME_None : FName(*PoseNameString);
		}

		FString ResolvedPoseAssetPath;
		UPoseAsset* LoadedPoseAsset = ResolveRecognizerTargetPoseAsset(PoseAssetPath, PoseNameString, RecognizerAsset, SourceFilename, ResolvedPoseAssetPath);
		if (LoadedPoseAsset != nullptr)
		{
			ImportedTargetPoseAsset = LoadedPoseAsset;
		}
		else if (!PoseAssetPath.IsEmpty())
		{
			OutError = FString::Printf(TEXT("Failed to load pose asset '%s'. Also tried same-directory path '%s'."), *PoseAssetPath, *ResolvedPoseAssetPath);
			return false;
		}
	}

	const TArray<TSharedPtr<FJsonValue>>* RuleValues = nullptr;
	if (RootObject->TryGetArrayField(TEXT("feature_rules"), RuleValues) && RuleValues != nullptr)
	{
		ImportedFeatureRules.Reset();
		for (int32 RuleIndex = 0; RuleIndex < RuleValues->Num(); ++RuleIndex)
		{
			const TSharedPtr<FJsonObject>* RuleObject = nullptr;
			if (!(*RuleValues)[RuleIndex].IsValid() || !(*RuleValues)[RuleIndex]->TryGetObject(RuleObject) || RuleObject == nullptr || !RuleObject->IsValid())
			{
				OutError = FString::Printf(TEXT("Semantic rule entry %d is not an object."), RuleIndex);
				return false;
			}

			FString FeatureName;
			if (!(*RuleObject)->TryGetStringField(TEXT("feature"), FeatureName))
			{
				OutError = FString::Printf(TEXT("Semantic rule entry %d is missing 'feature'."), RuleIndex);
				return false;
			}

			EPICOHandSemanticFeatureType FeatureType = EPICOHandSemanticFeatureType::ThumbCurl;
			if (!PICOHandGestureSemantic::TryParseFeatureType(FeatureName, FeatureType))
			{
				OutError = FString::Printf(TEXT("Semantic rule entry %d has unsupported feature '%s'."), RuleIndex, *FeatureName);
				return false;
			}

			FPICOHandSemanticFeatureRule& Rule = ImportedFeatureRules.AddDefaulted_GetRef();
			Rule.Feature = FeatureType;

			bool bBoolValue = Rule.bEnabled;
			if ((*RuleObject)->TryGetBoolField(TEXT("enabled"), bBoolValue))
			{
				Rule.bEnabled = bBoolValue;
			}
			bBoolValue = Rule.bRequired;
			if ((*RuleObject)->TryGetBoolField(TEXT("required"), bBoolValue))
			{
				Rule.bRequired = bBoolValue;
			}

			double NumberValue = Rule.TargetValue;
			if ((*RuleObject)->TryGetNumberField(TEXT("target_value"), NumberValue))
			{
				Rule.TargetValue = static_cast<float>(NumberValue);
			}
			NumberValue = Rule.Tolerance;
			if ((*RuleObject)->TryGetNumberField(TEXT("tolerance"), NumberValue))
			{
				Rule.Tolerance = FMath::Max(static_cast<float>(NumberValue), 0.001f);
			}
			NumberValue = Rule.Weight;
			if ((*RuleObject)->TryGetNumberField(TEXT("weight"), NumberValue))
			{
				Rule.Weight = FMath::Max(static_cast<float>(NumberValue), 0.0f);
			}
			NumberValue = Rule.MinPassScore;
			if ((*RuleObject)->TryGetNumberField(TEXT("min_pass_score"), NumberValue))
			{
				Rule.MinPassScore = FMath::Clamp(static_cast<float>(NumberValue), 0.0f, 1.0f);
			}
		}
	}

	RecognizerAsset->MatchThreshold = ImportedMatchThreshold;
	RecognizerAsset->TargetPoseAsset = ImportedTargetPoseAsset;
	RecognizerAsset->PoseName = ImportedPoseName;
	RecognizerAsset->FeatureRules = MoveTemp(ImportedFeatureRules);
	RecognizerAsset->MarkPackageDirty();
	RecognizerAsset->PostEditChange();
	return true;
}
}

bool UPICOHandGestureEditorLibrary::InitializeSemanticRecognizerFromPoseAsset(UPoseAsset* PoseAsset, UPICOHandGestureSemanticRecognizerAsset* RecognizerAsset, FString& OutError)
{
	OutError.Reset();

	if (PoseAsset == nullptr || RecognizerAsset == nullptr)
	{
		OutError = TEXT("PoseAsset or RecognizerAsset is null.");
		return false;
	}

	FPICOHandSemanticFeatures PoseFeatures;
	if (!ExtractSemanticPoseFeaturesFromPoseAsset(PoseAsset, NAME_None, PoseFeatures, OutError))
	{
		return false;
	}

	RecognizerAsset->TargetPoseAsset = PoseAsset;
	RecognizerAsset->PoseName = ResolvePoseIndex(PoseAsset, NAME_None) != INDEX_NONE
		? (PoseAsset->GetPoseIndexByName(TEXT("Pose_0")) != INDEX_NONE ? FName(TEXT("Pose_0")) : PoseAsset->GetPoseNameByIndex(0))
		: NAME_None;
	PICOHandGestureSemantic::GenerateSuggestedFeatureRules(PoseFeatures, RecognizerAsset->FeatureRules, RecognizerAsset->MatchThreshold);
	RecognizerAsset->MarkPackageDirty();
	RecognizerAsset->PostEditChange();
	return true;
}

bool UPICOHandGestureEditorLibrary::ImportOpenXRHandPoseJsonFileToPoseAsset(const FString& JsonFilename, UPoseAsset* PoseAsset, FString& OutError)
{
	OutError.Reset();

	const FString AbsoluteJsonFilename = FPaths::ConvertRelativePathToFull(JsonFilename);
	FString JsonString;
	if (!FFileHelper::LoadFileToString(JsonString, *AbsoluteJsonFilename))
	{
		OutError = FString::Printf(TEXT("Failed to read pose JSON file '%s'."), *AbsoluteJsonFilename);
		UE_LOG(LogPICOHandGestureEditorLibrary, Error, TEXT("%s"), *OutError);
		return false;
	}

	return ImportOpenXRHandPoseJsonToPoseAsset(JsonString, PoseAsset, OutError);
}

bool UPICOHandGestureEditorLibrary::ImportOpenXRHandPoseJsonToPoseAsset(const FString& JsonString, UPoseAsset* PoseAsset, FString& OutError)
{
	OutError.Reset();

	if (!PoseAsset)
	{
		OutError = TEXT("PoseAsset is null.");
		return false;
	}

	USkeletalMesh* HandMesh = nullptr;
	USkeleton* Skeleton = nullptr;
	const TCHAR* HandPrefix = nullptr;
	TArray<FTransform> LocalTransforms;
	FName JsonPoseName;
	if (!BuildOpenXRHandLocalTransformsFromJson(JsonString, HandMesh, Skeleton, HandPrefix, LocalTransforms, OutError, &JsonPoseName))
	{
		return false;
	}

	UAnimSequence* TempSequence = NewObject<UAnimSequence>(GetTransientPackage(), NAME_None, RF_Transient);
	if (!FillAnimSequenceWithLocalTransforms(TempSequence, HandMesh, Skeleton, LocalTransforms, OutError))
	{
		return false;
	}

	const FName TargetPoseName = !JsonPoseName.IsNone()
		? JsonPoseName
		: (PoseAsset->GetNumPoses() > 0 ? PoseAsset->GetPoseNameByIndex(0) : FName(TEXT("Pose_0")));

	PoseAsset->SetSkeleton(Skeleton);
	PoseAsset->SetPreviewSkeletalMesh(HandMesh);
	TArray<FName> PoseNames;
	PoseNames.Init(TargetPoseName, FMath::Max(TempSequence->GetNumberOfSampledKeys(), 1));
	PoseAsset->CreatePoseFromAnimation(TempSequence, &PoseNames);
	PoseAsset->MarkPackageDirty();
	PoseAsset->PostEditChange();

	UE_LOG(
		LogPICOHandGestureEditorLibrary,
		Log,
		TEXT("Imported OpenXR 26-joint hand pose into '%s' using the built-in %s hand skeleton."),
		*PoseAsset->GetPathName(),
		HandPrefix);

	return true;
}
