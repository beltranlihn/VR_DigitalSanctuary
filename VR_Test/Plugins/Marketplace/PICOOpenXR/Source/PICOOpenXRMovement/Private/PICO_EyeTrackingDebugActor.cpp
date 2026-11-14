// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_EyeTrackingDebugActor.h"

#include "DrawDebugHelpers.h"
#include "Engine/Engine.h"

APICOEyeTrackingDebugActor::APICOEyeTrackingDebugActor()
{
	PrimaryActorTick.bCanEverTick = true;
}

void APICOEyeTrackingDebugActor::BeginPlay()
{
	Super::BeginPlay();

	if (bStartOnBeginPlay)
	{
		TryStartEyeTracking();
	}
}

void APICOEyeTrackingDebugActor::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
       if (bStopOnEndPlay && bStartedEyeTracking && UMovementFunctionLibraryPICO::IsEyeTrackingRunningPICO())
	{
		UMovementFunctionLibraryPICO::StopEyeTrackingPICO();
	}
       bStartedEyeTracking = false;

	Super::EndPlay(EndPlayReason);
}

void APICOEyeTrackingDebugActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	TimeSinceLastPrint += DeltaSeconds;
	TimeSinceLastRetry += DeltaSeconds;

	if (bAutoRetryStart && !UMovementFunctionLibraryPICO::IsEyeTrackingRunningPICO() && TimeSinceLastRetry >= RetryStartInterval)
	{
		TimeSinceLastRetry = 0.0f;
		TryStartEyeTracking();
	}

	FEyeDataPICO LeftEye;
	FEyeDataPICO RightEye;
	FEyeTrackerGazeData GazeData;
	bool bDepthValid = false;
	float DepthConfidence = 0.0f;
	float Depth = 0.0f;

	const bool bDataValid = UMovementFunctionLibraryPICO::GetEyeTrackingDataPICO(
		LeftEye,
		RightEye,
		bDepthValid,
		DepthConfidence,
		Depth,
		true,
		GazeData);

	if (bDrawDebug)
	{
		DrawEyeTrackingData(LeftEye, RightEye, GazeData, bDataValid);
	}

	if (TimeSinceLastPrint >= PrintInterval)
	{
		TimeSinceLastPrint = 0.0f;
		PrintEyeTrackingData(LeftEye, RightEye, bDataValid, bDepthValid, DepthConfidence, Depth);
	}
}

bool APICOEyeTrackingDebugActor::TryStartEyeTracking()
{
	bool bSupported = false;
	bHasSupportResult = UMovementFunctionLibraryPICO::IsEyeTrackerSupportedPICO(bSupported);
	bLastSupported = bSupported;

       const bool bWasRunning = UMovementFunctionLibraryPICO::IsEyeTrackingRunningPICO();
       const bool bStarted = bSupported && UMovementFunctionLibraryPICO::StartEyeTrackingPICO();
       bStartedEyeTracking |= bStarted && !bWasRunning;

	if (bPrintToLog)
	{
		UE_LOG(LogTemp, Log, TEXT("PICO ET Debug: IsEyeTrackerSupported call=%d supported=%d StartEyeTracking=%d Running=%d"),
			bHasSupportResult ? 1 : 0,
			bLastSupported ? 1 : 0,
			bStarted ? 1 : 0,
			UMovementFunctionLibraryPICO::IsEyeTrackingRunningPICO() ? 1 : 0);
	}

	if (bPrintToScreen && GEngine != nullptr)
	{
		const FString Message = FString::Printf(TEXT("PICO ET Start: supportCall=%d supported=%d started=%d running=%d"),
			bHasSupportResult ? 1 : 0,
			bLastSupported ? 1 : 0,
			bStarted ? 1 : 0,
			UMovementFunctionLibraryPICO::IsEyeTrackingRunningPICO() ? 1 : 0);
		GEngine->AddOnScreenDebugMessage(reinterpret_cast<uint64>(this) + 1, 2.0f, bStarted ? FColor::Green : FColor::Red, Message);
	}

	return bStarted;
}

void APICOEyeTrackingDebugActor::PrintEyeTrackingData(const FEyeDataPICO& LeftEye, const FEyeDataPICO& RightEye, bool bDataValid, bool bDepthValid, float DepthConfidence, float Depth)
{
	const FString Message = FString::Printf(
		TEXT("PICO ET data=%d running=%d supported=%d | L pose=%d open=%d %.2f loc=%s rot=%s | R pose=%d open=%d %.2f loc=%s rot=%s | depth=%d conf=%.2f value=%.2f"),
		bDataValid ? 1 : 0,
		UMovementFunctionLibraryPICO::IsEyeTrackingRunningPICO() ? 1 : 0,
		bLastSupported ? 1 : 0,
		LeftEye.bPoseValid ? 1 : 0,
		LeftEye.bOpennessValid ? 1 : 0,
		LeftEye.Openness,
		*LeftEye.Location.ToCompactString(),
		*LeftEye.Rotation.ToCompactString(),
		RightEye.bPoseValid ? 1 : 0,
		RightEye.bOpennessValid ? 1 : 0,
		RightEye.Openness,
		*RightEye.Location.ToCompactString(),
		*RightEye.Rotation.ToCompactString(),
		bDepthValid ? 1 : 0,
		DepthConfidence,
		Depth);

	if (bPrintToLog)
	{
		UE_LOG(LogTemp, Log, TEXT("%s"), *Message);
	}

	if (bPrintToScreen && GEngine != nullptr)
	{
		GEngine->AddOnScreenDebugMessage(reinterpret_cast<uint64>(this) + 2, PrintInterval + 0.1f, bDataValid ? FColor::Green : FColor::Yellow, Message);
	}
}

void APICOEyeTrackingDebugActor::DrawEyeTrackingData(const FEyeDataPICO& LeftEye, const FEyeDataPICO& RightEye, const FEyeTrackerGazeData& GazeData, bool bGazeDataValid)
{
	DrawEyeDebug(LeftEye, FColor::Red, TEXT("L"));
	DrawEyeDebug(RightEye, FColor::Blue, TEXT("R"));

	UWorld* World = GetWorld();
	if (World != nullptr && bGazeDataValid)
	{
		const FVector CombinedEnd = GazeData.GazeOrigin + GazeData.GazeDirection.GetSafeNormal() * DebugLineLength;
		DrawDebugLine(World, GazeData.GazeOrigin, CombinedEnd, FColor::Green, false, DebugLifeTime, 0, 1.5f);
		DrawDebugSphere(World, GazeData.GazeOrigin, DebugSphereRadius * 1.25f, 12, FColor::Green, false, DebugLifeTime);
	}
}

void APICOEyeTrackingDebugActor::DrawEyeDebug(const FEyeDataPICO& EyeData, const FColor& Color, const FString& Label) const
{
	UWorld* World = GetWorld();
	if (World == nullptr || !EyeData.bPoseValid)
	{
		return;
	}

	const FVector Start = EyeData.Location;
	const FVector End = Start + EyeData.Rotation.Vector() * DebugLineLength;
	DrawDebugSphere(World, Start, DebugSphereRadius, 12, Color, false, DebugLifeTime);
	DrawDebugLine(World, Start, End, Color, false, DebugLifeTime, 0, 1.0f);
	DrawDebugCoordinateSystem(World, Start, EyeData.Rotation, DebugSphereRadius * 4.0f, false, DebugLifeTime, 0, 0.5f);
	DrawDebugString(World, Start + FVector(0.0f, 0.0f, DebugSphereRadius * 4.0f), Label, nullptr, Color, DebugLifeTime);
}
