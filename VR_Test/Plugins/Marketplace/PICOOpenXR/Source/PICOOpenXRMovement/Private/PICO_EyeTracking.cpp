// Copyright 2023 PICO Inc. All Rights Reserved.

#include "PICO_EyeTracking.h"
#include "PICO_MovementModule.h"
#include "OpenXRCore.h"
#include "Engine/Engine.h"
#include "IXRTrackingSystem.h"
#include "IOpenXRHMDModule.h"
#include "EyeTrackerTypes.h"
#include "PICO_HMDFunctionLibrary.h"

#if PLATFORM_ANDROID
#include "Android/AndroidApplication.h"
#endif

namespace
{
	bool IsSystemExtensionAvailable(
		PFN_xrEnumerateSystemExtensionPropertiesEXT EnumerateSystemExtensionPropertiesEXT,
		XrInstance InInstance,
		XrSystemId InSystem,
		const ANSICHAR* ExtensionName)
	{
		if (EnumerateSystemExtensionPropertiesEXT == nullptr || ExtensionName == nullptr)
		{
			return false;
		}

		uint32 ExtensionCount = 0;
		XrResult Result = EnumerateSystemExtensionPropertiesEXT(InInstance, InSystem, 0, &ExtensionCount, nullptr);
		if (XR_FAILED(Result))
		{
			return false;
		}

		TArray<XrExtensionProperties> ExtensionProperties;
		ExtensionProperties.SetNum(ExtensionCount);
		for (XrExtensionProperties& Property : ExtensionProperties)
		{
			Property.type = XR_TYPE_EXTENSION_PROPERTIES;
			Property.next = nullptr;
		}

		Result = EnumerateSystemExtensionPropertiesEXT(
			InInstance,
			InSystem,
			static_cast<uint32>(ExtensionProperties.Num()),
			&ExtensionCount,
			ExtensionProperties.GetData());
		if (XR_FAILED(Result))
		{
			return false;
		}

		for (const XrExtensionProperties& Property : ExtensionProperties)
		{
			if (FCStringAnsi::Strcmp(Property.extensionName, ExtensionName) == 0)
			{
				return true;
			}
		}

		return false;
	}

	bool TryGetWorldEyeTransform(
		IXRTrackingSystem* XRTrackingSystem,
		const XrEyeGazeBD& EyeGaze,
		FTransform& OutEyeTransform)
	{
		if (XRTrackingSystem == nullptr || EyeGaze.isValid != XR_TRUE)
		{
			return false;
		}

		const float WorldToMeters = XRTrackingSystem->GetWorldToMetersScale();
		const FTransform EyeTrackerTransform = ToFTransform(EyeGaze.pose, WorldToMeters);
		OutEyeTransform = EyeTrackerTransform * XRTrackingSystem->GetTrackingToWorldTransform();
		return true;
	}

	bool TryGetWorldEyeTransform(
			IXRTrackingSystem* XRTrackingSystem,
			const XrEyeGazePICO& EyeGaze,
			FTransform& OutEyeTransform)
	{
		if (XRTrackingSystem == nullptr || EyeGaze.isValid != XR_TRUE)
		{
			return false;
		}

		const float WorldToMeters = XRTrackingSystem->GetWorldToMetersScale();
		const FTransform EyeTrackerTransform = ToFTransform(EyeGaze.pose, WorldToMeters);
		OutEyeTransform = EyeTrackerTransform * XRTrackingSystem->GetTrackingToWorldTransform();
		return true;
	}

