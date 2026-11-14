// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "EyeTrackerTypes.h"
#include "GameFramework/Actor.h"
#include "PICO_MovementFunctionLibrary.h"
#include "PICO_EyeTrackingDebugActor.generated.h"

UCLASS(Blueprintable)
class PICOOPENXRMOVEMENT_API APICOEyeTrackingDebugActor : public AActor
{
	GENERATED_BODY()

public:
	APICOEyeTrackingDebugActor();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void Tick(float DeltaSeconds) override;

private:
	bool TryStartEyeTracking();
	void PrintEyeTrackingData(const FEyeDataPICO& LeftEye, const FEyeDataPICO& RightEye, bool bDataValid, bool bDepthValid, float DepthConfidence, float Depth);
	void DrawEyeTrackingData(const FEyeDataPICO& LeftEye, const FEyeDataPICO& RightEye, const FEyeTrackerGazeData& GazeData, bool bGazeDataValid);
	void DrawEyeDebug(const FEyeDataPICO& EyeData, const FColor& Color, const FString& Label) const;

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug")
	bool bStartOnBeginPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug")
	bool bStopOnEndPlay = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug")
	bool bAutoRetryStart = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug", meta = (ClampMin = "0.1"))
	float RetryStartInterval = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug")
	bool bPrintToScreen = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug")
	bool bPrintToLog = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug", meta = (ClampMin = "0.05"))
	float PrintInterval = 0.5f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug")
	bool bDrawDebug = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug", meta = (ClampMin = "1.0"))
	float DebugLineLength = 100.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug", meta = (ClampMin = "0.0"))
	float DebugLifeTime = 0.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "PICO|EyeTracking Debug", meta = (ClampMin = "0.1"))
	float DebugSphereRadius = 2.0f;

private:
	float TimeSinceLastPrint = 0.0f;
	float TimeSinceLastRetry = 0.0f;
	bool bLastSupported = false;
	bool bHasSupportResult = false;
       bool bStartedEyeTracking = false;
};
