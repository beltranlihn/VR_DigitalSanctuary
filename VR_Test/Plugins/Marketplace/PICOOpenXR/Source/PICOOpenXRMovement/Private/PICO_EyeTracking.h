// Copyright 2023 PICO Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "PICO_MovementFunctionLibrary.h"
#include "openxr_pico/private/ext_system_extensions_compat.h"

class FEyeTrackingPICO
{
public:
	FEyeTrackingPICO();
	virtual ~FEyeTrackingPICO() {}

	void GetRequiredExtensions(TArray<const ANSICHAR*>& OutExtensions);
	void GetOptionalExtensions(TArray<const ANSICHAR*>& OutExtensions);
	void PostGetSystem(XrInstance InInstance, XrSystemId InSystem);
	void PostCreateSession(XrSession InSession);
       void OnDestroySession(XrSession InSession);
	const void* OnBeginSession(XrSession InSession, const void* InNext);
	void UpdateDeviceLocations(XrSession InSession, XrTime DisplayTime, XrSpace TrackingSpace);

	bool IsEyeTrackerSupported(bool& Supported);
	bool IsEyeTrackingRunning() { return bIsEyeTrackingRunning; }
	bool StartEyeTracking();
	bool StopEyeTracking();
	bool GetEyeTrackingData(FEyeDataPICO& LeftEye, FEyeDataPICO& RightEye, bool& bDepthValid, float& DepthConfidence, float& Depth, bool QueryGazeData, FEyeTrackerGazeData& OutGazeData);


private:
       void RefreshActiveEyeTrackerBackend();

	enum class EEyeTrackerBackend : uint8
	{
		None,
		BD,
		PICO
	};

	XrSession Session = XR_NULL_HANDLE;

	PFN_xrCreateEyeTrackerBD xrCreateEyeTrackerBD = nullptr;
	PFN_xrDestroyEyeTrackerBD xrDestroyEyeTrackerBD = nullptr;
	PFN_xrGetEyeDataBD xrGetEyeDataBD = nullptr;
	PFN_xrGetEyeGazeBD xrGetEyeGazeBD = nullptr;
	PFN_xrEnumerateSystemExtensionPropertiesEXT xrEnumerateSystemExtensionPropertiesEXT = nullptr;

	PFN_xrCreateEyeTrackerPICO xrCreateEyeTrackerPICO = nullptr;
	PFN_xrDestroyEyeTrackerPICO xrDestroyEyeTrackerPICO = nullptr;
	PFN_xrGetEyeDataPICO xrGetEyeDataPICO = nullptr;
	PFN_xrGetEyeGazePICO xrGetEyeGazePICO = nullptr;

	bool bBDEyeTrackerSupported = false;
	bool bPICOEyeTrackerSupported = false;
	bool bIsEyeTrackerSupported = false;
	bool bIsEyeTrackingRunning = false;
	EEyeTrackerBackend ActiveEyeTrackerBackend = EEyeTrackerBackend::None;

	XrEyeTrackerBD EyeTrackerBD = XR_NULL_HANDLE;
	XrEyeTrackerPICO EyeTrackerPICO = XR_NULL_HANDLE;
	XrTime DisplayTime = 0;
	XrSpace TrackingSpace = XR_NULL_HANDLE;

	class IXRTrackingSystem* XRTrackingSystem = nullptr;
};