	bool PopulateCombinedGazeData(
		const FTransform* LeftEyeTransform,
		const FTransform* RightEyeTransform,
		const FEyeDataPICO& LeftEye,
		const FEyeDataPICO& RightEye,
		FEyeTrackerGazeData& OutGazeData)
	{
		OutGazeData = FEyeTrackerGazeData();

		FVector CombinedOrigin = FVector::ZeroVector;
		FVector CombinedDirection = FVector::ZeroVector;
		int32 ValidEyeCount = 0;

		if (LeftEyeTransform != nullptr)
		{
			CombinedOrigin += LeftEyeTransform->GetLocation();
			CombinedDirection += LeftEyeTransform->GetRotation().GetForwardVector();
			++ValidEyeCount;
		}

		if (RightEyeTransform != nullptr)
		{
			CombinedOrigin += RightEyeTransform->GetLocation();
			CombinedDirection += RightEyeTransform->GetRotation().GetForwardVector();
			++ValidEyeCount;
		}

		if (ValidEyeCount == 0)
		{
			return false;
		}

		CombinedOrigin /= static_cast<float>(ValidEyeCount);
		CombinedDirection = CombinedDirection.GetSafeNormal();

		OutGazeData.GazeOrigin = CombinedOrigin;
		OutGazeData.GazeDirection = CombinedDirection;
		OutGazeData.ConfidenceValue = ValidEyeCount == 2 ? 1.0f : 0.5f;
		OutGazeData.bIsLeftEyeBlink = LeftEye.bOpennessValid && LeftEye.Openness <= 0.0f;
		OutGazeData.bIsRightEyeBlink = RightEye.bOpennessValid && RightEye.Openness <= 0.0f;
		return true;
	}
}

FEyeTrackingPICO::FEyeTrackingPICO()
{
}

bool FEyeTrackingPICO::IsEyeTrackerSupported(bool& Supported)
{
	Supported = bIsEyeTrackerSupported;
	return bIsEyeTrackerSupported;
}

void FEyeTrackingPICO::GetRequiredExtensions(TArray<const ANSICHAR*>& OutExtensions)
{
}

void FEyeTrackingPICO::GetOptionalExtensions(TArray<const ANSICHAR*>& OutExtensions)
{
	OutExtensions.Add(XR_PICO_EYE_TRACKER_EXTENSION_NAME);
}

void FEyeTrackingPICO::RefreshActiveEyeTrackerBackend()
{
       ActiveEyeTrackerBackend = EEyeTrackerBackend::None;
       if (bBDEyeTrackerSupported &&
		       Session != XR_NULL_HANDLE &&
		       UHMDFunctionLibraryPICO::IsSystemExtensionEnabledForActiveSystemPICO(XR_BD_EYE_TRACKER_EXTENSION_NAME))
       {
	       ActiveEyeTrackerBackend = EEyeTrackerBackend::BD;
       }
       else if (bPICOEyeTrackerSupported)
       {
	       ActiveEyeTrackerBackend = EEyeTrackerBackend::PICO;
       }

       bIsEyeTrackerSupported = ActiveEyeTrackerBackend != EEyeTrackerBackend::None;
}

