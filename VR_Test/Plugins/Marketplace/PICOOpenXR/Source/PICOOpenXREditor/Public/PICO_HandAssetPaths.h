// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

namespace PICOOpenXREditor
{
	struct FBuiltInHandAssetPaths
	{
		const TCHAR* SkeletalMeshPath;
		const TCHAR* SkeletonPath;
	};

	inline constexpr FBuiltInHandAssetPaths LeftHandAssetPaths = {
		TEXT("/PICOOpenXR/Meshes/Hand/Left/SM_Hand_L.SM_Hand_L"),
		TEXT("/PICOOpenXR/Meshes/Hand/Left/SK_Hand_L.SK_Hand_L")
	};

	inline constexpr FBuiltInHandAssetPaths RightHandAssetPaths = {
		TEXT("/PICOOpenXR/Meshes/Hand/Right/SM_Hand_R.SM_Hand_R"),
		TEXT("/PICOOpenXR/Meshes/Hand/Right/SK_Hand_R.SK_Hand_R")
	};

	inline const FBuiltInHandAssetPaths& GetBuiltInHandAssetPaths(const TCHAR* HandPrefix)
	{
		return FCString::Stricmp(HandPrefix, TEXT("right")) == 0 ? RightHandAssetPaths : LeftHandAssetPaths;
	}
}
