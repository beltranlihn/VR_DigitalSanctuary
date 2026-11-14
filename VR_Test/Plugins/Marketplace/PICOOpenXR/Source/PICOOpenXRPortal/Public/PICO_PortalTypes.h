// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/ObjectMacros.h"
#include "PICO_PortalTypes.generated.h"

UENUM(BlueprintType)
enum class EAppLogTypePICO : uint8
{
	None,
	//Version
	EngineVersion,
	SDKVersion,
	SDKType,
	EngineType,

	PICOXRPortalStartUp,
	ProjectVerificationStartUp,
	PICOSettingsStartUp,
	//Download
	PICODeveloperCenter,
	PICOEmulator,
	//Samples
	GetStartedSample,
	PlatformSample,
	SpatialAudioSample,
	MRSample,
	HandTrackingSample,
	ControllerInteraction,
	BodyTracking,
	//About
	PICODeveloperWebsite,
	DownloadFromPICO_Official,
	DownloadFromUnreal_Fab,
	DownloadPICOForkOfUnrealEngine,
	//Actor
	SpatialMeshActor,
	SpatialAnchorActor,
	SceneCapturesGenerator,
	PICOXRPawn,
	//Components
	HandTrackingComponent,
	EyeTrackingComponent,
	FaceTrackingComponent,
	BodyTrackingComponent,
	//Settings
	DeferredShading,
	ForwardShading,
	MobileHDR,
	LateLatching,
	MovableSpotlight,
	ApplicationSpaceWarp,
	ToneMapping,
	FXAA,
	TAA,
	MSAA,
};

UENUM(BlueprintType)
enum class EVerificationLevelPICO : uint8
{
	None,
	Error,
	Warning,
	Recommended,
};

UENUM(BlueprintType)
enum class EVerificationsStatusPICO : uint8
{
	Required,
	Applied
};

UENUM()
namespace EUnrealEngineTypePICO
{
	enum Type : int
	{
		Official_Engine = 0 UMETA(DisplayName = "Official Engine"),
		PICO_Custom_Engine = 1 UMETA(DisplayName = "PICO Custom Engine"),
	};
}