void FEyeTrackingPICO::PostGetSystem(XrInstance InInstance, XrSystemId InSystem)
{
	xrCreateEyeTrackerBD = nullptr;
	xrDestroyEyeTrackerBD = nullptr;
	xrGetEyeDataBD = nullptr;
	xrGetEyeGazeBD = nullptr;
	xrEnumerateSystemExtensionPropertiesEXT = nullptr;
	xrCreateEyeTrackerPICO = nullptr;
	xrDestroyEyeTrackerPICO = nullptr;
	xrGetEyeDataPICO = nullptr;
	xrGetEyeGazePICO = nullptr;
	bBDEyeTrackerSupported = false;
	bPICOEyeTrackerSupported = false;
	bIsEyeTrackerSupported = false;
	ActiveEyeTrackerBackend = EEyeTrackerBackend::None;

	const bool bSystemExtensionsEnabled = IOpenXRHMDModule::Get().IsExtensionEnabled(XR_EXT_SYSTEM_EXTENSIONS_EXTENSION_NAME);
	if (bSystemExtensionsEnabled)
	{
		xrGetInstanceProcAddr(InInstance, "xrEnumerateSystemExtensionPropertiesEXT", (PFN_xrVoidFunction*)&xrEnumerateSystemExtensionPropertiesEXT);
		xrGetInstanceProcAddr(InInstance, "xrCreateEyeTrackerBD", (PFN_xrVoidFunction*)&xrCreateEyeTrackerBD);
		xrGetInstanceProcAddr(InInstance, "xrDestroyEyeTrackerBD", (PFN_xrVoidFunction*)&xrDestroyEyeTrackerBD);
		xrGetInstanceProcAddr(InInstance, "xrGetEyeDataBD", (PFN_xrVoidFunction*)&xrGetEyeDataBD);
		xrGetInstanceProcAddr(InInstance, "xrGetEyeGazeBD", (PFN_xrVoidFunction*)&xrGetEyeGazeBD);

		bBDEyeTrackerSupported =
				xrCreateEyeTrackerBD != nullptr &&
				xrDestroyEyeTrackerBD != nullptr &&
				xrGetEyeDataBD != nullptr &&
				xrGetEyeGazeBD != nullptr &&
				IsSystemExtensionAvailable(
						xrEnumerateSystemExtensionPropertiesEXT,
						InInstance,
						InSystem,
						XR_BD_EYE_TRACKER_EXTENSION_NAME);
	}

	xrGetInstanceProcAddr(InInstance, "xrCreateEyeTrackerPICO", (PFN_xrVoidFunction*)&xrCreateEyeTrackerPICO);
	xrGetInstanceProcAddr(InInstance, "xrDestroyEyeTrackerPICO", (PFN_xrVoidFunction*)&xrDestroyEyeTrackerPICO);
	xrGetInstanceProcAddr(InInstance, "xrGetEyeDataPICO", (PFN_xrVoidFunction*)&xrGetEyeDataPICO);
	xrGetInstanceProcAddr(InInstance, "xrGetEyeGazePICO", (PFN_xrVoidFunction*)&xrGetEyeGazePICO);

	bPICOEyeTrackerSupported =
			IOpenXRHMDModule::Get().IsExtensionEnabled(XR_PICO_EYE_TRACKER_EXTENSION_NAME) &&
			xrCreateEyeTrackerPICO != nullptr &&
			xrDestroyEyeTrackerPICO != nullptr &&
			xrGetEyeDataPICO != nullptr &&
			xrGetEyeGazePICO != nullptr;

	if (bPICOEyeTrackerSupported && IOpenXRHMDModule::Get().IsExtensionEnabled(XR_EXT_EYE_GAZE_INTERACTION_EXTENSION_NAME))
	{
		XrSystemEyeGazeInteractionPropertiesEXT EyeGazeInteractionProperties = { XR_TYPE_SYSTEM_EYE_GAZE_INTERACTION_PROPERTIES_EXT };
		XrSystemProperties SystemProperties = { XR_TYPE_SYSTEM_PROPERTIES, &EyeGazeInteractionProperties };
		XR_ENSURE(xrGetSystemProperties(InInstance, InSystem, &SystemProperties));
		bPICOEyeTrackerSupported = EyeGazeInteractionProperties.supportsEyeGazeInteraction == XR_TRUE;
	}

       RefreshActiveEyeTrackerBackend();
	UE_LOG(
			PICOOpenXRMovement,
			Log,
		       TEXT("EyeTracking backend selection after PostGetSystem: XR_EXT_system_extensions=%d, BD_available=%d, PICO_supported=%d, ActiveBackend=%d"),
			bSystemExtensionsEnabled ? 1 : 0,
			bBDEyeTrackerSupported ? 1 : 0,
			bPICOEyeTrackerSupported ? 1 : 0,
			static_cast<int32>(ActiveEyeTrackerBackend));
}

void FEyeTrackingPICO::PostCreateSession(XrSession InSession)
{
	Session = InSession;
	EyeTrackerBD = XR_NULL_HANDLE;
	EyeTrackerPICO = XR_NULL_HANDLE;
	bIsEyeTrackingRunning = false;
	DisplayTime = 0;
	TrackingSpace = XR_NULL_HANDLE;

	RefreshActiveEyeTrackerBackend();
	UE_LOG(
		PICOOpenXRMovement,
		Log,
		TEXT("EyeTracking backend selection after PostCreateSession: BD_available=%d, BD_session_enabled=%d, PICO_supported=%d, ActiveBackend=%d"),
		bBDEyeTrackerSupported ? 1 : 0,
		UHMDFunctionLibraryPICO::IsSystemExtensionEnabledForActiveSystemPICO(XR_BD_EYE_TRACKER_EXTENSION_NAME) ? 1 : 0,
		bPICOEyeTrackerSupported ? 1 : 0,
		static_cast<int32>(ActiveEyeTrackerBackend));
}

void FEyeTrackingPICO::OnDestroySession(XrSession InSession)
{
	if (InSession != Session)
	{
		return;
	}

	if (EyeTrackerBD != XR_NULL_HANDLE || EyeTrackerPICO != XR_NULL_HANDLE)
	{
		StopEyeTracking();
	}

	EyeTrackerBD = XR_NULL_HANDLE;
	EyeTrackerPICO = XR_NULL_HANDLE;
	bIsEyeTrackingRunning = false;
	Session = XR_NULL_HANDLE;
	DisplayTime = 0;
	TrackingSpace = XR_NULL_HANDLE;
	ActiveEyeTrackerBackend = EEyeTrackerBackend::None;
	bIsEyeTrackerSupported = false;
}

const void* FEyeTrackingPICO::OnBeginSession(XrSession InSession, const void* InNext)
{
	static FName SystemName(TEXT("OpenXR"));
	if (GEngine->XRSystem.IsValid() && (GEngine->XRSystem->GetSystemName() == SystemName))
	{
		XRTrackingSystem = GEngine->XRSystem.Get();
	}
	return InNext;
}

void FEyeTrackingPICO::UpdateDeviceLocations(XrSession InSession, XrTime InDisplayTime, XrSpace InTrackingSpace)
{
	if (InSession != Session)
	{
		return;
	}

	this->DisplayTime = InDisplayTime;
	this->TrackingSpace = InTrackingSpace;
}

bool FEyeTrackingPICO::StartEyeTracking()
{
	if (bIsEyeTrackingRunning &&
			((ActiveEyeTrackerBackend == EEyeTrackerBackend::BD && EyeTrackerBD != XR_NULL_HANDLE) ||
			(ActiveEyeTrackerBackend == EEyeTrackerBackend::PICO && EyeTrackerPICO != XR_NULL_HANDLE)))
	{
		return true;
	}

	if (Session == XR_NULL_HANDLE || !bIsEyeTrackerSupported)
	{
		return false;
	}

	if (ActiveEyeTrackerBackend == EEyeTrackerBackend::BD && xrCreateEyeTrackerBD != nullptr)
	{
		UE_LOG(PICOOpenXRMovement, Log, TEXT("Start EyeTracking with XR_BD_eye_tracker."));
		XrEyeTrackerCreateInfoBD EyeTrackerCreateInfoBD = { XR_TYPE_EYE_TRACKER_CREATE_INFO_BD };
		XrResult Result = xrCreateEyeTrackerBD(Session, &EyeTrackerCreateInfoBD, &EyeTrackerBD);
		if (XR_SUCCEEDED(Result) && EyeTrackerBD != XR_NULL_HANDLE)
		{
			bIsEyeTrackingRunning = true;
			return true;
		}

		UE_LOG(PICOOpenXRMovement, Warning, TEXT("xrCreateEyeTrackerBD failed: %d"), static_cast<int32>(Result));
		EyeTrackerBD = XR_NULL_HANDLE;
	       bBDEyeTrackerSupported = false;
		if (!bPICOEyeTrackerSupported)
		{
		       RefreshActiveEyeTrackerBackend();
			return false;
		}

		UE_LOG(PICOOpenXRMovement, Log, TEXT("Falling back to XR_PICO_eye_tracker after XR_BD_eye_tracker create failure."));
		ActiveEyeTrackerBackend = EEyeTrackerBackend::PICO;
	       bIsEyeTrackerSupported = true;
	}

	if (ActiveEyeTrackerBackend == EEyeTrackerBackend::PICO && xrCreateEyeTrackerPICO != nullptr)
	{
		UE_LOG(PICOOpenXRMovement, Log, TEXT("Start EyeTracking with XR_PICO_eye_tracker."));
		XrEyeTrackerCreateInfoPICO EyeTrackerCreateInfoPICO = { XR_TYPE_EYE_TRACKER_CREATE_INFO_PICO };
		XrResult Result = xrCreateEyeTrackerPICO(Session, &EyeTrackerCreateInfoPICO, &EyeTrackerPICO);
		if (XR_SUCCEEDED(Result) && EyeTrackerPICO != XR_NULL_HANDLE)
		{
			bIsEyeTrackingRunning = true;
			return true;
		}

		UE_LOG(PICOOpenXRMovement, Warning, TEXT("xrCreateEyeTrackerPICO failed: %d"), static_cast<int32>(Result));
		EyeTrackerPICO = XR_NULL_HANDLE;
	}

	return false;
}

bool FEyeTrackingPICO::StopEyeTracking()
{
	if (EyeTrackerBD == XR_NULL_HANDLE && EyeTrackerPICO == XR_NULL_HANDLE)
	{
		bIsEyeTrackingRunning = false;
		return true;
	}

	if (EyeTrackerBD != XR_NULL_HANDLE && xrDestroyEyeTrackerBD != nullptr)
	{
		UE_LOG(PICOOpenXRMovement, Log, TEXT("Stop EyeTracking XR_BD_eye_tracker."));
		XrResult Result = xrDestroyEyeTrackerBD(EyeTrackerBD);
		if (XR_SUCCEEDED(Result))
		{
			EyeTrackerBD = XR_NULL_HANDLE;
			bIsEyeTrackingRunning = false;
			return true;
		}

		UE_LOG(PICOOpenXRMovement, Warning, TEXT("xrDestroyEyeTrackerBD failed: %d"), static_cast<int32>(Result));
		return false;
	}

	if (EyeTrackerPICO != XR_NULL_HANDLE && xrDestroyEyeTrackerPICO != nullptr)
	{
		UE_LOG(PICOOpenXRMovement, Log, TEXT("Stop EyeTracking XR_PICO_eye_tracker."));
		XrResult Result = xrDestroyEyeTrackerPICO(EyeTrackerPICO);
		if (XR_SUCCEEDED(Result))
		{
			EyeTrackerPICO = XR_NULL_HANDLE;
			bIsEyeTrackingRunning = false;
			return true;
		}

		UE_LOG(PICOOpenXRMovement, Warning, TEXT("xrDestroyEyeTrackerPICO failed: %d"), static_cast<int32>(Result));
		return false;
	}

	return false;
}

bool FEyeTrackingPICO::GetEyeTrackingData(FEyeDataPICO& LeftEye, FEyeDataPICO& RightEye, bool& bDepthValid, float& DepthConfidence, float& Depth, bool QueryGazeData, FEyeTrackerGazeData& OutGazeData)
{
	bDepthValid = false;
	DepthConfidence = 0.0f;
	Depth = 0.0f;
	OutGazeData = FEyeTrackerGazeData();

	if (bIsEyeTrackingRunning && XRTrackingSystem && TrackingSpace != XR_NULL_HANDLE && ActiveEyeTrackerBackend == EEyeTrackerBackend::BD && xrGetEyeDataBD != nullptr && xrGetEyeGazeBD != nullptr)
	{
		XrEyeTrackerDataBD EyeTrackingData = { XR_TYPE_EYE_TRACKER_DATA_BD };
		EyeTrackingData.next = nullptr;
		EyeTrackingData.leftEyeData.type = XR_TYPE_EYE_DATA_BD;
		EyeTrackingData.leftEyeData.next = nullptr;
		EyeTrackingData.rightEyeData.type = XR_TYPE_EYE_DATA_BD;
		EyeTrackingData.rightEyeData.next = nullptr;

		XrEyeTrackerDataInfoBD EyeTrackerDataInfo = { XR_TYPE_EYE_TRACKER_DATA_INFO_BD };
		XrResult Result = xrGetEyeDataBD(EyeTrackerBD, &EyeTrackerDataInfo, &EyeTrackingData);
		bool bOpennessValid = LeftEye.bOpennessValid = RightEye.bOpennessValid = XR_SUCCEEDED(Result);
		if (bOpennessValid)
		{
			LeftEye.Openness = EyeTrackingData.leftEyeData.openness == XR_TRUE ? 1.0f : 0.0f;
			RightEye.Openness = EyeTrackingData.rightEyeData.openness == XR_TRUE ? 1.0f : 0.0f;
		}

		XrEyeTrackerGazeInfoBD EyeTrackerGazeInfoBD = { XR_TYPE_EYE_TRACKER_GAZE_INFO_BD };
		EyeTrackerGazeInfoBD.baseSpace = TrackingSpace;
		EyeTrackerGazeInfoBD.time = DisplayTime;
		EyeTrackerGazeInfoBD.flags = XR_EYE_TRACKER_LEFT_BIT_BD | XR_EYE_TRACKER_RIGHT_BIT_BD;

		XrEyeTrackerGazeBD EyeGazeBD = { XR_TYPE_EYE_TRACKER_GAZE_BD };
		EyeGazeBD.next = nullptr;
		EyeGazeBD.leftEyeGaze.type = XR_TYPE_EYE_GAZE_BD;
		EyeGazeBD.leftEyeGaze.next = nullptr;
		EyeGazeBD.rightEyeGaze.type = XR_TYPE_EYE_GAZE_BD;
		EyeGazeBD.rightEyeGaze.next = nullptr;

		Result = xrGetEyeGazeBD(EyeTrackerBD, &EyeTrackerGazeInfoBD, &EyeGazeBD);
		if (XR_SUCCEEDED(Result))
		{
			FTransform LeftEyeTransform;
			LeftEye.bPoseValid = TryGetWorldEyeTransform(XRTrackingSystem, EyeGazeBD.leftEyeGaze, LeftEyeTransform);
			if (LeftEye.bPoseValid)
			{
				LeftEye.Location = LeftEyeTransform.GetLocation();
				LeftEye.Rotation = LeftEyeTransform.GetRotation().Rotator();
			}

			FTransform RightEyeTransform;
			RightEye.bPoseValid = TryGetWorldEyeTransform(XRTrackingSystem, EyeGazeBD.rightEyeGaze, RightEyeTransform);
			if (RightEye.bPoseValid)
			{
				RightEye.Location = RightEyeTransform.GetLocation();
				RightEye.Rotation = RightEyeTransform.GetRotation().Rotator();
			}

			if (QueryGazeData)
			{
				return PopulateCombinedGazeData(
					LeftEye.bPoseValid ? &LeftEyeTransform : nullptr,
					RightEye.bPoseValid ? &RightEyeTransform : nullptr,
					LeftEye,
					RightEye,
					OutGazeData);
			}

			return true;
		}

		LeftEye.bPoseValid = RightEye.bPoseValid = false;
	}
	else if (bIsEyeTrackingRunning && XRTrackingSystem && TrackingSpace != XR_NULL_HANDLE && ActiveEyeTrackerBackend == EEyeTrackerBackend::PICO && xrGetEyeDataPICO != nullptr && xrGetEyeGazePICO != nullptr)
	{
		XrEyeTrackerDataPICO EyeTrackingData = { XR_TYPE_EYE_TRACKER_DATA_PICO };
		EyeTrackingData.leftEyeData.type = XR_TYPE_EYE_DATA_PICO;
		EyeTrackingData.rightEyeData.type = XR_TYPE_EYE_DATA_PICO;

		XrEyeTrackerDataInfoPICO EyeTrackerDataInfo = { XR_TYPE_EYE_TRACKER_DATA_INFO_PICO };
		XrResult Result = xrGetEyeDataPICO(EyeTrackerPICO, &EyeTrackerDataInfo, &EyeTrackingData);
		bool bOpennessValid = LeftEye.bOpennessValid = RightEye.bOpennessValid = XR_SUCCEEDED(Result);
		if (bOpennessValid)
		{
			LeftEye.Openness = EyeTrackingData.leftEyeData.openness;
			RightEye.Openness = EyeTrackingData.rightEyeData.openness;
		}

		XrEyeTrackerGazeInfoPICO EyeTrackerGazeInfoPICO = { XR_TYPE_EYE_TRACKER_GAZE_INFO_PICO };
		EyeTrackerGazeInfoPICO.baseSpace = TrackingSpace;
		EyeTrackerGazeInfoPICO.time = DisplayTime;
		EyeTrackerGazeInfoPICO.flags = XR_EYE_TRACKER_LEFT_BIT_PICO | XR_EYE_TRACKER_RIGHT_BIT_PICO;

		XrEyeTrackerGazeDepthPICO EyeGazeDepthPICO = { XR_TYPE_EYE_TRACKER_GAZE_DEPTH_PICO };
		XrEyeTrackerGazePICO EyeGazePICO = { XR_TYPE_EYE_TRACKER_GAZE_PICO, &EyeGazeDepthPICO };

		Result = xrGetEyeGazePICO(EyeTrackerPICO, &EyeTrackerGazeInfoPICO, &EyeGazePICO);
		if (XR_SUCCEEDED(Result))
		{
			FTransform LeftEyeTransform;
			LeftEye.bPoseValid = TryGetWorldEyeTransform(XRTrackingSystem, EyeGazePICO.leftEyeGaze, LeftEyeTransform);
			if (LeftEye.bPoseValid)
			{
				LeftEye.Location = LeftEyeTransform.GetLocation();
				LeftEye.Rotation = LeftEyeTransform.GetRotation().Rotator();
			}

			FTransform RightEyeTransform;
			RightEye.bPoseValid = TryGetWorldEyeTransform(XRTrackingSystem, EyeGazePICO.rightEyeGaze, RightEyeTransform);
			if (RightEye.bPoseValid)
			{
				RightEye.Location = RightEyeTransform.GetLocation();
				RightEye.Rotation = RightEyeTransform.GetRotation().Rotator();
			}

			bDepthValid = EyeGazeDepthPICO.isValid == XR_TRUE;
			if (bDepthValid)
			{
				DepthConfidence = EyeGazeDepthPICO.depthConfidence;
				Depth = EyeGazeDepthPICO.gazeDepth * XRTrackingSystem->GetWorldToMetersScale();
			}

			if (QueryGazeData)
			{
				return PopulateCombinedGazeData(
						LeftEye.bPoseValid ? &LeftEyeTransform : nullptr,
						RightEye.bPoseValid ? &RightEyeTransform : nullptr,
						LeftEye,
						RightEye,
						OutGazeData);
			}

			return true;
		}

		LeftEye.bPoseValid = RightEye.bPoseValid = false;
	}

	return false;
}
